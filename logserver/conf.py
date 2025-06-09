# Configuration settings for the log viewer system

LOG_FILE = "/var/log/logserver/messages"
MAX_ARRAY_SIZE = 2200
TRIM_SIZE = 200
SOCKET_PATH = "/tmp/logbuffer.sock"

NUM_LINES_OPTIONS = [10, 20, 30, 40, 50, 60, 80, 100]
DEFAULT_NUM_LINES = 30

# Refresh interval options for live search (in milliseconds)
REFRESH_INTERVAL_OPTIONS = [
    (1000, "1 second"),
    (2000, "2 seconds"),
    (5000, "5 seconds"),
    (10000, "10 seconds"),
    (30000, "30 seconds"),
    (60000, "1 minute"),
]
DEFAULT_REFRESH_INTERVAL = 2000  # 2 seconds

# Authentication (plaintext, for demonstration)
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "changeme"
SECRET_KEY = "changethissecret"  # for Flask session

# Log rotation pattern and retention
ROTATED_LOG_PATTERN = "/var/log/logserver/messages.*-to-*.gz"
ROTATED_LOG_DELETE_OLDEST = True    # Set to True to enable deletion of oldest .gz after each rotation
ROTATED_LOG_DELETE_MIN_COUNT = 20   # Minimum number of gz files to keep before deleting

ROTATED_LOG_TOTAL_MAX_MB = 500      # Maximum total gzipped log size in MB (default 500MB)
ROTATED_LOG_MAX_DAYS = 60           # Maximum number of days to keep rotated logs (default 60)

# Logging level configuration
# Available levels: DEBUG < INFO < WARN < ERROR
LOG_LEVEL = "INFO"

# Log rotation conditions and check interval (new parameters)
LOG_ROTATE_MAX_AGE_DAYS = 30            # Rotate if log started more than 30 days ago
LOG_ROTATE_MAX_SIZE_MB = 100            # Rotate if log file is larger than 100 MB
LOG_ROTATE_CHECK_INTERVAL_SECONDS = 300 # Check every 5 minutes (300 seconds)
