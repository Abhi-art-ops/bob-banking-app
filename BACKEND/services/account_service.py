"""
account_service.py - Account and transaction business logic.

Return convention:
  'success'            - operation completed
  'insufficient_funds' - withdrawal rejected (amount > balance)
  'error'              - unexpected exception (transaction rolled back)
  None                 - no account found (get_balance)
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_connection, close_connection  # noqa: E402


def get_balance(user_id: int):
    conn = None
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT balance FROM accounts WHERE user_id = ?", (user_id,)
        ).fetchone()
        return float(row["balance"]) if row else None
    finally:
        close_connection(conn)


def deposit(user_id: int, amount: float) -> str:
    conn = None
    try:
        conn = get_connection()
        account_row = conn.execute(
            "SELECT id, balance FROM accounts WHERE user_id = ?", (user_id,)
        ).fetchone()
        if account_row is None:
            return "error"
        account_id = account_row["id"]
        new_balance = float(account_row["balance"]) + amount
        conn.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, account_id))
        conn.execute(
            "INSERT INTO transactions (account_id, type, amount, created_at) VALUES (?, 'deposit', ?, ?)",
            (account_id, amount, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return "success"
    except Exception:
        if conn:
            conn.rollback()
        return "error"
    finally:
        close_connection(conn)


def withdraw(user_id: int, amount: float) -> str:
    conn = None
    try:
        conn = get_connection()
        account_row = conn.execute(
            "SELECT id, balance FROM accounts WHERE user_id = ?", (user_id,)
        ).fetchone()
        if account_row is None:
            return "error"
        current_balance = float(account_row["balance"])
        if amount > current_balance:
            return "insufficient_funds"
        account_id = account_row["id"]
        new_balance = current_balance - amount
        conn.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, account_id))
        conn.execute(
            "INSERT INTO transactions (account_id, type, amount, created_at) VALUES (?, 'withdrawal', ?, ?)",
            (account_id, amount, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return "success"
    except Exception:
        if conn:
            conn.rollback()
        return "error"
    finally:
        close_connection(conn)
