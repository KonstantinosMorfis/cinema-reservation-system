@echo off
cd /d "%~dp0"
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env. Edit FLASK_SECRET_KEY and ADMIN_PASSWORD before continuing.
  pause
  exit /b 1
)

docker compose up -d
if errorlevel 1 (
  echo Docker did not start MongoDB. Start Docker Desktop and try again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Python 3 is required. Install Python and try again.
    pause
    exit /b 1
  )
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Python dependencies could not be installed.
  pause
  exit /b 1
)

echo Open http://127.0.0.1:5000/ in your browser.
".venv\Scripts\python.exe" app.py
pause
