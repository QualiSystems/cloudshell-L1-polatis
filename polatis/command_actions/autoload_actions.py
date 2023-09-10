from __future__ import annotations

import re
from typing import TYPE_CHECKING

from cloudshell.cli.command_template.command_template_executor import (
    CommandTemplateExecutor,
)
from cloudshell.layer_one.core.helper.logger import get_l1_logger

import polatis.command_templates.autoload as command_template

if TYPE_CHECKING:
    from cloudshell.cli.service.cli_service import CliService

logger = get_l1_logger(name=__name__)


class AutoloadActions:
    """Autoload actions."""

    def __init__(self, cli_service: CliService) -> None:
        self._cli_service = cli_service

    def get_switch_serial(self) -> str:
        """Determine Polatis Switch serial number."""
        output = CommandTemplateExecutor(
            self._cli_service, command_template.PSERIAL
        ).execute_command()
        match = re.search(r"SN=(?P<serial>\w+)", output)
        if match:
            serial = match.groupdict()["serial"]
        else:
            logger.warning(f"Failed to extract serial number: {output}")
            serial = "-1"

        return serial

    def get_switch_details(self) -> dict[str, str]:
        """Determine Polatis Switch detailed information."""
        result = {}
        output = CommandTemplateExecutor(
            self._cli_service, command_template.NETYPE
        ).execute_command()
        match = re.search(
            r'"(?P<vendor>.*),(?P<model>.*),(?P<type>.*),(?P<version>.*)"', output
        )
        if not match:
            match = re.search(
                r"(?P<vendor>.*),(?P<model>.*),(?P<type>.*),(?P<version>.*)", output
            )

        if match:
            result = {
                "Vendor": match.groupdict()["vendor"],
                "Hardware Type": match.groupdict()["type"],
                "Version": match.groupdict()["version"],
                "Model": match.groupdict()["model"],
            }
        else:
            logger.error(f"Unable to parse system info: {output}")

        return result

    def get_connections(
        self, logical_ports_count: int, is_logical: bool = False
    ) -> dict[int, int]:
        """Determine Polatis Switch connections."""
        conn_info = {}
        output = CommandTemplateExecutor(
            self._cli_service, command_template.PATCH
        ).execute_command()
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

    def get_port_status(self, size: int) -> dict[int, str]:
        """Determine ports status."""
        port_status = {}
        try:
            output = CommandTemplateExecutor(
                self._cli_service, command_template.SHUTTERS
            ).execute_command(size=size)
            for port, status in re.findall(r'"(?P<port>\d+):(?P<status>\S+)"', output):
                port_status[int(port)] = status
        finally:
            return port_status

    def get_port_power(self, ports_count: int) -> dict[int, str]:
        """Determine ports power."""
        port_power = {}
        try:
            output = CommandTemplateExecutor(
                self._cli_service, command_template.POWER
            ).execute_command(size=ports_count)
            for port, power in re.findall(r'"(?P<port>\d+):(?P<power>\S+)"', output):
                port_power[int(port)] = power
        finally:
            return port_power

    def get_port_wavelength(self, ports_count: int) -> dict[int, str]:
        """Determine ports wavelength."""
        port_wavelength = {}
        try:
            output = CommandTemplateExecutor(
                self._cli_service, command_template.WAVE
            ).execute_command(size=ports_count)
            for port, wave in re.findall(r'"(?P<port>\d+):(?P<wave>\S+?),.*"', output):
                port_wavelength[int(port)] = wave
        finally:
            return port_wavelength
