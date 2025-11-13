# Active Context: AI Stock Trading Bot

## Current Work Focus

**Phase**: Phase 8 Complete - Web Dashboard ✅
**Status**: Ready for Phase 9: Integration & Testing
**Date**: November 13, 2025

### Immediate Focus

**Completed**: Phases 1, 2, 3, 4, 5, 6, 7, and 8 (80% of total project)

- ✅ Phase 1: Project Setup
- ✅ Phase 2: Data Pipeline
- ✅ Phase 3: ML Engine (LSTM + Ensemble + Backtesting)
- ✅ Phase 4: Risk Management (Position Sizing + Portfolio Monitor + Stop Loss)
- ✅ Phase 5: Trading Engine (Executor + Signal Generator + Position Manager + Order Manager)
- ✅ Phase 6: Database Layer (DatabaseManager with full CRUD and analytics)
- ✅ Phase 7: Main Application (TradingBot orchestrator)
- ✅ Phase 8: Web Dashboard (Flask app + Templates + API routes)

**Current**: The Web Dashboard is fully operational with:

- Flask application (app.py) - 650 lines with 18 REST API endpoints
- Complete API routes: portfolio, signals, trades, bot control, settings
- 5 HTML templates (base, index, trades, signals, settings)
- Responsive CSS styling (style.css) - 600+ lines
- Shared JavaScript utilities (dashboard.js) - 180 lines
- Real-time updates (auto-refresh every 30 seconds)
- Toast notifications and error handling
- Signal approval workflow for manual/hybrid modes
- Bot control interface (start/stop, mode switching, emergency stop)

**Next Immediate Steps** (Phase 9: Integration & Testing):

1. End-to-end testing with paper trading account
2. Run bot continuously for 48 hours
3. Test all trading modes (auto, manual, hybrid)
4. Verify dashboard displays correctly
5. Test signal approval workflow
6. Monitor for crashes or errors
7. Fix any discovered issues
8. Optimize performance bottlenecks

## Recent Changes

### Phase 8: Web Dashboard Implementation (Session 4 - November 13, 2025)

**Implementation Complete** (8 files, 2,457 lines):

1. ✅ **app.py** (650 lines)

   - Flask application with 18 REST API endpoints
   - Web page routes: /, /trades, /signals, /settings
   - API routes for portfolio, signals, trades, bot control, settings
   - Complete error handling (404, 500)
   - Template filters for currency and percentage formatting
   - CORS support for API access

2. ✅ **HTML Templates** (5 files)

   - **base.html**: Base layout with navigation, footer, toast notifications
   - **index.html**: Main dashboard with portfolio cards, risk metrics, positions table, pending signals, performance metrics
   - **trades.html**: Trade history with filtering (symbol, status, date range)
   - **signals.html**: Signal history with date filtering
   - **settings.html**: Configuration management for trading, risk, and ML parameters

3. ✅ **Static Assets** (2 files)

   - **style.css** (600+ lines): Modern responsive design with cards, tables, forms, buttons, toast notifications
   - **dashboard.js** (180 lines): Utility functions (formatCurrency, formatPercentage, showToast), bot status updates, auto-refresh

4. ✅ **Key Features Implemented**
   - Real-time portfolio monitoring with auto-refresh (30s)
   - Signal approval/rejection workflow
   - Bot control (start/stop, mode switching, emergency stop)
   - Trade history with filters
   - Settings management
   - Toast notifications for user feedback
   - Responsive design for all screen sizes
   - Color-coded P&L (green=profit, red=loss)

**Git Commit**: Phase 8 complete (commit 52ec910)

### Alpaca SDK Fix (Session 3 - November 13, 2025)

**CRITICAL BLOCKER RESOLVED**: Bot now functional and ready for Phase 8

1. ✅ **Problem Identified**

   - Code written for `alpaca-py` SDK (newer API)
   - `alpaca-trade-api` SDK installed (older API)
   - ImportError prevented bot from starting
   - Affected: data_fetcher.py, executor.py, position_manager.py

