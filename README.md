# Cinema Reservation System

An academic web application for browsing films and reserving cinema tickets. Built for the Network-Centric Information Systems course at the University of Piraeus using Python, Flask, MongoDB, Jinja templates, HTML and CSS.

## Features

- Browse the current films and submit a registration request.
- Sign in as a user to book tickets and view your reservations.
- Approve or reject registrations as an administrator.
- Manage users and films from the administration pages.

## Run locally on Windows

Install Python 3.10+ (with the `py` launcher) and Docker Desktop, then start Docker Desktop. Unzip the project into a folder. Double-click `start_windows.bat` once: it creates `.env` and stops so you can edit it. Set a unique `ADMIN_PASSWORD` and a random `FLASK_SECRET_KEY` in `.env`; for example, generate the secret in PowerShell with `py -c "import secrets; print(secrets.token_hex(32))"`. Keep the `.env` file private. Double-click `start_windows.bat` again. It starts MongoDB, creates a Python virtual environment, installs dependencies, and starts the app.

Open `http://127.0.0.1:5000/`. To stop the web app, press Ctrl+C in its terminal. To stop MongoDB, run `docker compose down` from the project folder. The `mongo_data` Docker volume retains your local data across restarts; `docker compose down -v` **deletes** that data.

## Run locally on Linux/macOS

With Python 3.10+ and Docker installed, create `.env` from `.env.example` and replace the two placeholder secrets. Then:

```bash
docker compose up -d
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The application loads `.env` automatically. MongoDB uses the `DigitalCinema` database. The app creates example films on the first visit and creates the initial admin account when opening `/login`, if both `ADMIN_USERNAME` and `ADMIN_PASSWORD` are set. The country list comes from an external API; when it is unavailable, Greece is shown as a fallback.

## Repository layout

- `app.py`: Flask routes and MongoDB operations.
- `templates/`: Jinja/HTML pages.
- `static/`: styles.
- `compose.yaml`: local MongoDB service.
- `start_windows.bat`: setup and start command for Windows.
- `.env.example`: example local configuration; `.env` itself is excluded from Git.

## Academic project notes

This repository is a cleaned presentation of the original coursework. The original included a hard-coded Flask session secret, a default `admin/admin` account and plaintext passwords. This version reads secrets from the environment, hashes new passwords and checks access to role-specific pages. Use a fresh database: existing plaintext accounts are not migrated. It has not been designed or audited for public deployment. In particular, it lacks CSRF protection and rate limiting. It uses an external country-list API and falls back to Greece if that API is unavailable. Run it locally with demo data only.

The project report and original logo are excluded because they contain submission details or have unverified reuse rights.
