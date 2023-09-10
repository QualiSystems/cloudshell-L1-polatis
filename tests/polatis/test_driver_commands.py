from unittest import TestCase
from unittest.mock import Mock

from cloudshell.layer_one.core.driver_commands_interface import DriverCommandsInterface

from polatis.driver_commands import DriverCommands


class TestDriverCommands(TestCase):
    def setUp(self):
        self._runtime_config_instance = Mock()
        self._instance = DriverCommands(self._runtime_config_instance)

    def test_implementing_interface(self):
        self.assertIsInstance(self._instance, DriverCommandsInterface)
