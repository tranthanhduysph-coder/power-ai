@echo off
setlocal
cd /d "%~dp0..\..\"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONPATH=apps\api

if not exist "apps\api\.venv\Scripts\python.exe" (
  echo [ERROR] Missing apps\api\.venv\Scripts\python.exe
  exit /b 2
)

"apps\api\.venv\Scripts\python.exe" scripts\release\finalize_local_v17.py
exit /b %ERRORLEVEL%
