# Configuration settings for the log viewer system

import configparser
import os
import signal
import logging
from typing import Dict, Any, List, Tuple

class Settings:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.load_config()
        self._load_settings()

    def load_config(self) -> None:
        """Load configuration from file."""
        self.config.read(self.config_path)

    def save_config(self, form_data: Dict[str, Any]) -> None:
        """Save configuration from form data."""
        # Group form data by section
        sections = {}
        for key, value in form_data.items():
            if '.' in key:
                section, option = key.split('.')
                if section not in sections:
                    sections[section] = {}
                sections[section][option] = value

        # Update config with new values
        for section, options in sections.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for option, value in options.items():
                self.config.set(section, option, str(value))

        # Write to file
        with open(self.config_path, 'w') as f:
            self.config.write(f)

        # Reload settings
        self._load_settings()

    def get_config_dict(self) -> Dict[str, Dict[str, str]]:
        """Get configuration as a dictionary."""
        config_dict = {}
        for section in self.config.sections():
            config_dict[section] = dict(self.config[section])
        return config_dict

    def reload_config(self) -> None:
        """Reload configuration in all processes."""
        # Send SIGHUP to main process
        try:
            with open('/tmp/logserver.pid', 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGHUP)
            logging.info("Sent SIGHUP to main process")
        except Exception as e:
            logging.error(f"Failed to send SIGHUP: {e}")

    def _load_settings(self) -> None:
        """Load all settings from config into module-level variables."""
        # Paths
        self.LOG_FILE = self.config.get('paths', 'log_file')
        self.SOCKET_PATH = self.config.get('paths', 'socket_path')

        # Buffer settings
        self.MAX_ARRAY_SIZE = self.config.getint('buffer', 'max_array_size')
        self.TRIM_SIZE = self.config.getint('buffer', 'trim_size')

        # Display settings
        self.NUM_LINES_OPTIONS = [int(x) for x in self.config.get('display', 'num_lines_options').split(',')]
        self.DEFAULT_NUM_LINES = self.config.getint('display', 'default_num_lines')

        # Refresh settings
        self.REFRESH_INTERVAL_OPTIONS = [
            (int(value), label) for value, label in 
            [pair.split(':') for pair in self.config.get('refresh', 'refresh_interval_options').split(',')]
        ]
        self.DEFAULT_REFRESH_INTERVAL = self.config.getint('refresh', 'default_refresh_interval')

        # Authentication
        self.AUTH_USERNAME = self.config.get('auth', 'username')
        self.AUTH_PASSWORD = self.config.get('auth', 'password')
        self.SECRET_KEY = self.config.get('auth', 'secret_key')

        # Log rotation settings
        self.ROTATED_LOG_PATTERN = self.config.get('rotation', 'pattern')
        self.ROTATED_LOG_DELETE_OLDEST = self.config.getboolean('rotation', 'delete_oldest')
        self.ROTATED_LOG_DELETE_MIN_COUNT = self.config.getint('rotation', 'delete_min_count')
        self.ROTATED_LOG_TOTAL_MAX_MB = self.config.getint('rotation', 'total_max_mb')
        self.ROTATED_LOG_MAX_DAYS = self.config.getint('rotation', 'max_days')
        self.LOG_ROTATE_MAX_AGE_DAYS = self.config.getint('rotation', 'max_age_days')
        self.LOG_ROTATE_MAX_SIZE_MB = self.config.getint('rotation', 'max_size_mb')
        self.LOG_ROTATE_CHECK_INTERVAL_SECONDS = self.config.getint('rotation', 'check_interval_seconds')

        # Logging level
        self.LOG_LEVEL = self.config.get('logging', 'level')

# Create global instance
settings = Settings(os.path.join(os.path.dirname(__file__), 'settings.conf'))

# Export all settings as module-level variables
LOG_FILE = settings.LOG_FILE
SOCKET_PATH = settings.SOCKET_PATH
MAX_ARRAY_SIZE = settings.MAX_ARRAY_SIZE
TRIM_SIZE = settings.TRIM_SIZE
NUM_LINES_OPTIONS = settings.NUM_LINES_OPTIONS
DEFAULT_NUM_LINES = settings.DEFAULT_NUM_LINES
REFRESH_INTERVAL_OPTIONS = settings.REFRESH_INTERVAL_OPTIONS
DEFAULT_REFRESH_INTERVAL = settings.DEFAULT_REFRESH_INTERVAL
AUTH_USERNAME = settings.AUTH_USERNAME
AUTH_PASSWORD = settings.AUTH_PASSWORD
SECRET_KEY = settings.SECRET_KEY
ROTATED_LOG_PATTERN = settings.ROTATED_LOG_PATTERN
ROTATED_LOG_DELETE_OLDEST = settings.ROTATED_LOG_DELETE_OLDEST
ROTATED_LOG_DELETE_MIN_COUNT = settings.ROTATED_LOG_DELETE_MIN_COUNT
ROTATED_LOG_TOTAL_MAX_MB = settings.ROTATED_LOG_TOTAL_MAX_MB
ROTATED_LOG_MAX_DAYS = settings.ROTATED_LOG_MAX_DAYS
LOG_ROTATE_MAX_AGE_DAYS = settings.LOG_ROTATE_MAX_AGE_DAYS
LOG_ROTATE_MAX_SIZE_MB = settings.LOG_ROTATE_MAX_SIZE_MB
LOG_ROTATE_CHECK_INTERVAL_SECONDS = settings.LOG_ROTATE_CHECK_INTERVAL_SECONDS
LOG_LEVEL = settings.LOG_LEVEL
