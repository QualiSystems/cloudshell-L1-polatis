#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict

from cloudshell.cli.command_template.command_template import CommandTemplate

# ACTION_MAP = OrderedDict()
# ERROR_MAP = OrderedDict(
#     [(r'[Ee]rror:', 'Command error'), (r'[Hh]ardware\s[Ii]ncompatibility', 'Mapping error, Hardware incompatibility'),
#      (r'%\s[Cc]ommand\sincomplete', 'Incorrect command')])

# MAP_BIDI = CommandTemplate('map bidir {src_port} {dst_port}', ACTION_MAP, ERROR_MAP)
# MAP_UNI = CommandTemplate('map {src_port} also-to {dst_port}', ACTION_MAP, ERROR_MAP)
# MAP_CLEAR_TO = CommandTemplate('map {src_port} not-to {dst_port}', ACTION_MAP, ERROR_MAP)
# MAP_CLEAR = CommandTemplate('map {port} clear-all', ACTION_MAP, ERROR_MAP)


PORT_MAP = CommandTemplate("ENT-PATCH:<name>:{dst_port},{src_port}:<counter>:;")
MAP_CLEAR = CommandTemplate("DLT-PATCH:<name>:{port}:<counter>:;")
