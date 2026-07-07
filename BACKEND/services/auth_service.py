"""
auth_service.py - Authentication business logic.

Security notes:
- Passwords never stored or compared in plain text.
- check_password_hash() uses timing-safe comparison.
- Combined error message prevents username enumeration.
"""

import os
import sys

from werkzeug.security import check_password_hash

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_connection, close_connection  # noqa: E402


def validate_credentials(username: str, password: str):
    """
    Validate username/password against the users table.
    Returns dict with id and username on success, None on failure.
    """
    conn = None
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT id, username, password FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        if row is None:
            return None
        if not check_password_hash(row["password"], password):
            return None
        return {"id": row["id"], "username": row["username"]}
    finally:
        close_connection(conn)
