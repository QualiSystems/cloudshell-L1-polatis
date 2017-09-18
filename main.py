# CloudShell L1 main
#
# It is not necessary to edit this file.
#
# This file will be the entry point of PolatisPython.exe
#
# It will be invoked by CloudShell as PolatisPython.exe <listening port number>

from cloudshell.core.logger.qs_logger import get_qs_logger
from l1_driver import l1_driver_main_loop
from polatis_l1_handler import PolatisL1Handler
import os
import sys


# LOG_PATH required for qs_logger startup
os.environ['LOG_PATH'] = os.path.join(os.path.dirname(sys.argv[0]), '..', 'Logs')

logger = get_qs_logger(log_group='Polatis',
                       log_file_prefix='Polatis',
                       log_category='INTERNAL')


# Instantiate your implementation of L1HandlerBase
handler = PolatisL1Handler(logger=logger)

# Listen for commands forever - never returns
l1_driver_main_loop(handler=handler, listen_port=int(sys.argv[1]), logger=logger)
