@echo off
setlocal enabledelayedexpansion

set "PORT=%~1"
if "%PORT%"=="" set "PORT=8000"

where python >nul 2>nul
if errorlevel 1 (
  echo 未找到 python：请先安装 Python 3.11+ 并确保已加入 PATH。
  exit /b 1
)

cd /d "%~dp0\.."

if not exist ".venv" (
  python -m venv .venv
)

set "PY=%cd%\.venv\Scripts\python.exe"

"%PY%" -m pip install -U pip
"%PY%" -m pip install -r requirements.txt
"%PY%" -m alembic upgrade head
"%PY%" -m uvicorn app.main:app --reload --host 0.0.0.0 --port %PORT%

