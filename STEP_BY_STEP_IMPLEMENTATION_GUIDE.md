# Banking Web Application - Step-by-Step Implementation Guide

> **Reference:** IMPLEMENTATION_PLAN.md
> **Purpose:** Plain-English instructions covering how each part is built and why each decision is made.

## Table of Contents
1. Environment Setup
2. Backend Implementation
3. Frontend Implementation
4. Integration Steps
5. Validation Rules
6. Testing
7. Deployment

---

## 1. Environment Setup

### 1.1 Install Python
Verify Python 3.9+ is installed. Python includes pip and venv built in.

### 1.2 Create a Virtual Environment
Create a virtual environment at the project root named `venv`. Activate it:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

All pip installs go into this isolated environment.

### 1.3 Install Dependencies
Create `BACKEND/requirements.txt` with Flask and Werkzeug, then run:
```bash
pip install -r BACKEND/requirements.txt
```

### 1.4 Create Folder Structure
```
Banking_app/
|- FRONTEND/templates/
|- BACKEND/routes/       <- add __init__.py
|- BACKEND/services/     <- add __init__.py
|- BACKEND/database/     <- add __init__.py
|- BACKEND/tests/        <- add __init__.py
```

---

## 2. Backend Implementation

### 2.1 config.py
Centralise all settings: SECRET_KEY, DATABASE_PATH, DEBUG, TEMPLATE_FOLDER.
Use os.environ.get() so values can be overridden in production without changing code.

### 2.2 database/db.py
Write get_connection() and close_connection() functions.
Use sqlite3.Row as the row factory so columns are accessible by name.
Read DATABASE_PATH from Flask app context when available (enables test injection),
fall back to config.py when running as a standalone script.

### 2.3 database/init_db.py
Create three tables:
- users: id, username, hashed_password
- accounts: id, user_id (FK), balance
- transactions: id, account_id (FK), type (deposit/withdrawal), amount, created_at

Seed two test customers. Hash all passwords with generate_password_hash() before storing.
Make the script idempotent - check for existing rows before inserting.

### 2.4 services/auth_service.py
validate_credentials(username, password):
- Query users table for the given username
- If not found, return None (do not reveal which field failed)
- Use check_password_hash() to verify the password
- Return dict with id and username on success, None on failure

### 2.5 services/account_service.py
get_balance(user_id): fetch balance from accounts table.

deposit(user_id, amount):
1. Fetch account row
2. Compute new_balance = current + amount
3. UPDATE accounts SET balance
4. INSERT transaction record (type='deposit')
5. COMMIT - return 'success' or 'error'

withdraw(user_id, amount):
1. Fetch account row
2. If amount > balance: return 'insufficient_funds' (no DB change)
3. Compute new_balance = current - amount
4. UPDATE accounts SET balance
5. INSERT transaction record (type='withdrawal')
6. COMMIT - return 'success', 'insufficient_funds', or 'error'

All writes are wrapped in try/except with conn.rollback() on failure.

### 2.6 routes/auth.py (Blueprint)
GET /login: if session has user_id, redirect to /dashboard; else render login.html
POST /login: validate form fields, call validate_credentials, create session, redirect
GET /logout: session.clear(), flash message, redirect to /login

Use Post-Redirect-Get pattern on all POST handlers.

### 2.7 routes/account.py (Blueprint)
Write login_required decorator: checks session["user_id"], redirects to /login if absent.
Apply to all routes in this file.

Write _parse_amount(raw): validates the form amount string.
Rejects: empty, non-numeric, <= 0, >2 decimal places, >1,000,000.

GET /dashboard: get_balance(user_id), render dashboard.html with username and balance
GET/POST /deposit: render form; process deposit; flash success/error; redirect
GET/POST /withdraw: render form with balance; process withdrawal; handle insufficient_funds specially

### 2.8 app.py
Create Flask app with template_folder pointing to FRONTEND/templates/.
Load config, register both Blueprints, add root redirect / -> /login.
Register 404 and 500 error handlers.
Add if __name__ == '__main__' guard to start dev server.

### 2.9 Error Handling
- 404: render 404.html with a link back to login
- 500: render 500.html (only active when DEBUG=False)
- Form validation: flash specific error, redirect back to form
- DB errors: rollback transaction, return 'error' signal, flash generic message
- Never expose stack traces or internal paths to users in production

---

## 3. Frontend Implementation

