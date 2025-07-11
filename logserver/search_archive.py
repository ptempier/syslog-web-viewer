from flask import request, render_template, session, redirect, url_for, jsonify
import logging
import os
import glob
from settings import (
    LOG_FILE, ROTATED_LOG_PATTERN, NUM_LINES_OPTIONS, DEFAULT_NUM_LINES,
    LOG_LEVEL, AUTH_USERNAME, AUTH_PASSWORD
)
import gzip
from datetime import datetime, timezone, timedelta
from back import fetch_log_array
from utils import is_authenticated, get_unique_values, parse_log_date
import pytz
import re

def get_unique_values(rows, col_idx):
    return sorted(set(row[col_idx] for row in rows if len(row) > col_idx and row[col_idx]))

def parse_datetime(date_str):
    """Parse datetime string that may or may not include seconds."""
    try:
        # Try parsing with seconds first
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        try:
            # If that fails, try without seconds
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            raise ValueError(f"Invalid datetime format: {date_str}")

def format_datetime_for_display(dt, tz_offset_min):
    """Format a UTC datetime for display in the user's local timezone."""
    if dt is None:
        return None
    if tz_offset_min is not None:
        # Subtract the offset to convert from UTC to local
        local_dt = dt - timedelta(minutes=tz_offset_min)
        return local_dt.strftime('%Y-%m-%dT%H:%M')
    return dt.strftime('%Y-%m-%dT%H:%M')

def get_file_date_range(filename):
    """Extract date range from log filename.
    Returns (start_date, end_date) or None if no dates found."""
    # Match pattern like YYYY-MM-DD_HH-MM-SS-to-YYYY-MM-DD_HH-MM-SS
    date_pattern = r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})-to-(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})'
    match = re.search(date_pattern, filename)
    
    if match:
        try:
            start_str = match.group(1).replace('_', 'T').replace('-', ':')
            end_str = match.group(2).replace('_', 'T').replace('-', ':')
            start_date = datetime.strptime(start_str, '%Y-%m-%dT%H:%M:%S')
            end_date = datetime.strptime(end_str, '%Y-%m-%dT%H:%M:%S')
            return (start_date, end_date)
        except ValueError:
            return None
    
    # If no date range found, check if it's the current log file
    if filename.endswith('messages') and not filename.endswith('.gz'):
        return None
    
    return None

def find_relevant_log_files(start_date_utc, end_date_utc):
    """Find log files that might contain entries within the date range."""
    log_dir = os.path.dirname(LOG_FILE)
    log_base = os.path.basename(LOG_FILE)
    pattern = os.path.join(log_dir, f"{log_base}*")
    all_files = sorted(glob.glob(pattern))
    
    relevant_files = []
    for file_path in all_files:
        filename = os.path.basename(file_path)
        
        # Always include the current messages file
        if filename == "messages":
            relevant_files.append(file_path)
            continue
            
        # For rotated files, check if they might contain relevant dates
        if not filename.endswith('.gz'):
            continue
            
        # Extract dates from filename like messages.2025-06-09_12-10-21-to-2025-06-09_23-48-40.gz
        try:
            date_part = filename.split('.', 1)[1].replace('.gz', '')
            start_str, end_str = date_part.split('-to-')
            
            # Convert filename dates to datetime objects
            file_start = datetime.strptime(start_str, '%Y-%m-%d_%H-%M-%S')
            file_end = datetime.strptime(end_str, '%Y-%m-%d_%H-%M-%S')
            
            # Check if date ranges overlap
            if file_start <= end_date_utc and file_end >= start_date_utc:
                relevant_files.append(file_path)
        except Exception as e:
            logging.error(f"Error parsing dates from filename {filename}: {e}")
            # If we can't parse the dates, include the file to be safe
            relevant_files.append(file_path)
    
    return relevant_files

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

