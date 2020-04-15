#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict

from cloudshell.cli.command_template.command_template import CommandTemplate

# ACTION_MAP = OrderedDict()
# ERROR_MAP = OrderedDict([(r'[Ee]rror:', 'Command error')])

PSERIAL = CommandTemplate("RTRV-INV:\"<name>\":OCS:<counter>:;")
NETYPE = CommandTemplate('RTRV-NETYPE:\"<name>\"::<counter>:;')
PATCH = CommandTemplate("RTRV-PATCH:\"<name>\"::<counter>:;")
SHUTTERS = CommandTemplate("RTRV-PORT-SHUTTER:\"<name>\":1&&{size}:<counter>:;")
POWER = CommandTemplate("RTRV-PORT-POWER:\"<name>\":1&&{size}:<counter>:;")
WAVE = CommandTemplate("RTRV-PORT-PMON:\"<name>\":1&&{size}:<counter>:;")