#!/usr/bin/env python3
import os
import logging
from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
from settings import LOG_FILE
from rotate import rotate_log

def files_view():
    """Display the files list page."""
    log_dir = os.path.dirname(LOG_FILE)
    files_list = []
    
    for filename in os.listdir(log_dir):
        filepath = os.path.join(log_dir, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            size = stat.st_size
            # Convert size to human readable format
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/(1024*1024):.1f} MB"
            
            modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            files_list.append({
                'name': filename,
                'size': size_str,
                'modified': modified
            })
    
    # Sort by modification time, newest first
    files_list.sort(key=lambda x: x['modified'], reverse=True)
    return render_template('files.html', files=files_list)

def rotate_now():
    """Manually trigger log rotation."""
    try:
        rotate_log()
        flash('Log rotation triggered successfully', 'success')
    except Exception as e:
        flash(f'Failed to trigger log rotation: {str(e)}', 'danger')
    return redirect(url_for('files_route')) 