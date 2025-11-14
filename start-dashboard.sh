#!/bin/bash
# Start React Dashboard
# This starts the modern React dashboard on port 3000

set -e  # Exit on error

echo "📊 Starting React Dashboard..."

# Check if dashboard directory exists
if [ ! -d "dashboard" ]; then
    echo "❌ Error: dashboard/ directory not found."
    exit 1
fi

# Navigate to dashboard directory
cd dashboard

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies (this may take a few minutes)..."
    npm install
fi

# Check if port 3000 is available
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Warning: Port 3000 is already in use."
    echo "Kill the process or the dev server will use a different port."
fi

# Start React dev server
echo "✅ Starting React Dashboard on http://localhost:3000 (Press Ctrl+C to stop)..."
echo "📝 Note: Make sure Flask API is running on port 5000 for full functionality!"
npm run dev
