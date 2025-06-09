import logging
from multiprocessing.connection import Client
from conf import SOCKET_PATH

def fetch_log_array():
    try:
        conn = Client(SOCKET_PATH, 'AF_UNIX')
        conn.send("get_lines")
        resp = conn.recv()
        conn.close()
        lines = resp.get("lines", [])
        fill_level = resp.get("fill_level", len(lines))
        max_size = resp.get("max_size", 1)
        logging.debug(f"Fetched log buffer from back.py (fill: {fill_level}/{max_size})")
        return lines, fill_level, max_size
    except Exception as e:
        logging.error(f"IPC error fetching log buffer: {e}")
        return [["Error", "", "", "", "", "", "", f"IPC error: {e}"]], 0, 1
