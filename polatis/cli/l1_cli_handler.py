#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from cloudshell.cli.cli import CLI
from cloudshell.cli.session.scpi_session import SCPISession
from cloudshell.cli.session.ssh_session import SSHSession
from cloudshell.cli.session.telnet_session import TelnetSession
from cloudshell.cli.session.tl1_session import TL1Session
from cloudshell.cli.session_pool_manager import SessionPoolManager
from cloudshell.layer_one.core.helper.runtime_configuration import RuntimeConfiguration
from cloudshell.layer_one.core.layer_one_driver_exception import LayerOneDriverException


class TL1Session_Polatis(TL1Session):
    def __init__(self, host, username, password, port, on_session_start=None, *args, **kwargs):
        super(TL1Session_Polatis, self).__init__(host, username, password, port,
                                                 on_session_start, *args, **kwargs)

    def _connect_actions(self, prompt, logger):
        output = self.hardware_expect('ACT-USER::%s:<counter>::%s;' % (self._username, self._password),
                                      expected_string=None,
                                      logger=logger)
        if '( nil )' in output:
            self.switch_name = ''
            logger.info('Switch name was "( nil )" - using blank switch name')
        else:
            match = re.search(r'^(.*)\s+\d+-', output, re.MULTILINE)
            if match:
                self.switch_name = match.groups()[0].strip()
                logger.info('Taking as switch name: "%s"' % self.switch_name)
            else:
                logger.warn('Switch name regex not found: %s - using blank switch name' % output)
                self.switch_name = ''
        if self.on_session_start and callable(self.on_session_start):
            self.on_session_start(self, logger)
        self._active = True

    def hardware_expect(self, command, expected_string, logger, action_map=None, error_map=None, timeout=None,
                        retries=None, check_action_loop_detector=True, empty_loop_timeout=None,
                        remove_command_from_output=True, **optional_args):
        self._tl1_counter += 1
        command = command.replace('<counter>', str(self._tl1_counter))
        command = command.replace('<name>', self.switch_name)
        prompt = r'M\s+%d\s+([A-Z ]+)[^;]*;' % self._tl1_counter

        rv = super(TL1Session, self).hardware_expect(command, prompt, logger, action_map, error_map, timeout,
                                                     retries, check_action_loop_detector, empty_loop_timeout,
                                                     remove_command_from_output, **optional_args)

        m = re.search(prompt, rv)
        status = m.groups()[0]
        if status != 'COMPLD':
            raise Exception('Error: Status "%s": %s' % (status, rv))
        return rv


class L1CliHandler(object):
    def __init__(self, logger):
        self._logger = logger
        self._cli = CLI(session_pool=SessionPoolManager(max_pool_size=1))
        self._defined_session_types = {"SSH": SSHSession,
                                       "TELNET": TelnetSession,
                                       "TL1": TL1Session_Polatis,
                                       "SCPI": SCPISession,
                                       }

        self._session_types = RuntimeConfiguration().read_key("CLI.TYPE") or self._defined_session_types.keys()
        self._ports = RuntimeConfiguration().read_key("CLI.PORTS")

        self._host = None
        self._username = None
        self._password = None

    def _new_sessions(self):
        sessions = []
        for session_type in self._session_types:
            session_class = self._defined_session_types.get(session_type)
            if not session_class:
                raise LayerOneDriverException(self.__class__.__name__,
                                              "Session type {} is not defined".format(session_type))
            port = self._ports.get(session_type)
            sessions.append(session_class(self._host, self._username, self._password, port))
        return sessions

    def define_session_attributes(self, address, username, password):
        """
        Define session attributes
        :param address:
        :type address: str
        :param username:
        :param password:
        :return:
        """

        address_list = address.split(":")
        if len(address_list) > 1:
            raise LayerOneDriverException(self.__class__.__name__, "Incorrect resource address")
        self._host = address
        self._username = username
        self._password = password

    def get_cli_service(self, command_mode):
        """
        Create new cli service or get it from pool
        :param command_mode:
        :return:
        """
        if not self._host or not self._username or not self._password:
            raise LayerOneDriverException(self.__class__.__name__,
                                          "Cli Attributes is not defined, call Login command first")
        return self._cli.get_session(self._new_sessions(), command_mode, self._logger)
