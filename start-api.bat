@echo off
REM Start Flask API Backend (Windows)
REM This starts the REST API server that the React dashboard connects to

echo 🔌 Starting Flask API Backend...

REM Check if virtual environment exists
if not exist "venv\" (
    echo ❌ Error: Virtual environment not found.
    echo Please run: python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Flask API
echo ✅ Starting Flask API on http://localhost:5000 (Press Ctrl+C to stop)...
python src\dashboard\app.py
