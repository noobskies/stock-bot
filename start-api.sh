#!/bin/bash
# Start Flask API Backend
# This starts the REST API server that the React dashboard connects to

set -e  # Exit on error

echo "🔌 Starting Flask API Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found."
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Error: Dependencies not installed."
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# Check if port 5000 is available
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Warning: Port 5000 is already in use."
    echo "Kill the process or use a different port."
fi

# Start Flask API
echo "✅ Starting Flask API on http://localhost:5000 (Press Ctrl+C to stop)..."
python src/dashboard/app.py
