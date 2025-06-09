#!/usr/bin/env python3
import subprocess
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sys
from multiprocessing.connection import Client
import logging
from conf import (
    SOCKET_PATH, NUM_LINES_OPTIONS, DEFAULT_NUM_LINES,
    AUTH_USERNAME, AUTH_PASSWORD, SECRET_KEY
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [front.py]: %(message)s"
)

app = Flask(__name__, template_folder=".")
app.secret_key = SECRET_KEY

def fetch_log_array():
    try:
        conn = Client(SOCKET_PATH, 'AF_UNIX')
        conn.send("get_lines")
        resp = conn.recv()
        conn.close()
        lines = resp.get("lines", [])
        fill_level = resp.get("fill_level", len(lines))
        max_size = resp.get("max_size", 1)
        logging.info(f"Fetched log buffer from back.py (fill: {fill_level}/{max_size})")
        return lines, fill_level, max_size
    except Exception as e:
        logging.error(f"IPC error fetching log buffer: {e}")
        return [["Error", "", "", "", "", "", "", f"IPC error: {e}"]], 0, 1

def get_unique_values(rows, col_idx):
    return sorted(set(row[col_idx] for row in rows if row[col_idx]))

def is_authenticated():
    return session.get("logged_in", False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == AUTH_USERNAME and password == AUTH_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for('show_log_table'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def show_log_table():
    if not is_authenticated():
        return redirect(url_for('login'))
    buffer_rows, fill_level, max_size = fetch_log_array()
    logging.info(f"Rendering main log table for request {request.remote_addr}.")
    hosts = [v for v in get_unique_values(buffer_rows, 2) if v]
    facilities = [v for v in get_unique_values(buffer_rows, 3) if v]
    levels = [v for v in get_unique_values(buffer_rows, 4) if v]
    programs = [v for v in get_unique_values(buffer_rows, 5) if v]
    pids = [v for v in get_unique_values(buffer_rows, 6) if v]

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
        'logtable.html',
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
        msgonly_filter=msgonly_filter,
        request=request
    )

@app.route('/api/table')
def api_table():
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

if __name__ == '__main__':
    logging.info("Starting Flask frontend.")
    app.run(host='0.0.0.0', port=7321)
