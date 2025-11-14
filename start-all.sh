#!/bin/bash
# Start All Components
# This provides instructions and commands to start the bot, API, and dashboard

echo "🚀 Stock Trading Bot - Complete Startup"
echo "========================================"
echo ""
echo "To run the complete system, you need 3 separate terminal windows/tabs:"
echo ""
echo "Terminal 1 - Flask API Backend (required for dashboard):"
echo "  ./start-api.sh"
echo ""
echo "Terminal 2 - React Dashboard (web interface):"
echo "  ./start-dashboard.sh"
echo ""
echo "Terminal 3 - Trading Bot (optional - for actual trading):"
echo "  ./start-bot.sh"
echo ""
echo "========================================"
echo ""
echo "Quick Start Order:"
echo "  1. Start Flask API first (Terminal 1)"
echo "  2. Wait for 'Running on http://127.0.0.1:5000'"
echo "  3. Start React Dashboard (Terminal 2)"
echo "  4. Open browser to http://localhost:3000"
echo "  5. Optionally start Trading Bot (Terminal 3)"
echo ""
echo "📝 Note: All scripts are executable and include error checking."
echo "💡 Tip: Use 'tmux' or 'screen' to manage multiple terminals easily."
echo ""

# Ask if user wants to start Flask API in this terminal
read -p "Start Flask API in this terminal? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./start-api.sh
fi