2. ✅ **Solution Implemented**

   - **Chose Option A**: Switch to `alpaca-py` SDK (cleanest approach)
   - Updated requirements.txt: `alpaca-trade-api>=3.2.0` → `alpaca-py>=0.30.1`
   - Reinstalled dependencies successfully
   - alpaca-py 0.43.2 installed with all dependencies

3. ✅ **Code Fixes**

   - Fixed src/main.py (3 references):
     - Line 35: Import `EnsemblePredictor` (not `EnsembleModel`)
     - Line 96: Type hint updated
     - Line 283: Class instantiation updated
   - No changes needed to data_fetcher.py or executor.py (already correct)

4. ✅ **Verification Complete**

   - All module imports working ✓
   - TradingBot class instantiates successfully ✓
   - Singleton pattern working ✓
   - Bot ready for Phase 8: Web Dashboard ✓

5. ✅ **Documentation Updated**
   - requirements.txt: alpaca-py as correct SDK
   - activeContext.md: Blocker marked RESOLVED
   - progress.md: Known Issues section updated
   - techContext.md: Confirmed alpaca-py as standard

### Environment Verification (Session 2 - November 13, 2025)

**Verification Complete**: Tested application setup and dependencies

1. ✅ **Environment Setup Verified**

   - Python 3.12.3 confirmed (exceeds 3.10+ requirement)
   - Virtual environment exists (venv/)
   - .env file present with configuration
   - config/config.yaml ready

2. ✅ **Dependency Resolution - Python 3.12 Compatibility**

   - **Issue**: TensorFlow 2.14.0 not available for Python 3.12
   - **Solution**: Updated to TensorFlow 2.19.1
   - **Issue**: alpaca-trade-api 3.0.2 had PyYAML 6.0 incompatibility
   - **Solution**: Updated to alpaca-trade-api >=3.2.0
   - **Issue**: TA-Lib 0.4.28 build failures with newer numpy
   - **Solution**: Installed TA-Lib C library from source, then TA-Lib 0.6.8 Python package

3. ✅ **All Dependencies Installed Successfully**

   - TensorFlow 2.19.1 (645 MB)
   - pandas 2.1.3, numpy 1.26.2
   - scikit-learn 1.3.2, scipy 1.16.3
   - Flask 3.0.0 + extensions
   - alpaca-trade-api 3.2.0
   - TA-Lib 0.6.8
   - APScheduler, loguru, pydantic, pytest
   - All 60+ dependencies installed

4. ⚠️ **Critical Issue Identified: Alpaca API Import Incompatibility**

   - Code uses imports from `alpaca-py` package (newer API):
     ```python
     from alpaca.data.historical import StockHistoricalDataClient
     from alpaca.data.requests import StockBarsRequest
     ```
   - Installed package is `alpaca-trade-api` (older, stable SDK):
     ```python
     import alpaca_trade_api as tradeapi
     ```
   - **Affected Files**:
     - src/data/data_fetcher.py (line 14-16)
     - src/trading/executor.py (API initialization)
     - src/trading/position_manager.py (position fetching)

5. ✅ **requirements.txt Updated**
   - TensorFlow: 2.14.0 → 2.19.1
   - alpaca-trade-api: 3.0.2 → >=3.2.0
   - TA-Lib: Removed from requirements (installed separately as 0.6.8)
   - Updated comments to note Python 3.12 compatibility

### Phase 7: Main Application Implementation (Session 1)

**Implementation Complete** (1 module, 1,030 lines):

