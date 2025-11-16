# Test 14: 48-Hour Continuous Run - Verification Checklist

## Test Information

- **Test Start Time**: ********\_\_\_********
- **Expected End Time**: ********\_\_\_********
- **Tester Name**: ********\_\_\_********
- **Environment**: Paper Trading ($100K account)

## Pre-Test Verification (Before Starting)

### Environment Setup

- [ ] Virtual environment activated (`source venv/bin/activate`)
- [ ] All dependencies installed (`pip list | grep -E "(tensorflow|alpaca|pandas|flask)"`)
- [ ] Python version 3.12.3 confirmed (`python --version`)

### Configuration

- [ ] `.env` file exists with Alpaca credentials
- [ ] `ALPACA_IS_PAPER=true` confirmed
- [ ] `config/config.yaml` reviewed and appropriate
- [ ] Trading mode set (recommend: hybrid or manual)
- [ ] Database exists (`ls -lh trading_bot.db`)

### System Resources

- [ ] At least 10GB free disk space (`df -h`)
- [ ] Stable internet connection verified
- [ ] System will not go to sleep (power settings checked)
- [ ] No conflicting processes running (`lsof -i :5000`)

### Baseline Metrics

- [ ] Current Alpaca paper account balance: $****\_\_\_****
- [ ] Open positions at start: ****\_\_\_****
- [ ] Database size at start: ****\_\_\_**** MB

## Test Execution Steps

### Starting the Test

1. **Terminal 1 - Start Bot**

   ```bash
   python src/main.py
   ```

   - [ ] Bot initialization messages appear
   - [ ] All 14 modules initialize successfully
   - [ ] Alpaca API connection confirmed
   - [ ] "Bot started successfully" message seen

2. **Terminal 2 - Start Dashboard**

   ```bash
   python src/dashboard/app.py
   ```

   - [ ] Dashboard starts on port 5000
   - [ ] No Flask errors

3. **Terminal 3 - Start Monitor**

   ```bash
   python test_14_monitor.py
   ```

   - [ ] Monitor starts generating reports
   - [ ] First report shows bot is running

4. **Browser - Verify Dashboard**
   - [ ] Open http://localhost:5000
   - [ ] Portfolio value displays correctly
   - [ ] Bot status shows "Running"
   - [ ] No JavaScript console errors

### Initial Validation (First 30 Minutes)

- [ ] Trading cycle executes (check logs or dashboard)
- [ ] Position monitoring runs (check logs)
- [ ] Risk monitoring active (check logs)
- [ ] Dashboard updates correctly
- [ ] No errors in logs/errors.log
- [ ] Memory usage < 200MB (check monitor report)

## Hourly Checks (During Market Hours)

### Hour 1: **\_** (Time: **\_\_\_**)

- [ ] Bot process running (monitor report)
- [ ] Memory usage: **\_** MB (should be stable)
- [ ] CPU usage: **\_** % (should be < 50%)
- [ ] Logs active (modified within last 5 min)
- [ ] No errors in error log
- [ ] Dashboard accessible

### Hour 2: **\_** (Time: **\_\_\_**)

- [ ] Bot process running
- [ ] Memory usage: **\_** MB (check for growth)
- [ ] Trading cycles executed successfully
- [ ] Database updated (check last modified time)
- [ ] No errors in error log

### Hour 3: **\_** (Time: **\_\_\_**)

- [ ] Bot process running
- [ ] Memory usage: **\_** MB
- [ ] Position monitoring working
- [ ] No errors in error log

### Hour 4: **\_** (Time: **\_\_\_**)

- [ ] Bot process running
- [ ] Memory usage: **\_** MB
- [ ] Risk checks functioning
- [ ] No errors in error log

### Hour 5: **\_** (Time: **\_\_\_**)

- [ ] Bot process running
- [ ] Memory usage: **\_** MB
- [ ] All scheduled jobs running
- [ ] No errors in error log

### Hour 6: **\_** (Time: **\_\_\_**)

- [ ] Bot process running
- [ ] Memory usage: **\_** MB
- [ ] Dashboard still responsive
- [ ] No errors in error log

## Market Close Verification (4:00 PM ET)

- [ ] Market close handler executed (check logs)
- [ ] Positions closed if configured (`close_positions_eod: true`)
- [ ] Daily performance calculated
- [ ] Performance metrics saved to database

## Overnight Monitoring (Every 4 Hours)

### Check 1: **\_** (Time: **\_\_\_**)

- [ ] Bot process still running
- [ ] Memory stable
- [ ] No crashes during inactive period

### Check 2: **\_** (Time: **\_\_\_**)

- [ ] Bot process still running
- [ ] No unexpected activity
- [ ] Logs clean

### Check 3: **\_** (Time: **\_\_\_**)

- [ ] Bot process still running
- [ ] System resources normal
- [ ] Ready for next market day

## Second Day Market Open (9:30 AM ET)

- [ ] Bot resumes trading cycle automatically
- [ ] Data fetching working
- [ ] Predictions generated
- [ ] Signals created (if conditions met)
- [ ] Risk checks functioning

## Second Day Hourly Checks (During Market Hours)

### Hour 1 (Day 2): **\_** (Time: **\_\_\_**)

- [ ] Bot running
- [ ] Memory: **\_** MB
- [ ] No errors

### Hour 2 (Day 2): **\_** (Time: **\_\_\_**)

- [ ] Bot running
- [ ] Memory: **\_** MB
- [ ] No errors

### Hour 3 (Day 2): **\_** (Time: **\_\_\_**)

