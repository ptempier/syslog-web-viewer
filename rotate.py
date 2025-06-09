#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import gzip
import shutil
import logging
from datetime import datetime, timedelta
import glob
import signal

print("rotate.py: Starting...")  # DEBUG

try:
    from conf import (
        LOG_FILE, 
        ROTATED_LOG_PATTERN, ROTATED_LOG_DELETE_OLDEST, ROTATED_LOG_DELETE_MIN_COUNT,
        ROTATED_LOG_TOTAL_MAX_MB, ROTATED_LOG_MAX_DAYS,
        LOG_ROTATE_MAX_AGE_DAYS, LOG_ROTATE_MAX_SIZE_MB, LOG_ROTATE_CHECK_INTERVAL_SECONDS
    )
except Exception as e:
    print(f"rotate.py: Error importing conf.py: {e}")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [rotate.py]: %(message)s"
)

SYSLOG_NG_CTL = "/usr/sbin/syslog-ng-ctl"

def run_cmd(cmd):
    logging.info(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        logging.error(f"Failed to run {' '.join(cmd)}: {e}")

def get_isodate_range_from_log(logfile):
    if not os.path.exists(logfile):
        logging.warning(f"Log file does not exist: {logfile}")
        return None, None
    earliest = None
    latest = None
    try:
        with open(logfile, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "|" in line:
                    isodate = line.split("|", 1)[0].strip()
                    if not earliest:
                        earliest = isodate
                    latest = isodate
        return earliest, latest
    except Exception as e:
        logging.error(f"Failed to parse {logfile}: {e}")
        return None, None

def format_isodate_str(isodate):
    try:
        dt = datetime.fromisoformat(isodate.replace("T", " ").replace("Z", ""))
        return dt.strftime("%Y-%m-%d_%H-%M-%S")
    except Exception:
        s = isodate.replace("T", "_").replace(":", "-").replace(" ", "_")
        return s[:19].replace(":", "-")

def delete_oldest_gz_if_needed():
    pattern = ROTATED_LOG_PATTERN
    min_count = ROTATED_LOG_DELETE_MIN_COUNT
    max_mb = ROTATED_LOG_TOTAL_MAX_MB
    max_days = ROTATED_LOG_MAX_DAYS
    now = time.time()

    gz_files = sorted(glob.glob(pattern), key=os.path.getmtime)
    # 1. Delete if count exceeds
    while len(gz_files) > min_count:
        oldest = gz_files[0]
        try:
            os.remove(oldest)
            logging.info(f"Deleted oldest rotated log file (count limit): {oldest}")
        except Exception as e:
            logging.error(f"Failed to delete {oldest}: {e}")
        gz_files = sorted(glob.glob(pattern), key=os.path.getmtime)

    # 2. Delete if total size exceeds
    def total_mb(files):
        return sum(os.path.getsize(f) for f in files) / (1024*1024)
    while gz_files and total_mb(gz_files) > max_mb:
        oldest = gz_files[0]
        try:
            os.remove(oldest)
            logging.info(f"Deleted oldest rotated log file (size limit): {oldest}")
        except Exception as e:
            logging.error(f"Failed to delete {oldest}: {e}")
        gz_files = sorted(glob.glob(pattern), key=os.path.getmtime)

    # 3. Delete if file is older than max_days
    cutoff = now - (max_days * 86400)
    deleted_due_to_age = False
    for f in gz_files:
        mtime = os.path.getmtime(f)
        if mtime < cutoff:
            try:
                os.remove(f)
                logging.info(f"Deleted rotated log file (age limit): {f}")
                deleted_due_to_age = True
            except Exception as e:
                logging.error(f"Failed to delete {f}: {e}")
    if deleted_due_to_age:
        gz_files = sorted(glob.glob(pattern), key=os.path.getmtime)

    # Log the final stats
    final_count = len(gz_files)
    final_mb = total_mb(gz_files)
    logging.info(f"Rotated logs retained: {final_count} files, total {final_mb:.1f} MB")

def signal_backpy():
    try:
        with open("/tmp/back.pid", "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGHUP)
        print(f"Signaled back.py (PID {pid}) to re-open inotify.")
    except Exception as e:
        print(f"Could not signal back.py: {e}")

def rotate_log():
    earliest, latest = get_isodate_range_from_log(LOG_FILE)
    if not earliest or not latest:
        logging.warning(f"No valid isodate found in {LOG_FILE}, skipping rotation.")
        return
    earliest_fmt = format_isodate_str(earliest)
    latest_fmt = format_isodate_str(latest)
    rotated_name = f"{LOG_FILE}.{earliest_fmt}-to-{latest_fmt}"
    logging.info(f"Rotating log: {LOG_FILE} -> {rotated_name}")

    # Step 1: Rename the log file
    try:
        os.rename(LOG_FILE, rotated_name)
        logging.info(f"Renamed {LOG_FILE} to {rotated_name}")
    except Exception as e:
        logging.error(f"Failed to rename {LOG_FILE}: {e}")
        return

    # Step 2: syslog-ng-ctl reload, then reopen again
    run_cmd([SYSLOG_NG_CTL, "reopen"])

    # Step 3: gzip the rotated file
    gz_name = rotated_name + ".gz"
    try:
        with open(rotated_name, 'rb') as f_in, gzip.open(gz_name, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(rotated_name)
        logging.info(f"Compressed {rotated_name} to {gz_name}")
    except Exception as e:
        logging.error(f"Failed to gzip {rotated_name}: {e}")

    # Step 4: Optionally delete old logs by count, size, and age
    if ROTATED_LOG_DELETE_OLDEST:
        delete_oldest_gz_if_needed()

    # Step 5: Signal back.py to re-open inotify
    signal_backpy()

def should_rotate(logfile):
    # Check log age (from first ISODATE)
    earliest, _ = get_isodate_range_from_log(logfile)
    age_exceeded = False
    size_exceeded = False

    # 1. Age check
    if earliest:
        try:
            # Try to parse ISODATE (assume ISO 8601)
            earliest_dt = datetime.fromisoformat(earliest.replace("Z", "+00:00"))
            days_old = (datetime.now(earliest_dt.tzinfo) - earliest_dt).days
            if days_old > LOG_ROTATE_MAX_AGE_DAYS:
                logging.info(f"Log is older than {LOG_ROTATE_MAX_AGE_DAYS} days ({days_old} days) -> should rotate")
                age_exceeded = True
        except Exception as e:
            logging.warning(f"Could not parse log start date: {e}")

    # 2. Size check
    try:
        size_mb = os.path.getsize(logfile) / (1024 * 1024)
        if size_mb > LOG_ROTATE_MAX_SIZE_MB:
            logging.info(f"Log file {logfile} is {size_mb:.2f}MB (> {LOG_ROTATE_MAX_SIZE_MB}MB) -> should rotate")
            size_exceeded = True
    except Exception as e:
        logging.warning(f"Could not get log file size: {e}")
    
    return age_exceeded or size_exceeded

def main():
    print("rotate.py: Running main loop...")  # DEBUG
    logging.info(f"Checking log for rotation every {LOG_ROTATE_CHECK_INTERVAL_SECONDS} seconds.")
    while True:
        try:
            if os.path.exists(LOG_FILE) and should_rotate(LOG_FILE):
                rotate_log()
            else:
                logging.debug("No rotation needed.")
        except Exception as e:
            logging.error(f"Exception during log rotation: {e}")
        time.sleep(LOG_ROTATE_CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
