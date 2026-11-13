# Luma Login — FastAPI + PostgreSQL (Debugged)

Runing Command: uvicorn app.main:app --reload

A responsive glossy login/signup page backed by FastAPI and PostgreSQL.

## Features
- Responsive glass-inspired login and signup UI.
- User records saved in PostgreSQL `users` table.
- Passwords stored as Argon2 hashes (never plaintext).
- Successful logins update `last_login_at` and `login_count`.
- JWT access token returned after signup/login.
- `/health`, `/db-check`, and interactive `/docs` endpoints.
- Database password configured separately, so `@` and other special characters work without URL encoding.

## 1. Create the database
In pgAdmin, create a database named **Ateeb** (or change `DB_NAME` in `.env`). The PostgreSQL server must be running.

## 2. Configure `.env`
Copy `.env.example` to `.env` in this project folder. Then set your own PostgreSQL password:

```env
DB_USER=postgres
DB_PASSWORD=your_actual_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Ateeb
SECRET_KEY=replace_with_a_long_random_secret_key_at_least_32_chars
```

**Important:** Use the raw password in `DB_PASSWORD` (for example, if it contains `@`, type `@` normally). Do not put `DATABASE_URL` in this file when using the `DB_*` settings. Never share or commit `.env`.

## 3. Install and run (Windows PowerShell)
Run these commands from the folder containing `requirements.txt`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

Open **http://127.0.0.1:8000**.

## 4. Verify everything
1. Open `http://127.0.0.1:8000/health` — app should return `{"status":"ok", ...}`.
2. Open `http://127.0.0.1:8000/db-check` — status should be `connected`.
3. Open `http://127.0.0.1:8000/docs` — API documentation.
4. Create an account on the page, then inspect the `users` table in pgAdmin.

## API routes
- `POST /api/auth/signup` — `{ "full_name": "Your Name", "email": "you@example.com", "password": "at-least-8-chars" }`
- `POST /api/auth/login` — `{ "email": "you@example.com", "password": "at-least-8-chars" }`
- `GET /api/auth/me` — send `Authorization: Bearer YOUR_TOKEN`

## Troubleshooting
- `Could not parse SQLAlchemy URL`: use the separate `DB_*` variables above; remove the old `DATABASE_URL` line.
- `connection refused`: start the PostgreSQL Windows service and confirm port `5432`.
- `database "Ateeb" does not exist`: create it in pgAdmin or change `DB_NAME` to an existing database.
- `password authentication failed`: check `DB_USER` and `DB_PASSWORD`.
- `No module named ...`: activate `.venv` and run `pip install -r requirements.txt`.

This is a local learning project. Before public deployment, configure HTTPS, a strong secret, rate limiting, secure token storage/cookies, email verification, password reset, and database migrations. Do not expose your local PostgreSQL server directly to the internet.
