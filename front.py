#!/usr/bin/env python3
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash

from conf import (
    SECRET_KEY, LOG_LEVEL
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

app = Flask(__name__, template_folder=".")
app.secret_key = SECRET_KEY

def is_authenticated():
    return session.get("logged_in", False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        from conf import AUTH_USERNAME, AUTH_PASSWORD
        if username == AUTH_USERNAME and password == AUTH_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for('live'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not is_authenticated():
        return redirect(url_for('login'))
    # Default to live tab
    return redirect(url_for('live'))

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

if __name__ == '__main__':
    logging.info("Starting Flask frontend.")
    app.run(host='0.0.0.0', port=7321)
