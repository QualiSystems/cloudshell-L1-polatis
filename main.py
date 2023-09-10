from __future__ import annotations

import importlib
import os
import sys
from datetime import datetime

from cloudshell.layer_one.core.command_executor import CommandExecutor
from cloudshell.layer_one.core.driver_listener import DriverListener
from cloudshell.layer_one.core.helper.runtime_configuration import RuntimeConfiguration
from cloudshell.layer_one.core.helper.xml_logger import XMLLogger
from cloudshell.logging.qs_logger import get_qs_logger, set_log_level


class Main:
    def __init__(
        self,
        file_path: str | None = None,
        port: int | None = 1024,
        log_path: str | None = None,
    ):
        self._driver_path = os.path.dirname(file_path or sys.argv[0])
        self._port = port
        self._log_path = log_path or os.path.join(self._driver_path, "..", "Logs")
        os.environ["LOG_PATH"] = self._log_path

    def run_driver(self, driver_name: str):
        # Reading runtime configuration
        runtime_config = RuntimeConfiguration(
            os.path.join(self._driver_path, f"{driver_name}_runtime_config.yml")
        )

        # Creating XMl logger instance
        xml_file_name = (
            f"{driver_name}--{datetime.now().strftime('%d-%b-%Y--%H-%M-%S')}.xml"
        )
        xml_logger = XMLLogger(os.path.join(self._log_path, driver_name, xml_file_name))

        # Creating command logger instance
        command_logger = get_qs_logger(
            log_group=driver_name,
            log_file_prefix=f"{driver_name}_commands",
            use_context=False,
        )
        log_level = runtime_config.read_key("LOGGING.LEVEL", "INFO")
        set_log_level(command_logger, log_level)

        command_logger.info(
            f"Starting driver {driver_name} on port {self._port}, PID: {os.getpid()}"
        )

        # Importing and creating driver commands instance
        driver_commands = importlib.import_module(
            f"{driver_name.replace('-', '_')}.driver_commands", package=None
        )
        driver_instance = driver_commands.DriverCommands(runtime_config)

        # Creating command executor instance
        command_executor = CommandExecutor(driver_instance)

        # Creating listener instance
        server = DriverListener(command_executor, xml_logger)

        # Start listening
        server.start_listening(port=self._port)


if __name__ == "__main__":
    Main(*sys.argv).run_driver("polatis")