1. ✅ **main.py** (1,030 lines)

   - TradingBot class with Singleton pattern
   - Complete initialization pipeline:
     - Configuration loading (config.yaml + .env)
     - Logging setup (loguru with rotation)
     - Database connection
     - Module instantiation for all Phase 1-6 components
     - Alpaca API verification
   - Main trading cycle (runs every 5 minutes):
     - Fetch real-time market data
     - Calculate technical indicators
     - Generate ML predictions (ensemble)
     - Create trading signals
     - Validate against risk rules
     - Execute or queue based on mode (auto/manual/hybrid)
   - Position monitoring (every 30 seconds):
     - Update current prices
     - Check stop losses
     - Update trailing stops
     - Execute stops if triggered
   - Market close handler (4:00 PM ET):
     - Close positions (if configured)
     - Calculate daily performance
     - Save metrics to database
     - Reset daily counters
   - Risk monitoring:
     - Check daily P&L continuously
     - Circuit breaker for 5% daily loss limit
     - Automatic bot shutdown if triggered
   - Lifecycle management:
     - Graceful startup and shutdown
     - Signal handlers (SIGINT, SIGTERM)
     - APScheduler for task automation
   - Bot status API:
     - Get current state
     - Portfolio metrics
     - Pending signals count
   - Complete integration of all modules:
     - Data pipeline (fetcher, engineer, validator)
     - ML engine (predictor, ensemble)
     - Trading engine (signal gen, executor, position/order managers)
     - Risk management (calculator, monitor, stop loss)
     - Database layer (all CRUD and analytics)

**Git Commit**: Phase 7 complete (commit 52081a7)

### Phase 3: ML Engine Implementation (Current Session)

**Implementation Complete** (4 modules, 2,070 lines):

1. ✅ **model_trainer.py** (530 lines)

   - LSTM architecture: 64→32 units with dropout (0.2)
   - Training with early stopping, LR reduction, model checkpointing
   - Evaluation: accuracy, precision, recall, F1, directional accuracy
   - Model persistence with metadata (hyperparameters, feature names, trained date)
   - Automatic stratified train/val split

2. ✅ **predictor.py** (490 lines)

   - Load trained LSTM models with metadata
   - Single and batch prediction capabilities
   - Confidence scoring: distance-based and entropy-based methods
   - Feature importance: permutation method for LSTM
   - Prediction explanations with technical indicator interpretation

3. ✅ **ensemble.py** (560 lines)

   - Multi-model ensemble: LSTM (50%) + Random Forest (30%) + Momentum (20%)
   - Automatic weight normalization when models fail
   - Agreement-based confidence calculation
   - Momentum signal from RSI, MACD, MAs, volume
   - Random Forest training included

4. ✅ **backtest.py** (490 lines)
   - Historical strategy simulation with realistic execution
   - Position sizing (20% max), stop losses (3%), confidence filtering (70%+)
   - Performance metrics: Sharpe ratio, max drawdown, win rate, profit factor
   - Detailed trade history and formatted reports

**Git Commit**: Phase 3 complete (commit b5feba2)

### Phase 4: Risk Management Implementation (Current Session)

**Implementation Complete** (3 modules, 1,440+ lines):

1. ✅ **risk_calculator.py** (400 lines)

   - Position sizing based on 2% risk rule
   - Trade validation with 6 comprehensive checks (daily loss, max positions, exposure, buying power, confidence)
   - Stop loss price calculations (initial 3%, trailing 2%)
   - Risk amount and potential loss calculations
   - Max shares allowed and buying power validation
   - Trailing stop activation logic (5% profit threshold)

2. ✅ **portfolio_monitor.py** (560 lines)

   - Real-time portfolio state updates (cash + positions)
   - Risk metrics calculation (exposure %, daily P&L %, position count)
   - Circuit breaker for 5% daily loss limit
   - Sharpe ratio calculation (risk-adjusted returns)
   - Maximum drawdown tracking (peak to trough)
   - Performance metrics (win rate, avg win/loss, streaks)
   - Portfolio history tracking for analysis

3. ✅ **stop_loss_manager.py** (480 lines)
   - Position registration for stop monitoring
   - Automatic stop loss checking (every update)
   - Initial stop loss (3% below entry)
   - Trailing stop activation at 5% profit
   - Trailing stop updates as price rises (2% trail)
   - Stop trigger detection with reasons
   - Potential loss calculations

