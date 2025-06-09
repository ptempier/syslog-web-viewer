from flask import session

def is_authenticated():
    """Check if the user is authenticated."""
    return session.get("logged_in", False)

def get_unique_values(rows, col_idx):
    """Get unique values from a specific column in the rows."""
    return sorted(set(row[col_idx] for row in rows if row[col_idx])) 