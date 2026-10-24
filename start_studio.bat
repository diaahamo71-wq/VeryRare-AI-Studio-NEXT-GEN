@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo The environment is not set up yet. Run setup_windows.bat first.
  pause
  exit /b 1
)

echo Starting VeryRare AI Studio locally...
echo Keep this window open while using the app.
echo Open http://127.0.0.1:8765 in Chrome or Edge.
echo Press Ctrl+C in this window to stop the server.
".venv\Scripts\python.exe" -m uvicorn app.web_app:app --host 127.0.0.1 --port 8765
pause
