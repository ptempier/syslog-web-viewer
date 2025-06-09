#!/usr/bin/env python3
import subprocess
from flask import Flask, render_template, request, jsonify
import threading
import sys
import time
import os
import pyinotify

app = Flask(__name__, template_folder=".")

LOG_FILE = "/var/log/messages"

def parse_log_line(line):
    parts = line.rstrip('\n').split('|', 7)
    while len(parts) < 8:
        parts.append("")
    return tuple(parts)

realtime_lines = []
realtime_lock = threading.Lock()

NUM_LINES_OPTIONS = [10, 20, 30, 40, 50, 60, 80, 100]
DEFAULT_NUM_LINES = 30

def tail_logfile_realtime(path, default_num_lines=DEFAULT_NUM_LINES):
    global realtime_lines
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_MODIFY

    while not os.path.exists(path):
        time.sleep(0.5)

    def get_tail(num_lines):
        try:
            with open(path) as f:
                lines = f.readlines()[-num_lines:]
                return [parse_log_line(line) for line in lines]
        except Exception as e:
            return [("Error", "", "", "", "", "", "", str(e))]
    with realtime_lock:
        realtime_lines[:] = get_tail(default_num_lines)

    class EventHandler(pyinotify.ProcessEvent):
        def process_IN_MODIFY(self, event):
            try:
                with open(path) as f:
                    f.seek(0, os.SEEK_END)
                    size = f.tell()
                    read_size = 20480
                    f.seek(max(0, size - read_size))
                    data = f.read()
                    lines = data.splitlines()[-default_num_lines:]
                    parsed = [parse_log_line(line) for line in lines]
                    with realtime_lock:
                        realtime_lines[:] = parsed
            except Exception as e:
                with realtime_lock:
                    realtime_lines[:] = [("Error", "", "", "", "", "", "", str(e))]

    handler = EventHandler()
    notifier = pyinotify.ThreadedNotifier(wm, handler)
    notifier.start()
    wm.add_watch(path, mask)
    while True:
        time.sleep(1)

def get_unique_values(rows, col_idx):
    return sorted(set(row[col_idx] for row in rows if row[col_idx]))

def start_syslog_ng():
    process = subprocess.Popen(
        ["/usr/sbin/syslog-ng", "-F", "--no-caps", "--verbose"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    for line in process.stdout:
        print(f"[syslog-ng] {line}", end='', file=sys.stdout, flush=True)

@app.route('/')
def show_log_table():
    log_rows = []
    realtime = request.args.get('realtime', 'off') == 'on'
    selected_host = request.args.get('host', '')
    selected_facility = request.args.get('facility', '')
    selected_level = request.args.get('level', '')
    selected_program = request.args.get('program', '')
    selected_pid = request.args.get('pid', '')
    refresh = request.args.get('refresh', 'off')
    msgonly_filter = request.args.get('msgonly_filter', '')
    try:
        num_lines = int(request.args.get('num_lines', str(DEFAULT_NUM_LINES)))
    except Exception:
        num_lines = DEFAULT_NUM_LINES
    if num_lines not in NUM_LINES_OPTIONS:
        num_lines = DEFAULT_NUM_LINES

    if realtime:
        with realtime_lock:
            log_rows = list(realtime_lines)[-num_lines:]
    else:
        try:
            with open(LOG_FILE) as f:
                for line in f.readlines()[-num_lines:]:
                    log_rows.append(parse_log_line(line))
        except Exception as e:
            log_rows = [("Error", "", "", "", "", "", "", str(e))]

    filtered = log_rows
    if selected_host:
        filtered = [r for r in filtered if r[2] == selected_host]
    if selected_facility:
        filtered = [r for r in filtered if r[3] == selected_facility]
    if selected_level:
        filtered = [r for r in filtered if r[4] == selected_level]
    if selected_program:
        filtered = [r for r in filtered if r[5] == selected_program]
    if selected_pid:
        filtered = [r for r in filtered if r[6] == selected_pid]
    if msgonly_filter:
        filtered = [r for r in filtered if msgonly_filter.lower() in r[7].lower()]

    hosts = [v for v in get_unique_values(log_rows, 2) if v]
    facilities = [v for v in get_unique_values(log_rows, 3) if v]
    levels = [v for v in get_unique_values(log_rows, 4) if v]
    programs = [v for v in get_unique_values(log_rows, 5) if v]
    pids = [v for v in get_unique_values(log_rows, 6) if v]

    return render_template(
        'logtable.html',
        rows=filtered,
        total_rows=len(log_rows),
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
        refresh=refresh,
        realtime=realtime,
        num_lines=num_lines,
        num_lines_options=NUM_LINES_OPTIONS,
        msgonly_filter=msgonly_filter,
        request=request
    )

@app.route('/realtime_api')
def realtime_api():
    selected_host = request.args.get('host', '')
    selected_facility = request.args.get('facility', '')
    selected_level = request.args.get('level', '')
    selected_program = request.args.get('program', '')
    selected_pid = request.args.get('pid', '')
    msgonly_filter = request.args.get('msgonly_filter', '')
    try:
        num_lines = int(request.args.get('num_lines', str(DEFAULT_NUM_LINES)))
    except Exception:
        num_lines = DEFAULT_NUM_LINES
    if num_lines not in NUM_LINES_OPTIONS:
        num_lines = DEFAULT_NUM_LINES

    with realtime_lock:
        log_rows = list(realtime_lines)[-num_lines:]
    filtered = log_rows
    if selected_host:
        filtered = [r for r in filtered if r[2] == selected_host]
    if selected_facility:
        filtered = [r for r in filtered if r[3] == selected_facility]
    if selected_level:
        filtered = [r for r in filtered if r[4] == selected_level]
    if selected_program:
        filtered = [r for r in filtered if r[5] == selected_program]
    if selected_pid:
        filtered = [r for r in filtered if r[6] == selected_pid]
    if msgonly_filter:
        filtered = [r for r in filtered if msgonly_filter.lower() in r[7].lower()]

    hosts = [v for v in get_unique_values(log_rows, 2) if v]
    facilities = [v for v in get_unique_values(log_rows, 3) if v]
    levels = [v for v in get_unique_values(log_rows, 4) if v]
    programs = [v for v in get_unique_values(log_rows, 5) if v]
    pids = [v for v in get_unique_values(log_rows, 6) if v]

    return jsonify({
        "rows": filtered,
        "total_rows": len(log_rows),
        "filters": {
            "hosts": hosts,
            "facilities": facilities,
            "levels": levels,
            "programs": programs,
            "pids": pids,
        }
    })

def start_realtime_thread():
    thread = threading.Thread(target=tail_logfile_realtime, args=(LOG_FILE,DEFAULT_NUM_LINES), daemon=True)
    thread.start()

if __name__ == '__main__':
    threading.Thread(target=start_syslog_ng, daemon=True).start()
    start_realtime_thread()
    app.run(host='0.0.0.0', port=7321)
