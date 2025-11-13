# Implementation Plan: AI Stock Trading Bot

## [Overview]

Create a production-ready AI stock trading bot using machine learning for personal stock trading with Alpaca API integration.

The bot will use LSTM neural networks combined with ensemble methods to predict stock price movements and generate trading signals. It features a hybrid trading mode (automatic + manual approval), comprehensive risk management tailored for a $10,000 portfolio, and a web-based dashboard for monitoring and control. The system will start with paper trading for safe testing before any real money deployment.

Key architectural decisions:

- Python-based for ML ecosystem compatibility
- LSTM for time series prediction with ensemble confirmation
- Alpaca API for commission-free trading and excellent Python support
- Flask web dashboard for real-time monitoring
- SQLite for lightweight data persistence
- Modular design for easy testing and future enhancements

## [Types]

Define all data structures, enums, and type hints for the trading bot.

```python
# src/types/trading_types.py
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

class TradingMode(Enum):
    AUTO = "auto"           # Full automation (confidence > 80%)
    MANUAL = "manual"       # All trades require approval
    HYBRID = "hybrid"       # Auto for high confidence, manual for medium

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class OrderStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PositionStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"

@dataclass
class TradingSignal:
    symbol: str
    signal_type: SignalType
    confidence: float  # 0.0 to 1.0
    predicted_direction: str  # 'up' or 'down'
    timestamp: datetime
    features: dict  # Technical indicators used
    status: OrderStatus = OrderStatus.PENDING

@dataclass
class Position:
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    stop_loss: float
    trailing_stop: Optional[float]
    unrealized_pnl: float
    status: PositionStatus
    entry_time: datetime

@dataclass
class RiskMetrics:
    portfolio_value: float
    cash_available: float
    total_exposure: float
    daily_pnl: float
    daily_pnl_percent: float
    max_position_size: float
    available_positions: int
    stop_loss_triggered: bool

@dataclass
class ModelPrediction:
    symbol: str
    predicted_price: float
    direction: str
    confidence: float
    features_used: List[str]
    timestamp: datetime
```

## [Files]

Create new files and modify existing structure to build the complete trading bot system.

**New Directory Structure:**

```
stock-bot/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── config/
│   └── config.yaml
├── memory-bank/
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── activeContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   └── progress.md
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── types/
│   │   ├── __init__.py
│   │   └── trading_types.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_fetcher.py
│   │   ├── feature_engineer.py
│   │   └── data_validator.py
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── model_trainer.py
│   │   ├── predictor.py
│   │   ├── ensemble.py
│   │   └── backtest.py
│   ├── trading/
│   │   ├── __init__.py
│   │   ├── executor.py
│   │   ├── signal_generator.py
│   │   ├── position_manager.py
│   │   └── order_manager.py
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── risk_calculator.py
│   │   ├── portfolio_monitor.py
│   │   └── stop_loss_manager.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.py
│   │   └── db_manager.py
│   └── dashboard/
│       ├── __init__.py
│       ├── app.py
│       ├── routes.py
│       ├── models.py
│       ├── templates/
│       │   ├── base.html
│       │   ├── index.html
│       │   ├── trades.html
│       │   ├── signals.html
│       │   └── settings.html
│       └── static/
│           ├── css/
│           │   └── style.css
│           └── js/
│               └── dashboard.js
├── models/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
└── tests/
    ├── __init__.py
    ├── test_data_fetcher.py
    ├── test_ml_engine.py
    ├── test_trading.py
    └── test_risk.py
```

**Key Files to Create:**

1. **requirements.txt** - All Python dependencies
2. **.env.example** - Environment variable template
3. **config/config.yaml** - Bot configuration settings
4. **src/main.py** - Main entry point and orchestration
5. **src/data/data_fetcher.py** - Alpaca and Yahoo Finance integration
6. **src/ml/model_trainer.py** - LSTM model training pipeline
7. **src/ml/predictor.py** - Real-time prediction service
8. **src/trading/executor.py** - Order execution via Alpaca API
9. **src/risk/risk_calculator.py** - Position sizing and risk rules
10. **src/dashboard/app.py** - Flask web application
11. **src/database/schema.py** - SQLAlchemy models for all tables
12. **Memory Bank files** - Project documentation per .clinerules

## [Functions]

