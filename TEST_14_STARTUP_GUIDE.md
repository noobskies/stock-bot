# Test 14: 48-Hour Continuous Run - Startup Guide

## Quick Reference

**Estimated Time**: 48 hours continuous operation
**Requirements**: 3 terminal windows, stable internet, ~10GB disk space
**Safety**: Paper trading only ($100K virtual account)

---

## Prerequisites Verification

Before starting, verify all prerequisites are met:

### 1. Environment Check

```bash
# Navigate to project directory
cd /home/noobskie/workspace/stock-bot

# Verify Python version
python --version
# Expected: Python 3.12.3

# Activate virtual environment
source venv/bin/activate

# Verify critical packages
pip list | grep -E "(tensorflow|alpaca|pandas|flask|psutil)"
# Should show: tensorflow 2.19.1, alpaca-trade-api 3.2.0+, pandas 2.1.3, Flask 3.0.0, psutil (any version)
```

### 2. Configuration Check

```bash
# Verify .env exists
cat .env | grep -E "(ALPACA_API_KEY|ALPACA_IS_PAPER)"

# Verify config.yaml
cat config/config.yaml | grep -E "(mode:|symbols:|close_positions_eod:)"

# Expected output:
# - mode: hybrid (or manual for safer testing)
# - symbols: PLTR
# - close_positions_eod: true
# - ALPACA_IS_PAPER=true in .env
```

### 3. Database Check

```bash
# Check if database exists
ls -lh trading_bot.db

# If database doesn't exist, create it
python src/database/schema.py
```

### 4. System Resources

```bash
# Check disk space (need at least 10GB free)
df -h .

# Check available memory (need at least 4GB free)
free -h

# Verify no process is using port 5000
lsof -i :5000
# Should return empty (if not, kill that process)
```

---

## Starting Test 14

### Terminal 1: Bot Process

```bash
# From project root
cd /home/noobskie/workspace/stock-bot

# Activate virtual environment
source venv/bin/activate

# Start bot
python src/main.py
```

**Expected Output:**

```
[Timestamp] Bot initialization starting...
[Timestamp] Loading configuration from config/config.yaml
[Timestamp] All 14 modules initialized successfully
[Timestamp] Alpaca API connection verified (Paper Trading)
[Timestamp] Bot started successfully in HYBRID mode
[Timestamp] Trading cycle scheduled (every 5 minutes)
[Timestamp] Position monitor scheduled (every 30 seconds)
[Timestamp] Bot is ready to trade PLTR
```

**⚠️ DO NOT CLOSE THIS TERMINAL FOR 48 HOURS**

### Terminal 2: Dashboard

Open a new terminal window:

```bash
# From project root
cd /home/noobskie/workspace/stock-bot

# Activate virtual environment
source venv/bin/activate

# Start dashboard
python src/dashboard/app.py
```

**Expected Output:**

```
 * Running on http://127.0.0.1:5000
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
```

**⚠️ DO NOT CLOSE THIS TERMINAL FOR 48 HOURS**

### Terminal 3: Monitor

Open a third terminal window:

```bash
# From project root
cd /home/noobskie/workspace/stock-bot

# Activate virtual environment
source venv/bin/activate

# Start monitor (generates reports every hour)
python test_14_monitor.py
```

**Expected Output:**

```
================================================================================
Test 14 Monitor Started
================================================================================
Start Time: 2025-11-13 21:00:00
Report Interval: 3600 seconds (60 minutes)
Reports saved to: /home/noobskie/workspace/stock-bot/test_14_reports
================================================================================

Press Ctrl+C to stop monitoring

[2025-11-13 21:00:00] Generating report #1...

================================================================================
Bot Monitor Report - 2025-11-13 21:00:00
Monitor Uptime: 0:00:00
================================================================================

BOT PROCESS STATUS:
--------------------------------------------------------------------------------
✅ Bot is RUNNING (PID: 12345)
   Status: running
   Uptime: 0:00:01
   CPU: 5.2%
   Memory: 145.3 MB
   Threads: 8

... (full report)
```

**Note:** You can customize the interval:

```bash
# Generate reports every 30 minutes
python test_14_monitor.py 1800

# Generate reports every 2 hours
python test_14_monitor.py 7200
```

### Browser: Dashboard Verification

1. Open browser to: http://localhost:5000
2. Verify you see:
   - Portfolio value (~$100,000 from Alpaca paper account)
   - Bot status: "Running"
   - Mode: "Hybrid"
   - Current time display
3. Check browser console (F12) for JavaScript errors (should be none)

---

## Initial Validation (First 30 Minutes)

### Checklist

Within the first 30 minutes, verify:

#### Terminal 1 (Bot Logs)

- [ ] No ERROR messages in output
- [ ] "Trading cycle" messages appear (every 5 minutes during market hours)
- [ ] "Position update" messages appear (every 30 seconds)
- [ ] No "CRITICAL" messages

