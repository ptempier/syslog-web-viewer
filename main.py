#!/usr/bin/env python3
import subprocess
import sys

def start_front():
    return subprocess.Popen([sys.executable, "front.py"])

def start_back():
    return subprocess.Popen([sys.executable, "back.py"])

def start_rotate():
    return subprocess.Popen([sys.executable, "rotate.py"])

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
