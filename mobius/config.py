import os
import logging

basedir = os.path.abspath(os.path.dirname(__file__))


class DefaultConfig:
    ENV = "prod"
    LOG_LEVEL = logging.INFO
    SYSLOG = True  # Send logs to papertrail
    # Logging
    PAPERTRAIL = "logs2.papertrailapp.com:12345"

    TASKING_FETCH_INTERVAL_SECONDS = 20
    STAFFJOY_API_KEY = os.environ.get("STAFFJOY_API_KEY")
    DEFAULT_TZ = "utc"
    MAX_HOURS_PER_SHIFT = 23

    # Calculation stuff
    UNASSIGNED_PENALTY = -1000
    MIN_HOURS_VIOLATION_PENALTY = -1000
    THREADS = 16  # Max for what Dantzig can support

    # Gurobi tuning parameters
    MAX_TUNING_TIME = 1 * 60 * 60  # 1 Hour
    TUNE_FILE = "tuning.prm"

    # Happiness Timeout
    HAPPY_CALCULATION_TIMEOUT = 20 * 60  # 20 minutes

    # Destroy container if there was an error
    KILL_ON_ERROR = True
    KILL_DELAY = 60  # To prevent infinite loop, sleep before kill


class StageConfig(DefaultConfig):
    ENV = "stage"


class DevelopmentConfig(DefaultConfig):
    ENV = "dev"
    LOG_LEVEL = logging.DEBUG
    SYSLOG = False
    TASKING_FETCH_INTERVAL_SECONDS = 5
    STAFFJOY_API_KEY = "staffjoydev"
    THREADS = 16  # Max for what Dantzig can support
    MAX_TUNING_TIME = 5 * 60  # 5 minutes
    KILL_ON_ERROR = False


class TestConfig(DefaultConfig):
    ENV = "test"
    SYSLOG = False
    LOG_LEVEL = logging.DEBUG
    THREADS = 6
    KILL_ON_ERROR = False


config = {  # Determined in main.py
    "test": TestConfig,
    "dev": DevelopmentConfig,
    "stage": StageConfig,
    "prod": DefaultConfig,
}
