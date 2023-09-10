from __future__ import annotations

from cloudshell.cli.command_template.command_template import CommandTemplate

PORT_MAP = CommandTemplate('ENT-PATCH:"<name>":{dst_port},{src_port}:<counter>:;')
MAP_CLEAR = CommandTemplate('DLT-PATCH:"<name>":{port}:<counter>:;')
