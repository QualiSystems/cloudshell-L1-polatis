#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict

from cloudshell.cli.command_template.command_template import CommandTemplate

# ACTION_MAP = OrderedDict()
# ERROR_MAP = OrderedDict([(r'[Ee]rror:', 'Command error')])

DEVICE_HDR = CommandTemplate("RTRV-HDR:::<counter>:;")
DEVICE_EQPT = CommandTemplate("RTRV-EQPT:\"<name>\":SYSTEM:<counter>:::PARAMETER=SIZE;")
