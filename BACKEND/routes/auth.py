"""
routes/auth.py - Authentication Blueprint.

GET  /login  - render login form (redirect to /dashboard if already logged in)
POST /login  - validate credentials, create session, redirect to /dashboard
GET  /logout - clear session, flash confirmation, redirect to /login
"""

import os
import sys

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import validate_credentials  # noqa: E402

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET"])
def login_get():
    if session.get("user_id"):
        return redirect(url_for("account.dashboard"))
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username:
        flash("Username is required.", "danger")
        return redirect(url_for("auth.login_get"))

    if not password:
        flash("Password is required.", "danger")
        return redirect(url_for("auth.login_get"))

    user = validate_credentials(username, password)

    if user is None:
        flash("Invalid username or password.", "danger")
        return redirect(url_for("auth.login_get"))

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]

    flash(f"Welcome back, {user['username']}!", "success")
    return redirect(url_for("account.dashboard"))


@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login_get"))
