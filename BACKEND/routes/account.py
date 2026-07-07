"""
routes/account.py - Account management Blueprint.

All routes are protected by the login_required decorator.

GET  /dashboard - display balance and navigation
GET  /deposit   - render deposit form
POST /deposit   - process deposit, update balance, redirect
GET  /withdraw  - render withdrawal form (with current balance)
POST /withdraw  - process withdrawal, update balance, redirect
"""

import os
import sys
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.account_service import deposit, get_balance, withdraw  # noqa: E402

account_bp = Blueprint("account", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login_get"))
        return f(*args, **kwargs)
    return decorated


def _parse_amount(raw: str):
    if not raw or not raw.strip():
        return None, "Amount is required."
    try:
        value = Decimal(raw.strip())
    except InvalidOperation:
        return None, "Please enter a valid number."
    if value <= 0:
        return None, "Amount must be greater than zero."
    if value != value.quantize(Decimal("0.01")):
        return None, "Amount cannot have more than 2 decimal places."
    if value > Decimal("1000000"):
        return None, "Amount exceeds the maximum allowed value of $1,000,000."
    return float(value), None


@account_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    user_id = session["user_id"]
    username = session["username"]
    balance = get_balance(user_id)
    if balance is None:
        flash("Account not found. Please contact support.", "danger")
        session.clear()
        return redirect(url_for("auth.login_get"))
    return render_template("dashboard.html", username=username, balance=balance)


@account_bp.route("/deposit", methods=["GET"])
@login_required
def deposit_get():
    return render_template("deposit.html")


@account_bp.route("/deposit", methods=["POST"])
@login_required
def deposit_post():
    raw_amount = request.form.get("amount", "")
    amount, error = _parse_amount(raw_amount)
    if error:
        flash(error, "danger")
        return redirect(url_for("account.deposit_get"))
    result = deposit(session["user_id"], amount)
    if result == "success":
        flash(f"Deposit of ${amount:,.2f} was successful.", "success")
        return redirect(url_for("account.dashboard"))
    flash("Deposit failed. Please try again.", "danger")
    return redirect(url_for("account.deposit_get"))


@account_bp.route("/withdraw", methods=["GET"])
@login_required
def withdraw_get():
    balance = get_balance(session["user_id"])
    return render_template("withdraw.html", balance=balance)


@account_bp.route("/withdraw", methods=["POST"])
@login_required
def withdraw_post():
    raw_amount = request.form.get("amount", "")
    amount, error = _parse_amount(raw_amount)
    if error:
        flash(error, "danger")
        return redirect(url_for("account.withdraw_get"))
    result = withdraw(session["user_id"], amount)
    if result == "success":
        flash(f"Withdrawal of ${amount:,.2f} was successful.", "success")
        return redirect(url_for("account.dashboard"))
    if result == "insufficient_funds":
        flash(
            f"Insufficient funds. You attempted to withdraw ${amount:,.2f} "
            f"but your available balance is less than that amount.",
            "danger"
        )
        return redirect(url_for("account.withdraw_get"))
    flash("Withdrawal failed. Please try again.", "danger")
    return redirect(url_for("account.withdraw_get"))
