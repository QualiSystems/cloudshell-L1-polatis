#!/usr/bin/python
# -*- coding: utf-8 -*-
import importlib
import os
import sys
from datetime import datetime

from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.layer_one.core.command_executor import CommandExecutor
from cloudshell.layer_one.core.driver_listener import DriverListener
from cloudshell.layer_one.core.helper.runtime_configuration import RuntimeConfiguration
from cloudshell.layer_one.core.helper.xml_logger import XMLLogger


class Main(object):
    def __init__(self, file_path=None, port=1024, log_path=None):
        self._driver_path = os.path.dirname(file_path or sys.argv[0])
        self._port = port
        self._log_path = log_path or os.path.join(self._driver_path, '..', 'Logs')
        os.environ['LOG_PATH'] = self._log_path

    def run_driver(self, driver_name):
        # Reading runtime configuration
        runtime_config = RuntimeConfiguration(
            os.path.join(self._driver_path, driver_name + '_runtime_config.yml'))

        # Creating XMl logger instance
        xml_file_name = driver_name + '--' + datetime.now().strftime('%d-%b-%Y--%H-%M-%S') + '.xml'
        xml_logger = XMLLogger(os.path.join(self._log_path, driver_name, xml_file_name))

        # Creating command logger instance
        command_logger = get_qs_logger(log_group=driver_name,
                                       log_file_prefix=driver_name + '_commands', log_category='COMMANDS')
        log_level = runtime_config.read_key('LOGGING.LEVEL', 'INFO')
        command_logger.setLevel(log_level)

        command_logger.info('Starting driver {0} on port {1}, PID: {2}'.format(driver_name, self._port, os.getpid()))

        # Importing and creating driver commands instance
        driver_commands = importlib.import_module('{}.driver_commands'.format(driver_name), package=None)
        driver_instance = driver_commands.DriverCommands(command_logger, runtime_config)

        # Creating command executor instance
        command_executor = CommandExecutor(driver_instance, command_logger)

        # Creating listener instance
        server = DriverListener(command_executor, xml_logger, command_logger)

        # Start listening
        server.start_listening(port=self._port)


if __name__ == '__main__':
    Main(*sys.argv).run_driver('polatis')
