@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher "py" was not found. Install Python 3.11 or 3.12 from python.org.
  pause
  exit /b 1
)

py -3.11 --version >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_CMD=py -3.11"
) else (
  py -3.12 --version >nul 2>nul
  if errorlevel 1 (
    echo Python 3.11 or 3.12 is required.
    pause
    exit /b 1
  )
  set "PYTHON_CMD=py -3.12"
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating local virtual environment...
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto :failed
)

echo Updating pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed

echo Installing VeryRare AI Studio dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed

echo.
echo Setup complete. Double-click start_studio.bat to launch the UI.
pause
exit /b 0

:failed
echo.
echo Setup failed. Copy the error text before retrying.
pause
exit /b 1
