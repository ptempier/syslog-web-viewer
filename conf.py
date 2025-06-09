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
