# Stock Trading Bot - Startup Guide

This guide explains how to start the trading bot system using the convenient startup scripts.

## Quick Start (TL;DR)

### Linux/Mac:

```bash
# Terminal 1 - Start Flask API (required)
./start-api.sh

# Terminal 2 - Start React Dashboard
./start-dashboard.sh

# Terminal 3 - Start Trading Bot (optional)
./start-bot.sh
```

### Windows:

```cmd
REM Window 1 - Start Flask API (required)
start-api.bat

REM Window 2 - Start React Dashboard
start-dashboard.bat

REM Window 3 - Start Trading Bot (optional)
start-bot.bat
```

## System Architecture

The trading bot system consists of 3 independent components:

1. **Flask API Backend** (Port 5000) - REST API server

   - Required for dashboard to function
   - Provides data from database and bot state
   - Can run without the trading bot

2. **React Dashboard** (Port 3000) - Web interface

   - Modern React-based UI
   - Connects to Flask API for data
   - Monitor portfolio, trades, signals, and bot status

3. **Trading Bot** (No port) - Core trading engine
   - Optional - only needed for actual trading
   - Executes ML predictions and manages positions
   - Runs scheduled tasks (every 5 min during market hours)

## Available Scripts

### Individual Component Scripts

| Script                   | Description            | Port | Required?           |
| ------------------------ | ---------------------- | ---- | ------------------- |
| `start-api.sh/bat`       | Flask API Backend      | 5000 | Yes (for dashboard) |
| `start-dashboard.sh/bat` | React Dashboard        | 3000 | No                  |
| `start-bot.sh/bat`       | Trading Bot            | -    | No                  |
| `start-all.sh/bat`       | Instructions + Options | -    | No                  |

### Script Features

All scripts include:

- ✅ Virtual environment checks
- ✅ Dependency verification
- ✅ Port availability checks (where applicable)
- ✅ Clear error messages
- ✅ Auto-installation prompts

## Detailed Startup Instructions

### Step 1: Prerequisites

Ensure you have completed initial setup:

```bash
# 1. Virtual environment created and activated
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# 2. Python dependencies installed
pip install -r requirements.txt

# 3. Environment variables configured
cp .env.example .env
# Edit .env with your Alpaca API keys

# 4. Node.js dependencies installed (for dashboard)
cd dashboard
npm install
cd ..
```

### Step 2: Start Flask API Backend (Required)

**Linux/Mac:**

```bash
./start-api.sh
```

**Windows:**

```cmd
start-api.bat
```

**Expected Output:**

```
🔌 Starting Flask API Backend...
✅ Starting Flask API on http://localhost:5000 (Press Ctrl+C to stop)...
 * Running on http://127.0.0.1:5000
```

**Wait** until you see "Running on http://127.0.0.1:5000" before proceeding.

### Step 3: Start React Dashboard

Open a **new terminal/command window**.

**Linux/Mac:**

```bash
./start-dashboard.sh
```

**Windows:**

```cmd
start-dashboard.bat
```

**Expected Output:**

```
📊 Starting React Dashboard...
✅ Starting React Dashboard on http://localhost:3000 (Press Ctrl+C to stop)...
📝 Note: Make sure Flask API is running on port 5000 for full functionality!

  VITE v6.0.1  ready in 382 ms

  ➜  Local:   http://localhost:3000/
```

**Access Dashboard:**
Open your browser to http://localhost:3000

### Step 4: Start Trading Bot (Optional)

Only start the bot if you want to:

- Generate trading signals
- Execute trades (paper or live)
- Monitor positions in real-time

Open a **new terminal/command window**.

**Linux/Mac:**

```bash
./start-bot.sh
```

**Windows:**

```cmd
start-bot.bat
```

**Expected Output:**

```
🤖 Starting Trading Bot...
✅ Starting bot (Press Ctrl+C to stop)...
[2025-11-14 14:21:15] INFO - Bot initialized successfully
[2025-11-14 14:21:15] INFO - Connected to Alpaca API (Paper Trading)
[2025-11-14 14:21:15] INFO - Trading Bot started in HYBRID mode
```

## Component Dependencies

