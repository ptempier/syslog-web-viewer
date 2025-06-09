import os
import time
import threading
import pyinotify
from multiprocessing.connection import Listener
import logging
from conf import LOG_FILE, MAX_ARRAY_SIZE, TRIM_SIZE, SOCKET_PATH

logging.basicConfig(
    level=logging.INFO,
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

def tail_logfile_realtime(logfile, buffer: LogBuffer):
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_MODIFY

    if os.path.exists(logfile):
        try:
            with open(logfile) as f:
                lines = f.readlines()[-buffer.maxlen:]
                buffer.add_lines(lines)
            logging.info(f"Loaded last {buffer.maxlen} lines from log file.")
        except Exception as e:
            logging.error(f"Error reading log file at startup: {e}")

    class EventHandler(pyinotify.ProcessEvent):
        def __init__(self, logfile, buffer):
            super().__init__()
            self.logfile = logfile
            self.buffer = buffer
            self.last_size = os.path.getsize(logfile) if os.path.exists(logfile) else 0

        def process_IN_MODIFY(self, event):
            try:
                with open(self.logfile) as f:
                    f.seek(self.last_size)
                    new_data = f.read()
                    self.last_size = f.tell()
                    new_lines = new_data.splitlines()
                    if new_lines:
                        self.buffer.add_lines(new_lines)
                        logging.info(f"Added {len(new_lines)} new log lines from {self.logfile}.")
            except Exception as e:
                logging.error(f"Error on inotify event: {e}")

    handler = EventHandler(logfile, buffer)
    notifier = pyinotify.ThreadedNotifier(wm, handler)
    notifier.start()
    wm.add_watch(logfile, mask)
    logging.info(f"Started log tailing on {logfile}.")
    while True:
        time.sleep(1)

def ipc_server(buffer: LogBuffer, socket_path=SOCKET_PATH):
    if os.path.exists(socket_path):
        os.remove(socket_path)
    listener = Listener(socket_path, 'AF_UNIX')
    logging.info(f"IPC server listening on {socket_path}")
    while True:
        try:
            conn = listener.accept()
            msg = conn.recv()
            logging.info(f"IPC request received: {msg}")
            if msg == "get_lines":
                lines = buffer.get_lines()
                fill_level = len(lines)
                conn.send({
                    "lines": lines,
                    "fill_level": fill_level,
                    "max_size": buffer.maxlen
                })
            else:
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
    t1 = threading.Thread(target=tail_logfile_realtime, args=(LOG_FILE, buffer), daemon=True)
    t1.start()
    ipc_server(buffer)
