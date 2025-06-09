#!/usr/bin/env python3
import subprocess
import sys
import os

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

def main():
    processes = []
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

if __name__ == "__main__":
    main()
