from flask import session
from datetime import datetime

def is_authenticated():
    """Check if the user is authenticated."""
    return session.get("logged_in", False)

def get_unique_values(rows, col_idx):
    """Get unique values from a specific column in the provided rows."""
    return sorted(set(row[col_idx] for row in rows if len(row) > col_idx and row[col_idx]))

def parse_log_date(date_str):
    """Parse the date format from the log buffer.
    Handles both ISO 8601 format with timezone and the old format."""
    try:
        # Try parsing ISO 8601 format with timezone first
        return datetime.fromisoformat(date_str)
    except ValueError:
        try:
            # Fall back to the old format
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError(f"Invalid log date format: {date_str}") 