- [ ] Bot running
- [ ] Memory: **\_** MB
- [ ] No errors

### Hour 4 (Day 2): **\_** (Time: **\_\_\_**)

- [ ] Bot running
- [ ] Memory: **\_** MB
- [ ] No errors

### Hour 5 (Day 2): **\_** (Time: **\_\_\_**)

- [ ] Bot running
- [ ] Memory: **\_** MB
- [ ] No errors

### Hour 6 (Day 2): **\_** (Time: **\_\_\_**)

- [ ] Bot running
- [ ] Memory: **\_** MB
- [ ] No errors

## Test Completion (After 48 Hours)

### Graceful Shutdown

1. **Stop Monitor** (Terminal 3)

   - [ ] Press Ctrl+C
   - [ ] Note total reports generated: **\_**
   - [ ] Monitor uptime: **\_**

2. **Stop Bot** (Terminal 1)

   - [ ] Press Ctrl+C (graceful shutdown)
   - [ ] Wait for "Bot stopped" message
   - [ ] Verify all resources released

3. **Stop Dashboard** (Terminal 2)
   - [ ] Press Ctrl+C
   - [ ] Dashboard shutdown clean

### Final Verification

- [ ] Bot ran for full 48 hours without crashes
- [ ] Total uptime: **\_** hours (should be ~48)
- [ ] Final memory usage: **\_** MB
- [ ] No memory leak detected (usage stayed < 500MB)
- [ ] Total monitor reports: **\_** (should be ~48 for hourly)

## Post-Test Analysis

### Log Analysis

Run: `python analyze_logs.py`

- [ ] Total trading cycles executed: **\_**
- [ ] Successful cycles: **\_**
- [ ] Failed cycles: **\_**
- [ ] Total errors logged: **\_**
- [ ] Total warnings logged: **\_**
- [ ] Critical errors: **\_** (should be 0)

### Database Integrity

- [ ] Database file not corrupted (`sqlite3 trading_bot.db "PRAGMA integrity_check;"`)
- [ ] All trades recorded: **\_**
- [ ] All predictions recorded: **\_**
- [ ] All signals recorded: **\_**
- [ ] Position history complete
- [ ] Performance metrics calculated

### Risk Management Verification

- [ ] No trades exceeded 2% risk limit
- [ ] No single position exceeded 20% of portfolio
- [ ] Total exposure never exceeded 20%
- [ ] Daily loss limit never exceeded 5%
- [ ] All stop losses executed if triggered

### Performance Metrics

- [ ] Total trades executed: **\_**
- [ ] Winning trades: **\_**
- [ ] Losing trades: **\_**
- [ ] Win rate: **\_**%
- [ ] Average profit: $**\_**
- [ ] Average loss: $**\_**
- [ ] Max drawdown: **\_**%
- [ ] Final portfolio value: $**\_**
- [ ] Net P&L: $**\_**

### Dashboard Verification

- [ ] Dashboard accessible throughout test
- [ ] Real-time updates worked correctly
- [ ] No UI errors or glitches
- [ ] All API endpoints responded
- [ ] Data displayed accurately

### API Reliability

- [ ] Alpaca API calls succeeded (check retry counts)
- [ ] No prolonged API outages
- [ ] Retry logic worked when needed
- [ ] Data fetching reliable

## Success Criteria Evaluation

### Critical (Must Pass)

- [ ] ✅ Bot ran continuously for 48 hours without crashes
- [ ] ✅ Zero unhandled exceptions
- [ ] ✅ Database-Alpaca sync maintained 1:1 accuracy
- [ ] ✅ Risk limits enforced 100% of the time
- [ ] ✅ Dashboard remained accessible throughout

### Important (Should Pass)

- [ ] ✅ Memory usage remained < 500MB (no leaks)
- [ ] ✅ All scheduled jobs executed on time (0% missed)
- [ ] ✅ All API calls handled correctly (retries worked)
- [ ] ✅ Logs rotated properly (no disk space issues)
- [ ] ✅ No data corruption or loss

### Performance (Good to Have)

- [ ] ⭐ CPU usage averaged < 30%
- [ ] ⭐ Response time < 2s for dashboard
- [ ] ⭐ Prediction latency < 5s
- [ ] ⭐ Zero warnings in logs

## Issues Found (If Any)

### Issue 1

- **Description**:
- **Severity**: (Critical/High/Medium/Low)
- **When Occurred**:
- **How Resolved**:
- **Status**: (Fixed/Workaround/Deferred)

### Issue 2

- **Description**:
- **Severity**:
- **When Occurred**:
- **How Resolved**:
- **Status**:

### Issue 3

- **Description**:
- **Severity**:
- **When Occurred**:
- **How Resolved**:
- **Status**:

## Test Result

- [ ] ✅ **PASS** - All critical criteria met, bot ready for Phase 10
- [ ] ⚠️ **PASS WITH ISSUES** - Criteria met but issues need addressing
- [ ] ❌ **FAIL** - Critical criteria not met, fixes required

### Overall Assessment

---

---

---

---

### Next Steps

- [ ] Document all findings in INTEGRATION_TEST_RESULTS.md
- [ ] Update Memory Bank (activeContext.md, progress.md)
- [ ] Address any issues found
- [ ] Proceed to Phase 10: Documentation & Deployment
- [ ] Begin 2-week paper trading validation

## Signatures

**Tester**: **********\_\_********** Date: ****\_\_****

**Reviewer**: **********\_\_********** Date: ****\_\_****

---

## Notes & Observations

Use this space to record any observations, anomalies, or insights during the test:

---

---

---

---

---

---

---

---
