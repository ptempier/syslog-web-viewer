# Syslog Web Viewer

![Alt text](/screenshot.jpeg?raw=true "Optional Title")

A comprehensive web-based system log viewer that provides real-time monitoring, archiving, and search capabilities for system logs.

## Features

### Core Functionality
- Real-time log viewing and monitoring
- Log archiving and rotation
- Search capabilities for both live and archived logs
- Filtering by various log attributes (host, facility, level, program, PID)
- Configurable refresh intervals for live updates

### Architecture
- Frontend: Flask-based web interface with a modern UI
- Backend: Multiple components working together:
  - `syslog-ng` for log collection and processing
  - `back.py` for log buffering and real-time monitoring
  - `front.py` for web interface and authentication
  - `rotate.py` for log rotation management

### Key Features
- Real-time log monitoring with configurable refresh rates
- Log filtering by multiple criteria:
  - Host
  - Facility
  - Log level
  - Program
  - Process ID (PID)
- Message content filtering
- Configurable number of lines to display
- Log rotation with size and age-based policies
- Authentication system for secure access

### Technical Details
- Uses `syslog-ng` for log collection on port 7322 (UDP)
- Web interface runs on port 7321
- Implements log rotation with configurable:
  - Maximum log size (100MB)
  - Maximum age (30 days)
  - Total storage limit (500MB)
- Uses inotify for efficient file monitoring
- Implements a buffer system to manage log data in memory

### Deployment
- Containerized using Docker
- Uses Fedora 42 as the base image
- Includes a docker-compose configuration for easy deployment
- Persists logs in a mounted volume

## Usage

The application is designed to be a comprehensive log management solution, particularly useful for system administrators and developers who need to monitor and analyze system logs in real-time while maintaining historical records.

### Ports
- 7321: Web interface
- 7322: UDP port for syslog-ng log collection

### Default Credentials
- Username: admin
- Password: changeme

**Note:** It is recommended to change the default credentials in production environments. 