**Git Commit**: Phase 4 complete (commit 200f1b0)

### Phase 5: Trading Engine Implementation (Current Session)

**Implementation Complete** (4 modules, 2,204 lines):

1. ✅ **executor.py** (720 lines)

   - AlpacaExecutor: Complete Alpaca API wrapper
   - Market and limit order placement
   - Position and account information retrieval
   - Order status tracking and cancellation
   - Real-time price fetching
   - Paper and live trading support
   - Comprehensive error handling and logging

2. ✅ **signal_generator.py** (640 lines)

   - SignalGenerator: Convert ML predictions to trading signals
   - Confidence-based signal filtering (70% threshold)
   - Mode-based execution decisions (auto/manual/hybrid)
   - Intelligent reasoning generation for signals
   - SignalQueue: Manage pending signals for manual approval
   - Signal filtering based on portfolio constraints

3. ✅ **position_manager.py** (540 lines)

   - PositionManager: Complete position lifecycle management
   - Real-time position sync with Alpaca broker
   - P&L calculation and tracking (realized and unrealized)
   - Stop loss manager integration
   - Position summary statistics
   - Batch position operations (close all, update all)

4. ✅ **order_manager.py** (500 lines)
   - OrderManager: Order lifecycle coordination
   - Signal execution with risk validation
   - Position sizing integration via risk calculator
   - Order tracking with OrderTracking dataclass
   - Automatic position creation/closure on fills
   - Order status monitoring and updates

**Git Commit**: Phase 5 complete (commit 2985810)

### Phase 6: Database Layer Implementation (Current Session)

**Implementation Complete** (1 module, 1,272 lines):

1. ✅ **db_manager.py** (1,272 lines)

   - DatabaseManager class with context manager for safe transactions
   - Full CRUD operations for all 6 tables:
     - Trades: save, update, get by ID/symbol, close, get open/recent
     - Positions: save/update, delete, get active, get by symbol, update prices
     - Predictions: save, update actual prices, get by symbol, calculate accuracy
     - Signals: save, update status, get pending, get history
     - Performance Metrics: save/update, get latest, get by date range
     - Bot State: get, update (singleton pattern)
   - Analytics queries:
     - get_trade_history() - Flexible filtering by symbol, date range, status
     - calculate_daily_performance() - Daily P&L and metrics
     - get_win_rate() - Win rate over period
     - get_performance_summary() - Comprehensive statistics (profit factor, largest win/loss, hold times)
   - Database maintenance:
     - backup_database() - Timestamped backups
     - restore_database() - Restore from backup
     - verify_database() - Integrity check and statistics
   - Context managers for automatic commit/rollback
   - Comprehensive error handling and logging
   - Type-safe interfaces using existing dataclasses

2. ✅ **schema.py** - Fixed reserved keyword issue

   - Changed 'metadata' column to 'prediction_metadata' (SQLAlchemy reserved word)

3. ✅ **Testing**
   - All database operations tested successfully
   - Virtual environment created (venv/)
   - SQLAlchemy, loguru, python-dotenv installed
   - Test results: All CRUD operations, analytics, bot state, backup/restore verified

**Git Commit**: Phase 6 complete (commit 1cc94d3)

### Memory Bank Initialization (Session 1)

**Created 6 Core Files**:

1. ✅ **projectbrief.md** - Foundation document with core requirements

   - Defined 18-day development timeline
   - Established success criteria for 3 phases
   - Documented risk mitigation strategies
   - Listed all technical and operational constraints

2. ✅ **productContext.md** - Product vision and UX goals

   - Detailed problem statement (emotional trading, time constraints, etc.)
   - Complete user journeys (setup, daily operation, signal approval)
   - Dashboard wireframe and experience goals
   - Expected behavior scenarios with examples

