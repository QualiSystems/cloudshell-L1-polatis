from __future__ import annotations

from typing import TYPE_CHECKING

from cloudshell.layer_one.core.driver_commands_interface import DriverCommandsInterface
from cloudshell.layer_one.core.helper.logger import get_l1_logger
from cloudshell.layer_one.core.response.resource_info.entities.chassis import Chassis
from cloudshell.layer_one.core.response.resource_info.entities.port import Port
from cloudshell.layer_one.core.response.response_info import (
    GetStateIdResponseInfo,
    ResourceDescriptionResponseInfo,
)

from polatis.cli.polatis_cli_handler import PolatisCliHandler
from polatis.command_actions.autoload_actions import AutoloadActions
from polatis.command_actions.mapping_actions import MappingActions
from polatis.command_actions.system_actions import SystemActions

if TYPE_CHECKING:
    from cloudshell.layer_one.core.helper.runtime_configuration import (
        RuntimeConfiguration,
    )

logger = get_l1_logger(name=__name__)


class DriverCommands(DriverCommandsInterface):
    """Driver commands implementation."""

    LOGICAL_PORT_MODE = "LOGICAL"

    def __init__(self, runtime_config: RuntimeConfiguration) -> None:
        self._runtime_config = runtime_config
        self._driver_port_mode = runtime_config.read_key(
            "DRIVER.PORT_MODE", self.LOGICAL_PORT_MODE
        )
        self._cli_handler = PolatisCliHandler()
        self.total_ports_count: int | None = None
        self.logical_ports_count: int | None = None

    @property
    def _is_logical_port_mode(self) -> bool:
        return self._driver_port_mode.lower() == self.LOGICAL_PORT_MODE.lower()

    def _get_device_size(self, session) -> tuple[int, int]:
        """Determine ports count."""
        if not self.total_ports_count or not self.logical_ports_count:
            system_actions = SystemActions(session)
            size1, size2 = system_actions.get_device_size()

            self.total_ports_count = size1 + size2
            self.logical_ports_count = min(size1, size2)

        return self.total_ports_count, self.logical_ports_count

    def login(self, address: str, username: str, password: str) -> None:
        """Perform login operation on the device.

        Example:
        -------
            # Define session attributes
            self._cli_handler.define_session_attributes(address, username, password)

            # Obtain cli session
            with self._cli_handler.default_mode_service() as session:
                # Executing simple command
                device_info = session.send_command("show version")
                logger.info(device_info)
        """
        self._cli_handler.define_session_attributes(address, username, password)
        with self._cli_handler.default_mode_service() as session:
            actions = AutoloadActions(session)
            logger.info(actions.get_switch_serial())

    def get_resource_description(self, address: str) -> ResourceDescriptionResponseInfo:
        """Auto-load function to retrieve all information from the device.

        Example:
        -------
        from cloudshell.layer_one.core.response.resource_info.entities.chassis import \
            Chassis
        from cloudshell.layer_one.core.response.resource_info.entities.blade import \
            Blade
        from cloudshell.layer_one.core.response.resource_info.entities.port import Port

        chassis_resource_id = chassis_info.get_id()
        chassis_address = chassis_info.get_address()
        chassis_model_name = "Polatis Chassis"
        chassis_serial_number = chassis_info.get_serial_number()
        chassis = Chassis(resource_id, address, model_name, serial_number)

        blade_resource_id = blade_info.get_id()
        blade_model_name = "Generic L1 Module"
        blade_serial_number = blade_info.get_serial_number()
        blade.set_parent_resource(chassis)

        port_id = port_info.get_id()
        port_serial_number = port_info.get_serial_number()
        port = Port(port_id, "Generic L1 Port", port_serial_number)
        port.set_parent_resource(blade)

        return ResourceDescriptionResponseInfo([chassis])
        """
        with self._cli_handler.default_mode_service() as session:
            autoload_actions = AutoloadActions(session)

            serial_number = autoload_actions.get_switch_serial()
            switch_details = autoload_actions.get_switch_details()

            chassis = Chassis("", address, "Polatis Chassis", serial_number)
            chassis.set_model_name(switch_details["Model"])
            chassis.set_os_version(switch_details["Version"])
            chassis.set_serial_number(serial_number)

            total_ports_count, logical_ports_count = self._get_device_size(
                session=session
            )

            connections = autoload_actions.get_connections(
                logical_ports_count=logical_ports_count,
                is_logical=self._is_logical_port_mode,
            )

            ports_power = autoload_actions.get_port_power(ports_count=total_ports_count)
            ports_wavelength = autoload_actions.get_port_wavelength(
                ports_count=total_ports_count
            )

            logger.debug(f"PORT MODE: {self._is_logical_port_mode}")

            ports = {}
            ports_len = len(str(total_ports_count))
            for port_addr in range(
                1,
                (
                    logical_ports_count
                    if self._is_logical_port_mode
                    else total_ports_count
                )
                + 1,
            ):
                port_serial = f"{serial_number}.{port_addr}"
                port_id = "{:0{}d}".format(port_addr, ports_len)
                logger.debug(f"Port id : {port_id}")
                port = Port(port_id, "Generic L1 Port", port_serial)

                ports[port_addr] = port
                port.set_parent_resource(chassis)
                port.set_wavelength(ports_wavelength.get(port_addr, 0))

                if self._is_logical_port_mode:
                    port.set_tx_power(ports_power.get(port_addr, 0))
                    port.set_rx_power(
                        ports_power.get(port_addr + logical_ports_count, 0)
                    )
                else:
                    port_power = ports_power.get(port_addr, 0)
                    if port_addr <= logical_ports_count:
                        port.set_tx_power(port_power)
                    else:
                        port.set_rx_power(port_power)

            for src_address, dst_address in connections.items():
                src_port = ports.get(src_address)
                dst_port = ports.get(dst_address)
                if src_port and dst_port:
                    src_port.add_mapping(dst_port)

            return ResourceDescriptionResponseInfo([chassis])

    def map_uni(self, src_port: str, dst_ports: list[str]) -> None:
        """Unidirectional mapping of two ports."""
        if self._is_logical_port_mode:
            with self._cli_handler.default_mode_service() as session:
                mapping_actions = MappingActions(session)

                _, logical_ports_count = self._get_device_size(session=session)

                src = int(src_port.split("/")[-1]) + logical_ports_count
                for dst_port in dst_ports:
                    dst = int(dst_port.split("/")[-1])
                    mapping_actions.map_uni(src, dst)

        else:
            raise Exception(
                "Unidirectional connection is not available in physical port mode"
            )

    def map_bidi(self, src_port: str, dst_port: str) -> None:
        """Create a bidirectional connection between source and destination ports."""
        with self._cli_handler.default_mode_service() as session:
            mapping_actions = MappingActions(session)

            src = int(src_port.split("/")[-1])
            dst = int(dst_port.split("/")[-1])

            total_ports_count, logical_ports_count = self._get_device_size(
                session=session
            )

            if self._is_logical_port_mode:
                for a, b in [(dst, src), (src, dst)]:
                    b += logical_ports_count
                    # lower number must be the first in the command
                    mapping_actions.map_uni(src_port=b, dst_port=a)
            else:
                mapping_actions.map_uni(src_port=max(src, dst), dst_port=min(src, dst))

    def map_clear_to(self, src_port: str, dst_ports: list[str]) -> None:
        """Remove simplex/multi-cast/duplex connection ending on the dst port."""
        with self._cli_handler.default_mode_service() as session:
            mapping_actions = MappingActions(session)
            src = int(src_port.split("/")[-1])
            for dst_port in dst_ports:
                dst = int(dst_port.split("/")[-1])

                if self._is_logical_port_mode:
                    port = dst
                else:
                    port = min(src, dst)
                mapping_actions.map_clear_to(port=port)

    def map_clear(self, ports: list[str]) -> None:
        """Remove simplex/multi-cast/duplex connection ending on the destination port.

        Example:
        -------
        exceptions = []
        with self._cli_handler.config_mode_service() as session:
            for port in ports:
                try:
                    session.send_command("map clear {}".format(convert_port(port)))
                except Exception as e:
                    exceptions.append(str(e))
            if exceptions:
                raise Exception(",".join(exceptions))
        """
        with self._cli_handler.default_mode_service() as session:
            mapping_actions = MappingActions(session)
            for str_port in ports:
                port = int(str_port.split("/")[-1])
                if self._is_logical_port_mode:
                    total_ports_count, logical_ports_count = self._get_device_size(
                        session=session
                    )
                    mapping_actions.map_clear(ports=[port, port + logical_ports_count])
                else:
                    mapping_actions.map_clear_to(port=port)

    def map_tap(self, src_port: str, dst_ports: list[str]) -> None:
        """Add TAP connection."""
        raise NotImplementedError

    def set_speed_manual(
        self, src_port: str, dst_port: str, speed: str, duplex: str
    ) -> None:
        """Set connection speed.

        It is not used with new standard
        """
        raise NotImplementedError

    def get_attribute_value(self, cs_address: str, attribute_name: str) -> None:
        """Retrieve attribute value from the device.

        Example:
        -------
        with self._cli_handler.config_mode_service() as session:
            command = AttributeCommandFactory.get_attribute_command(
                cs_address,
                attribute_name
                )
            value = session.send_command(command)
            return AttributeValueResponseInfo(value)
        """
        raise NotImplementedError

    def set_attribute_value(
        self, cs_address: str, attribute_name: str, attribute_value: str
    ) -> None:
        """Set attribute value to the device.

        Example:
        -------
        with self._cli_handler.config_mode_service() as session:
            command = AttributeCommandFactory.set_attribute_command(
                cs_address,
                attribute_name,
                attribute_value
                )
            session.send_command(command)
            return AttributeValueResponseInfo(attribute_value)
        """
        raise NotImplementedError

    def get_state_id(self) -> GetStateIdResponseInfo:
        """Check if CS synchronized with the device.

        Example:
        -------
        # Obtain cli session
        with self._cli_handler.default_mode_service() as session:
            # Execute command
            chassis_name = session.send_command("show chassis name")
            return chassis_name
        """
        logger.info("Command 'get state id' called")
        return GetStateIdResponseInfo("-1")

    def set_state_id(self, state_id: str) -> None:
        """Set synchronization state id to the device.

        Called after Autoload or SyncFomDevice commands

        Example:
        -------
        # Obtain cli session
        with self._cli_handler.config_mode_service() as session:
            # Execute command
            session.send_command("set chassis name {}".format(state_id))
        """
        logger.info(f"set_state_id {state_id}")
