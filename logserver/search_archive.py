from flask import request, render_template, session, redirect, url_for, jsonify
import logging
from conf import (
    LOG_FILE, ROTATED_LOG_PATTERN, NUM_LINES_OPTIONS, DEFAULT_NUM_LINES
)
import glob
import gzip
from datetime import datetime, timezone, timedelta
from back_client import fetch_log_array
from utils import is_authenticated, get_unique_values

def get_unique_values(rows, col_idx):
    return sorted(set(row[col_idx] for row in rows if len(row) > col_idx and row[col_idx]))

def is_authenticated():
    return session.get("logged_in", False)

def parse_datetime_local_with_offset(dt_str, tz_offset_min):
    """Parse a local datetime string and convert to UTC using the user's timezone offset in minutes."""
    if not dt_str:
        return None
    try:
        # Parse as naive local time
        if len(dt_str) == 16:
            dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
        elif len(dt_str) == 19:
            dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        else:
            dt = datetime.fromisoformat(dt_str)
        
        # Convert to UTC using the timezone offset
        if tz_offset_min is not None:
            # Add the offset to convert from local to UTC
            dt_utc = dt + timedelta(minutes=tz_offset_min)
            return dt_utc
        return dt
    except Exception as e:
        logging.error(f"Failed to parse datetime string '{dt_str}': {e}")
        return None

def format_datetime_for_display(dt, tz_offset_min):
    """Format a UTC datetime for display in the user's local timezone."""
    if dt is None:
        return None
    if tz_offset_min is not None:
        # Subtract the offset to convert from UTC to local
        local_dt = dt - timedelta(minutes=tz_offset_min)
        return local_dt.strftime('%Y-%m-%dT%H:%M')
    return dt.strftime('%Y-%m-%dT%H:%M')

def find_files_for_dates(start_date, end_date):
    files = []
    for fname in glob.glob(ROTATED_LOG_PATTERN):
        try:
            base = fname.split("messages.")[1].split(".gz")[0]
            d1, d2 = base.split("-to-")
            dt1 = datetime.strptime(d1, "%Y-%m-%d_%H-%M-%S")
            dt2 = datetime.strptime(d2, "%Y-%m-%d_%H-%M-%S")
            if (not start_date and not end_date) or \
               (start_date and end_date and dt2 >= start_date and dt1 <= end_date) or \
               (start_date and not end_date and dt2 >= start_date) or \
               (end_date and not start_date and dt1 <= end_date):
                files.append(fname)
        except Exception as e:
            logging.warning(f"Failed to parse rotated log filename '{fname}': {e}")
            continue
    files.append(LOG_FILE)
    logging.info(f"Archive search: using files {files} for start_date={start_date}, end_date={end_date}")
    return files

