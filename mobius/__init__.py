import logging
from logging.handlers import SysLogHandler
import sys
import os

from .config import config
"""
This file initializes the Chomp package.

Within the chomp files, you want to import these:

* logger - for logging
* config - for getting different configurations

"""

# Now when things import, we load the settings based on their env
config = config[os.environ.get("ENV", "dev")]

# Logging configuration
logger = logging.getLogger(__name__)


class ContextFilter(logging.Filter):
    hostname = "mobius-%s" % config.ENV

    def filter(self, record):
        record.hostname = self.hostname
        return True


f = ContextFilter()
logger.setLevel(config.LOG_LEVEL)
logger.addFilter(f)

if config.SYSLOG:
    # Send to papertrail server
    papertrail_tuple = config.PAPERTRAIL.split(":")
    handler = SysLogHandler(
        address=(papertrail_tuple[0], int(papertrail_tuple[1])))
else:
    # Just print to standard out
    handler = logging.StreamHandler(sys.stdout)

formatter = logging.Formatter(
    '%(asctime)s %(hostname)s mobius %(levelname)s %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S')
handler.setFormatter(formatter)
handler.setLevel(config.LOG_LEVEL)
logger.addHandler(handler)

# Import things we are exporting
from .assign import Assign
from .tasking import Tasking
from .environment import Environment
from .employee import Employee

logger.info("Initialized environment %s" % config.ENV)
