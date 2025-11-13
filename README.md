# AI Stock Trading Bot

An intelligent stock trading bot using LSTM neural networks and ensemble machine learning for automated trading with comprehensive risk management.

## 🎯 Project Overview

This bot uses machine learning to predict stock price movements and execute trades automatically via the Alpaca API. It features hybrid trading modes (automatic + manual approval), strict risk management for a $10,000 portfolio, and a web-based dashboard for monitoring and control.

**Current Status:** Phase 1 - Project Setup Complete ✅

## ✨ Key Features

- **ML-Powered Predictions**: LSTM neural networks combined with Random Forest for ensemble predictions
- **Three Trading Modes**:
  - **Auto**: Full automation for high-confidence signals (>80%)
  - **Manual**: All trades require human approval
  - **Hybrid**: Auto for high confidence, manual review for medium confidence (default)
- **Comprehensive Risk Management**:
  - 2% risk per trade maximum
  - 5% daily loss limit (circuit breaker)
  - 20% maximum portfolio exposure
  - Automatic stop losses and trailing stops
- **Web Dashboard**: Real-time portfolio monitoring and trade approval interface
- **Paper Trading First**: Mandatory paper trading before live deployment

## 🏗️ Architecture

```
stock-bot/
├── src/
│   ├── data/          # Data fetching and feature engineering
│   ├── ml/            # LSTM models and predictions
│   ├── trading/       # Order execution and position management
│   ├── risk/          # Risk calculation and portfolio monitoring
│   ├── database/      # SQLite persistence layer
│   ├── dashboard/     # Flask web interface
│   └── types/         # Type definitions
├── config/            # Configuration files
├── models/            # Trained ML models
├── logs/              # Application logs
└── tests/             # Test suite
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- TA-Lib C library (see installation below)
- Alpaca paper trading account (free at [alpaca.markets](https://alpaca.markets))

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd stock-bot
```

2. **Install TA-Lib C library**

**Linux (Ubuntu/Debian):**

```bash
sudo apt-get update
sudo apt-get install ta-lib
```

**macOS:**

```bash
brew install ta-lib
```

**Windows (WSL2):**

```bash
# In WSL2 Ubuntu terminal
sudo apt-get install ta-lib
```

3. **Create virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

4. **Install Python dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

5. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your Alpaca API credentials
nano .env  # or use your preferred editor
```

6. **Initialize database**

```bash
python src/database/schema.py
```

### Running the Bot

**Start the trading bot:**

```bash
python src/main.py
```

**Start the web dashboard (separate terminal):**

```bash
python src/dashboard/app.py
# Dashboard available at http://localhost:5000
```

## ⚙️ Configuration

### Environment Variables (.env)

- `ALPACA_API_KEY`: Your Alpaca API key (paper trading)
- `ALPACA_SECRET_KEY`: Your Alpaca secret key (paper trading)
- `TRADING_MODE`: Trading mode (auto/manual/hybrid)
- See `.env.example` for all configuration options

### Bot Settings (config/config.yaml)

- Trading parameters (symbols, position limits)
- Risk management rules
- ML model configuration
- Dashboard settings

## 📊 Trading Strategy

### Entry Criteria

1. LSTM model predicts price increase
2. Ensemble confidence >70% (manual) or >80% (auto)
3. Technical indicators confirm (RSI, MACD, Bollinger Bands)
4. Risk validation passes (portfolio limits, position sizing)

### Exit Criteria

1. Stop loss triggered (3% below entry)
2. Trailing stop triggered (2% below peak after 5% profit)
3. End of day (positions closed by default)
4. ML model predicts reversal

### Risk Management

- **Position Sizing**: 2% of portfolio at risk per trade
- **Stop Loss**: 3% below entry price (automatic)
- **Trailing Stop**: Activates at 5% profit, trails by 2%
- **Daily Loss Limit**: 5% maximum (circuit breaker stops trading)
- **Portfolio Limits**: Max 5 positions, 20% total exposure

## 🧪 Testing

### Run Unit Tests

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest --cov=src tests/
```

### Backtesting

```bash
python src/ml/backtest.py --symbol PLTR --start 2020-01-01 --end 2023-12-31
```

## 📈 Performance Metrics

Target performance (validated in paper trading):

- **Win Rate**: >50% of trades profitable
- **Sharpe Ratio**: >1.0 (risk-adjusted returns)
- **Maximum Drawdown**: <10% from peak
- **Uptime**: >99% during market hours

## 🛡️ Safety Features

- **Paper Trading Default**: Starts in paper trading mode
- **Manual Override**: Always available for any decision
- **Risk Limits**: Hard-coded constraints, never bypassed
- **Circuit Breaker**: Auto-stops at 5% daily loss
- **Comprehensive Logging**: Every decision recorded
- **Emergency Stop**: Instant shutdown capability

## 📝 Development Status

### Phase 1: Project Setup ✅ (Complete)

- [x] Directory structure created
- [x] Configuration files set up
- [x] Git repository initialized
- [x] Dependencies documented

### Phase 2: Data Pipeline (Days 3-4)

- [ ] Implement data fetcher
- [ ] Build feature engineer
- [ ] Create data validator

### Phase 3: ML Engine (Days 5-7)

- [ ] LSTM model architecture
- [ ] Training pipeline
- [ ] Prediction service
- [ ] Backtesting framework

### Phase 4-10: See implementation_plan.md for full roadmap

## 🤝 Contributing

This is a personal project currently in active development. Contributions and suggestions are welcome once the initial version is complete.

## ⚠️ Disclaimer

**This bot is for educational and personal use only.**

- Trading stocks involves substantial risk of loss
- Past performance does not guarantee future results
- Use paper trading extensively before considering live deployment
- Start with small capital if transitioning to live trading
- The authors are not responsible for any financial losses

## 📚 Documentation

- **Memory Bank**: Comprehensive project documentation in `memory-bank/`
- **Implementation Plan**: Detailed roadmap in `implementation_plan.md`
- **API Documentation**: Coming soon

## 🔗 Resources

- [Alpaca API Documentation](https://alpaca.markets/docs/)
- [TensorFlow Keras Guide](https://www.tensorflow.org/guide/keras)
- [TA-Lib Documentation](https://mrjbq7.github.io/ta-lib/)

## 📜 License

MIT License - See LICENSE file for details

## 🏃 Next Steps

1. Complete data pipeline implementation (Phase 2)
2. Build and train LSTM model (Phase 3)
3. Implement trading execution (Phase 5)
4. Create web dashboard (Phase 8)
5. Run 2+ weeks of paper trading validation
6. Consider supervised live deployment

---

**Status**: In Development | **Version**: 0.1.0 | **Last Updated**: November 13, 2025