Define all major functions across the system with signatures and purposes.

### Data Module Functions

**src/data/data_fetcher.py:**

```python
def fetch_historical_data(symbol: str, start_date: str, end_date: str, timeframe: str) -> pd.DataFrame
    """Fetch historical OHLCV data from Alpaca/Yahoo Finance"""

def fetch_realtime_data(symbol: str) -> dict
    """Get current price and volume for a symbol"""

def get_market_calendar() -> pd.DataFrame
    """Get trading days and market hours"""

def stream_market_data(symbols: List[str], callback: callable) -> None
    """Stream real-time price updates"""
```

**src/data/feature_engineer.py:**

```python
def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame
    """Calculate RSI, MACD, Bollinger Bands, etc."""

def create_ml_features(df: pd.DataFrame, lookback_window: int = 60) -> np.ndarray
    """Create feature matrix for ML model"""

def normalize_features(features: np.ndarray) -> np.ndarray
    """Normalize features using StandardScaler"""

def create_sequences(data: np.ndarray, sequence_length: int = 60) -> Tuple[np.ndarray, np.ndarray]
    """Create sequences for LSTM training"""
```

### ML Module Functions

**src/ml/model_trainer.py:**

```python
def build_lstm_model(input_shape: tuple, units: List[int]) -> tf.keras.Model
    """Build LSTM neural network architecture"""

def train_model(X_train: np.ndarray, y_train: np.ndarray, epochs: int = 50) -> tf.keras.Model
    """Train LSTM model with validation"""

def evaluate_model(model: tf.keras.Model, X_test: np.ndarray, y_test: np.ndarray) -> dict
    """Calculate accuracy, precision, recall, F1"""

def save_model(model: tf.keras.Model, path: str) -> None
    """Save trained model to disk"""

def load_model(path: str) -> tf.keras.Model
    """Load pre-trained model"""
```

**src/ml/predictor.py:**

```python
def predict_next_day(symbol: str, model: tf.keras.Model) -> ModelPrediction
    """Generate prediction for next trading day"""

def calculate_confidence(prediction: np.ndarray, historical_accuracy: float) -> float
    """Calculate confidence score for prediction"""

def get_feature_importance() -> dict
    """Return feature importance scores"""
```

**src/ml/ensemble.py:**

```python
def ensemble_predict(lstm_pred: float, rf_pred: float, momentum: float) -> TradingSignal
    """Combine multiple model predictions"""

def calculate_ensemble_confidence(predictions: List[float]) -> float
    """Aggregate confidence from multiple models"""
```

### Trading Module Functions

**src/trading/signal_generator.py:**

```python
def generate_signal(prediction: ModelPrediction, current_position: Optional[Position]) -> TradingSignal
    """Convert ML prediction to trading signal"""

def should_execute_trade(signal: TradingSignal, mode: TradingMode) -> bool
    """Determine if trade should execute based on mode and confidence"""

def calculate_target_quantity(symbol: str, portfolio_value: float, risk_percent: float) -> int
    """Calculate shares to buy based on risk management"""
```

**src/trading/executor.py:**

```python
def place_market_order(symbol: str, qty: int, side: str) -> dict
    """Execute market order via Alpaca"""

def place_limit_order(symbol: str, qty: int, side: str, limit_price: float) -> dict
    """Execute limit order"""

def cancel_order(order_id: str) -> bool
    """Cancel pending order"""

def get_order_status(order_id: str) -> OrderStatus
    """Check order execution status"""
```

**src/trading/position_manager.py:**

```python
def get_open_positions() -> List[Position]
    """Retrieve all open positions from Alpaca"""

def update_position_prices() -> None
    """Update current prices for all positions"""

def close_position(symbol: str) -> bool
    """Close position by selling all shares"""

def calculate_unrealized_pnl(position: Position) -> float
    """Calculate unrealized profit/loss"""
```

### Risk Module Functions

**src/risk/risk_calculator.py:**

```python
def calculate_position_size(account_value: float, risk_percent: float, entry_price: float, stop_price: float) -> int
    """Calculate position size based on risk per trade"""

def check_portfolio_limits(current_exposure: float, max_exposure: float) -> bool
    """Verify portfolio exposure limits"""

def validate_trade(signal: TradingSignal, portfolio: RiskMetrics) -> Tuple[bool, str]
    """Validate if trade meets risk criteria"""
```

