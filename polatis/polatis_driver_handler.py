#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from common.configuration_parser import ConfigurationParser
from common.driver_handler_base import DriverHandlerBase
from common.resource_info import ResourceInfo


class PolatisDriverHandler(DriverHandlerBase):
    def __init__(self):
        DriverHandlerBase.__init__(self)

        self._ctag = 1
        self._switch_name = ''
        self._mapping_info = dict()

        self._resource_info = None

        self._service_mode = ConfigurationParser.get("driver_variable", "service_mode")

    def _incr_ctag(self):
        self._ctag += 1
        return self._ctag

    def login(self, address, username, password, command_logger=None):
        self._session.connect(address, username, password, port=None)

        if self._service_mode.lower() == "scpi":
            pass
        elif self._service_mode.lower() == "tl1":
            command = 'ACT-USER::{0}:1::{1};'.format(username, password)
            command_result = self._session.send_command(command, re_string=self._prompt)
            command_logger.info(command_result)

            command = 'RTRV-HDR:::{0}:;'.format(self._incr_ctag())
            command_result = self._session.send_command(command, re_string=self._prompt)
            command_logger.info(command_result)

            match_result = re.search(r" ([A-Za-z0-9]+) ", command_result)
            if match_result is not None:
                self._switch_name = match_result.group()[1:-1]
        else:
            raise Exception("PolatisDriverHandler", "From service mode type (current mode: '" +
                            self._service_mode + "'!")

    def _get_device_data(self):
        device_data = dict()

        if self._service_mode.lower() == "scpi":
            pass
        elif self._service_mode.lower() == "tl1":
            command = "RTRV-NETYPE:{0}::{1}:;".format(self._switch_name, self._incr_ctag())
            device_data["RTRV-NETYPE"] = self._session.send_command(command, re_string=self._prompt)

            command = "RTRV-EQPT:{0}:SYSTEM:{1}:::PARAMETER=SIZE;".format(self._switch_name, self._incr_ctag())
            device_data["RTRV-EQPT-SIZE"] = self._session.send_command(command, re_string=self._prompt)

            size_match = re.search(r"SYSTEM:SIZE=(?P<src>\d+)x(?P<dst>\d+)", device_data["RTRV-EQPT-SIZE"])

            switch_size = -1
            if size_match is not None:
                size_dict = size_match.groupdict()

                switch_size = int(size_dict["src"]) + int(size_dict["dst"])
            else:
                raise Exception("PolatisDriverHandler", "Can't find 'size' parameter!")

            command = "RTRV-PORT-SHUTTER:{0}:{1}&&{2}:{3}:;".format(self._switch_name, 1, switch_size,
                                                                    self._incr_ctag())
            device_data["RTRV-PORT-SHUTTER"] = self._session.send_command(command, re_string=self._prompt)

            command = "RTRV-PATCH:{0}::{1}:;".format(self._switch_name, self._incr_ctag())
            device_data["RTRV-PATCH"] = self._session.send_command(command, re_string=self._prompt)

            command = "RTRV-INV:{0}:OCS:{1}:;".format(self._switch_name, self._incr_ctag())
            device_data["RTRV-INV-SN"] = self._session.send_command(command, re_string=self._prompt)
        else:
            raise Exception("PolatisDriverHandler", "From service mode type (current mode: '" +
                            self._service_mode + "'!")

        return device_data

    def get_resource_description(self, address, command_logger=None):
        device_data = self._get_device_data()

        self._resource_info = ResourceInfo()
        self._resource_info.set_depth(0)
        self._resource_info.set_index(1)

        self._resource_info.set_address(address)

        if self._service_mode.lower() == "scpi":
            pass
        elif self._service_mode.lower() == "tl1":
            model_info_match = re.search(r"\"*(?P<vendor>.*),(?P<model>.*),(?P<type>.*),(?P<version>\S+)",
                                         device_data["RTRV-NETYPE"])

            # add chassis info
            model_name = ''
            if model_info_match is not None:
                model_info_dict = model_info_match.groupdict()

                self._resource_info.add_attribute("Vendor", model_info_dict["vendor"])
                self._resource_info.add_attribute("Type", model_info_dict["type"])
                self._resource_info.add_attribute("Version", model_info_dict["version"])
                self._resource_info.add_attribute("Model", model_info_dict["model"])

                model_name = model_info_dict["model"]

                self._resource_info.set_model_name(model_info_dict["model"])
            else:
                raise Exception("PolatisDriverHandler", "Can't parse model info!")

            serial_info_match = re.search(r"SN=(?P<serial>\d*)", device_data["RTRV-INV-SN"])
            if serial_info_match is not None:
                serial_info_dict = serial_info_match.groupdict()

                self._resource_info.set_serial_number(serial_info_dict["serial"])
            else:
                raise Exception("PolatisDriverHandler", "Can't parse serial number info!")

            # get port mappings
            address_prefix = address + "/"

            port_map_list = device_data["RTRV-PATCH"].split("\n")

            for port_data in port_map_list:
                port_map_match = re.search(r"(?P<src_port>\d+),(?P<dst_port>\d+)", port_data)

                if port_map_match is not None:
                    port_map_dict = port_map_match.groupdict()

                    src_port = port_map_dict["src_port"]
                    dst_port = port_map_dict["dst_port"]
                    self._mapping_info[src_port] = dst_port
                    self._mapping_info[dst_port] = src_port

            # add port info
            port_list = device_data["RTRV-PORT-SHUTTER"].split("\n")

            for port_data in port_list:
                port_info_match = re.search(r"(?P<id>\d+):(?P<state>OPEN|CLOSED){1}", port_data)

                if port_info_match is not None:
                    port_info_dict = port_info_match.groupdict()

                    port_resource_info = ResourceInfo()
                    port_resource_info.set_depth(1)

                    port_id = port_info_dict["id"]
                    port_resource_info.set_index(port_id)
                    port_resource_info.set_model_name(model_name)

                    if port_id in self._mapping_info:
                        port_resource_info.set_mapping(address_prefix + self._mapping_info[port_id])

                    if port_info_dict["state"].lower() == "open":
                        port_resource_info.add_attribute("State", "Enable")
                    else:
                        port_resource_info.add_attribute("State", "Disable")

                    port_resource_info.add_attribute("Protocol Type", 0)

                    self._resource_info.add_child(port_info_dict["id"], port_resource_info)
        else:
            raise Exception("PolatisDriverHandler", "From service mode type (current mode: '" +
                            self._service_mode + "'!")

        return self._resource_info.convert_to_xml()

    def map_bidi(self, src_port, dst_port, command_logger=None):
        if self._service_mode.lower() == "scpi":
            pass
        elif self._service_mode.lower() == "tl1":

            min_port = min(int(src_port[1]), int(dst_port[1]))
            max_port = max(int(src_port[1]), int(dst_port[1]))

            command = "ENT-PATCH:{0}:{1},{2}:{3}:;".format(self._switch_name, min_port, max_port, self._incr_ctag())

            command_result = self._session.send_command(command, re_string=self._prompt)
            command_logger.info(command_result)

    def map_clear_to(self, src_port, dst_port, command_logger=None):
        if self._service_mode.lower() == "scpi":
            pass
        elif self._service_mode.lower() == "tl1":

            min_port = min(int(src_port[1]), int(dst_port[1]))
            max_port = max(int(src_port[1]), int(dst_port[1]))

            command = "DLT-PATCH:{0}:{1}:{2}:;".format(self._switch_name, min_port, max_port,
                                                       self._incr_ctag())

            self._session.send_command(command, re_string=self._prompt)

    def map_clear(self, src_port, dst_port, command_logger=None):
        if self._service_mode.lower() == "scpi":
            pass
        elif self._service_mode.lower() == "tl1":

            min_port = min(int(src_port[1]), int(dst_port[1]))
            max_port = max(int(src_port[1]), int(dst_port[1]))

            command = "DLT-PATCH:{0}:{1}:{2}:;".format(self._switch_name, min_port, max_port,
                                                       self._incr_ctag())

            self._session.send_command(command, re_string=self._prompt)
