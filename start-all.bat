@echo off
REM Start All Components (Windows)
REM This provides instructions and commands to start the bot, API, and dashboard

echo 🚀 Stock Trading Bot - Complete Startup
echo ========================================
echo.
echo To run the complete system, you need 3 separate command prompt windows:
echo.
echo Window 1 - Flask API Backend (required for dashboard):
echo   start-api.bat
echo.
echo Window 2 - React Dashboard (web interface):
echo   start-dashboard.bat
echo.
echo Window 3 - Trading Bot (optional - for actual trading):
echo   start-bot.bat
echo.
echo ========================================
echo.
echo Quick Start Order:
echo   1. Start Flask API first (Window 1)
echo   2. Wait for 'Running on http://127.0.0.1:5000'
echo   3. Start React Dashboard (Window 2)
echo   4. Open browser to http://localhost:3000
echo   5. Optionally start Trading Bot (Window 3)
echo.
echo 📝 Note: All batch files include error checking.
echo 💡 Tip: You can start each component in a new cmd window.
echo.
pause
