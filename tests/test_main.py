from unittest import TestCase

from mock import patch, Mock, call

from main import Main


class TestMain(TestCase):
    def setUp(self):
        self._driver_path = Mock()
        self._port = Mock()
        self._log_path = Mock()
        self._instance = self._create_instance()

    @patch('main.os')
    @patch('main.sys')
    def _create_instance(self, sys_mod, os_mod):
        os_mod.path.dirname.return_value = self._driver_path
        return Main(None, self._port, self._log_path)

    @patch('main.os')
    @patch('main.sys')
    def test_init(self, sys_mod, os_mod):
        file_path = Mock()
        os_mod.path.dirname.return_value = self._driver_path
        os_mod.environ = {}
        instance = Main(file_path, self._port, self._log_path)
        os_mod.path.dirname.assert_called_once_with(file_path)
        self.assertIs(instance._driver_path, self._driver_path)
        self.assertIs(instance._log_path, self._log_path)
        self.assertIs(os_mod.environ.get('LOG_PATH'), self._log_path)

    @patch('main.os')
    @patch('main.sys')
    def test_init_default_values(self, sys_mod, os_mod):
        file_path = Mock()
        os_mod.path.dirname.return_value = self._driver_path
        args = [file_path]
        sys_mod.argv = args
        os_mod.path.join.return_value = self._log_path
        os_mod.environ = {}
        instance = Main(None, self._port, None)
        os_mod.path.dirname.assert_called_once_with(file_path)
        os_mod.path.join.assert_called_once_with(self._driver_path, '..', 'Logs')
        self.assertIs(instance._driver_path, self._driver_path)
        self.assertIs(instance._log_path, self._log_path)
        self.assertIs(os_mod.environ.get('LOG_PATH'), self._log_path)

    @patch('main.os')
    @patch('main.importlib')
    @patch('main.datetime')
    @patch('main.RuntimeConfiguration')
    @patch('main.XMLLogger')
    @patch('main.get_qs_logger')
    @patch('main.CommandExecutor')
    @patch('main.DriverListener')
    def test_run_driver(self, driver_listener_class, command_executor_class,
                        get_qs_logger_mod, xml_logger_class, runtime_configuration_class, datetime_mod, importlib_mod,
                        os_mod):
        config_path = Mock()
        xml_log_path = Mock()
        os_mod.path.join.side_effect = [config_path, xml_log_path]
        runtime_config_instance = Mock()
        log_level = Mock()
        runtime_config_instance.read_key.return_value = log_level
        runtime_configuration_class.return_value = runtime_config_instance
        xml_logger_inst = Mock()
        xml_logger_class.return_value = xml_logger_inst
        driver_name = 'test driver'
        time_inst = Mock()
        datetime_mod.now.return_value = time_inst
        time = 'test_time'
        time_inst.strftime.return_value = time
        command_logger = Mock()
        get_qs_logger_mod.return_value = command_logger

        driver_commands_inst = Mock()
        driver_commands_mod = Mock()
        driver_commands_mod.DriverCommands.return_value = driver_commands_inst
        importlib_mod.import_module.return_value = driver_commands_mod

        command_executor_inst = Mock()
        command_executor_class.return_value = command_executor_inst

        server_inst = Mock()
        driver_listener_class.return_value = server_inst

        self._instance.run_driver(driver_name)
        runtime_configuration_class.assert_called_once_with(config_path)
        join_calls = [call(self._driver_path, driver_name + '_' + 'RuntimeConfig.yml'),
                      call(driver_name + '--' + time + '.xml')]
        os_mod.path.join.has_calls(join_calls)
        datetime_mod.now.assert_called_once_with()
        time_inst.strftime.assert_called_once_with('%d-%b-%Y--%H-%M-%S')
        xml_logger_class.assert_called_once_with(xml_log_path)
        get_qs_logger_mod.assert_called_once_with(log_group=driver_name, log_file_prefix=driver_name + '_commands',
                                                  log_category='COMMANDS')
        runtime_config_instance.read_key.assert_called_once_with('LOGGING.LEVEL', 'INFO')
        command_logger.setLevel.assert_called_once_with(log_level)
        importlib_mod.import_module.assert_called_once_with('{}.driver_commands'.format(driver_name), package=None)
        driver_commands_mod.DriverCommands.assert_called_once_with(command_logger, runtime_config_instance)
        command_executor_class.assert_called_once_with(driver_commands_inst, command_logger)
        driver_listener_class.assert_called_once_with(command_executor_inst, xml_logger_inst, command_logger)
        server_inst.start_listening.assert_called_once_with(port=self._port)