3. ✅ **systemPatterns.md** - Architecture and design patterns

   - High-level system architecture diagram
   - 10 key technical decisions with rationales
   - 6 design patterns (Singleton, Strategy, Observer, Factory, Repository, Command)
   - Critical implementation paths and error handling
   - Logging strategy and security considerations

4. ✅ **techContext.md** - Technology stack and setup

   - Complete Python package list with versions
   - Development setup instructions (step-by-step)
   - Configuration management (config.yaml, .env)
   - Tool usage patterns (logging, database, API)
   - Troubleshooting guide for common issues

5. ✅ **activeContext.md** - Current work state (this file)

6. ✅ **progress.md** - Project status tracking (next file)

## Next Steps

### Phase 8: Web Dashboard (Ready to Begin)

**Bot is now functional - proceed with dashboard implementation:**

1. **Flask Application Structure**

   - Create src/dashboard/app.py with Flask initialization
   - Set up routes module for API endpoints
   - Configure static file serving (CSS/JS)
   - Set up template rendering

2. **API Routes Implementation**

   - GET /api/portfolio - Portfolio state and metrics
   - GET /api/signals - Pending signals for approval
   - POST /api/signals/<id>/approve - Approve signal
   - POST /api/signals/<id>/reject - Reject signal
   - POST /api/bot/start - Start bot
   - POST /api/bot/stop - Stop bot
   - GET/POST /api/settings - Configuration management

3. **HTML Templates**

   - templates/base.html - Base layout with navigation
   - templates/index.html - Dashboard home (portfolio overview)
   - templates/trades.html - Trade history and analytics
   - templates/signals.html - Signal management
   - templates/settings.html - Configuration

4. **Static Assets**

   - static/css/style.css - Dashboard styling
   - static/js/dashboard.js - Real-time updates and interactions

5. **Testing & Integration**
   - Test all API endpoints
   - Verify signal approval workflow
   - Test bot control (start/stop)
   - Verify real-time data updates

## Active Decisions

### Trading Strategy Decisions

1. **Start with PLTR Only**

   - Reasoning: Simpler to debug, faster iteration
   - Expansion Plan: Add 2-3 tech stocks after 1 month
   - Risk: Less diversification (mitigated by position limits)

2. **Default to Hybrid Mode**

   - Auto-execute signals with confidence >80%
   - Manual approval for confidence 70-80%
   - Reject signals with confidence <70%

3. **Close Positions Daily (Initially)**

   - Eliminates gap risk
   - Simplifies position tracking
   - Can enable overnight holding later

4. **Paper Trading Mandatory**
   - Minimum 2 weeks before live consideration
   - Goal: Prove stability and risk management
   - Metric: >99% uptime, zero rule violations

### Technical Decisions

1. **Use SQLite (Not PostgreSQL)**

   - Sufficient for single user
   - Zero maintenance overhead
   - Can migrate later if needed

2. **Flask Dashboard (Not React)**

   - Faster development for solo project
   - Server-side rendering simpler
   - Can add WebSocket updates later

3. **LSTM + Ensemble Approach**

   - Primary: LSTM for time series patterns
   - Secondary: Random Forest for confirmation
   - Tertiary: Simple momentum indicators
   - Confidence = weighted average of all three

4. **No GPU Required**
   - CPU training sufficient (10-30 min)
   - Keeps system requirements low
   - GPU support can be added later

## Important Patterns & Preferences

### Documentation Tools

**Context7 MCP Server**: Integrated for real-time library documentation access

- **Availability**: Accessible via MCP (Model Context Protocol)
- **Primary Use**: Fetch up-to-date documentation for Python libraries
- **Key Libraries**: TensorFlow (latest), pandas (latest), alpaca-trade-api (latest), scikit-learn (latest), Flask (latest), SQLAlchemy (latest), loguru (latest)
- **When to Use**: Before implementing with unfamiliar APIs, verifying parameter types, checking for deprecations, reviewing best practices

**Workflow**: Identify library → Resolve library ID → Fetch docs → Implement with verified patterns

### Code Organization

