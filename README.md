# Syslog Web Viewer

A web-based syslog viewer that provides real-time log monitoring and historical log search capabilities.

## Features

- **Live View**: Real-time monitoring of syslog entries with automatic refresh
- **Archive Search**: Search through historical logs with date range filtering
- **Files Management**: View and manage log files, including manual rotation
- **Log Rotation**: Automatic log rotation based on size and age, with configurable retention policies
- **Embedded syslog-ng**: Built-in syslog server for direct log collection
- **Filtering**: Filter logs by host, facility, level, program, and PID
- **Message Search**: Search within log messages
- **Responsive Design**: Modern UI that works on both desktop and mobile devices

## How Live Search Works

The live search functionality is implemented through two main components:

1. `back.py` continuously monitors the log file using inotify, reads new lines, parses them into a structured format (timestamp, host, facility, etc.), and maintains a fixed-size buffer in memory (default 1000 lines) by removing oldest entries when the buffer is full.

2. `front.py` provides a web page that displays the logs and automatically refreshes every 2 seconds by calling an API endpoint that returns the latest buffer contents from `back.py`.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ptempier/syslog-web-viewer.git
cd syslog-web-viewer
```

2. Build and run with Docker:
```bash
docker build -t syslog-web-viewer .
docker run -d --name logserver -p 7321:7321 -p 7322:7322/udp -v /var/log:/var/log syslog-web-viewer
```

Or using docker-compose:
```bash
docker-compose up -d
```

## Usage

Access the web interface at `http://localhost:7321`

### Live View
- Real-time monitoring of syslog entries
- Configurable refresh interval
- Automatic scrolling to new entries
- Filter by host, facility, level, program, and PID

### Archive Search
- Search through historical logs
- Date range selection with timezone support
- Filter by host, facility, level, program, and PID
- Message content search
- Configurable number of results

### Files Management
- View all log files with their sizes and last modified dates
- Manual log rotation with "Rotate Now" button
- Automatic log rotation based on size and age
- Compressed archive files with date ranges in filenames

### Log Rotation
- Automatic rotation based on file size and age
- Configurable rotation policies:
  - Maximum file size
  - Maximum age
  - Retention period
  - Minimum number of files to keep
- Compressed archive files with date ranges
- Manual rotation trigger

### Embedded syslog-ng Server
- Built-in syslog server on port 7322 (UDP)
- Direct log collection from network devices
- No additional syslog server required
- Configurable through web interface

## Configuration

The application can be configured through the web interface:

- Log file paths
- Rotation settings (size, age, retention)
- Buffer settings
- Authentication credentials
- syslog-ng settings

## Development

### Project Structure
```
logserver/
├── front.py          # Web interface and routes
├── back.py          # Log monitoring and processing
├── rotate.py        # Log rotation and archiving
├── search_live.py   # Live search functionality
├── search_archive.py # Archive search functionality
├── files.py         # Files management functionality
├── settings.py      # Configuration management
├── utils.py         # Shared utilities
├── templates/       # HTML templates
└── static/         # CSS and JavaScript files
```

