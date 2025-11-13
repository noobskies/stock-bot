# Active Context: AI Stock Trading Bot

## Current Work Focus

**Phase**: Project Initialization
**Status**: Memory Bank setup complete, ready to begin implementation
**Date**: November 13, 2025

### Immediate Focus

We are at the **very beginning** of the AI Stock Trading Bot project. The Memory Bank has been initialized with complete documentation covering:

- Project requirements and scope (projectbrief.md)
- Product vision and user experience (productContext.md)
- System architecture and patterns (systemPatterns.md)
- Technology stack and setup (techContext.md)
- Current state (this file - activeContext.md)
- Progress tracking (progress.md)

**Next Immediate Steps**:

1. Set up project directory structure
2. Create configuration files (.env.example, config.yaml, .gitignore)
3. Initialize Git repository
4. Create requirements.txt with all dependencies
5. Begin Phase 1: Data Pipeline implementation

## Recent Changes

### Memory Bank Initialization (Current Session)

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

### Immediate Actions (Phase 1: Days 1-2)

1. **Project Structure Setup**

   - Create all directories per implementation plan
   - Set up Git repository and .gitignore
   - Create placeholder files for core modules

2. **Configuration Files**

   - Create .env.example template
   - Create config/config.yaml with default values
   - Document all configuration options

3. **Dependency Management**

   - Create requirements.txt with pinned versions
   - Set up virtual environment
   - Test TA-Lib installation (potential blocker)

4. **Database Schema**

   - Create SQLAlchemy models (schema.py)
   - Define tables: trades, positions, predictions, signals
   - Add indices for performance

5. **Alpaca API Verification**
   - Test connection with paper trading keys
   - Verify account access
   - Test basic order placement (paper trading)

### Short-term Goals (Next 7 Days)

**Phase 1: Project Setup (Days 1-2)**

- Complete directory structure
- Initialize database
- Verify all external dependencies

**Phase 2: Data Pipeline (Days 3-4)**

- Implement data_fetcher.py
- Build feature_engineer.py
- Create data_validator.py
- Test with PLTR historical data

**Phase 3: ML Engine Foundation (Days 5-7)**

- Implement LSTM model architecture
- Build training pipeline
- Create predictor.py for inference

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

**None** - Project is at initialization stage with clear path forward.

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
- Python 3.10+, TensorFlow, Alpaca API, Flask, SQLite
- 18-day implementation plan, currently at Day 0 (initialization)
- Paper trading mandatory, PLTR only initially
- Hybrid trading mode (auto >80% confidence, manual otherwise)
- All risk rules are hard constraints (no exceptions)

**Project Status**:

- ✅ Memory Bank initialized
- ❌ No code written yet
- ❌ No dependencies installed yet
- ❌ No Alpaca account configured yet
- 📋 Ready to begin Phase 1: Project Setup

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
