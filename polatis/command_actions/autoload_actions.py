#!/usr/bin/python
# -*- coding: utf-8 -*-
import re

import polatis.command_templates.autoload as command_template
from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor


class AutoloadActions(object):
    """
    Autoload actions
    """

    def __init__(self, cli_service, logger):
        """
        :param cli_service: default mode cli_service
        :type cli_service: CliService
        :param logger:
        :type logger: Logger
        :return:
        """
        self._cli_service = cli_service
        self._logger = logger

    def get_switch_serial(self):
        """ Determine Polatis Switch serial number """

        output = CommandTemplateExecutor(self._cli_service, command_template.PSERIAL).execute_command()
        match = re.search(r"SN=(?P<serial>\w+)", output)
        if match:
            serial = match.groupdict()["serial"]
        else:
            self._logger.warn("Failed to extract serial number: {}".format(output))
            serial = "-1"

        return serial

    def get_switch_details(self):
        """ Determine Polatis Switch detailed information like vendor, type, version, model """

        output = CommandTemplateExecutor(self._cli_service, command_template.NETYPE).execute_command()
        match = re.search(r'"(?P<vendor>.*),(?P<model>.*),(?P<type>.*),(?P<version>.*)"', output)
        if not match:
            match = re.search(r'(?P<vendor>.*),(?P<model>.*),(?P<type>.*),(?P<version>.*)', output)

        if match:
            return {"Vendor": match.groupdict()["vendor"],
                    "Hardware Type": match.groupdict()["type"],
                    "Version": match.groupdict()["version"],
                    "Model": match.groupdict()["model"]}
        else:
            self._logger.error("Unable to parse system info: {}".format(output))

    def get_connections(self, logical_ports_count, is_logical=False):
        """ Determine Polatis Switch connections """

        conn_info = {}
        output = CommandTemplateExecutor(self._cli_service, command_template.PATCH).execute_command()
        for src, dst in re.findall(r'"(\d+),(\d+)"', output):
            conn_info.update({int(src): int(dst), int(dst): int(src)})

        if is_logical:
            conn_info_fixed = {}
            for src, dst in conn_info.items():
                if src > logical_ports_count:
                    conn_info_fixed[src - logical_ports_count] = dst
                elif dst > logical_ports_count:
                    conn_info_fixed[dst - logical_ports_count] = src

                conn_info = conn_info_fixed
        
        return conn_info

    def get_port_status(self, size):
        """ Determine ports status """

        port_status = {}
        try:
            output = CommandTemplateExecutor(self._cli_service, command_template.SHUTTERS).execute_command(size=size)
            for port, status in re.findall(r'"(?P<port>\d+):(?P<status>\S+)"', output):
                port_status[int(port)] = status
        finally:
            return port_status

    def get_port_power(self, ports_count):
        """ Determine ports power """

        port_power = {}
        try:
            output = CommandTemplateExecutor(self._cli_service, command_template.POWER).execute_command(size=ports_count)
            for port, power in re.findall(r'"(?P<port>\d+):(?P<power>\S+)"', output):
                port_power[int(port)] = power
        finally:
            return port_power

    def get_port_wavelength(self, ports_count):
        """ Determine ports wavelength """

        port_wavelength = {}
        try:
            output = CommandTemplateExecutor(self._cli_service, command_template.WAVE).execute_command(size=ports_count)
            for port, wave in re.findall(r'"(?P<port>\d+):(?P<wave>\S+?),.*"', output):
                port_wavelength[int(port)] = wave
        finally:
            return port_wavelength
