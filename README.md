# SecureBank — Banking Web Application

A lightweight full-stack banking application built with **Python Flask**, **Bootstrap 5**, and **SQLite**.

---

## Features

| Feature | Details |
|---|---|
| Customer Login | Session-based auth with hashed passwords (Werkzeug) |
| Dashboard | Displays username and live account balance |
| Deposit Funds | Validated deposits with atomic DB writes |
| Withdraw Funds | Validated withdrawals with insufficient-funds guard |
| Logout | Full session clear and redirect |
| Error pages | Custom 404 and 500 templates |

---

## Quick Start

### 1. Create and activate a virtual environment

```bash
# From Banking_app/ root
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r BACKEND/requirements.txt
```

### 3. Initialise the database

```bash
cd BACKEND
python database/init_db.py
```

### 4. Run the application

```bash
# From BACKEND/
python app.py
```

Open your browser at **http://127.0.0.1:5000**

---

## Demo Credentials

| Username | Password | Starting Balance |
|---|---|---|
| `john_doe` | `password123` | $5,000.00 |
| `jane_smith` | `securepass` | $12,500.50 |

---

## Running Tests

```bash
# From BACKEND/
python -m pytest tests/ -v
```

**50 tests** — 20 unit tests + 30 integration tests (all passing).

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5 + Bootstrap 5 + Bootstrap Icons |
| Templating | Jinja2 (served by Flask) |
| Backend | Python 3.9+ · Flask 3.0 |
| Auth | Werkzeug `generate_password_hash` / `check_password_hash` |
| Database | SQLite 3 (built-in) |
| Tests | Python `unittest` + Flask test client + pytest |

---

## Security Notes

- Passwords **never stored in plain text** — Werkzeug PBKDF2 hashing.
- Session cookies cryptographically signed with `SECRET_KEY`.
- Login errors use a combined message to prevent username enumeration.
- All protected routes enforce `@login_required`.
- Database writes use explicit transactions with rollback on failure.

---

## Production Checklist

- [ ] Set `FLASK_SECRET_KEY` environment variable
- [ ] Set `FLASK_DEBUG=false`
- [ ] Run behind Gunicorn: `gunicorn --workers 2 app:app`
- [ ] Terminate HTTPS at a reverse proxy (Nginx / Caddy)
