@echo off
setlocal
cd /d "%~dp0"
python -c "import customtkinter, openpyxl, win32com.client" >nul 2>&1
if errorlevel 1 (
  echo Installing required Python packages...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Failed to install requirements.
    pause
    exit /b 1
  )
)
python main.py
if errorlevel 1 pause
endlocal