def read_log_file(file_path, start_date_utc, end_date_utc, local_tz, utc):
    """Read and filter log entries from a single file."""
    rows = []
    open_fn = gzip.open if file_path.endswith('.gz') else open
    
    try:
        with open_fn(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if "|" in line:
                    try:
                        parts = line.rstrip('\n').split('|', 7)
                        while len(parts) < 8:
                            parts.append("")
                        
                        # Parse log date and convert to UTC if needed
                        log_date = parse_log_date(parts[0])
                        if log_date.tzinfo is None:
                            # If date is naive, assume it's in local time and convert to UTC
                            log_date = local_tz.localize(log_date).astimezone(utc)
                        else:
                            # If date already has timezone, just convert to UTC
                            log_date = log_date.astimezone(utc)
                        
                        # Check if date is in range
                        if start_date_utc <= log_date <= end_date_utc:
                            rows.append(tuple(parts))
                    except ValueError as e:
                        logging.error(f"Error parsing log line: {e}")
                        continue
    except Exception as e:
        logging.error(f"Error reading log file {file_path}: {e}")
    return rows

def archive_search():
    if not is_authenticated():
        return redirect(url_for('login'))
    logging.debug(f"HTTP GET /archive request: args={request.args}, remote_addr={request.remote_addr}")

    selected_host = request.args.get('host', '')
    selected_facility = request.args.get('facility', '')
    selected_level = request.args.get('level', '')
    selected_program = request.args.get('program', '')
    selected_pid = request.args.get('pid', '')
    msgonly_filter = request.args.get('msgonly_filter', '')

    # Get timezone offset from request
    tz_offset = request.args.get('timezone_offset', '0')
    try:
        tz_offset = int(tz_offset)
    except ValueError:
        tz_offset = 0

    # Initialize default dates in UTC
    utc = pytz.UTC
    now_utc = datetime.now(utc)
    default_start_date_utc = now_utc - timedelta(minutes=5)
    default_end_date_utc = now_utc

    # Convert to local time for display
    local_tz = pytz.FixedOffset(tz_offset)
    default_start_date = default_start_date_utc.astimezone(local_tz).strftime('%Y-%m-%dT%H:%M')
    default_end_date = default_end_date_utc.astimezone(local_tz).strftime('%Y-%m-%dT%H:%M')

    # Get dates from request or use defaults
    start_date_str = request.args.get('start_date', default_start_date)
    end_date_str = request.args.get('end_date', default_end_date)

    logging.debug(f"Input dates - start: {start_date_str}, end: {end_date_str}")

    # Convert input dates to UTC for comparison
    try:
        start_date_local = parse_datetime(start_date_str)
        start_date_local = local_tz.localize(start_date_local)
        start_date_utc = start_date_local.astimezone(utc)
        logging.debug(f"Start date UTC: {start_date_utc}")
    except ValueError as e:
        logging.error(f"Error parsing start date: {e}")
        start_date_utc = default_start_date_utc

    try:
        end_date_local = parse_datetime(end_date_str)
        end_date_local = local_tz.localize(end_date_local)
        end_date_utc = end_date_local.astimezone(utc)
        logging.debug(f"End date UTC: {end_date_utc}")
    except ValueError as e:
        logging.error(f"Error parsing end date: {e}")
        end_date_utc = default_end_date_utc

    try:
        num_lines = int(request.args.get('num_lines', str(DEFAULT_NUM_LINES)))
    except Exception:
        num_lines = DEFAULT_NUM_LINES
    if num_lines not in NUM_LINES_OPTIONS:
        num_lines = DEFAULT_NUM_LINES

    # Find and read only relevant log files
    all_rows = []
    relevant_files = find_relevant_log_files(start_date_utc, end_date_utc)
    logging.debug(f"Found {len(relevant_files)} relevant log files")
    
    for log_file in relevant_files:
        logging.debug(f"Reading log file: {log_file}")
        rows = read_log_file(log_file, start_date_utc, end_date_utc, local_tz, utc)
        all_rows.extend(rows)

    # Get unique values for filters
    hosts = get_unique_values(all_rows, 2)
    facilities = get_unique_values(all_rows, 3)
    levels = get_unique_values(all_rows, 4)
    programs = get_unique_values(all_rows, 5)
    pids = get_unique_values(all_rows, 6)

    # Apply filters
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

    # Sort by date and get the last N lines
    log_rows.sort(key=lambda x: x[0])
    log_rows = log_rows[-num_lines:]
    logging.debug(f"After filtering: {len(log_rows)} rows")

    return render_template(
        'logtable_archive.html',
        rows=log_rows,
        total_rows=len(all_rows),
        fill_level=len(all_rows),
        max_size=len(all_rows),
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
        start_date=start_date_str,
        end_date=end_date_str,
        timezone_offset=tz_offset,
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
        start_date = parse_datetime(start_date_str)
    else:
        start_date = now_utc_minus_5m

    if end_date_str:
        end_date = parse_datetime(end_date_str)
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