**src/risk/stop_loss_manager.py:**

```python
def set_stop_loss(position: Position, stop_percent: float) -> float
    """Calculate and set stop loss price"""

def update_trailing_stop(position: Position, current_price: float) -> Optional[float]
    """Update trailing stop if profit threshold reached"""

def check_stops() -> List[str]
    """Check all positions for stop loss triggers"""

def execute_stop_loss(symbol: str) -> bool
    """Execute stop loss order"""
```

### Database Functions

**src/database/db_manager.py:**

```python
def init_database() -> None
    """Initialize database and create tables"""

def save_trade(trade: dict) -> int
    """Save trade to database"""

def save_prediction(prediction: ModelPrediction) -> int
    """Save ML prediction"""

def get_trade_history(days: int = 30) -> List[dict]
    """Retrieve trade history"""

def calculate_performance_metrics() -> dict
    """Calculate win rate, Sharpe ratio, etc."""

def save_performance_metrics(metrics: dict) -> None
    """Save daily performance metrics"""
```

### Dashboard Functions

**src/dashboard/routes.py:**

```python
@app.route('/')
def dashboard() -> str
    """Main dashboard view"""

@app.route('/api/portfolio')
def get_portfolio() -> dict
    """API: Get current portfolio state"""

@app.route('/api/signals')
def get_pending_signals() -> List[dict]
    """API: Get signals awaiting approval"""

@app.route('/api/signals/<int:signal_id>/approve', methods=['POST'])
def approve_signal(signal_id: int) -> dict
    """API: Approve pending signal"""

@app.route('/api/bot/start', methods=['POST'])
def start_bot() -> dict
    """API: Start trading bot"""

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot() -> dict
    """API: Stop trading bot"""

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings() -> dict
    """API: Get/update bot settings"""
```

## [Classes]

Define all major classes with their methods and responsibilities.

### Core Trading Classes

**src/trading/executor.py:**

```python
class AlpacaExecutor:
    """Handles all order execution via Alpaca API"""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True)
    def connect() -> bool
    def get_account() -> dict
    def get_buying_power() -> float
    def place_order(symbol: str, qty: int, side: str, order_type: str) -> dict
    def get_positions() -> List[dict]
    def close_all_positions() -> bool
```

**src/trading/order_manager.py:**

```python
class OrderManager:
    """Manages order lifecycle and tracking"""

    def __init__(self, executor: AlpacaExecutor, db_manager)
    def submit_order(signal: TradingSignal) -> str
    def track_order(order_id: str) -> OrderStatus
    def cancel_pending_orders() -> int
    def get_active_orders() -> List[dict]
```

### ML Classes

**src/ml/model_trainer.py:**

```python
class LSTMTrainer:
    """Trains and manages LSTM models"""

    def __init__(self, sequence_length: int = 60, features: int = 20)
    def prepare_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]
    def build_model() -> tf.keras.Model
    def train(X_train, y_train, X_val, y_val, epochs: int) -> History
    def evaluate(X_test, y_test) -> dict
    def save(path: str) -> None
    def load(path: str) -> None
```

**src/ml/ensemble.py:**

```python
class EnsemblePredictor:
    """Combines multiple prediction models"""

    def __init__(self, lstm_model, rf_model, weights: List[float])
    def predict(features: np.ndarray) -> ModelPrediction
    def update_weights(performance: dict) -> None
    def get_confidence(predictions: List[float]) -> float
```

### Risk Management Classes

**src/risk/portfolio_monitor.py:**

```python
class PortfolioMonitor:
    """Monitors portfolio health and risk metrics"""

    def __init__(self, initial_capital: float = 10000)
    def update_state() -> None
    def get_risk_metrics() -> RiskMetrics
    def check_daily_limit() -> bool
    def check_position_limits() -> bool
    def calculate_sharpe_ratio(returns: pd.Series) -> float
```

**src/risk/risk_calculator.py:**

```python
class RiskCalculator:
    """Calculates position sizes and risk parameters"""

    def __init__(self, max_risk_per_trade: float = 0.02, max_portfolio_risk: float = 0.20)
    def calculate_position_size(price: float, stop_loss: float) -> int
    def validate_trade(signal: TradingSignal, portfolio: RiskMetrics) -> Tuple[bool, str]
    def calculate_stop_loss(entry_price: float, direction: str) -> float
```