### 3.1 base.html
Master layout extended by all pages. Contains:
- Bootstrap 5 CSS and JS CDN links
- Dark navbar with brand, conditional nav links (only if session.user_id)
- Flash message container using get_flashed_messages(with_categories=True)
- Bootstrap alerts with dismiss buttons
- Empty block content placeholder for child templates

### 3.2 login.html
Extends base.html. Centred Bootstrap card with:
- Username (type=text, required) and password (type=password, required) inputs
- Login submit button
- Demo credentials hint in card footer

### 3.3 dashboard.html
Extends base.html. Shows:
- Welcome card with username
- Balance card with large formatted balance (balance-amount CSS class)
- Deposit and Withdraw action cards with links

### 3.4 deposit.html
Extends base.html. Centred card with:
- number input (min=0.01, step=0.01, required)
- Submit and Back to Dashboard buttons

### 3.5 withdraw.html
Extends base.html. Centred card with:
- Available balance displayed at top for reference
- number input (min=0.01, step=0.01, max=balance, required)
- Submit and Back to Dashboard buttons

---

## 4. Integration Steps

### 4.1 Template Folder
Pass template_folder=config.TEMPLATE_FOLDER when creating the Flask app.
Verify by visiting /login - styled page confirms Flask found the templates.

### 4.2 Blueprint Registration
app.register_blueprint(auth_bp) and app.register_blueprint(account_bp).
No URL prefix - routes stay at /login, /dashboard, etc.

### 4.3 Form Wiring
Every form action must exactly match a route URL.
Every input name must match request.form.get() keys in the route.
Every method=POST must match @route methods=["POST"].

### 4.4 SQLite Connection
Option A (used here): open/close connection inside each service function.
Option B: use Flask g object for per-request connection.
Confirm wiring by running init_db.py and checking banking.db is created.

### 4.5 Session Verification
Manual checks:
1. Visit /dashboard without login -> should redirect to /login
2. Login with correct credentials -> should reach /dashboard
3. Inspect browser cookies -> session cookie should be present (encrypted)
4. Logout -> cookie should be cleared
5. Browser Back -> should redirect to /login

---

## 5. Validation Rules

### Login
| Rule | Enforced Where | On Failure |
|---|---|---|
| Username not empty | HTML required + Flask route | Flash 'Username is required.' |
| Password not empty | HTML required + Flask route | Flash 'Password is required.' |
| Username exists | auth_service | Flash 'Invalid username or password.' |
| Password matches hash | check_password_hash | Flash 'Invalid username or password.' |

Always use a combined error message - never reveal which field failed.

### Deposit / Withdrawal
| Rule | On Failure |
|---|---|
| Amount not empty | Flash 'Amount is required.' |
| Amount is a valid number | Flash 'Please enter a valid number.' |
| Amount > 0 | Flash 'Amount must be greater than zero.' |
| Amount <= 2 decimal places | Flash 'Amount cannot have more than 2 decimal places.' |
| Withdrawal <= balance | Flash 'Insufficient funds.' (from service) |

Always re-fetch balance from DB at withdrawal time - never trust the page-displayed value.

---

## 6. Testing

### 6.1 Unit Tests (tests/test_auth_service.py, tests/test_account_service.py)
Test individual service functions in isolation using in-memory SQLite.
Patch get_connection() and close_connection() with unittest.mock.
Cover: valid credentials, wrong password, unknown user, empty fields.
Cover: get_balance, deposit success/error, withdraw success/insufficient_funds/error.

### 6.2 Integration Tests (tests/test_routes.py)
Use Flask app.test_client() with a temporary SQLite file per test class.
Each test method gets its own client instance (setUp/tearDown) to prevent session bleed.
Test all routes: GET/POST login, logout, dashboard, deposit, withdraw, 404.

### 6.3 Run Tests
```bash
# From BACKEND/
python -m pytest tests/ -v
```
Expected: 50 tests passing.

---

## 7. Deployment

### 7.1 Run Locally
1. Activate venv
2. pip install -r BACKEND/requirements.txt
3. cd BACKEND && python database/init_db.py
4. python app.py
5. Open http://127.0.0.1:5000

### 7.2 Production
| Concern | Change |
|---|---|
| Debug mode | Set FLASK_DEBUG=false |
| Secret key | Set FLASK_SECRET_KEY env var to a long random string |
| WSGI server | Use Gunicorn: gunicorn --workers 2 app:app |
| HTTPS | Use Nginx reverse proxy with TLS |
| Static files | Serve from Nginx, not Flask |
| Dependencies | Pin versions with pip freeze |