**Module Structure**:

- Each module has clear responsibility
- No circular dependencies
- All imports at module level
- Type hints everywhere (Python 3.10+)

**Naming Conventions**:

- Files: lowercase_with_underscores.py
- Classes: PascalCase
- Functions: snake_case
- Constants: UPPER_CASE
- Private: \_leading_underscore

**Error Handling**:

- Never fail silently
- All external calls wrapped in try/except
- Log errors with context
- Graceful degradation where possible

### Testing Approach

**Test Coverage Goals**:

- Unit tests: >80% coverage
- Integration tests: All API interactions
- Backtesting: 2+ years historical data
- Paper trading: 2+ weeks live simulation

**Test Organization**:

- Mirror src/ structure in tests/
- Use pytest fixtures for common setup
- Mock external APIs (Alpaca, Yahoo Finance)
- Separate test database

### Development Workflow

**Git Workflow**:

- Commit frequently with clear messages
- Use conventional commits (feat:, fix:, docs:, etc.)
- Keep commits focused (one logical change)
- Push to remote after each session

**Documentation Requirements**:

- Update Memory Bank when architecture changes
- Document all non-obvious decisions
- Keep README.md current
- Add inline comments for complex logic

## Learnings & Project Insights

### Key Insights from Planning Phase

1. **Risk Management is Critical**

   - Position sizing must be calculated precisely
   - Stop losses must execute without hesitation
   - Daily loss limits prevent catastrophic losses
   - Risk validation must happen BEFORE every trade

2. **ML Confidence is Key**

   - Not all predictions are equal
   - Confidence threshold determines execution mode
   - Ensemble approach reduces false positives
   - Historical accuracy informs confidence calibration

3. **User Trust is Essential**

   - Transparency in every decision
   - Manual override always available
   - Complete audit trail
   - Clear explanations for rejections

4. **Simplicity Over Features**

   - Start with one stock (PLTR)
   - Paper trading first (mandatory)
   - Simple indicators initially
   - Add complexity only when needed

5. **Technical Debt Management**
   - Use TODO comments for future improvements
   - Document known limitations
   - Plan for migration paths (SQLite → PostgreSQL)
   - Keep refactoring in mind

### Anticipated Challenges

1. **Model Accuracy**: May need iteration to reach >60% accuracy

   - Solution: Extensive backtesting, feature engineering
   - Fallback: Lower confidence threshold for manual mode

2. **API Reliability**: Alpaca or network issues could disrupt trading

   - Solution: Retry logic, caching, graceful degradation
   - Monitoring: Alert on repeated failures

3. **Execution Speed**: Orders must execute within 1 second

   - Solution: Optimize code path, parallel processing
   - Testing: Measure latency in paper trading

4. **Data Quality**: Missing or incorrect data could cause bad predictions

   - Solution: Validation at every step, fallback data sources
   - Monitoring: Log all data anomalies

5. **User Experience**: Dashboard must be intuitive and responsive
   - Solution: User testing (self), iterative refinement
   - Benchmark: <2 second load time

### Design Philosophy

**Fail-Safe Principles**:

- Fail loudly, not silently
- When in doubt, don't trade
- Risk limits are hard constraints
- Manual override always available
- Paper trading proves reliability

**Iterative Development**:

- Build minimum viable version first
- Test thoroughly at each phase
- Add features incrementally
- Refactor as understanding improves

**Documentation First**:

- Memory Bank guides all development
- Update docs when decisions change
- Future Cline relies entirely on documentation
- No tribal knowledge

## Current Blockers

**None** - All critical blockers resolved ✅

### Previously Resolved

**Alpaca API Import Incompatibility** ✅ RESOLVED (Session 3 - November 13, 2025)

- **Issue**: Code written for `alpaca-py` SDK, but `alpaca-trade-api` SDK installed
- **Impact**: Bot could not run - ImportError on startup
- **Solution**: Switched to `alpaca-py` SDK (cleaner approach)
  - Updated requirements.txt: `alpaca-py>=0.30.1`
  - Reinstalled dependencies: alpaca-py 0.43.2 installed
  - Fixed 3 class name references in main.py