### Dashboard Classes

**src/dashboard/models.py:**

```python
class Trade(db.Model):
    """SQLAlchemy model for trades table"""
    id, symbol, action, quantity, price, timestamp, status, pnl, confidence_score

class Position(db.Model):
    """SQLAlchemy model for positions table"""
    id, symbol, quantity, entry_price, current_price, unrealized_pnl, stop_loss

class Prediction(db.Model):
    """SQLAlchemy model for predictions table"""
    id, symbol, predicted_direction, confidence, actual_outcome, timestamp

class Signal(db.Model):
    """SQLAlchemy model for signals table"""
    id, symbol, action, confidence, status, created_at, approved_at
```

### Main Application Class

**src/main.py:**

```python
class TradingBot:
    """Main orchestrator for the trading bot"""

    def __init__(self, config: dict)
    def initialize() -> bool
    def start() -> None
    def stop() -> None
    def run_trading_cycle() -> None
    def process_signal(signal: TradingSignal) -> None
    def update_positions() -> None
    def check_risk_limits() -> bool
    def handle_market_close() -> None
```

## [Dependencies]

All required Python packages and their purposes.

**requirements.txt:**

```txt
# Trading & Market Data
alpaca-trade-api==3.0.2          # Alpaca broker integration
yfinance==0.2.32                  # Yahoo Finance historical data

# Machine Learning
tensorflow==2.14.0                # LSTM neural networks
scikit-learn==1.3.2               # Preprocessing, ensemble methods
pandas==2.1.3                     # Data manipulation
numpy==1.26.2                     # Numerical computing
ta-lib-python==0.4.28             # Technical indicators (requires TA-Lib C library)

# Web Dashboard
Flask==3.0.0                      # Web framework
Flask-SQLAlchemy==3.1.1           # Database ORM
Flask-Cors==4.0.0                 # CORS support

# Infrastructure
SQLAlchemy==2.0.23                # Database toolkit
APScheduler==3.10.4               # Task scheduling
python-dotenv==1.0.0              # Environment management
loguru==0.7.2                     # Advanced logging
pydantic==2.5.2                   # Data validation

# Utilities
requests==2.31.0                  # HTTP requests
python-dateutil==2.8.2            # Date utilities
pytz==2023.3                      # Timezone handling

# Testing
pytest==7.4.3                     # Testing framework
pytest-cov==4.1.0                 # Coverage reports
```

**System Requirements:**

- Python 3.10 or higher
- TA-Lib C library: `sudo apt-get install ta-lib` (Linux) or `brew install ta-lib` (macOS)
- 4GB RAM minimum (8GB recommended for model training)
- 10GB disk space

## [Testing]

Comprehensive testing strategy for all components.

**Test Files Structure:**

**tests/test_data_fetcher.py:**

```python
def test_fetch_historical_data()
def test_fetch_realtime_data()
def test_feature_engineering()
def test_data_validation()
def test_handle_missing_data()
```

**tests/test_ml_engine.py:**

```python
def test_model_building()
def test_model_training()
def test_model_prediction()
def test_ensemble_prediction()
def test_model_save_load()
def test_prediction_confidence()
```

**tests/test_trading.py:**

```python
def test_signal_generation()
def test_order_placement()
def test_position_management()
def test_order_cancellation()
def test_alpaca_connection()
```

**tests/test_risk.py:**

```python
def test_position_sizing()
def test_stop_loss_calculation()
def test_portfolio_limits()
def test_daily_drawdown_limit()
def test_risk_validation()
```

**Testing Strategy:**

1. Unit tests for all functions with >80% coverage
2. Integration tests for API connections
3. Mock Alpaca API responses for testing without live connection
4. Backtesting on historical data (2020-2023)
5. Paper trading for 2 weeks minimum before live deployment
6. Performance benchmarks (accuracy, latency, Sharpe ratio)

**Test Data:**

- Use PLTR historical data for consistent testing
- Generate synthetic edge cases (gaps, splits, extreme volatility)
- Test with various market conditions (bull, bear, sideways)

## [Implementation Order]

Step-by-step implementation sequence to minimize conflicts and ensure working increments.

### Phase 1: Project Setup (Days 1-2)

