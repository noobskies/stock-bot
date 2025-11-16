@echo off
REM Start React Dashboard (Windows)
REM This starts the modern React dashboard on port 3000

echo 📊 Starting React Dashboard...

REM Check if dashboard directory exists
if not exist "dashboard\" (
    echo ❌ Error: dashboard\ directory not found.
    exit /b 1
)

REM Navigate to dashboard directory
cd dashboard

REM Check if node_modules exists
if not exist "node_modules\" (
    echo 📦 Installing dependencies (this may take a few minutes)...
    call npm install
)

REM Start React dev server
echo ✅ Starting React Dashboard on http://localhost:3000 (Press Ctrl+C to stop)...
echo 📝 Note: Make sure Flask API is running on port 5000 for full functionality!
call npm run dev