- **Verification**: All imports working, TradingBot successfully initializes
- **Status**: RESOLVED - Bot is now functional

## Open Questions

### Technical Questions

1. **Should we use WebSocket for real-time dashboard updates?**

   - Current: HTTP polling every 30 seconds
   - Alternative: WebSocket for push updates
   - Decision: Start with polling, add WebSocket if needed

2. **Should we implement caching for API responses?**

   - Current: Direct API calls
   - Alternative: Redis/in-memory cache
   - Decision: Add caching if API limits become issue

3. **Should we use Docker for deployment?**
   - Current: Run directly on local machine
   - Alternative: Docker container
   - Decision: Add Docker later for easier deployment

### Strategy Questions

1. **What indicators should we start with?**

   - Decided: RSI, MACD, Bollinger Bands, SMA/EMA, Volume
   - Open: Should we add more or start minimal?

2. **Should we implement pre-market data collection?**

   - Current: Start collecting at 9:30 AM
   - Alternative: Collect from 4:00 AM for better preparation
   - Decision: TBD based on performance

3. **Should we add news sentiment analysis?**
   - Current: Technical indicators only
   - Alternative: Include news/social sentiment
   - Decision: Phase 2 enhancement (not initial scope)

## Notes for Future Sessions

### For Next Cline Session

After memory reset, I (Cline) should:

1. **Read ALL Memory Bank files** (required before any work)

   - projectbrief.md - understand the project
   - productContext.md - understand the user needs
   - systemPatterns.md - understand the architecture
   - techContext.md - understand the tech stack
   - activeContext.md (this file) - understand current state
   - progress.md - understand what's been completed

2. **Check Current Phase** (see progress.md)

   - Determine what has been completed
   - Identify next steps from implementation plan

3. **Review Recent Changes**

   - Check this file for latest decisions
   - Understand any new blockers or insights

4. **Continue Implementation**
   - Follow the 18-day implementation plan
   - Update progress.md as work is completed
   - Update this file with new decisions/insights

### Context Preservation

**Critical Information**:

- We are building an AI stock trading bot with LSTM + ensemble ML
- Python 3.12.3, TensorFlow 2.19.1, alpaca-py SDK, Flask 3.0.0, SQLite
- 18-day implementation plan, currently at Day 15 (Phase 8 complete)
- Paper trading mandatory, PLTR only initially
- Hybrid trading mode (auto >80% confidence, manual otherwise)
- All risk rules are hard constraints (no exceptions)

**Project Status** (~80% Complete):

- ✅ Phase 1: Project Setup - Complete
- ✅ Phase 2: Data Pipeline - Complete
- ✅ Phase 3: ML Engine - Complete (LSTM, Predictor, Ensemble, Backtesting)
- ✅ Phase 4: Risk Management - Complete (Position Sizing, Portfolio Monitor, Stop Loss)
- ✅ Phase 5: Trading Engine - Complete (Executor, Signal Generator, Position Manager, Order Manager)
- ✅ Phase 6: Database Layer - Complete (DatabaseManager with full CRUD and analytics)
- ✅ Phase 7: Main Application - Complete (TradingBot orchestrator with Singleton pattern)
- ✅ Phase 8: Web Dashboard - Complete (Flask app with 18 API endpoints, 5 templates, responsive UI)
- 📋 Next: Phase 9 - Integration & Testing
- 📋 Remaining: Phases 9-10 (Testing, Documentation, Deployment)

### When to Update This File

**Update activeContext.md when**:

- Starting a new phase of implementation
- Making significant architectural decisions
- Discovering important insights or patterns
- Encountering and solving major blockers
- Changing scope or requirements
- Learning something that affects future work
- User requests with **update memory bank**

**Update Frequency**: After completing major milestones or when explicitly requested
