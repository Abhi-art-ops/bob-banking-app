"""
config.py - Centralised configuration for the Banking application.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = os.environ.get(
    "FLASK_SECRET_KEY",
    "dev-secret-key-change-in-production-xK9#mP2@qL7"
)

DATABASE_PATH = os.path.join(BASE_DIR, "database", "banking.db")

DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

TEMPLATE_FOLDER = os.path.join(BASE_DIR, "..", "FRONTEND", "templates")
