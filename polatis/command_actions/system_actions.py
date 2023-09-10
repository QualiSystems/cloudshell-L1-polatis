from __future__ import annotations

import re
from typing import TYPE_CHECKING

from cloudshell.cli.command_template.command_template_executor import (
    CommandTemplateExecutor,
)

import polatis.command_templates.system as command_template

if TYPE_CHECKING:
    from cloudshell.cli.service.cli_service import CliService


class SystemActions:
    """System actions."""

    def __init__(self, cli_service: CliService) -> None:
        self._cli_service = cli_service

    def get_device_size(self) -> tuple[int, int]:
        """Device info."""
        output = CommandTemplateExecutor(
            self._cli_service, command_template.DEVICE_EQPT
        ).execute_command()
        match = re.search(r"SYSTEM:SIZE=(?P<size1>\d+)x(?P<size2>\d+)", output)
        if match:
            size1 = int(match.groupdict()["size1"])
            size2 = int(match.groupdict()["size2"])
            return size1, size2
        else:
            raise Exception(f"Unable to determine system size: {output}")
