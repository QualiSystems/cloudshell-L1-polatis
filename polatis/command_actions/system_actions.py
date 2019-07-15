#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import polatis.command_templates.system as command_template
from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor


class SystemActions(object):
    """System actions"""

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

    def get_device_size(self):
        """
        Device info
        :return:
        """

        output = CommandTemplateExecutor(self._cli_service, command_template.DEVICE_EQPT).execute_command()
        match = re.search(r"SYSTEM:SIZE=(?P<size1>\d+)x(?P<size2>\d+)", output)
        if match:
            size1 = int(match.groupdict()['size1'])
            size2 = int(match.groupdict()['size2'])
            return size1, size2
        else:
            raise Exception('Unable to determine system size: %s' % output)
