"""
tests/test_auth_service.py - Unit tests for auth_service.validate_credentials().
Tests run against in-memory SQLite only - no web server, no banking.db touched.
"""

import os
import sqlite3
import sys
import unittest
from unittest.mock import patch
from werkzeug.security import generate_password_hash

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from services.auth_service import validate_credentials  # noqa: E402


def _make_in_memory_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    conn.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("alice", generate_password_hash("alicepass"))
    )
    conn.commit()
    return conn


class TestValidateCredentials(unittest.TestCase):

    def setUp(self):
        self.mem_conn = _make_in_memory_db()
        self.patcher_get = patch("services.auth_service.get_connection", return_value=self.mem_conn)
        self.patcher_close = patch("services.auth_service.close_connection", side_effect=lambda c: None)
        self.patcher_get.start()
        self.patcher_close.start()

    def tearDown(self):
        self.patcher_get.stop()
        self.patcher_close.stop()
        self.mem_conn.close()

    def test_valid_credentials_return_user_dict(self):
        result = validate_credentials("alice", "alicepass")
        self.assertIsNotNone(result)
        self.assertEqual(result["username"], "alice")
        self.assertIn("id", result)
        self.assertNotIn("password", result)

    def test_wrong_password_returns_none(self):
        self.assertIsNone(validate_credentials("alice", "wrongpassword"))

    def test_unknown_username_returns_none(self):
        self.assertIsNone(validate_credentials("nobody", "alicepass"))

    def test_empty_username_returns_none(self):
        self.assertIsNone(validate_credentials("", "alicepass"))

    def test_empty_password_returns_none(self):
        self.assertIsNone(validate_credentials("alice", ""))

    def test_both_empty_returns_none(self):
        self.assertIsNone(validate_credentials("", ""))


if __name__ == "__main__":
    unittest.main()
