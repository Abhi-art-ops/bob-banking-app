"""
init_db.py - Database initialisation and seed script.

Usage (from Banking_app/BACKEND/):
    python database/init_db.py
"""

import os
import sqlite3
import sys
from datetime import datetime, timezone

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from config import DATABASE_PATH  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT    NOT NULL UNIQUE,
    password TEXT    NOT NULL
);
"""

CREATE_ACCOUNTS_TABLE = """
CREATE TABLE IF NOT EXISTS accounts (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    balance REAL    NOT NULL DEFAULT 0.0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id         INTEGER  PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER  NOT NULL,
    type       TEXT     NOT NULL CHECK(type IN ('deposit', 'withdrawal')),
    amount     REAL     NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);
"""

SEED_CUSTOMERS = [
    {"username": "john_doe",   "password": "password123", "balance": 5000.00},
    {"username": "jane_smith", "password": "securepass",  "balance": 12500.50},
]


def init_db() -> None:
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        cursor = conn.cursor()
        cursor.execute(CREATE_USERS_TABLE)
        cursor.execute(CREATE_ACCOUNTS_TABLE)
        cursor.execute(CREATE_TRANSACTIONS_TABLE)
        conn.commit()
        print("[init_db] Tables created (or already exist).")
        for customer in SEED_CUSTOMERS:
            existing = cursor.execute(
                "SELECT id FROM users WHERE username = ?", (customer["username"],)
            ).fetchone()
            if existing:
                print(f"[init_db] Customer '{customer['username']}' already exists - skipping.")
                continue
            hashed_pw = generate_password_hash(customer["password"])
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (customer["username"], hashed_pw)
            )
            user_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO accounts (user_id, balance) VALUES (?, ?)",
                (user_id, customer["balance"])
            )
            account_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO transactions (account_id, type, amount, created_at) VALUES (?, ?, ?, ?)",
                (account_id, "deposit", customer["balance"],
                 datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
            print(f"[init_db] Customer '{customer['username']}' created with balance ${customer['balance']:.2f}.")
        print("[init_db] Database initialisation complete.")
        print(f"[init_db] Database location: {DATABASE_PATH}")
    except Exception as exc:
        conn.rollback()
        print(f"[init_db] ERROR: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