1. Create directory structure and initialize git repository
2. Set up virtual environment and install dependencies
3. Create Memory Bank files (projectbrief.md, productContext.md, etc.)
4. Create configuration files (.env.example, config.yaml)
5. Set up .gitignore for Python project
6. Initialize SQLite database schema
7. Verify Alpaca API connection with test script

### Phase 2: Data Pipeline (Days 3-4)

8. Implement data_fetcher.py with Alpaca and yfinance integration
9. Build feature_engineer.py with technical indicators
10. Create data_validator.py for data quality checks
11. Test data fetching for PLTR and multiple symbols
12. Implement data caching to avoid redundant API calls
13. Create unit tests for data module

### Phase 3: ML Engine (Days 5-7)

14. Implement LSTM model architecture in model_trainer.py
15. Build training pipeline with train/validation split
16. Implement predictor.py for real-time predictions
17. Create ensemble.py combining LSTM + Random Forest
18. Build backtest.py for historical validation
19. Train initial model on 2 years of PLTR data
20. Evaluate model performance (accuracy, precision, recall)
21. Create unit tests for ML module

### Phase 4: Risk Management (Days 8-9)

22. Implement risk_calculator.py with position sizing
23. Build portfolio_monitor.py for risk metrics tracking
24. Create stop_loss_manager.py with trailing stops
25. Implement all risk validation rules
26. Test risk calculations with edge cases
27. Create unit tests for risk module

### Phase 5: Trading Engine (Days 10-11)

28. Implement executor.py with Alpaca integration
29. Build signal_generator.py to convert predictions to signals
30. Create position_manager.py for position tracking
31. Implement order_manager.py for order lifecycle
32. Test order placement in paper trading account
33. Verify position tracking and P&L calculation
34. Create integration tests for trading module

### Phase 6: Database Layer (Day 12)

35. Implement SQLAlchemy models in schema.py
36. Build db_manager.py with CRUD operations
37. Create database migration scripts
38. Test database operations
39. Implement performance metrics calculation
40. Add database indices for query optimization

### Phase 7: Main Application (Day 13)

41. Implement main.py with TradingBot orchestrator
42. Connect all modules (data → ML → trading → risk)
43. Implement trading cycle loop
44. Add signal processing workflow
45. Implement mode switching (auto/manual/hybrid)
46. Add comprehensive logging with loguru
47. Create configuration loading and validation

### Phase 8: Web Dashboard (Days 14-15)

48. Set up Flask application structure
49. Create database models for dashboard
50. Implement API routes for portfolio, signals, trades
51. Build HTML templates with Bootstrap
52. Create JavaScript for real-time updates
53. Implement signal approval interface
54. Add bot start/stop controls
55. Create settings management page
56. Test dashboard with sample data

### Phase 9: Integration & Testing (Days 16-17)

57. Run end-to-end integration tests
58. Test with paper trading account (live mode)
59. Monitor bot behavior for 48 hours
60. Fix any bugs or issues discovered
61. Optimize performance (API calls, database queries)
62. Add error handling and recovery mechanisms
63. Create operational runbooks

### Phase 10: Documentation & Deployment (Day 18)

64. Write comprehensive README.md
65. Document API endpoints and configuration
66. Create user guide for dashboard
67. Document trading strategy and risk parameters
68. Set up logging and monitoring
69. Create backup and recovery procedures
70. Perform final security review
71. Deploy to production environment (still paper trading)
72. Update Memory Bank with final state

**Critical Path:**

- Data Pipeline → ML Engine → Trading Engine → Integration
- Risk Management can be developed in parallel with ML Engine
- Dashboard can be developed in parallel with Trading Engine
- Testing should occur throughout, not just at the end

**Validation Checkpoints:**

- After Phase 2: Verify data quality and feature engineering
- After Phase 3: Confirm model accuracy >60% on validation set
- After Phase 5: Successful paper trades with proper risk management
- After Phase 8: Dashboard displays real-time data correctly
- After Phase 9: Bot runs autonomously for 2 weeks without crashes

**Risk Mitigation:**

- Use paper trading exclusively for first month
- Start with single symbol (PLTR) before expanding
- Implement kill switch for immediate bot shutdown
- Set conservative risk limits (2% per trade, 5% daily max)
- Monitor bot performance daily during initial deployment
- Keep manual override always available
