# Project Brief: AI Stock Trading Bot

## Project Overview

Build a production-ready AI stock trading bot using machine learning to automate personal stock trading with intelligent risk management and human oversight capabilities.

## Core Objectives

1. **Automated Trading**: Use LSTM neural networks to predict stock price movements and generate trading signals
2. **Risk Management**: Implement comprehensive risk controls for a $10,000 portfolio with strict position sizing and stop losses
3. **Hybrid Control**: Support automatic, manual, and hybrid trading modes for flexible human oversight
4. **Real-time Monitoring**: Provide web-based dashboard for portfolio tracking and trade approval
5. **Safe Testing**: Start with paper trading for thorough validation before real money deployment

## Technical Approach

### Machine Learning Strategy

- **Primary Model**: LSTM (Long Short-Term Memory) neural networks for time series prediction
- **Ensemble Method**: Combine LSTM with Random Forest for signal confirmation
- **Prediction Target**: Next-day price direction (up/down) with confidence scores
- **Features**: Technical indicators (RSI, MACD, Bollinger Bands, moving averages, volume)

### Trading Strategy

- **Initial Focus**: Single stock (Palantir - PLTR) for concentrated learning
- **Signal Generation**: ML predictions → confidence scoring → trade signals
- **Execution Modes**:
  - AUTO: Full automation for high-confidence signals (>80%)
  - MANUAL: All trades require human approval
  - HYBRID: Auto for high confidence, manual review for medium confidence
- **Order Types**: Market orders for execution, limit orders for precision

### Risk Management Framework

- **Position Sizing**: 2% risk per trade maximum
- **Portfolio Limits**:
  - Maximum 5 concurrent positions
  - Maximum 20% total portfolio exposure
  - 5% daily loss limit (circuit breaker)
- **Stop Losses**:
  - Initial stop: 3% below entry
  - Trailing stop: Activate at 5% profit, trail by 2%
- **Validation**: All trades validated against risk rules before execution

### Architecture

- **Language**: Python 3.10+ (ML ecosystem compatibility)
- **Broker API**: Alpaca (commission-free, excellent Python SDK)
- **Database**: SQLite (lightweight, sufficient for personal use)
- **Web Framework**: Flask (simple, proven, easy to deploy)
- **Design**: Modular components with clear separation of concerns

## Key Components

### 1. Data Pipeline

- Fetch historical and real-time market data
- Calculate technical indicators
- Engineer features for ML models
- Validate data quality

### 2. ML Engine

- Train LSTM models on historical data
- Generate real-time predictions
- Ensemble multiple prediction methods
- Backtest strategies on historical data

### 3. Trading Engine

- Generate trading signals from ML predictions
- Execute orders via Alpaca API
- Manage positions and track P&L
- Handle order lifecycle

### 4. Risk Management

- Calculate position sizes based on risk rules
- Monitor portfolio exposure and limits
- Implement stop loss mechanisms
- Validate trades before execution

### 5. Web Dashboard

- Real-time portfolio monitoring
- Trade history and performance metrics
- Signal approval interface (for manual/hybrid modes)
- Bot control (start/stop, mode switching)
- Configuration management

### 6. Database Layer

- Store trades, predictions, and signals
- Track performance metrics
- Maintain position history
- Support dashboard queries

## Success Criteria

### Phase 1: Development & Testing (Weeks 1-3)

- [ ] All components implemented and unit tested
- [ ] ML model achieves >60% directional accuracy on validation data
- [ ] Paper trading runs successfully for 2 weeks without crashes
- [ ] Dashboard displays accurate real-time data
- [ ] Risk management prevents rule violations

### Phase 2: Paper Trading Validation (Month 1)

- [ ] Bot trades autonomously in paper account for 30 days
- [ ] Risk limits enforced correctly (no violations)
- [ ] Sharpe ratio > 1.0 on paper trading results
- [ ] Win rate > 50% on executed trades
- [ ] Maximum drawdown < 10%

### Phase 3: Live Deployment (Month 2+)

- [ ] Transition to live trading with real money
- [ ] Start with $1,000 capital for cautious rollout
- [ ] Monitor daily for first 2 weeks
- [ ] Scale to full $10,000 after proven stability
- [ ] Maintain documentation and performance tracking

## Constraints & Requirements

### Technical Constraints

- Must use paper trading initially (safety)
- Internet connection required (API access)
- Trading limited to market hours (9:30 AM - 4:00 PM ET)
- US stocks only (Alpaca limitation)
- Minimum $2,000 capital for pattern day trading rules

### Development Constraints

- Solo developer project (no team)
- 18-day development timeline
- Budget: Free tier APIs where possible
- Local development environment

### Operational Constraints

- Must be runnable on personal computer
- Dashboard accessible via localhost
- Logs must be comprehensive for debugging
- Manual override always available
- Data backup and recovery procedures required

## Non-Goals (Out of Scope)

- ❌ Options or futures trading (too complex initially)
- ❌ Cryptocurrency trading (different market dynamics)
- ❌ High-frequency trading (requires different infrastructure)
- ❌ Multiple simultaneous bots (focus on one strategy)
- ❌ Mobile app (web dashboard sufficient)
- ❌ Social trading or signal sharing (personal use only)
- ❌ Advanced portfolio optimization (keep it simple initially)

## Risk Mitigation

### Technical Risks

- **Model Accuracy**: Mitigate with ensemble methods and backtesting
- **API Failures**: Implement retry logic and error handling
- **Data Quality**: Validate all data before use
- **System Crashes**: Comprehensive logging and graceful degradation

### Financial Risks

- **Large Losses**: Strict position sizing and stop losses
- **Over-trading**: Daily loss limits and trade frequency caps
- **Market Gaps**: Avoid holding overnight initially
- **Fat-finger Errors**: Manual approval mode for validation

### Operational Risks

- **Missed Trades**: Paper trading first to identify issues
- **Configuration Errors**: Validation on all settings
- **Network Issues**: Timeout handling and reconnection logic
- **Data Loss**: Regular database backups

## Timeline

**Total Duration**: 18 days (development) + 30 days (paper trading)

- **Days 1-2**: Project setup and configuration
- **Days 3-4**: Data pipeline implementation
- **Days 5-7**: ML engine development
- **Days 8-9**: Risk management system
- **Days 10-11**: Trading engine
- **Day 12**: Database layer
- **Day 13**: Main application orchestrator
- **Days 14-15**: Web dashboard
- **Days 16-17**: Integration testing
- **Day 18**: Documentation and deployment

## Dependencies

### External Services

- **Alpaca Markets**: Broker API (free paper trading account)
- **Yahoo Finance**: Historical data backup source
- **TA-Lib**: Technical analysis library (C library required)

### Python Packages

- TensorFlow 2.14 (ML models)
- scikit-learn 1.3 (preprocessing, ensemble)
- pandas 2.1 (data manipulation)
- Flask 3.0 (web framework)
- alpaca-trade-api 3.0 (broker integration)

## Stakeholders

- **Primary User**: Solo developer/trader
- **No External Stakeholders**: Personal project

## Definition of Done

The project is complete when:

1. ✅ All 6 Memory Bank files are created and accurate
2. ✅ All code modules implemented per implementation plan
3. ✅ Unit tests pass with >80% coverage
4. ✅ Paper trading runs successfully for 2 weeks
5. ✅ Dashboard functional and displaying accurate data
6. ✅ Risk management prevents all rule violations
7. ✅ Documentation complete (README, API docs, runbooks)
8. ✅ Bot ready for supervised live deployment
