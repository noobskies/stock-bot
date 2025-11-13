# Product Context: AI Stock Trading Bot

## Why This Project Exists

### The Problem

Personal stock trading faces several fundamental challenges:

1. **Emotional Decision-Making**: Fear and greed drive poor trading decisions

   - Panic selling during dips
   - FOMO buying at peaks
   - Holding losing positions too long
   - Taking profits too early

2. **Time Constraints**: Active trading requires constant market monitoring

   - Full-time job conflicts with market hours
   - Cannot watch positions all day
   - Miss optimal entry/exit points
   - Slow reaction to market changes

3. **Information Overload**: Too much data, too little insight

   - Thousands of stocks to analyze
   - Complex technical indicators
   - News and sentiment analysis
   - Difficulty synthesizing multiple signals

4. **Inconsistent Discipline**: Hard to follow a trading plan consistently

   - Skip stop losses "just this once"
   - Over-trade after wins
   - Revenge trading after losses
   - Position sizing varies emotionally

5. **Limited Capital Efficiency**: Manual trading wastes opportunities
   - Can't act on all good signals
   - Miss trades while sleeping
   - Slow execution loses edge
   - Underutilized buying power

### The Solution

An AI-powered trading bot that automates the entire trading process while maintaining human oversight:

- **Removes Emotion**: ML models make decisions based on data, not feelings
- **24/7 Vigilance**: Monitors positions continuously, executes stops automatically
- **Data-Driven**: Processes multiple indicators simultaneously for pattern recognition
- **Enforces Discipline**: Follows risk rules without exception
- **Maximizes Efficiency**: Executes trades instantly when signals trigger

## What Problem Does It Solve?

### For the User (Personal Trader)

**Primary Use Case**: Automated day trading with ML predictions

```
Morning (9:30 AM):
- Bot analyzes overnight data
- Generates predictions for PLTR
- If signal confidence >70%, prepares trade
- User reviews signal on dashboard (hybrid mode)
- Approves trade or overrides

During Market Hours:
- Bot monitors position continuously
- Updates stop loss if profit reaches 5%
- Executes stop automatically if triggered
- Logs all actions to database

End of Day (4:00 PM):
- Bot closes positions (if configured)
- Calculates daily P&L
- Updates performance metrics
- Prepares report for user review
```

**Secondary Use Case**: Paper trading for strategy validation

```
User wants to test new ML model:
1. Train new LSTM variant on historical data
2. Deploy to bot in paper trading mode
3. Run for 2 weeks to gather performance data
4. Review results (win rate, Sharpe ratio, drawdown)
5. If successful, switch to live trading
```

### Problems Solved

1. **Emotion Elimination**

   - Before: "Should I sell? It might go higher..." → holds too long, turns winner into loser
   - After: Bot executes stop loss at 3% without hesitation, preserves capital

2. **Time Freedom**

   - Before: Glued to screen all day, missing work meetings
   - After: Check dashboard twice daily, bot handles execution

3. **Consistent Execution**

   - Before: Sometimes follows plan, sometimes overrides it, inconsistent results
   - After: Every trade follows same rules, performance attributable to strategy

4. **Risk Management**

   - Before: "Just this once I'll risk 5%" → loses 20% in one bad trade
   - After: Bot enforces 2% maximum risk per trade, impossible to override

5. **Learning & Improvement**
   - Before: Hard to remember why past trades worked/failed
   - After: Complete trade history with predictions, can analyze what works

## User Experience Goals

### Primary Goals

1. **Trust & Confidence**

   - User must trust bot to manage their money
   - Transparency: Show all signals, predictions, and reasoning
   - Control: Easy emergency stop, manual override always available
   - History: Complete audit trail of all decisions

2. **Simplicity**

   - Start bot with one click
   - Dashboard shows key info at a glance
   - No complex configuration required
   - Default settings work well for most users

