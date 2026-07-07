"""
tests/test_routes.py - Integration tests for all Flask routes.

Uses Flask's built-in test client to send real HTTP requests through the
full stack (routes -> services -> database) without starting a TCP server.
Each test class gets its own temporary SQLite DB and fresh client instance.

Coverage:
  GET/POST /login, /logout, /dashboard, /deposit, /withdraw, 404 handler
"""

import os
import re
import sqlite3
import sys
import unittest

from werkzeug.security import generate_password_hash

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app import create_app  # noqa: E402


def _build_test_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL UNIQUE, balance REAL NOT NULL DEFAULT 0.0, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL, type TEXT NOT NULL CHECK(type IN ('deposit','withdrawal')), amount REAL NOT NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE);
    """)
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("testuser", generate_password_hash("testpass")))
    conn.execute("INSERT INTO accounts (user_id, balance) VALUES (?, ?)", (1, 2000.00))
    conn.commit()
    conn.close()


class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.TEST_DB = os.path.join(BACKEND_DIR, "tests", f"_test_{cls.__name__}.db")
        _build_test_db(cls.TEST_DB)
        cls.app = create_app({
            "TESTING": True, "DEBUG": False,
            "SECRET_KEY": "test-secret-key-not-for-production",
            "DATABASE_PATH": cls.TEST_DB,
        })

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.TEST_DB):
            os.remove(cls.TEST_DB)

    def setUp(self):
        self.client = self.app.test_client()
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def _login(self, username="testuser", password="testpass"):
        return self.client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    def _logout(self):
        return self.client.get("/logout", follow_redirects=True)


class TestRootRedirect(BaseTestCase):
    def test_root_redirects_to_login(self):
        resp = self.client.get("/", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Customer Login", resp.data)


class TestLoginGet(BaseTestCase):
    def test_login_page_renders(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Customer Login", resp.data)

    def test_login_redirects_if_already_authenticated(self):
        self._login()
        resp = self.client.get("/login", follow_redirects=True)
        self.assertIn(b"My Dashboard", resp.data)


class TestLoginPost(BaseTestCase):
    def test_valid_credentials_redirect_to_dashboard(self):
        resp = self._login()
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"My Dashboard", resp.data)

    def test_invalid_password_stays_on_login(self):
        self.assertIn(b"Invalid username or password", self._login(password="wrongpassword").data)

    def test_unknown_username_stays_on_login(self):
        self.assertIn(b"Invalid username or password", self._login(username="nobody", password="pass").data)

    def test_empty_username_shows_error(self):
        self.assertIn(b"Username is required", self._login(username="", password="testpass").data)

    def test_empty_password_shows_error(self):
        self.assertIn(b"Password is required", self._login(username="testuser", password="").data)


class TestLogout(BaseTestCase):
    def test_logout_clears_session_and_redirects(self):
        self._login()
        self.assertIn(b"logged out", self._logout().data)

    def test_after_logout_dashboard_redirects_to_login(self):
        self._login()
        self._logout()
        self.assertIn(b"Customer Login", self.client.get("/dashboard", follow_redirects=True).data)


class TestDashboard(BaseTestCase):
    def test_dashboard_requires_login(self):
        self.assertIn(b"Customer Login", self.client.get("/dashboard", follow_redirects=True).data)

    def test_dashboard_shows_username(self):
        self._login()
        self.assertIn(b"testuser", self.client.get("/dashboard").data)

    def test_dashboard_shows_balance(self):
        self._login()
        self.assertIn(b"2000.00", self.client.get("/dashboard").data)


class TestDeposit(BaseTestCase):
    def test_deposit_page_renders(self):
        self._login()
        resp = self.client.get("/deposit")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Deposit Funds", resp.data)

    def test_deposit_requires_login(self):
        self.assertIn(b"Customer Login", self.client.get("/deposit", follow_redirects=True).data)

    def test_valid_deposit_redirects_to_dashboard(self):
        self._login()
        resp = self.client.post("/deposit", data={"amount": "500"}, follow_redirects=True)
        self.assertIn(b"My Dashboard", resp.data)
        self.assertIn(b"successful", resp.data)

    def test_deposit_increases_balance_on_dashboard(self):
        self._login()
        self.client.post("/deposit", data={"amount": "500"})
        self.assertIn(b"2500.00", self.client.get("/dashboard").data)

    def test_deposit_zero_shows_error(self):
        self._login()
        self.assertIn(b"greater than zero", self.client.post("/deposit", data={"amount": "0"}, follow_redirects=True).data)

    def test_deposit_negative_shows_error(self):
        self._login()
        self.assertIn(b"greater than zero", self.client.post("/deposit", data={"amount": "-100"}, follow_redirects=True).data)

    def test_deposit_non_numeric_shows_error(self):
        self._login()
        self.assertIn(b"valid number", self.client.post("/deposit", data={"amount": "abc"}, follow_redirects=True).data)

    def test_deposit_empty_shows_error(self):
        self._login()
        self.assertIn(b"required", self.client.post("/deposit", data={"amount": ""}, follow_redirects=True).data)


class TestWithdraw(BaseTestCase):
    def test_withdraw_page_renders_with_balance(self):
        self._login()
        resp = self.client.get("/withdraw")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Withdraw Funds", resp.data)

    def test_withdraw_requires_login(self):
        self.assertIn(b"Customer Login", self.client.get("/withdraw", follow_redirects=True).data)

    def test_valid_withdrawal_redirects_to_dashboard(self):
        self._login()
        resp = self.client.post("/withdraw", data={"amount": "100"}, follow_redirects=True)
        self.assertIn(b"My Dashboard", resp.data)
        self.assertIn(b"successful", resp.data)

    def test_valid_withdrawal_updates_balance(self):
        self._login()

        def _get_balance(client):
            resp = client.get("/dashboard")
            assert resp.status_code == 200
            match = re.search(rb'balance-amount[^>]*>\s*\$([\d,]+\.\d{2})', resp.data)
            assert match, "balance-amount not found"
            return float(match.group(1).replace(b",", b""))

        bal_before = _get_balance(self.client)
        self.client.post("/withdraw", data={"amount": "100"})
        bal_after = _get_balance(self.client)
        self.assertAlmostEqual(bal_after, bal_before - 100.00, places=2)

    def test_withdraw_exceeding_balance_shows_error(self):
        self._login()
        self.assertIn(b"Insufficient funds", self.client.post("/withdraw", data={"amount": "999999"}, follow_redirects=True).data)

    def test_withdraw_zero_shows_error(self):
        self._login()
        self.assertIn(b"greater than zero", self.client.post("/withdraw", data={"amount": "0"}, follow_redirects=True).data)

    def test_withdraw_negative_shows_error(self):
        self._login()
        self.assertIn(b"greater than zero", self.client.post("/withdraw", data={"amount": "-50"}, follow_redirects=True).data)

    def test_withdraw_non_numeric_shows_error(self):
        self._login()
        self.assertIn(b"valid number", self.client.post("/withdraw", data={"amount": "xyz"}, follow_redirects=True).data)


class TestErrorHandlers(BaseTestCase):
    def test_404_renders_custom_page(self):
        resp = self.client.get("/this/does/not/exist")
        self.assertEqual(resp.status_code, 404)
        self.assertIn(b"404", resp.data)


if __name__ == "__main__":
    unittest.main()
