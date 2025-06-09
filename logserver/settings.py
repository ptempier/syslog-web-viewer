# Configuration settings for the log viewer system

import configparser
import os
from typing import List, Tuple

# Read the configuration file
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'settings.conf')
config.read(config_path)

# Paths
LOG_FILE = config.get('paths', 'log_file')
SOCKET_PATH = config.get('paths', 'socket_path')

# Buffer settings
MAX_ARRAY_SIZE = config.getint('buffer', 'max_array_size')
TRIM_SIZE = config.getint('buffer', 'trim_size')

# Display settings
NUM_LINES_OPTIONS = [int(x) for x in config.get('display', 'num_lines_options').split(',')]
DEFAULT_NUM_LINES = config.getint('display', 'default_num_lines')

# Refresh settings
REFRESH_INTERVAL_OPTIONS = [
    (int(value), label) for value, label in 
    [pair.split(':') for pair in config.get('refresh', 'refresh_interval_options').split(',')]
]
DEFAULT_REFRESH_INTERVAL = config.getint('refresh', 'default_refresh_interval')

# Authentication
AUTH_USERNAME = config.get('auth', 'username')
AUTH_PASSWORD = config.get('auth', 'password')
SECRET_KEY = config.get('auth', 'secret_key')

# Log rotation settings
ROTATED_LOG_PATTERN = config.get('rotation', 'pattern')
ROTATED_LOG_DELETE_OLDEST = config.getboolean('rotation', 'delete_oldest')
ROTATED_LOG_DELETE_MIN_COUNT = config.getint('rotation', 'delete_min_count')
ROTATED_LOG_TOTAL_MAX_MB = config.getint('rotation', 'total_max_mb')
ROTATED_LOG_MAX_DAYS = config.getint('rotation', 'max_days')
LOG_ROTATE_MAX_AGE_DAYS = config.getint('rotation', 'max_age_days')
LOG_ROTATE_MAX_SIZE_MB = config.getint('rotation', 'max_size_mb')
LOG_ROTATE_CHECK_INTERVAL_SECONDS = config.getint('rotation', 'check_interval_seconds')

# Logging level
LOG_LEVEL = config.get('logging', 'level')
