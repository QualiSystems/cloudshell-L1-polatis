#!/usr/bin/python
# -*- coding: utf-8 -*-

import polatis.command_templates.mapping as command_template
from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor


class MappingActions(object):
    def __init__(self, cli_service, logger):
        """ Mapping actions
        :param cli_service: default mode cli_service
        :type cli_service: CliService
        :param logger:
        :type logger: Logger
        :return:
        """
        self._cli_service = cli_service
        self._logger = logger

    def map_uni(self, src_port, dst_port):
        """ Unidirectional mapping
        :param src_port:
        :param dst_ports:
        :return:
        """

        executor = CommandTemplateExecutor(self._cli_service, command_template.PORT_MAP)
        output = executor.execute_command(src_port=src_port, dst_port=dst_port)
        return output

    def map_clear_to(self, port):
        """ Clear unidirectional mapping
        :param port:
        :return: 
        """

        executor = CommandTemplateExecutor(self._cli_service, command_template.MAP_CLEAR)
        output = executor.execute_command(port=port)
        return output

    def map_clear(self, ports):
        """ Clear bidirectional mapping
        :param ports:
        :return:
        """

        port = "&".join(ports)

        executor = CommandTemplateExecutor(self._cli_service, command_template.MAP_CLEAR)
        output = executor.execute_command(port=port)
        return output