from flask import request, render_template, session, redirect, url_for, jsonify
import logging
from settings import (
    NUM_LINES_OPTIONS, DEFAULT_NUM_LINES, DEFAULT_REFRESH_INTERVAL, REFRESH_INTERVAL_OPTIONS
)
from back_client import fetch_log_array
from utils import is_authenticated, get_unique_values

def live_search():
    if not is_authenticated():
        return redirect(url_for('login'))
    logging.debug(f"HTTP GET /live request: args={request.args}, remote_addr={request.remote_addr}")
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
    refresh = request.args.get('refresh', str(DEFAULT_REFRESH_INTERVAL))
    msgonly_filter = request.args.get('msgonly_filter', '')

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
    log_rows = log_rows[-num_lines:]

    return render_template(
        'logtable_live.html',
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
        refresh=refresh,
        num_lines=num_lines,
        num_lines_options=NUM_LINES_OPTIONS,
        refresh_interval_options=REFRESH_INTERVAL_OPTIONS,
        msgonly_filter=msgonly_filter,
        request=request
    )

def api_live():
    if not is_authenticated():
        return jsonify({"error": "unauthorized"}), 401
    buffer_rows, fill_level, max_size = fetch_log_array()
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
    log_rows = log_rows[-num_lines:]

    return jsonify({
        "rows": log_rows,
        "total_rows": len(buffer_rows),
        "fill_level": fill_level,
        "max_size": max_size
    })
