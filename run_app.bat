@echo off
title WhatsApp Bulk Sender with Emoji Support
color 0a

echo Checking system requirements...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Download Python from https://www.python.org/downloads/
    pause
    exit /b
)

echo Installing required packages...
pip install --upgrade flask selenium webdriver-manager >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Failed to install Python dependencies
    echo Make sure pip is available and try running:
    echo pip install --upgrade flask selenium webdriver-manager
    pause
    exit /b
)

echo.
echo Starting WhatsApp Bulk Sender...
echo Important:
echo 1. Make sure Chrome is installed
echo 2. First run will download ChromeDriver automatically
echo 3. Scan QR code when WhatsApp Web loads
echo 4. Emoji and multi-line messages are now supported!

start "" http://localhost:5000
python app.py

if %errorlevel% neq 0 (
    echo.
    echo Application crashed with error code %errorlevel%
    echo Common solutions:
    echo 1. Close all Chrome instances
    echo 2. Delete the whatsapp_session folder
    echo 3. Check if WhatsApp Web works manually in Chrome
    echo 4. Update Chrome to latest version
)
pause