def parse_log_file_lines(filepath, start_date=None, end_date=None):
    rows = []
    open_fn = gzip.open if filepath.endswith('.gz') else open
    try:
        with open_fn(filepath, 'rt', encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "|" in line:
                    isodate = line.split("|", 1)[0].strip()
                    try:
                        dt = datetime.fromisoformat(isodate.replace("Z", "+00:00"))
                        if dt.tzinfo is not None:
                            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                        line_dt = dt
                    except Exception:
                        continue
                    if start_date and line_dt < start_date:
                        continue
                    if end_date and line_dt >= end_date:
                        continue
                    rows.append(line.strip().split("|"))
    except Exception as e:
        logging.error(f"Failed to parse archive file {filepath}: {e}")
    return rows

def archive_search():
    if not is_authenticated():
        return redirect(url_for('login'))
    logging.debug(f"HTTP GET /archive request: args={request.args}, remote_addr={request.remote_addr}")
    buffer_rows, fill_level, max_size = fetch_log_array()
    hosts = get_unique_values(buffer_rows, 2)
    facilities = get_unique_values(buffer_rows, 3)
    levels = get_unique_values(buffer_rows, 4)
    programs = get_unique_values(buffer_rows, 5)
    pids = get_unique_values(buffer_rows, 6)

    selected_host = request.args.get('host', '')
    selected_facility = request.args.get('facility', '')
    selected_level = request.args.get('level', '')
    selected_program = request.args.get('program', '')
    selected_pid = request.args.get('pid', '')
    msgonly_filter = request.args.get('msgonly_filter', '')

    # Initialize default dates
    now = datetime.now()
    default_start_date = (now - timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%S')
    default_end_date = now.strftime('%Y-%m-%dT%H:%M:%S')

    start_date = request.args.get('start_date', default_start_date)
    end_date = request.args.get('end_date', default_end_date)

    try:
        num_lines = int(request.args.get('num_lines', str(DEFAULT_NUM_LINES)))
    except Exception:
        num_lines = DEFAULT_NUM_LINES
    if num_lines not in NUM_LINES_OPTIONS:
        num_lines = DEFAULT_NUM_LINES

    log_rows = buffer_rows
    if selected_host:
        log_rows = [r for r in log_rows if r[2] == selected_host]
    if selected_facility:
        log_rows = [r for r in log_rows if r[3] == selected_facility]
    if selected_level:
        log_rows = [r for r in log_rows if r[4] == selected_level]
    if selected_program:
        log_rows = [r for r in log_rows if r[5] == selected_program]
    if selected_pid:
        log_rows = [r for r in log_rows if r[6] == selected_pid]
    if msgonly_filter:
        log_rows = [r for r in log_rows if msgonly_filter.lower() in r[7].lower()]
    if start_date:
        log_rows = [r for r in log_rows if r[0] >= start_date]
    if end_date:
        log_rows = [r for r in log_rows if r[0] <= end_date]
    log_rows = log_rows[-num_lines:]

    return render_template(
        'logtable_archive.html',
        rows=log_rows,
        total_rows=len(buffer_rows),
        fill_level=fill_level,
        max_size=max_size,
        hosts=hosts,
        facilities=facilities,
        levels=levels,
        programs=programs,
        pids=pids,
        selected_host=selected_host,
        selected_facility=selected_facility,
        selected_level=selected_level,
        selected_program=selected_program,
        selected_pid=selected_pid,
        num_lines=num_lines,
        num_lines_options=NUM_LINES_OPTIONS,
        msgonly_filter=msgonly_filter,
        start_date=start_date,
        end_date=end_date,
        request=request
    )

def api_archive():
    if not is_authenticated():
        return jsonify({"error": "unauthorized"}), 401

    selected_host = request.args.get('host', '')
    selected_facility = request.args.get('facility', '')
    selected_level = request.args.get('level', '')
    selected_program = request.args.get('program', '')
    selected_pid = request.args.get('pid', '')
    msgonly_filter = request.args.get('msgonly_filter', '')
    num_lines = request.args.get('num_lines', str(DEFAULT_NUM_LINES))
    try:
        num_lines = int(num_lines)
    except Exception:
        num_lines = DEFAULT_NUM_LINES
    if num_lines not in NUM_LINES_OPTIONS:
        num_lines = DEFAULT_NUM_LINES

    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    now_utc_minus_5m = now_utc - timedelta(minutes=5)

    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    tz_offset_str = request.args.get('timezone_offset', '')
    try:
        tz_offset_min = int(tz_offset_str)
    except Exception:
        tz_offset_min = None

    if start_date_str:
        start_date = parse_datetime_local_with_offset(start_date_str, tz_offset_min)
    else:
        start_date = now_utc_minus_5m

    if end_date_str:
        end_date = parse_datetime_local_with_offset(end_date_str, tz_offset_min)
    else:
        end_date = now_utc

    files = find_files_for_dates(start_date, end_date)
    logging.info(f"Archive search selected files: {files}")
    all_rows = []
    for f in files:
        all_rows.extend(parse_log_file_lines(f, start_date, end_date))

    log_rows = all_rows
    if selected_host:
        log_rows = [r for r in log_rows if r[2] == selected_host]
    if selected_facility:
        log_rows = [r for r in log_rows if r[3] == selected_facility]
    if selected_level:
        log_rows = [r for r in log_rows if r[4] == selected_level]
    if selected_program:
        log_rows = [r for r in log_rows if r[5] == selected_program]
    if selected_pid:
        log_rows = [r for r in log_rows if r[6] == selected_pid]
    if msgonly_filter:
        log_rows = [r for r in log_rows if msgonly_filter.lower() in r[7].lower()]
    log_rows = log_rows[-num_lines:]

    return jsonify({
        "rows": log_rows,
        "total_rows": len(all_rows)
    })
