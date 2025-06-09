import os
import time
import threading
import pyinotify
from multiprocessing.connection import Listener
import logging
import signal
from settings import LOG_FILE, MAX_ARRAY_SIZE, TRIM_SIZE, SOCKET_PATH, LOG_LEVEL

# Map our custom levels to Python's logging
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
}
# Set log level based on conf.py, default to INFO if misconfigured
logging.basicConfig(
    level=LOG_LEVELS.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [back.py]: %(message)s"
)

class LogBuffer:
    def __init__(self, maxlen=MAX_ARRAY_SIZE, trimlen=TRIM_SIZE):
        self.lines = []
        self.lock = threading.Lock()
        self.maxlen = maxlen
        self.trimlen = trimlen

    def parse_log_line(self, line):
        parts = line.rstrip('\n').split('|', 7)
        while len(parts) < 8:
            parts.append("")
        return tuple(parts)

    def add_lines(self, new_lines):
        with self.lock:
            for line in new_lines:
                self.lines.append(self.parse_log_line(line))
            if len(self.lines) > self.maxlen:
                self.lines = self.lines[self.trimlen:]

    def get_lines(self):
        with self.lock:
            return list(self.lines)

class InotifyTailer:
    def __init__(self, logfile, buffer: LogBuffer):
        self.logfile = logfile
        self.buffer = buffer
        self._stop_event = threading.Event()
        self._restart_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._restart_event.set()
        self._thread.join()

    def refresh(self, signum=None, frame=None):
        logging.info("Received signal to refresh inotify tailer.")
        self._restart_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            self._restart_event.clear()
            self._tail_logfile()
            # If restart requested, loop and restart tailing
            if self._restart_event.is_set():
                logging.info("Restarting inotify watcher/tailer due to signal.")
                continue
            break

    def _tail_logfile(self):
        wm = pyinotify.WatchManager()
        mask = pyinotify.IN_MODIFY | pyinotify.IN_MOVE_SELF | pyinotify.IN_DELETE_SELF | pyinotify.IN_CREATE

        class EventHandler(pyinotify.ProcessEvent):
            def __init__(self, tailer):
                super().__init__()
                self.tailer = tailer
                self.logfile = tailer.logfile
                self.buffer = tailer.buffer
                self.last_size = os.path.getsize(self.logfile) if os.path.exists(self.logfile) else 0

            def process_default(self, event):
                pass

            def process_IN_MODIFY(self, event):
                try:
                    with open(self.logfile) as f:
                        f.seek(self.last_size)
                        new_data = f.read()
                        self.last_size = f.tell()
                        new_lines = new_data.splitlines()
                        if new_lines:
                            logging.debug(f"Added {len(new_lines)} new log lines from {self.logfile}.")
                            self.buffer.add_lines(new_lines)
                except Exception as e:
                    logging.error(f"Error on inotify event: {e}")

            def process_IN_MOVE_SELF(self, event):
                # Log was rotated
                logging.info(f"File moved (rotated): {self.logfile}")
                self.last_size = 0
                self.tailer._restart_event.set()

            def process_IN_DELETE_SELF(self, event):
                # Log was deleted (rotated)
                logging.info(f"File deleted (rotated): {self.logfile}")
                self.last_size = 0
                self.tailer._restart_event.set()

        handler = EventHandler(self)
        notifier = pyinotify.ThreadedNotifier(wm, handler)
        notifier.start()
        wdd = wm.add_watch(self.logfile, mask)
        logging.info(f"Started log tailing on {self.logfile}.")

        try:
            while not self._stop_event.is_set() and not self._restart_event.is_set():
                time.sleep(1)
        finally:
            notifier.stop()
            wm.rm_watch(list(wdd.values()))
            logging.info("Stopped inotify watcher.")

def ipc_server(buffer: LogBuffer, socket_path=SOCKET_PATH):
    if os.path.exists(socket_path):
        os.remove(socket_path)
    listener = Listener(socket_path, 'AF_UNIX')
    logging.info(f"IPC server listening on {socket_path}")
    while True:
        try:
            conn = listener.accept()
            msg = conn.recv()
            if msg == "get_lines":
                logging.debug(f"IPC request received: {msg}")
                lines = buffer.get_lines()
                fill_level = len(lines)
                conn.send({
                    "lines": lines,
                    "fill_level": fill_level,
                    "max_size": buffer.maxlen
                })
            else:
                logging.debug(f"IPC request received: {msg}")
                conn.send({
                    "lines": [],
                    "fill_level": 0,
                    "max_size": buffer.maxlen
                })
            conn.close()
        except Exception as e:
            logging.error(f"IPC error: {e}")

if __name__ == "__main__":
    logging.info("Starting back.py log buffer and IPC server.")
    buffer = LogBuffer()
    tailer = InotifyTailer(LOG_FILE, buffer)
    # Write our PID to a file for rotate.py to signal
    with open("/tmp/back.pid", "w") as f:
        f.write(str(os.getpid()))
    # Register SIGHUP to refresh inotify
    signal.signal(signal.SIGHUP, tailer.refresh)
    tailer.start()
    ipc_server(buffer)
