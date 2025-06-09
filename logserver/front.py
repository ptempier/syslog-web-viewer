#!/usr/bin/env python3
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from settings import (
    SECRET_KEY, LOG_LEVEL, AUTH_USERNAME, AUTH_PASSWORD, settings
)

# Map our custom levels to Python's logging
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
}
logging.basicConfig(
    level=LOG_LEVELS.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [front.py]: %(message)s"
)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Import search logic from external modules
import search_live
import search_archive
import files
from utils import is_authenticated

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = SECRET_KEY

@app.route('/')
def index():
    if not is_authenticated():
        return redirect(url_for('login'))
    return redirect(url_for('live'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == AUTH_USERNAME and password == AUTH_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/live')
def live():
    return search_live.live_search()

@app.route('/archive')
def archive():
    return search_archive.archive_search()

# Optionally: API endpoints for live and archive search
@app.route('/api/live')
def api_live():
    return search_live.api_live()

@app.route('/api/archive')
def api_archive():
    return search_archive.api_archive()

@app.route('/files')
def files_route():
    return files.files_view()

@app.route('/rotate_now', methods=['POST'])
def rotate_now():
    return files.rotate_now()

@app.route('/configure', methods=['GET', 'POST'])
def configure():
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Save configuration
        settings.save_config(request.form)
        # Reload configuration in all processes
        settings.reload_config()
        flash('Configuration saved and reloaded')
        return redirect(url_for('configure'))
    
    # Get current configuration
    config = settings.get_config_dict()
    return render_template('configure.html', config=config)

if __name__ == '__main__':
    logging.info("Starting Flask frontend.")
    app.run(host='0.0.0.0', port=7321)