3. **Safety First**

   - Paper trading mode is default
   - Clear warnings before live trading
   - Risk limits prevent catastrophic losses
   - Position limits prevent over-concentration

4. **Visibility**

   - Real-time portfolio value
   - Active positions with current P&L
   - Pending signals awaiting approval
   - Performance metrics (win rate, Sharpe ratio)

5. **Control**
   - Switch between auto/manual/hybrid modes instantly
   - Approve or reject signals individually
   - Override bot decisions when needed
   - Emergency stop kills all activity

### User Journey: First Time Setup

```
1. Clone repository
   - Simple git clone command
   - All dependencies in requirements.txt

2. Install dependencies
   - One pip install command
   - TA-Lib C library (documented with OS-specific instructions)

3. Configure Alpaca API
   - Copy .env.example to .env
   - Paste API key and secret (from Alpaca website)
   - Paper trading is default (safe)

4. Start bot
   - python src/main.py
   - Dashboard opens automatically at localhost:5000

5. Verify setup
   - Dashboard shows "Connected to Alpaca"
   - Portfolio value displays correctly
   - No errors in logs

6. Run in paper mode
   - Bot trades with virtual money
   - User monitors for 2 weeks
   - Builds confidence in system

7. Switch to live trading (optional)
   - Update .env with live API keys
   - Confirm multiple warnings
   - Start with small capital ($1,000)
```

### User Journey: Daily Operation

```
Morning Routine (5 minutes):
1. Check dashboard for overnight activity
2. Review pending signals (if any)
3. Approve high-confidence signals
4. Check current positions and P&L

Intraday (Zero time required):
- Bot monitors positions automatically
- Executes stops if triggered
- Sends notifications for important events (optional)

Evening Routine (5 minutes):
1. Review trades executed today
2. Check performance metrics
3. Verify bot is ready for tomorrow
4. Optional: Adjust settings based on market conditions
```

### User Journey: Signal Approval (Hybrid Mode)

```
Signal Generated:
- Bot predicts PLTR will go up
- Confidence: 72%
- Dashboard shows notification badge

User Reviews Signal:
1. Click "Pending Signals" tab
2. See prediction details:
   - Symbol: PLTR
   - Direction: UP
   - Confidence: 72%
   - Technical indicators: RSI oversold, MACD bullish crossover
   - Suggested position size: 45 shares ($1,350)
   - Risk: 2% ($270)
3. Decision options:
   - ✅ Approve → Bot executes immediately
   - ❌ Reject → Signal discarded, logged
   - ⏸️ Modify → Adjust quantity or wait

User Approves:
- Order submitted to Alpaca
- Position appears in "Active Positions"
- Stop loss set automatically
- Dashboard updates in real-time
```

### Dashboard Experience

**Homepage - Portfolio Overview**

