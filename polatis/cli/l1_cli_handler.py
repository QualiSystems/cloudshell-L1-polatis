from __future__ import annotations

import re
from typing import TYPE_CHECKING

from cloudshell.cli.service.cli import CLI
from cloudshell.cli.service.session_pool_manager import SessionPoolManager
from cloudshell.cli.session.scpi_session import SCPISession
from cloudshell.cli.session.ssh_session import SSHSession
from cloudshell.cli.session.telnet_session import TelnetSession
from cloudshell.cli.session.tl1_session import TL1Session
from cloudshell.layer_one.core.helper.logger import get_l1_logger
from cloudshell.layer_one.core.helper.runtime_configuration import RuntimeConfiguration
from cloudshell.layer_one.core.layer_one_driver_exception import LayerOneDriverException

if TYPE_CHECKING:
    from cloudshell.cli.service.command_mode import CommandMode
    from cloudshell.cli.service.session_pool_context_manager import (
        SessionPoolContextManager,
    )

logger = get_l1_logger(name=__name__)


class TL1SessionPolatis(TL1Session):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int | None,
        on_session_start=None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            host, username, password, port, on_session_start, *args, **kwargs
        )

    def _connect_actions(self, prompt: str) -> None:
        output = self.hardware_expect(
            f"ACT-USER::{self._username}:<counter>::{self._password};",
            expected_string=None,
        )
        if "( nil )" in output:
            self.switch_name = ""
            logger.info("Switch name was '( nil )' - using blank switch name")
        else:
            match = re.search(r"^(.*)\s+\d+-", output, re.MULTILINE)
            if match:
                self.switch_name = match.groups()[0].strip()
                logger.info(f"Taking as switch name: '{self.switch_name}'")
            else:
                logger.warning(
                    f"Switch name regex not found: {output} - using blank switch name"
                )
                self.switch_name = ""
        if self.on_session_start and callable(self.on_session_start):
            self.on_session_start(self, logger)
        self._active = True

    def hardware_expect(
        self,
        command: str,
        expected_string: str | None,
        action_map=None,
        error_map=None,
        timeout=None,
        retries=None,
        check_action_loop_detector=True,
        empty_loop_timeout=None,
        remove_command_from_output=True,
        **optional_args,
    ) -> str:
        self._tl1_counter += 1
        command = command.replace("<counter>", str(self._tl1_counter))
        command = command.replace("<name>", self.switch_name)
        prompt = r"M\s+%d\s+([A-Z ]+)[^;]*;" % self._tl1_counter

        rv = super().hardware_expect(
            command,
            prompt,
            action_map,
            error_map,
            timeout,
            retries,
            check_action_loop_detector,
            empty_loop_timeout,
            remove_command_from_output,
            **optional_args,
        )

        match = re.search(prompt, rv)
        if not match:
            raise Exception(f"Error: can not get prompt: {rv}")

        status = match.groups()[0]
        if status != "COMPLD":
            raise Exception(f"Error: Status '{status}': {rv}")
        return rv


class L1CliHandler:
    def __init__(self) -> None:
        self._cli = CLI(session_pool=SessionPoolManager(max_pool_size=1))
        self._defined_session_types = {
            "SSH": SSHSession,
            "TELNET": TelnetSession,
            "TL1": TL1SessionPolatis,
            "SCPI": SCPISession,
        }

        self._session_types = (
            RuntimeConfiguration().read_key("CLI.TYPE")
            or self._defined_session_types.keys()
        )
        self._ports = RuntimeConfiguration().read_key("CLI.PORTS", {"SSH": "22"})

        self._host: str | None = None
        self._username: str | None = None
        self._password: str | None = None

    def _new_sessions(
        self,
    ) -> list[SSHSession | TelnetSession | TL1SessionPolatis | SCPISession]:
        sessions = []
        for session_type in self._session_types:
            session_class = self._defined_session_types.get(session_type)
            if not session_class:
                raise LayerOneDriverException(
                    f"Session type {session_type} is not defined"
                )
            port = self._ports.get(session_type)
            sessions.append(
                session_class(self._host, self._username, self._password, port)
            )
        return sessions

    def define_session_attributes(
        self, address: str, username: str, password: str
    ) -> None:
        """Define session attributes."""
        address_list = address.split(":")
        if len(address_list) > 1:
            raise LayerOneDriverException("Incorrect resource address")
        self._host = address
        self._username = username
        self._password = password

    def get_cli_service(self, command_mode: CommandMode) -> SessionPoolContextManager:
        """Create new cli service or get it from pool."""
        if not self._host or not self._username or not self._password:
            raise LayerOneDriverException(
                "Cli Attributes is not defined, call Login command first"
            )
        return self._cli.get_session(self._new_sessions(), command_mode)
