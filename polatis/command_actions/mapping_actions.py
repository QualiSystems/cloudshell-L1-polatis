from __future__ import annotations

from typing import TYPE_CHECKING

from cloudshell.cli.command_template.command_template_executor import (
    CommandTemplateExecutor,
)

import polatis.command_templates.mapping as command_template

if TYPE_CHECKING:
    from cloudshell.cli.service.cli_service import CliService


class MappingActions:
    def __init__(self, cli_service: CliService) -> None:
        """Mapping actions."""
        self._cli_service = cli_service

    def map_uni(self, src_port: int, dst_port: int) -> str:
        """Unidirectional mapping."""
        executor = CommandTemplateExecutor(self._cli_service, command_template.PORT_MAP)
        output = executor.execute_command(src_port=src_port, dst_port=dst_port)
        return output

    def map_clear_to(self, port: int) -> str:
        """Clear unidirectional mapping."""
        executor = CommandTemplateExecutor(
            self._cli_service, command_template.MAP_CLEAR
        )
        output = executor.execute_command(port=port)
        return output

    def map_clear(self, ports: list[int]) -> str:
        """Clear bidirectional mapping."""
        port = "&".join(map(str, ports))

        executor = CommandTemplateExecutor(
            self._cli_service, command_template.MAP_CLEAR
        )
        output = executor.execute_command(port=port)
        return output
