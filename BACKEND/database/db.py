"""
db.py - SQLite connection helper.

Reads DATABASE_PATH from Flask app context when available (supports test
injection), falls back to config.py when running as a standalone script.
"""

import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _get_db_path() -> str:
    try:
        from flask import current_app
        if current_app:
            return current_app.config["DATABASE_PATH"]
    except RuntimeError:
        pass
    from config import DATABASE_PATH
    return DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def close_connection(conn: sqlite3.Connection) -> None:
    if conn:
        conn.close()
