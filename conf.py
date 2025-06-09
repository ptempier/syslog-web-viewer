# Configuration settings for the log viewer system

LOG_FILE = "/var/log/messages"
MAX_ARRAY_SIZE = 2200
TRIM_SIZE = 200
SOCKET_PATH = "/tmp/logbuffer.sock"

NUM_LINES_OPTIONS = [10, 20, 30, 40, 50, 60, 80, 100]
DEFAULT_NUM_LINES = 30

# Authentication (plaintext, for demonstration)
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "changeme"
SECRET_KEY = "changethissecret"  # for Flask session

# Log rotation
ROTATE_INTERVAL_SECONDS = 120  # 2 minutes (configurable)

ROTATED_LOG_PATTERN = "/var/log/messages.*-to-*.gz"
ROTATED_LOG_DELETE_OLDEST = True    # Set to True to enable deletion of oldest .gz after each rotation
ROTATED_LOG_DELETE_MIN_COUNT = 20   # Minimum number of gz files to keep before deleting

ROTATED_LOG_TOTAL_MAX_MB = 500      # Maximum total gzipped log size in MB (default 500MB)
ROTATED_LOG_MAX_DAYS = 60           # Maximum number of days to keep rotated logs (default 60)

# Logging level configuration
# Available levels: DEBUG < INFO < WARN < ERROR
LOG_LEVEL = "INFO"
