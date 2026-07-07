# Banking Web Application - Implementation Plan

> **Document Type:** High-Level Planning
> **Technology Stack:** HTML + Bootstrap (Frontend) - Python Flask (Backend) - SQLite (Database)
> **Status:** Complete

## 1. Solution Overview

### Objective
Build a lightweight, browser-based banking web application that allows registered customers to securely log in, view their account balance, and perform basic fund transactions (deposit and withdrawal).

### Scope
| In Scope | Out of Scope |
|---|---|
| Customer login and logout | Admin portal |
| View account balance | Multi-currency support |
| Deposit funds | Inter-account transfers |
| Withdraw funds | Payment gateway integration |
| Session-based authentication | Mobile native application |
| Responsive UI (Bootstrap) | Email / SMS notifications |

### Functional Requirements
1. Customer can log in using credentials (username + password).
2. After login, customer is redirected to a personal dashboard.
3. Dashboard displays customer name and current account balance.
4. Customer can deposit a positive monetary amount.
5. Customer can withdraw a positive amount not exceeding their balance.
6. Customer can log out, terminating the active session.
7. Unauthenticated users are redirected to the login page.

### Non-Functional Requirements
| Attribute | Expectation |
|---|---|
| Security | Passwords stored as hashed values; session tokens managed server-side |
| Usability | Responsive layout via Bootstrap; clear success/error feedback |
| Maintainability | Clean separation between frontend, backend, and data layer |
| Portability | SQLite file-based database, no external server required |

## 2. High-Level Architecture

```
Browser -> FRONTEND (HTML + Bootstrap + Jinja2)
        -> BACKEND (Flask routes + services)
        -> DATABASE (SQLite)
```

### Request Lifecycle
1. Browser submits HTTP request
2. Flask router matches URL to handler
3. Auth middleware checks session
4. Route handler validates input, calls service
5. Service layer reads/writes database
6. Response rendered and returned to browser

## 3. Component Design

### Frontend (FRONTEND/)
- Jinja2 HTML templates for login, dashboard, deposit, withdraw
- Bootstrap for responsive layout, buttons, alerts
- Flash messages from server rendered as Bootstrap alerts
- Shared base.html for navbar and layout

### Backend (BACKEND/)
- Flask routes: /login, /logout, /dashboard, /deposit, /withdraw
- Session-based auth using Flask session object
- Password hashing via werkzeug.security
- Business rules enforced in service layer

### Database (BACKEND/database/)
- Tables: users, accounts, transactions
- SQLite file, no network access required
- Init script creates schema and seeds test data

## 4. Folder Structure

```
Banking_app/
|- FRONTEND/templates/   # Jinja2 HTML templates
|- BACKEND/
   |- app.py             # Flask factory + entry point
   |- config.py          # Centralised configuration
   |- requirements.txt   # Python dependencies
   |- routes/            # Flask Blueprints
   |- services/          # Business logic
   |- database/          # SQLite layer
   |- tests/             # Unit + integration tests
```

## 5. Implementation Roadmap

| Phase | Goal | Status |
|---|---|---|
| 1 | Scaffolding - folder structure, config | Done |
| 2 | Database - schema, seed script | Done |
| 3 | Authentication - login, logout, session guard | Done |
| 4 | Dashboard - balance display | Done |
| 5 | Transactions - deposit, withdrawal | Done |
| 6 | Integration and testing | Done |
