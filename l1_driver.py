# CloudShell L1 driver core
#
# It should be unnecessary to edit this file.
#
# - Listens on a port passed on the command line, e.g. Sample.exe 4000
# - Receives commands from CloudShell
# - Dispatches commands to your L1 handler

import socket
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime
from threading import Thread


class L1Driver:
    def __init__(self, handler, listen_port, listen_host='0.0.0.0', backlog=100, logger=None):
        """
        :type handler: L1HandlerBase
        :type listen_host: str
        :type listen_port: int
        :type backlog: int
        :type logger: qs_logger
        :rtype: None
        """
        self._handler = handler
        self._listen_host = listen_host
        self._listen_port = listen_port
        self._backlog = backlog
        self._logger = logger

    def go(self):
        sock_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_listener.bind((self._listen_host, self._listen_port))
        sock_listener.listen(self._backlog)
        if self._logger:
            self._logger.info('Listening for CloudShell commands on {} port {}'.format(self._listen_host, self._listen_port))
        while True:
            sock_accepted, _ = sock_listener.accept()
            if not sock_accepted:
                break
            sock_accepted.settimeout(10)

            def sock_thread(sock, logger):
                if logger:
                    logger.info('Accepted command connection {}'.format(sock))
                buf = ''
                while True:
                    try:
                        r = sock.recv(2048)
                    except socket.timeout:
                        continue
                    except Exception as e:
                        tb = traceback.format_exc()
                        if logger:
                            logger.critical(tb)
                        return
                    if logger:
                        logger.info('Received [[[' + str(r) + ']]]')
                    buf += str(r)
                    if '</Commands>' in buf:
                        responses_xml_str = self._process_commands(buf)
                        if logger:
                            logger.info('Sending response [[[' + responses_xml_str + ']]]')
                        sock.send(responses_xml_str)
                        buf = ''
                    if not r:
                        if logger:
                            logger.info('Connection {} closed'.format(sock))
                        return

            t = Thread(target=sock_thread, args=(sock_accepted, self._logger))
            t.start()

    def _process_commands(self, commands_xml_str):
        commands_xml_str = commands_xml_str.replace('xmlns="http://schemas.qualisystems.com/ResourceManagement/DriverCommands.xsd"', '')
        all_success = True
        error_code_xml = '<ErrorCode />'
        responses_xml = ''
        for command_node in ET.fromstring(commands_xml_str):
            success, response_xml = self._process_command(command_node)
            if not success:
                all_success = False
                error_code_xml = '<ErrorCode>1</ErrorCode>'
            responses_xml += response_xml + '\r\n'

        return '''<Responses
                    xmlns="http://schemas.qualisystems.com/ResourceManagement/DriverCommandResult.xsd"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    Success="''' + ('true' if all_success else 'false') + '''">
                ''' + error_code_xml + '''
               <Log>No need for Sync</Log>''' +  \
               responses_xml + \
               '''</Responses>'''.replace('\r\n', '\n') + '\r\n\r\n'

    def _process_command(self, command_xml_node):
        command_id = command_xml_node.attrib['CommandId']
        command_name = command_xml_node.attrib['CommandName']
        p = command_xml_node.find('Parameters')
        success = True
        log_xml = '<Log />'
        error_xml = '<Error />'
        try:
            if command_name == 'Login':
                self._handler.login(
                    p.find('Address').text,
                    p.find('User').text,
                    p.find('Password').text
                )
                response_info_xml = '<ResponseInfo />'

            elif command_name == 'Logout':
                self._handler.logout()
                response_info_xml = '<ResponseInfo />'

            elif command_name == 'SetStateId':
                self._handler.set_state_id(
                    p.find('StateId').text
                )
                response_info_xml = '<ResponseInfo />'

            elif command_name == 'GetStateId':
                rv = self._handler.get_state_id()
                response_info_xml = '''<ResponseInfo xsi:type="StateInfo" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        <StateId>''' + str(rv) + '''</StateId>
                    </ResponseInfo>'''

            elif command_name == 'GetResourceDescription':
                rv = self._handler.get_resource_description(
                    p.find('Address').text
                )
                response_info_xml = '''<ResponseInfo xsi:type="ResourceInfoResponse" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        ''' + rv.to_string() + '''
                    </ResponseInfo>'''

            elif command_name == 'GetAttributeValue':
                rv = self._handler.get_attribute_value(
                    p.find('Address').text,
                    p.find('Attribute').text
                )
                response_info_xml = '''<ResponseInfo xsi:type="AttributeInfoResponse" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        <Attribute Name="''' + p.find('Attribute').text + '''" Type="String" Value="''' + str(rv) + '''"/>
                    </ResponseInfo>'''

            elif command_name == 'MapBidi':
                self._handler.map_bidi(
                    p.find('MapPort_A').text,
                    p.find('MapPort_B').text,
                    p.find('MappingGroupName').text
                )
                response_info_xml = '<ResponseInfo />'

            elif command_name == 'MapUni':
                self._handler.map_uni(
                    p.find('SrcPort').text,
                    p.find('DstPort').text
                )
                response_info_xml = '<ResponseInfo />'

            elif command_name == 'MapClear':
                self._handler.map_clear(
                    p.findall('MapPort')[0].text,
                    p.findall('MapPort')[1].text
                )
                response_info_xml = '<ResponseInfo />'

            elif command_name == 'MapClearTo':
                self._handler.map_clear_to(
                    p.find('SrcPort').text,
                    p.find('DstPort').text
                )
                response_info_xml = '<ResponseInfo />'

            elif command_name == 'SetSpeedManual':
                self._handler.set_speed_manual(
                    p.find('SrcPort').text,
                    p.find('DstPort').text,
                    p.find('Speed').text,
                    p.find('Duplex').text
                )
                response_info_xml = '<ResponseInfo />'

            else:
                raise Exception('Unimplemented command ' + command_name)
        except Exception as e:
            success = False
            tb = traceback.format_exc()
            if self._logger:
                self._logger.critical(tb)
            log_xml = "<Log>" + tb + "</Log>"
            if self._logger:
                self._logger.error(str(e))
            error_xml = "<Error>" + str(e) + "</Error>"
            response_info_xml = '<ResponseInfo />'

        return success, '''
            <CommandResponse CommandId="''' + command_id + '''" CommandName="''' + command_name + \
            '''" Success="''' + ('true' if success else 'false') + '''">
                ''' + error_xml + '''
                ''' + log_xml + '''
                <Timestamp>''' + datetime.now().strftime("%d.%m.%Y %H:%M:%S") + '''</Timestamp>
                ''' + response_info_xml + '''
            </CommandResponse>'''

