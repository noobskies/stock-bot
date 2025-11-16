@echo off
REM Start Trading Bot (Windows)
REM This starts the main trading bot that executes trades

echo 🤖 Starting Trading Bot...

REM Check if virtual environment exists
if not exist "venv\" (
    echo ❌ Error: Virtual environment not found.
    echo Please run: python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  Warning: .env file not found. Copy .env.example to .env and configure your API keys.
)

REM Start the bot
echo ✅ Starting bot (Press Ctrl+C to stop)...
python src\main.py
