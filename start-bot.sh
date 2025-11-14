#!/bin/bash
# Start Trading Bot
# This starts the main trading bot that executes trades

set -e  # Exit on error

echo "🤖 Starting Trading Bot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found."
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if required packages are installed
if ! python -c "import alpaca_trade_api" 2>/dev/null; then
    echo "❌ Error: Dependencies not installed."
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Copy .env.example to .env and configure your API keys."
fi

# Start the bot
echo "✅ Starting bot (Press Ctrl+C to stop)..."
python src/main.py
