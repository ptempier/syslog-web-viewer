#!/usr/bin/env python3
from conf import LOG_FILE, SOCKET_PATH
import subprocess
import time
import sys
import os
import signal

def wait_for_file(path, timeout=15):
    """Wait for a file to appear (with timeout, in seconds)."""
    start = time.time()
    while not os.path.exists(path):
        if time.time() - start > timeout:
            print(f"Timeout waiting for {path}")
            return False
        time.sleep(0.2)
    return True

def start_process(cmd, name, env=None, wait_file=None):
    print(f"Starting {name}: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if wait_file:
        if not wait_for_file(wait_file):
            print(f"{name} failed to start (missing {wait_file})")
            proc.terminate()
            return None
    return proc

def main():
    processes = []
    try:
        # 1. Start syslog-ng (foreground, no caps, verbose)
        syslog_ng_cmd = ["/usr/sbin/syslog-ng", "-F", "--no-caps", "--verbose"]
        syslog_ng = start_process(syslog_ng_cmd, "syslog-ng")
        processes.append(syslog_ng)
        # Give syslog-ng a moment to initialize the log file
        wait_for_file(LOG_FILE, timeout=10)
        time.sleep(0.5)

        # 2. Start back.py (IPC server, log tailer)
        back_py_cmd = [sys.executable, "back.py"]
        # Remove stale socket if present
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        back_py = start_process(back_py_cmd, "back.py", wait_file=SOCKET_PATH)
        processes.append(back_py)
        time.sleep(0.5)

        # 3. Start front.py (Flask web front)
        front_py_cmd = [sys.executable, "front.py"]
        front_py = start_process(front_py_cmd, "front.py")
        processes.append(front_py)

        print("All components started. Press Ctrl+C to stop.")
        # Forward stdout/stderr of processes to this terminal
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"Process {p.args} exited with code {p.returncode}")
                    sys.exit(1)
            time.sleep(1)

    except KeyboardInterrupt:
        print("Shutting down all processes...")
        for p in processes:
            if p and p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass
        # Allow graceful shutdown
        time.sleep(1)
        for p in processes:
            if p and p.poll() is None:
                try:
                    p.kill()
                except Exception:
                    pass

if __name__ == "__main__":
    main()
