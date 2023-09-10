from __future__ import annotations

from cloudshell.cli.command_template.command_template import CommandTemplate

PSERIAL = CommandTemplate('RTRV-INV:"<name>":OCS:<counter>:;')
NETYPE = CommandTemplate('RTRV-NETYPE:"<name>"::<counter>:;')
PATCH = CommandTemplate('RTRV-PATCH:"<name>"::<counter>:;')
SHUTTERS = CommandTemplate('RTRV-PORT-SHUTTER:"<name>":1&&{size}:<counter>:;')
POWER = CommandTemplate('RTRV-PORT-POWER:"<name>":1&&{size}:<counter>:;')
WAVE = CommandTemplate('RTRV-PORT-PMON:"<name>":1&&{size}:<counter>:;')
