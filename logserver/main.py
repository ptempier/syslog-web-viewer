#!/usr/bin/env python3
import subprocess
import sys
import os
import signal
import logging
from settings import settings

# Global variable to store process references
processes = []

def script_path(filename):
    # Get the directory where main.py is located and join it with filename
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)

def start_front():
    return subprocess.Popen([sys.executable, script_path("front.py")])

def start_back():
    return subprocess.Popen([sys.executable, script_path("back.py")])

def start_rotate():
    return subprocess.Popen([sys.executable, script_path("rotate.py")])

def start_syslog_ng():
    # Start syslog-ng in the foreground, no caps, verbose
    return subprocess.Popen([
        "/usr/sbin/syslog-ng", "-F", "--no-caps", "--verbose"
    ])

def signal_handler(signum, frame):
    """Handle SIGHUP to reload configuration."""
    global processes
    if signum == signal.SIGHUP:
        logging.info("Received SIGHUP, reloading configuration...")
        settings.load_config()
        
        # Restart child processes to pick up new configuration
        logging.info("Restarting child processes to apply new configuration...")
        
        # Restart back.py
        try:
            with open('/tmp/back.pid', 'r') as f:
                back_pid = int(f.read().strip())
            os.kill(back_pid, signal.SIGTERM)
            processes[1] = start_back()  # Restart back.py
            logging.info("Restarted back.py")
        except Exception as e:
            logging.error(f"Failed to restart back.py: {e}")
        
        # Restart front.py
        try:
            processes[2].terminate()
            processes[2] = start_front()  # Restart front.py
            logging.info("Restarted front.py")
        except Exception as e:
            logging.error(f"Failed to restart front.py: {e}")
        
        # Restart rotate.py
        try:
            processes[3].terminate()
            processes[3] = start_rotate()  # Restart rotate.py
            logging.info("Restarted rotate.py")
        except Exception as e:
            logging.error(f"Failed to restart rotate.py: {e}")

def main():
    global processes
    # Write PID to file
    with open('/tmp/logserver.pid', 'w') as f:
        f.write(str(os.getpid()))

    # Set up signal handler
    signal.signal(signal.SIGHUP, signal_handler)
    
    try:
        print("Starting syslog-ng...")
        processes.append(start_syslog_ng())
        print("Starting back.py...")
        processes.append(start_back())
        print("Starting front.py...")
        processes.append(start_front())
        print("Starting rotate.py...")
        processes.append(start_rotate())
        print("All services started. Press Ctrl+C to stop.")
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()
    except Exception as e:
        print(f"Error: {e}")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()
    finally:
        # Clean up PID file on exit
        try:
            os.remove('/tmp/logserver.pid')
        except:
            pass

if __name__ == "__main__":
    main()
