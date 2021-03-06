#!/usr/bin/python
# -*- coding: utf-8 -*-

from cloudshell.cli.command_mode import CommandMode


class PolatisRawCommandMode(CommandMode):
    PROMPT_REGEX = 'DUMMY_PROMPT'
    ENTER_COMMAND = ''
    EXIT_COMMAND = ''

    def __init__(self):
        CommandMode.__init__(self,
                             PolatisRawCommandMode.PROMPT_REGEX,
                             PolatisRawCommandMode.ENTER_COMMAND,
                             PolatisRawCommandMode.EXIT_COMMAND)

CommandMode.RELATIONS_DICT = {
    PolatisRawCommandMode: {
    }
}
