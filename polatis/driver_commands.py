#!/usr/bin/python
# -*- coding: utf-8 -*-

from cloudshell.layer_one.core.driver_commands_interface import DriverCommandsInterface
from cloudshell.layer_one.core.response.response_info import ResourceDescriptionResponseInfo, GetStateIdResponseInfo, \
    AttributeValueResponseInfo
from cloudshell.layer_one.core.response.resource_info.entities.chassis import Chassis
from cloudshell.layer_one.core.response.resource_info.entities.port import Port

from polatis.command_actions.autoload_actions import AutoloadActions
from polatis.command_actions.mapping_actions import MappingActions
from polatis.command_actions.system_actions import SystemActions

from polatis.cli.polatis_cli_handler import PolatisCliHandler


class DriverCommands(DriverCommandsInterface):
    """ Driver commands implementation """
    LOGICAL_PORT_MODE = "LOGICAL"

    def __init__(self, logger, runtime_config):
        """
        :type logger: logging.Logger
        :type runtime_config: cloudshell.layer_one.core.helper.runtime_configuration.RuntimeConfiguration
        """

        self._logger = logger
        self._runtime_config = runtime_config
        self._driver_port_mode = runtime_config.read_key('DRIVER.PORT_MODE', self.LOGICAL_PORT_MODE)
        self._cli_handler = PolatisCliHandler(logger)
        self.total_ports_count = None
        self.logical_ports_count = None

    @property
    def _is_logical_port_mode(self):
        return self._driver_port_mode.lower() == self.LOGICAL_PORT_MODE.lower()

    def _get_device_size(self, session):
        """ Determine ports count
        return: total ports count and logical port count
        rtype: tuple
        """

        if not self.total_ports_count or not self.logical_ports_count:
            system_actions = SystemActions(session, self._logger)
            size1, size2 = system_actions.get_device_size()

            self.total_ports_count = size1 + size2
            self.logical_ports_count = min(size1, size2)

        return self.total_ports_count, self.logical_ports_count

    def login(self, address, username, password):
        """
        Perform login operation on the device
        :param address: resource address, "192.168.42.240"
        :param username: username to login on the device
        :param password: password
        :return: None
        :raises Exception: if command failed
        Example:
            # Define session attributes
            self._cli_handler.define_session_attributes(address, username, password)

            # Obtain cli session
            with self._cli_handler.default_mode_service() as session:
                # Executing simple command
                device_info = session.send_command('show version')
                self._logger.info(device_info)
        """

        self._cli_handler.define_session_attributes(address, username, password)
        with self._cli_handler.default_mode_service() as session:
            actions = AutoloadActions(session, self._logger)
            self._logger.info(actions.get_switch_serial())

    def get_resource_description(self, address):
        """ Auto-load function to retrieve all information from the device
        :param address: resource address, '192.168.42.240'
        :type address: str
        :return: resource description
        :rtype: cloudshell.layer_one.core.response.response_info.ResourceDescriptionResponseInfo
        :raises cloudshell.layer_one.core.layer_one_driver_exception.LayerOneDriverException: Layer one exception.

        Example:

            from cloudshell.layer_one.core.response.resource_info.entities.chassis import Chassis
            from cloudshell.layer_one.core.response.resource_info.entities.blade import Blade
            from cloudshell.layer_one.core.response.resource_info.entities.port import Port

            chassis_resource_id = chassis_info.get_id()
            chassis_address = chassis_info.get_address()
            chassis_model_name = "Polatis Chassis"
            chassis_serial_number = chassis_info.get_serial_number()
            chassis = Chassis(resource_id, address, model_name, serial_number)

            blade_resource_id = blade_info.get_id()
            blade_model_name = 'Generic L1 Module'
            blade_serial_number = blade_info.get_serial_number()
            blade.set_parent_resource(chassis)

            port_id = port_info.get_id()
            port_serial_number = port_info.get_serial_number()
            port = Port(port_id, 'Generic L1 Port', port_serial_number)
            port.set_parent_resource(blade)

            return ResourceDescriptionResponseInfo([chassis])
        """

        with self._cli_handler.default_mode_service() as session:
            autoload_actions = AutoloadActions(session, self._logger)

            serial_number = autoload_actions.get_switch_serial()
            switch_details = autoload_actions.get_switch_details()

            chassis = Chassis("", address, "Polatis Chassis", serial_number)
            chassis.set_model_name(switch_details["Model"])
            chassis.set_os_version(switch_details["Version"])
            chassis.set_serial_number(serial_number)

            total_ports_count, logical_ports_count = self._get_device_size(session=session)

            connections = autoload_actions.get_connections(logical_ports_count=logical_ports_count,
                                                           is_logical=self._is_logical_port_mode)

            ports_power = autoload_actions.get_port_power(ports_count=total_ports_count)
            ports_wavelength = autoload_actions.get_port_wavelength(ports_count=total_ports_count)

            self._logger.debug("PORT MODE: {}".format(self._is_logical_port_mode))

            ports = {}
            ports_len = len(str(total_ports_count))
            for port_addr in range(1, (logical_ports_count if self._is_logical_port_mode else total_ports_count) + 1):

                port_serial = "{sw_serial}.{port_addr}".format(sw_serial=serial_number, port_addr=port_addr)
                port_id = "{:0{}d}".format(port_addr, ports_len)
                self._logger.debug("Port id : {}".format(port_id))
                port = Port(port_id, "Generic L1 Port", port_serial)

                ports[port_addr] = port
                port.set_parent_resource(chassis)
                port.set_wavelength(ports_wavelength.get(port_addr, 0))

                if self._is_logical_port_mode:
                    port.set_tx_power(ports_power.get(port_addr, 0))
                    port.set_rx_power(ports_power.get(port_addr + logical_ports_count, 0))
                else:
                    port_power = ports_power.get(port_addr, 0)
                    if port_addr <= logical_ports_count:
                        port.set_tx_power(port_power)
                    else:
                        port.set_rx_power(port_power)

            for src_address, dst_address in connections.iteritems():
                src_port = ports.get(src_address)
                dst_port = ports.get(dst_address)
                src_port.add_mapping(dst_port)

            return ResourceDescriptionResponseInfo([chassis])

    def map_uni(self, src_port, dst_ports):
        """ Unidirectional mapping of two ports
        :param src_port: src port address, '192.168.42.240/1/21'
        :type src_port: str
        :param dst_ports: list of dst ports addresses, ['192.168.42.240/1/22', '192.168.42.240/1/23']
        :type dst_ports: list
        :return: None
        :raises Exception: if command failed
        """

        if self._is_logical_port_mode:
            with self._cli_handler.default_mode_service() as session:
                mapping_actions = MappingActions(session, self._logger)

                _, logical_ports_count = self._get_device_size(session=session)

                src = int(src_port.split('/')[-1]) + logical_ports_count
                for dst_port in dst_ports:
                    dst = int(dst_port.split('/')[-1])
                    mapping_actions.map_uni(src, dst)

        else:
            raise Exception("Unidirectional connection is not available in physical port mode")

    def map_bidi(self, src_port, dst_port):
        """ Create a bidirectional connection between source and destination ports
        :param src_port: src port address, '192.168.42.240/1/21'
        :type src_port: str
        :param dst_port: dst port address, '192.168.42.240/1/22'
        :type dst_port: str
        :return: None
        :raises Exception: if command failed
        """

        with self._cli_handler.default_mode_service() as session:
            mapping_actions = MappingActions(session, self._logger)

            src = int(src_port.split('/')[-1])
            dst = int(dst_port.split('/')[-1])

            total_ports_count, logical_ports_count = self._get_device_size(session=session)

            if self._is_logical_port_mode:
                for a, b in [(dst, src), (src, dst)]:
                    b += logical_ports_count
                    # lower number must be the first in the command
                    mapping_actions.map_uni(src_port=b, dst_port=a)
                    # self._connection.command("ENT-PATCH:{name}:%d,%d:{counter}:;" % (a, b))
            else:
                mapping_actions.map_uni(src_port=max(src, dst), dst_port=min(src, dst))

    def map_clear_to(self, src_port, dst_ports):
        """ Remove simplex/multi-cast/duplex connection ending on the destination port
        :param src_port: src port address, '192.168.42.240/1/21'
        :type src_port: str
        :param dst_ports: list of dst ports addresses, ['192.168.42.240/1/21', '192.168.42.240/1/22']
        :type dst_ports: list
        :return: None
        :raises Exception: if command failed
        """

        with self._cli_handler.default_mode_service() as session:
            mapping_actions = MappingActions(session, self._logger)
            src = int(src_port.split('/')[-1])
            for dst_port in dst_ports:
                dst = int(dst_port.split('/')[-1])

                if self._is_logical_port_mode:
                    port = dst
                else:
                    port = min(src, dst)
                mapping_actions.map_clear_to(port=port)

    def map_clear(self, ports):
        """
        Remove simplex/multi-cast/duplex connection ending on the destination port
        :param ports: ports, ['192.168.42.240/1/21', '192.168.42.240/1/22']
        :type ports: list
        :return: None
        :raises Exception: if command failed

        Example:
            exceptions = []
            with self._cli_handler.config_mode_service() as session:
                for port in ports:
                    try:
                        session.send_command('map clear {}'.format(convert_port(port)))
                    except Exception as e:
                        exceptions.append(str(e))
                if exceptions:
                    raise Exception('self.__class__.__name__', ','.join(exceptions))
        """

        with self._cli_handler.default_mode_service() as session:
            mapping_actions = MappingActions(session, self._logger)
            for port in ports:
                port = int(port.split('/')[-1])
                if self._is_logical_port_mode:
                    total_ports_count, logical_ports_count = self._get_device_size(session=session)

                    mapping_actions.map_clear(ports=[port, port + logical_ports_count])

                else:
                    mapping_actions.map_clear_to(port=port)

    def map_tap(self, src_port, dst_ports):
        """
        Add TAP connection
        :param src_port: port to monitor '192.168.42.240/1/21'
        :type src_port: str
        :param dst_ports: ['192.168.42.240/1/22', '192.168.42.240/1/23']
        :type dst_ports: list
        :return: None
        :raises Exception: if command failed

        Example:
            return self.map_uni(src_port, dst_ports)
        """
        raise NotImplementedError

    def set_speed_manual(self, src_port, dst_port, speed, duplex):
        """
        Set connection speed. It is not used with new standard
        :param src_port:
        :param dst_port:
        :param speed:
        :param duplex:
        :return:
        """
        raise NotImplementedError

    def get_attribute_value(self, cs_address, attribute_name):
        """
        Retrieve attribute value from the device
        :param cs_address: address, '192.168.42.240/1/21'
        :type cs_address: str
        :param attribute_name: attribute name, "Port Speed"
        :type attribute_name: str
        :return: attribute value
        :rtype: cloudshell.layer_one.core.response.response_info.AttributeValueResponseInfo
        :raises Exception: if command failed

        Example:
            with self._cli_handler.config_mode_service() as session:
                command = AttributeCommandFactory.get_attribute_command(cs_address, attribute_name)
                value = session.send_command(command)
                return AttributeValueResponseInfo(value)
        """
        raise NotImplementedError

    def set_attribute_value(self, cs_address, attribute_name, attribute_value):
        """
        Set attribute value to the device
        :param cs_address: address, '192.168.42.240/1/21'
        :type cs_address: str
        :param attribute_name: attribute name, "Port Speed"
        :type attribute_name: str
        :param attribute_value: value, "10000"
        :type attribute_value: str
        :return: attribute value
        :rtype: cloudshell.layer_one.core.response.response_info.AttributeValueResponseInfo
        :raises Exception: if command failed

        Example:
            with self._cli_handler.config_mode_service() as session:
                command = AttributeCommandFactory.set_attribute_command(cs_address, attribute_name, attribute_value)
                session.send_command(command)
                return AttributeValueResponseInfo(attribute_value)
        """
        raise NotImplementedError

    def get_state_id(self):
        """
        Check if CS synchronized with the device.
        :return: Synchronization ID, GetStateIdResponseInfo(-1) if not used
        :rtype: cloudshell.layer_one.core.response.response_info.GetStateIdResponseInfo
        :raises Exception: if command failed

        Example:
            # Obtain cli session
            with self._cli_handler.default_mode_service() as session:
                # Execute command
                chassis_name = session.send_command('show chassis name')
                return chassis_name
        """

        self._logger.info("Command 'get state id' called")
        return GetStateIdResponseInfo("-1")

    def set_state_id(self, state_id):
        """
        Set synchronization state id to the device, called after Autoload or SyncFomDevice commands
        :param state_id: synchronization ID
        :type state_id: str
        :return: None
        :raises Exception: if command failed

        Example:
            # Obtain cli session
            with self._cli_handler.config_mode_service() as session:
                # Execute command
                session.send_command('set chassis name {}'.format(state_id))
        """

        self._logger.info('set_state_id {}'.format(state_id))
        # raise NotImplementedError