#### Terminal 2 (Dashboard)

- [ ] No Flask errors
- [ ] Server responding to requests
- [ ] No 500 errors

#### Terminal 3 (Monitor)

- [ ] First report shows bot is RUNNING
- [ ] Memory usage < 200 MB
- [ ] CPU usage < 50%
- [ ] Logs are active

#### Browser (Dashboard)

- [ ] Dashboard loads without errors
- [ ] Portfolio data displays correctly
- [ ] Bot controls work (don't stop the bot, just check UI)
- [ ] Real-time updates occur (refresh happens every 30 seconds)

### If Any Check Fails

1. **Bot Errors**: Check `logs/errors.log` for details
2. **Dashboard Issues**: Check Flask output in Terminal 2
3. **Monitor Issues**: Verify bot process is actually running (`ps aux | grep main.py`)
4. **Browser Issues**: Open browser console (F12) and check for JavaScript errors

**If critical issues are found, STOP THE TEST:**

```bash
# In Terminal 1 (Bot)
Ctrl+C

# In Terminal 2 (Dashboard)
Ctrl+C

# In Terminal 3 (Monitor)
Ctrl+C
```

Fix issues, then restart from the beginning.

---

## During Market Hours (9:30 AM - 4:00 PM ET)

### What to Expect

**Every 5 Minutes (Trading Cycle):**

- Bot fetches latest PLTR data
- Calculates technical indicators
- Runs ML prediction
- Generates signal if confidence > 70%
- If hybrid mode and confidence > 80%: Auto-execute
- If hybrid mode and confidence 70-80%: Wait for manual approval

**Every 30 Seconds (Position Monitor):**

- Updates position prices from Alpaca
- Calculates unrealized P&L
- Checks stop loss triggers
- Updates trailing stops if profit > 5%

**At Market Close (4:00 PM ET):**

- Market close handler executes
- Closes all positions (if `close_positions_eod: true`)
- Calculates daily performance
- Saves metrics to database

### Hourly Checks

Use the monitoring checklist in `TEST_14_CHECKLIST.md`:

```bash
# Quick status check
tail -50 logs/trading_bot_$(date +%Y-%m-%d).log

# Check for errors
tail -50 logs/errors.log

# Check latest monitor report
ls -lt test_14_reports/ | head -2
cat test_14_reports/status_YYYYMMDD_HHMMSS.txt
```

---

## Outside Market Hours

### What to Expect

- Bot continues running (no crashes)
- No trading cycles execute (market closed)
- Position monitoring pauses
- Memory usage stays stable
- Logs show minimal activity

### Overnight Checks (Every 4 Hours)

```bash
# Quick check - is bot still running?
ps aux | grep "python src/main.py"

# Check memory usage
ps aux | grep "python src/main.py" | awk '{print $6/1024 " MB"}'

# Check latest log timestamp
ls -lt logs/ | head -2
```

**Goal:** Confirm bot hasn't crashed during inactive period.

---

## Completing the Test (After 48 Hours)

### Step 1: Graceful Shutdown

**Terminal 3 (Monitor) - Stop First:**

```bash
# Press Ctrl+C
# Note the final statistics displayed
```

**Terminal 1 (Bot) - Stop Second:**

```bash
# Press Ctrl+C
# Wait for "Bot stopped" message
# Verify graceful shutdown (no errors)
```

**Terminal 2 (Dashboard) - Stop Last:**

```bash
# Press Ctrl+C
```

### Step 2: Run Log Analysis

```bash
# From project root, with venv activated
python analyze_logs.py
```

This generates `TEST_14_RESULTS.md` with comprehensive analysis:

- Total runtime duration
- Trading cycles executed
- Position updates performed
- Errors and warnings summary
- Pass/Fail assessment

### Step 3: Complete Checklist

Open `TEST_14_CHECKLIST.md` and fill in:

- All verification checkboxes
- Performance metrics
- Any issues encountered
- Final test result (PASS/FAIL)

### Step 4: Verify Database Integrity

```bash
# Check database is not corrupted
sqlite3 trading_bot.db "PRAGMA integrity_check;"
# Should output: ok

# Count records
sqlite3 trading_bot.db "SELECT
  (SELECT COUNT(*) FROM trades) as trades,
  (SELECT COUNT(*) FROM predictions) as predictions,
  (SELECT COUNT(*) FROM signals) as signals;"
```

---

## Success Criteria

Test 14 **PASSES** if all of the following are true:

### Critical (Must Pass)

- ✅ Bot ran continuously for 48 hours without crashes
- ✅ Zero unhandled exceptions (check `logs/errors.log`)
- ✅ Database-Alpaca sync maintained 1:1 accuracy
- ✅ Risk limits enforced 100% of the time
- ✅ Dashboard remained accessible throughout

### Important (Should Pass)

- ✅ Memory usage remained < 500MB (no leaks)
- ✅ All scheduled jobs executed on time
- ✅ All API calls handled correctly (retries worked)
- ✅ Logs rotated properly
- ✅ No data corruption

### Performance (Good to Have)

- ⭐ CPU usage averaged < 30%
- ⭐ Dashboard response time < 2s
- ⭐ Prediction latency < 5s
- ⭐ Minimal warnings in logs

---

## Troubleshooting

### Bot Crashes

**Symptoms:** Terminal 1 exits unexpectedly

**Actions:**

1. Check `logs/errors.log` for the crash reason
2. Check system resources: `free -h` and `df -h`
3. Review last monitor report
4. Document in TEST_14_CHECKLIST.md
5. Fix issue and restart test

### Dashboard Unresponsive

**Symptoms:** Browser can't connect to localhost:5000

**Actions:**

1. Check Terminal 2 - is Flask still running?
2. Check if port is blocked: `lsof -i :5000`
3. Try restarting dashboard (bot can continue running)
4. If bot depends on dashboard, restart entire test

### High Memory Usage

**Symptoms:** Memory > 500MB and growing

**Actions:**

1. Check monitor reports for memory trend
2. Review logs for memory-intensive operations
3. Consider if this is a memory leak
4. Document in TEST_14_CHECKLIST.md
5. May need to stop test and investigate

### No Trading Activity

**Symptoms:** No trading cycles in logs

**Actions:**

1. Check if market is open (9:30 AM - 4:00 PM ET)
2. Verify bot configuration: `cat config/config.yaml | grep mode`
3. Check for scheduler errors in logs
4. Verify Alpaca API connectivity

### API Rate Limiting

**Symptoms:** "Rate limit exceeded" in logs

**Actions:**

1. Retry logic should handle this automatically
2. Monitor if it persists
3. May need to reduce polling frequency (not recommended for this test)

---

## Post-Test Next Steps

After Test 14 completes successfully:

1. **Document Results**

   - Review `TEST_14_RESULTS.md`
   - Complete `TEST_14_CHECKLIST.md`
   - Update `INTEGRATION_TEST_RESULTS.md`

2. **Update Memory Bank**

   - Update `memory-bank/activeContext.md` with Test 14 results
   - Update `memory-bank/progress.md` - mark Test 14 as complete
   - Document any issues or insights discovered

3. **Proceed to Phase 10: Documentation & Deployment**

   - Update README.md
   - Create API documentation
   - Write user guide
   - Create operational procedures

4. **Begin 2-Week Paper Trading Validation**
   - Run bot continuously in paper trading mode
   - Monitor performance metrics
   - Build confidence before considering live trading

---

## Emergency Procedures

### Emergency Stop

If something goes wrong and you need to stop everything immediately:

```bash
# Kill bot process
pkill -f "python src/main.py"

# Kill dashboard
pkill -f "python src/dashboard/app.py"

# Kill monitor
pkill -f "python test_14_monitor.py"

# Verify all stopped
ps aux | grep python
```

### Data Backup

If you need to preserve data before stopping:

```bash
# Backup database
cp trading_bot.db trading_bot_backup_$(date +%Y%m%d_%H%M%S).db

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d_%H%M%S).tar.gz logs/

# Backup monitor reports
tar -czf reports_backup_$(date +%Y%m%d_%H%M%S).tar.gz test_14_reports/
```

---

## Contact & Support

If you encounter issues during Test 14:

1. **Check Documentation**: Review all Memory Bank files
2. **Check Logs**: `logs/errors.log` and `logs/trading_bot_*.log`
3. **Check Monitor Reports**: `test_14_reports/status_*.txt`
4. **Document Issues**: Record in TEST_14_CHECKLIST.md

---

## Appendix: Quick Commands Reference

```bash
# Check bot is running
ps aux | grep "python src/main.py"

# Check memory usage
ps aux | grep "python src/main.py" | awk '{print $6/1024 " MB"}'

# Check latest logs
tail -f logs/trading_bot_$(date +%Y-%m-%d).log

# Check errors only
tail -f logs/errors.log

# Check disk space
df -h .

# Check database size
ls -lh trading_bot.db

# Generate on-demand monitor report
python test_14_monitor.py 0  # Generates one report and exits

# Count log errors
grep -c "ERROR" logs/trading_bot_*.log

# Count log warnings
grep -c "WARNING" logs/trading_bot_*.log

# View Alpaca paper account balance
# (requires Alpaca API credentials)
python -c "import alpaca_trade_api as tradeapi; import os; from dotenv import load_dotenv; load_dotenv(); api = tradeapi.REST(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'), os.getenv('ALPACA_BASE_URL')); print(f'Portfolio Value: ${float(api.get_account().portfolio_value):,.2f}')"
```

---

## Good Luck! 🚀

Test 14 is the final validation before Phase 10. Take your time, follow the checklist, and document everything. This test proves the bot can run reliably for extended periods without human intervention.

**Remember:** This is paper trading - no real money at risk. The goal is to validate system stability and reliability.
