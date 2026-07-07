"""
tests/test_account_service.py - Unit tests for account_service functions.
Tests run against in-memory SQLite - no banking.db touched.
"""

import os
import sqlite3
import sys
import unittest
from unittest.mock import patch
from werkzeug.security import generate_password_hash

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from services.account_service import deposit, get_balance, withdraw  # noqa: E402


def _make_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL);
        CREATE TABLE accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL UNIQUE, balance REAL NOT NULL DEFAULT 0.0, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL, type TEXT NOT NULL CHECK(type IN ('deposit','withdrawal')), amount REAL NOT NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE);
    """)
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("bob", generate_password_hash("bobpass")))
    conn.execute("INSERT INTO accounts (user_id, balance) VALUES (?, ?)", (1, 1000.00))
    conn.commit()
    return conn


def _patch_db(test_case, conn):
    p_get = patch("services.account_service.get_connection", return_value=conn)
    p_close = patch("services.account_service.close_connection", side_effect=lambda c: None)
    p_get.start()
    p_close.start()
    test_case.addCleanup(p_get.stop)
    test_case.addCleanup(p_close.stop)


class TestGetBalance(unittest.TestCase):
    def setUp(self): self.conn = _make_db(); _patch_db(self, self.conn)
    def tearDown(self): self.conn.close()
    def test_returns_correct_balance(self): self.assertAlmostEqual(get_balance(1), 1000.00, places=2)
    def test_unknown_user_returns_none(self): self.assertIsNone(get_balance(999))


class TestDeposit(unittest.TestCase):
    def setUp(self): self.conn = _make_db(); _patch_db(self, self.conn)
    def tearDown(self): self.conn.close()
    def test_deposit_returns_success(self): self.assertEqual(deposit(1, 250.00), "success")
    def test_deposit_increases_balance(self):
        deposit(1, 250.00)
        self.assertAlmostEqual(self.conn.execute("SELECT balance FROM accounts WHERE user_id=1").fetchone()["balance"], 1250.00, places=2)
    def test_deposit_records_transaction(self):
        deposit(1, 100.00)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) as cnt FROM transactions WHERE type='deposit'").fetchone()["cnt"], 1)
    def test_multiple_deposits_accumulate(self):
        deposit(1, 100.00); deposit(1, 200.00)
        self.assertAlmostEqual(self.conn.execute("SELECT balance FROM accounts WHERE user_id=1").fetchone()["balance"], 1300.00, places=2)
    def test_deposit_unknown_user_returns_error(self): self.assertEqual(deposit(999, 100.00), "error")


class TestWithdraw(unittest.TestCase):
    def setUp(self): self.conn = _make_db(); _patch_db(self, self.conn)
    def tearDown(self): self.conn.close()
    def test_withdraw_returns_success(self): self.assertEqual(withdraw(1, 200.00), "success")
    def test_withdraw_decreases_balance(self):
        withdraw(1, 200.00)
        self.assertAlmostEqual(self.conn.execute("SELECT balance FROM accounts WHERE user_id=1").fetchone()["balance"], 800.00, places=2)
    def test_withdraw_records_transaction(self):
        withdraw(1, 100.00)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) as cnt FROM transactions WHERE type='withdrawal'").fetchone()["cnt"], 1)
    def test_withdraw_exact_balance_succeeds(self):
        self.assertEqual(withdraw(1, 1000.00), "success")
        self.assertAlmostEqual(self.conn.execute("SELECT balance FROM accounts WHERE user_id=1").fetchone()["balance"], 0.00, places=2)
    def test_withdraw_exceeds_balance_returns_insufficient_funds(self): self.assertEqual(withdraw(1, 1001.00), "insufficient_funds")
    def test_withdraw_exceeds_balance_does_not_modify_db(self):
        withdraw(1, 9999.00)
        self.assertAlmostEqual(self.conn.execute("SELECT balance FROM accounts WHERE user_id=1").fetchone()["balance"], 1000.00, places=2)
    def test_withdraw_unknown_user_returns_error(self): self.assertEqual(withdraw(999, 100.00), "error")


if __name__ == "__main__":
    unittest.main()