```
React Dashboard (Port 3000)
    ↓ requires
Flask API Backend (Port 5000)
    ↓ reads from
Database (SQLite)
    ↑ writes to
Trading Bot (background)
```

**Key Insight:** You can view the dashboard without running the bot. The dashboard displays historical data from the database and current Alpaca account state.

## Common Use Cases

### 1. Just View Dashboard (No Trading)

```bash
./start-api.sh      # Terminal 1
./start-dashboard.sh # Terminal 2
```

Use this to review past trades, analyze performance, and check account status.

### 2. Full System (Active Trading)

```bash
./start-api.sh      # Terminal 1
./start-dashboard.sh # Terminal 2
./start-bot.sh       # Terminal 3
```

Use this during market hours for live trading with real-time monitoring.

### 3. Bot Only (No Dashboard)

```bash
./start-bot.sh       # Terminal 1
```

Use this for headless operation (server deployment, no UI needed).

## Troubleshooting

### "Port already in use"

**Problem:** Port 5000 or 3000 is already occupied.

**Solution:**

```bash
# Linux/Mac - Find and kill process
lsof -ti:5000 | xargs kill -9  # Flask API
lsof -ti:3000 | xargs kill -9  # React Dashboard

# Windows - Find and kill process
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### "Virtual environment not found"

**Problem:** Scripts can't find `venv/` directory.

**Solution:**

```bash
# Create virtual environment first
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Dependencies not installed"

**Problem:** Required Python packages missing.

**Solution:**

```bash
source venv/bin/activate  # Activate venv first!
pip install -r requirements.txt
```

### "Dashboard shows 'Unknown' status"

**Problem:** React dashboard can't reach Flask API.

**Solution:**

1. Ensure Flask API is running (`./start-api.sh`)
2. Check Flask API shows "Running on http://127.0.0.1:5000"
3. Wait 2-3 seconds for dashboard to reconnect
4. Refresh browser (F5)

### ".env file not found"

**Problem:** Environment variables not configured.

**Solution:**

```bash
cp .env.example .env
# Edit .env file with your Alpaca API keys
nano .env  # or vim, code, etc.
```

## Script Permissions (Linux/Mac)

If you get "Permission denied" when running scripts:

```bash
chmod +x start-bot.sh start-api.sh start-dashboard.sh start-all.sh
```

This makes the shell scripts executable.

## Stopping Components

### Individual Components

Press **Ctrl+C** in each terminal window to stop that component.

### All Components

Press **Ctrl+C** in each terminal window, in this order:

1. Stop Trading Bot first (if running)
2. Stop React Dashboard
3. Stop Flask API Backend last

This ensures graceful shutdown with no data loss.

## Advanced: Using tmux (Linux/Mac)

For convenient multi-terminal management:

```bash
# Install tmux (if not installed)
sudo apt install tmux  # Ubuntu/Debian
brew install tmux      # macOS

# Start all components in tmux
tmux new-session -d -s trading './start-api.sh'
tmux split-window -h './start-dashboard.sh'
tmux split-window -v './start-bot.sh'
tmux attach -t trading

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t trading
# Kill session: tmux kill-session -t trading
```

## Production Deployment

For production deployments (VPS, cloud server):

### Using systemd (Linux)

Create systemd service files for each component:

```bash
# /etc/systemd/system/trading-api.service
[Unit]
Description=Trading Bot Flask API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/stock-bot
ExecStart=/path/to/stock-bot/venv/bin/python src/dashboard/app.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable trading-api
sudo systemctl start trading-api
```

### Using Docker (Future Enhancement)

Docker support is planned for Phase 10. This will simplify deployment with:

- Pre-built containers
- Orchestration with docker-compose
- One-command startup

## Next Steps

Once all components are running:

1. **Access Dashboard:** http://localhost:3000
2. **Review Account:** Check portfolio value, positions, cash
3. **Configure Bot:** Settings page to adjust trading mode
4. **Monitor Trades:** Trades page shows execution history
5. **Approve Signals:** Dashboard shows pending signals in hybrid mode

## Support

For issues or questions:

- Check troubleshooting section above
- Review logs in `logs/` directory
- Consult main README.md for detailed documentation
- Check Memory Bank files in `memory-bank/` for architecture details

---

**Happy Trading!** 🚀📈
