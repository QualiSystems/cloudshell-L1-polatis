from __future__ import annotations

from cloudshell.cli.command_template.command_template import CommandTemplate

DEVICE_HDR = CommandTemplate("RTRV-HDR:::<counter>:;")
DEVICE_EQPT = CommandTemplate('RTRV-EQPT:"<name>":SYSTEM:<counter>:::PARAMETER=SIZE;')