```
┌─────────────────────────────────────────────────────┐
│ Stock Trading Bot - Portfolio Dashboard            │
│ Status: 🟢 Active | Mode: Hybrid | Paper Trading   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Portfolio Value: $10,245.50                       │
│  Daily P&L: +$245.50 (+2.45%)                      │
│  Cash Available: $5,123.00                         │
│                                                     │
│  ┌────────────────────────────────────────┐       │
│  │ Quick Actions                          │       │
│  │ [Start Bot] [Stop Bot] [Emergency Stop] │      │
│  │ Mode: [Auto] [Manual] [●Hybrid]        │      │
│  └────────────────────────────────────────┘       │
│                                                     │
│  Active Positions (2)                              │
│  ┌────────────────────────────────────────┐       │
│  │ PLTR | 50 shares | +$127.50 (+2.55%)   │       │
│  │ Entry: $30.00 | Current: $32.55        │       │
│  │ Stop: $29.10 | Trailing: $31.50        │       │
│  └────────────────────────────────────────┘       │
│                                                     │
│  Pending Signals (1) 🔔                            │
│  ┌────────────────────────────────────────┐       │
│  │ PLTR | BUY | Confidence: 74%           │       │
│  │ [Approve] [Reject] [View Details]       │      │
│  └────────────────────────────────────────┘       │
│                                                     │
│  Recent Performance                                │
│  Win Rate: 58% | Sharpe Ratio: 1.2                │
│  Max Drawdown: -3.2% | Total Trades: 24           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Trades Page - Historical Performance**

- Table of all trades with sortable columns
- Filters: Date range, symbol, win/loss, confidence threshold
- Charts: P&L over time, win rate by confidence level
- Export: Download CSV for external analysis

**Signals Page - ML Insights**

- Historical predictions vs actual outcomes
- Model accuracy metrics by timeframe
- Feature importance visualization
- Confidence calibration chart

**Settings Page - Configuration**

- Trading mode selection (auto/manual/hybrid)
- Risk parameters (position size, stop loss %)
- Target stocks (currently just PLTR)
- API credentials (masked)
- Notification preferences

## How It Should Work

### Core Workflow

```
Data Collection → Feature Engineering → ML Prediction → Signal Generation
→ Risk Validation → Trade Execution → Position Monitoring → Stop Management
```

**Detailed Flow:**

1. **Data Collection** (Every 1 minute during market hours)

   - Fetch current PLTR price from Alpaca
   - Update OHLCV data in memory
   - Calculate technical indicators in real-time

2. **Prediction** (Every 5 minutes)

   - Prepare feature vector from recent data
   - Run LSTM model to predict next-day direction
   - Calculate ensemble confidence score
   - Generate prediction record

3. **Signal Generation** (When confidence threshold met)

   - If prediction confidence >70% → Generate signal
   - If long position exists and prediction is DOWN → Generate exit signal
   - If short-term reversal detected → Generate take-profit signal

4. **Risk Validation** (Before any trade)

   - Check: Is daily loss limit reached? (5% max)
   - Check: Is maximum position count reached? (5 max)
   - Check: Is total exposure acceptable? (20% max)
   - Calculate: Position size based on 2% risk rule
   - Validate: Sufficient buying power available
   - Result: Pass/Fail with reason

5. **Execution Decision** (Based on mode)

   - **Auto Mode**: If confidence >80% and risk checks pass → Execute immediately
   - **Manual Mode**: Add to pending signals → Wait for user approval
   - **Hybrid Mode**: If confidence >80% → Auto execute, else → Manual approval

6. **Trade Execution** (When approved/auto-triggered)

   - Submit market order to Alpaca
   - Wait for fill confirmation
   - Calculate actual entry price
   - Set stop loss at 3% below entry
   - Record trade in database
   - Update dashboard

7. **Position Monitoring** (Continuous during market hours)

   - Update current price every 30 seconds
   - Recalculate unrealized P&L
   - Check if stop loss triggered
   - If profit >5% → Activate trailing stop (2% trail)
   - Update trailing stop as price rises

8. **Stop Loss Execution** (When triggered)
   - Detect: Current price <= stop loss price
   - Execute: Submit market sell order immediately
   - Confirm: Wait for order fill
   - Record: Log trade closure with P&L
   - Notify: Update dashboard, send alert (optional)
   - Cleanup: Remove from active positions

### Expected Behavior Examples

**Scenario 1: High-Confidence Buy Signal (Auto Mode)**

```
10:15 AM: LSTM predicts PLTR will rise, confidence 85%
10:15 AM: Risk validation passes (all limits OK)
10:15 AM: Auto mode triggers immediate execution
10:15 AM: Market buy order submitted for 45 shares
10:15 AM: Order filled at $30.12 per share
10:15 AM: Stop loss set at $29.22 (3% below)
10:15 AM: Position appears on dashboard
10:15 AM: Trade logged to database
```

**Scenario 2: Medium-Confidence Signal (Hybrid Mode)**

```
11:30 AM: LSTM predicts PLTR will rise, confidence 72%
11:30 AM: Signal added to pending queue (below 80% auto threshold)
11:30 AM: Dashboard shows notification badge
12:45 PM: User reviews signal, sees technical indicators
12:45 PM: User approves signal
12:46 PM: Market buy order submitted for 45 shares
12:46 PM: Rest of flow same as Scenario 1
```

**Scenario 3: Stop Loss Triggered**

```
2:15 PM: PLTR drops from $32.00 to $29.22
2:15 PM: Stop loss manager detects trigger
2:15 PM: Market sell order submitted for 45 shares
2:15 PM: Order filled at $29.18 (slight slippage)
2:15 PM: Trade closed with -$42.30 loss (-2.3%)
2:15 PM: Position removed from active positions
2:15 PM: Dashboard updated with closed trade
2:15 PM: Loss counted toward daily loss limit
```

**Scenario 4: Trailing Stop Profit Protection**

```
11:00 AM: Enter PLTR at $30.00, stop at $29.10
11:45 AM: PLTR rises to $31.50 (+5% profit)
11:45 AM: Trailing stop activated at $30.87 (2% below)
1:30 PM: PLTR rises to $32.00
1:30 PM: Trailing stop updated to $31.36
2:45 PM: PLTR drops to $31.36
2:45 PM: Trailing stop triggered, sell order submitted
2:46 PM: Position closed with +$61.20 profit (+4.53%)
```

**Scenario 5: Daily Loss Limit Hit**

```
10:00 AM: Portfolio value starts at $10,000
11:00 AM: Trade 1 closed at -$200 loss (-2%)
1:00 PM: Trade 2 closed at -$150 loss (-1.5%)
2:00 PM: Trade 3 closed at -$180 loss (-1.8%)
2:00 PM: Total daily loss: -$530 (-5.3%)
2:00 PM: Daily loss limit exceeded (5% max)
2:00 PM: Bot automatically stops all trading
2:00 PM: Dashboard shows "CIRCUIT BREAKER TRIGGERED"
2:00 PM: No new positions allowed until next trading day
```

## Success Metrics

### User Satisfaction

- **Ease of Use**: User can set up bot in <30 minutes
- **Clarity**: User understands every trade decision
- **Control**: User feels in control, not replaced by bot
- **Reliability**: Bot runs for weeks without intervention

### System Performance

- **Uptime**: >99% during market hours
- **Response Time**: <1 second for dashboard updates
- **Execution Speed**: Orders submitted within 1 second of signal
- **Accuracy**: ML predictions >60% directional accuracy

### Trading Performance

- **Win Rate**: >50% of trades profitable
- **Sharpe Ratio**: >1.0 (risk-adjusted returns)
- **Maximum Drawdown**: <10% from peak
- **Risk Management**: Zero instances of rule violations

### Learning & Improvement

- **Data Collection**: 100% of trades logged with full context
- **Model Retraining**: Easy to retrain on new data
- **A/B Testing**: Can compare different model versions
- **Adaptability**: User can adjust parameters based on results

## Non-Functional Requirements

### Usability

- Dashboard must be intuitive for non-technical users
- All actions reversible or have confirmations
- Error messages must be clear and actionable
- Documentation must be comprehensive

### Reliability

- System must handle API failures gracefully
- No silent failures (all errors logged)
- Automatic reconnection after network issues
- Data integrity maintained even during crashes

### Performance

- Dashboard loads in <2 seconds
- Real-time updates without page refresh
- Predictions complete in <5 seconds
- Database queries optimized for speed

### Security

- API keys stored in environment variables (not code)
- Database credentials never exposed
- Web dashboard only accessible on localhost
- Logs don't contain sensitive information

### Maintainability

- Code organized into logical modules
- Clear naming conventions
- Comprehensive comments for complex logic
- Easy to add new features without breaking existing ones
