# Technical Context: AI Stock Trading Bot

## Technology Stack

### Core Technologies

**Programming Language**

- **Python 3.10+**
  - Type hints for better code quality
  - Structural pattern matching (match/case)
  - Better error messages
  - Performance improvements over 3.9

**Machine Learning**

- **TensorFlow 2.14.0**: LSTM neural network implementation
- **Keras**: High-level neural network API (included in TensorFlow)
- **scikit-learn 1.3.2**: Preprocessing, Random Forest, ensemble methods
- **pandas 2.1.3**: Data manipulation and time series handling
- **numpy 1.26.2**: Numerical computing and array operations

**Trading & Market Data**

- **alpaca-trade-api 3.0.2**: Alpaca broker integration
  - Paper trading (default)
  - Live trading (optional)
  - Real-time market data
  - Order management
- **yfinance 0.2.32**: Yahoo Finance data (backup/historical)

**Technical Analysis**

- **TA-Lib (Python wrapper 0.4.28)**: Technical indicators
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Moving Averages (SMA, EMA)
  - Volume indicators

**Web Framework**

- **Flask 3.0.0**: Lightweight web framework
- **Flask-SQLAlchemy 3.1.1**: Database ORM
- **Flask-Cors 4.0.0**: Cross-origin resource sharing

**Database**

- **SQLite 3**: Embedded database (via Python standard library)
- **SQLAlchemy 2.0.23**: Database toolkit and ORM

**Infrastructure**

- **APScheduler 3.10.4**: Task scheduling (trading cycle, monitoring)
- **python-dotenv 1.0.0**: Environment variable management
- **loguru 0.7.2**: Advanced logging with rotation and formatting
- **pydantic 2.5.2**: Data validation and settings management

**Utilities**

- **requests 2.31.0**: HTTP requests for APIs
- **python-dateutil 2.8.2**: Date/time utilities
- **pytz 2023.3**: Timezone handling (market hours)

**Testing**

- **pytest 7.4.3**: Testing framework
- **pytest-cov 4.1.0**: Code coverage reports

### Development Tools

**Version Control**

- **Git**: Source control
- **.gitignore**: Exclude venv, .env, **pycache**, logs, models, \*.db

**Code Quality**

- **Type hints**: Python 3.10+ type annotations throughout
- **Docstrings**: Google-style docstrings for all functions/classes
- **Black (optional)**: Code formatting
- **Pylint (optional)**: Code linting

**IDE**

- **Visual Studio Code** (recommended)
  - Python extension
  - Pylance (type checking)
  - Debugger configured
- **PyCharm** (alternative)

### Documentation Access

**Context7 MCP Server** - Real-time library documentation access

- **Purpose**: Fetch up-to-date documentation for any Python library used in the project
- **Availability**: Integrated via MCP (Model Context Protocol)
- **Use Cases**:
  - Verify TensorFlow/Keras API usage before implementation
  - Check current best practices for pandas operations
  - Validate Alpaca API endpoints and parameters
  - Reference scikit-learn preprocessing methods
  - Confirm Flask route patterns and decorators
  - Look up SQLAlchemy ORM patterns
  - Review loguru logging configuration

**Usage Pattern**:

1. **Resolve library identifier**: Use `resolve-library-id` to find the correct library
   - Example: Search for "tensorflow" returns `/tensorflow/tensorflow`
2. **Fetch documentation**: Use `get-library-docs` with the library ID and optional topic
   - Example: Get LSTM docs from TensorFlow
3. **Apply to implementation**: Use retrieved docs to ensure correct API usage

**Key Libraries Available**:

- **TensorFlow** (latest) - LSTM implementation, Keras API, model training
- **pandas** (latest) - DataFrame operations, time series manipulation
- **alpaca-trade-api** (latest) - order execution, market data, account management
- **scikit-learn** (latest) - preprocessing, ensemble methods, model evaluation
- **Flask** (latest) - routing, templates, request handling
- **SQLAlchemy** (latest) - ORM patterns, query building
- **loguru** (latest) - logging configuration, formatters
- **numpy** (latest) - array operations, numerical computing
- **TA-Lib** (latest) - technical indicators, financial functions

**When to Use Context7**:

- Before implementing new features with unfamiliar APIs
- When encountering deprecation warnings
- To verify parameter names and types
- When troubleshooting library-specific errors
- To check for new features or best practices
- During code review to ensure modern patterns

**Note**: Context7 provides current documentation, which is especially valuable for rapidly evolving libraries like TensorFlow and for ensuring the bot uses the most up-to-date API patterns.

## Development Setup

### Prerequisites

**Operating System**

- Linux (Ubuntu 20.04+, Debian, Fedora)
- macOS 12+
- Windows 10/11 (WSL2 recommended for TA-Lib)

**System Requirements**

- **CPU**: Multi-core processor (4+ cores recommended for ML training)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space (models, data, logs)
- **Internet**: Stable connection for API access

**Software Dependencies**

1. **Python 3.10 or higher**

   ```bash
   # Check version
   python --version  # Should show 3.10.x or higher
   ```

2. **TA-Lib C Library** (required before Python package)

   **Linux (Ubuntu/Debian):**

   ```bash
   sudo apt-get update
   sudo apt-get install ta-lib
   ```

   **macOS:**

   ```bash
   brew install ta-lib
   ```

   **Windows (via WSL2):**

   ```bash
   # In WSL2 Ubuntu terminal
   sudo apt-get install ta-lib
   ```

3. **pip** (Python package manager, usually comes with Python)

### Installation Steps

**1. Clone Repository**

```bash
git clone <repository-url>
cd stock-bot
```

**2. Create Virtual Environment**

```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

**3. Install Python Dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Configure Environment Variables**

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
nano .env  # or vim, code, etc.
```

**.env file structure:**

```bash
# Alpaca API Credentials (Paper Trading - Default)
ALPACA_API_KEY=your_paper_api_key_here
ALPACA_SECRET_KEY=your_paper_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_IS_PAPER=true

# Alpaca API Credentials (Live Trading - Optional)
# ALPACA_LIVE_API_KEY=your_live_api_key_here
# ALPACA_LIVE_SECRET_KEY=your_live_secret_key_here
# ALPACA_LIVE_BASE_URL=https://api.alpaca.markets

# Database
DATABASE_URL=sqlite:///trading_bot.db

# Trading Configuration
TRADING_MODE=hybrid  # auto, manual, or hybrid
INITIAL_CAPITAL=10000
MAX_POSITION_SIZE=0.2  # 20% of portfolio
MAX_POSITIONS=5
RISK_PER_TRADE=0.02  # 2%
DAILY_LOSS_LIMIT=0.05  # 5%

# ML Configuration
MODEL_PATH=models/lstm_model.h5
PREDICTION_CONFIDENCE_THRESHOLD=0.70
AUTO_EXECUTE_THRESHOLD=0.80

# Dashboard
FLASK_SECRET_KEY=your_random_secret_key_here
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

**5. Initialize Database**

```bash
python src/database/schema.py
```

**6. Verify Installation**

```bash
# Test Alpaca connection
python -c "from src.trading.executor import AlpacaExecutor; print('Success')"

# Test TA-Lib
python -c "import talib; print('TA-Lib OK')"

# Test TensorFlow
python -c "import tensorflow as tf; print(f'TensorFlow {tf.__version__}')"
```

### Running the Bot

**Start Main Bot**

```bash
# From project root
python src/main.py
```

**Start Dashboard (separate terminal)**

```bash
# Activate venv first
source venv/bin/activate

# Start Flask
python src/dashboard/app.py
```

**Access Dashboard**

```
http://localhost:5000
```

### Development Workflow

**1. Make Code Changes**

```bash
# Edit files in src/
code src/ml/predictor.py
```

**2. Run Tests**

```bash
# All tests
pytest

# Specific module
pytest tests/test_ml_engine.py

# With coverage
pytest --cov=src tests/
```

**3. Check for Issues**

```bash
# Type checking (if using mypy)
mypy src/

# Linting (if using pylint)
pylint src/
```

**4. Commit Changes**

```bash
git add .
git commit -m "feat: add ensemble prediction"
git push origin main
```

## Technical Constraints

### API Rate Limits

**Alpaca Markets**

- **Market Data**: 200 requests/minute
- **Trading API**: 200 requests/minute
- **WebSocket**: Real-time data, no request limits

**Strategy**: Cache data locally, batch requests, use WebSocket for real-time

**Yahoo Finance (yfinance)**

- **Unofficial API**: No official rate limits documented
- **Best Practice**: 1 request per 2 seconds, respect 429 errors
- **Use Case**: Historical data backup only

### Market Hours

**US Stock Market** (Eastern Time)

- **Pre-Market**: 4:00 AM - 9:30 AM ET (limited functionality)
- **Regular Hours**: 9:30 AM - 4:00 PM ET (main trading)
- **After-Hours**: 4:00 PM - 8:00 PM ET (limited functionality)

**Bot Operation**:

- **Active Trading**: Regular hours only (9:30 AM - 4:00 PM ET)
- **Data Collection**: Can run pre-market for preparation
- **Position Monitoring**: Active during regular hours
- **Model Training**: Can run anytime (offline)

### Pattern Day Trading Rules

**PDT Regulation** (US)

- **Definition**: 4+ day trades in 5 business days
- **Requirement**: $25,000 minimum account balance
- **Workaround**: Limit to 3 day trades per week OR hold overnight

**Bot Strategy**: Initially close all positions by end of day (no PDT issue)

### Data Storage

**SQLite Limits**

- **Max Database Size**: 281 TB (effectively unlimited for our use)
- **Max Row Size**: 1 GB (far exceeds our needs)
- **Concurrent Writers**: 1 (sufficient for single-user bot)
- **Concurrent Readers**: Unlimited

**Expected Data Volume**:

- **Trades**: ~10/day × 365 days = 3,650/year (~1MB)
- **Predictions**: ~50/day × 365 days = 18,250/year (~5MB)
- **Price Data**: 1 year OHLCV for PLTR (~50KB)
- **Total**: <10MB/year (SQLite easily handles this)

### Model Training Constraints

**LSTM Training Time**

- **Dataset**: 2 years of daily data (~500 samples)
- **Training Time**: 10-30 minutes (depending on hardware)
- **GPU**: Optional, speeds up 5-10x (not required)
- **Memory**: 2-4GB during training

**Inference Time**

- **Single Prediction**: <5 seconds (including feature calculation)
- **Batch Predictions**: Linear scaling, 10 predictions ~30 seconds

**Model File Size**

- **LSTM Model**: ~2-5MB
- **Random Forest**: ~1-2MB
- **Total Models**: <10MB

## Python Package Details

### Critical Dependencies

**TensorFlow 2.14.0**

- **Purpose**: LSTM neural network training and inference
- **GPU Support**: Optional (CUDA 11.8, cuDNN 8.6)
- **Alternatives**: PyTorch (not chosen due to Keras simplicity)

**Installation Issues**:

- M1/M2 Macs: Use `tensorflow-macos` instead
- Windows: May require Visual C++ redistributable

**scikit-learn 1.3.2**

- **Purpose**: Random Forest, preprocessing (StandardScaler), metrics
- **Thread Safety**: Yes (important for concurrent predictions)
- **Alternatives**: None, industry standard

**pandas 2.1.3**

- **Purpose**: Time series data manipulation, DataFrame operations
- **Performance**: Fast for <100K rows (our typical size: <1K)
- **Compatibility**: Works with TensorFlow, numpy, matplotlib

**alpaca-trade-api 3.0.2**

- **Purpose**: Broker integration, order execution
- **Documentation**: https://alpaca.markets/docs/python-sdk/
- **Authentication**: API key + secret (stored in .env)
- **Paper Trading**: Separate endpoint, realistic simulation

**TA-Lib (Python wrapper 0.4.28)**

- **Purpose**: Technical analysis indicators
- **C Dependency**: Requires TA-Lib C library installed first
- **Alternatives**: pandas-ta (pure Python, slower, less features)

**Common Installation Issues**:

```bash
# If TA-Lib fails to install
# 1. Ensure C library installed first (see Development Setup)
# 2. Try installing from source
pip install --no-binary :all: TA-Lib

# 3. Or use pandas-ta as alternative (add to requirements.txt)
pip install pandas-ta
```

### Optional Enhancements

**Development Tools (not in requirements.txt)**

```bash
# Code formatting
pip install black

# Linting
pip install pylint

# Type checking
pip install mypy

# Jupyter notebooks (for model experimentation)
pip install jupyter notebook matplotlib
```

**Monitoring Tools**

```bash
# System monitoring
pip install psutil  # CPU, memory usage

# API monitoring
pip install requests-cache  # Cache API responses for testing
```

## Configuration Management

### Config File Structure

**config/config.yaml**

```yaml
trading:
  mode: hybrid # auto, manual, hybrid
  symbols:
    - PLTR
  initial_capital: 10000
  max_positions: 5
  close_positions_eod: true # Close at end of day

risk:
  risk_per_trade: 0.02 # 2% of portfolio
  max_position_size: 0.20 # 20% of portfolio
  max_portfolio_exposure: 0.20 # 20% total
  daily_loss_limit: 0.05 # 5% circuit breaker
  stop_loss_percent: 0.03 # 3% stop loss
  trailing_stop_percent: 0.02 # 2% trailing stop
  trailing_stop_activation: 0.05 # Activate at 5% profit

ml:
  model_path: models/lstm_model.h5
  sequence_length: 60 # Days of history for LSTM
  prediction_confidence_threshold: 0.70
  auto_execute_threshold: 0.80
  retrain_frequency: monthly # daily, weekly, monthly

features:
  technical_indicators:
    - RSI
    - MACD
    - BB # Bollinger Bands
    - SMA_20
    - SMA_50
    - EMA_12
    - EMA_26
    - Volume
  lookback_window: 60 # Days

database:
  path: trading_bot.db
  backup_frequency: daily
  backup_retention_days: 30

logging:
  level: INFO # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_dir: logs/
  rotation: 1 day
  retention: 30 days

dashboard:
  host: 127.0.0.1
  port: 5000
  auto_open_browser: true
  refresh_interval: 30 # seconds
```

### Loading Configuration

```python
# src/config.py
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

# Usage
from src.config import load_config
config = load_config()
risk_per_trade = config['risk']['risk_per_trade']
```

## Tool Usage Patterns

### Logging

**Setup** (src/main.py):

```python
from loguru import logger
import sys

# Remove default handler
logger.remove()

# Console output (during development)
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# File output (production)
logger.add(
    "logs/trading_bot_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
)

# Error log
logger.add(
    "logs/errors.log",
    level="ERROR",
    rotation="10 MB",
    backtrace=True,
    diagnose=True
)
```

**Usage**:

```python
from loguru import logger

logger.info("Bot started successfully")
logger.warning(f"Low confidence signal: {confidence:.2f}")
logger.error(f"Failed to fetch data: {error}")
logger.critical("Daily loss limit exceeded - STOPPING BOT")
```

### Environment Variables

**Loading** (src/main.py):

```python
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Access variables
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
TRADING_MODE = os.getenv('TRADING_MODE', 'hybrid')  # Default value
```

### Database Operations

**Connection** (src/database/db_manager.py):

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create engine
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Use session
session = Session()
try:
    # Perform database operations
    trade = Trade(symbol='PLTR', action='BUY', ...)
    session.add(trade)
    session.commit()
except Exception as e:
    session.rollback()
    logger.error(f"Database error: {e}")
finally:
    session.close()
```

### API Requests (Alpaca)

**Setup** (src/trading/executor.py):

```python
import alpaca_trade_api as tradeapi

# Initialize API
api = tradeapi.REST(
    key_id=ALPACA_API_KEY,
    secret_key=ALPACA_SECRET_KEY,
    base_url=ALPACA_BASE_URL,
    api_version='v2'
)

# Get account info
account = api.get_account()
buying_power = float(account.buying_power)

# Place order with error handling
try:
    order = api.submit_order(
        symbol='PLTR',
        qty=10,
        side='buy',
        type='market',
        time_in_force='day'
    )
    logger.info(f"Order placed: {order.id}")
except Exception as e:
    logger.error(f"Order failed: {e}")
```

### Scheduling Tasks

**Setup** (src/main.py):

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Run trading cycle every 5 minutes during market hours
scheduler.add_job(
    func=run_trading_cycle,
    trigger='cron',
    day_of_week='mon-fri',
    hour='9-16',
    minute='*/5',
    timezone='America/New_York'
)

# Update positions every 30 seconds
scheduler.add_job(
    func=update_positions,
    trigger='interval',
    seconds=30
)

# Start scheduler
scheduler.start()
```

## Troubleshooting

### Common Issues

**1. TA-Lib Installation Fails**

```bash
# Error: "command 'gcc' failed" or "ta-lib not found"

# Solution (Linux/WSL):
sudo apt-get install build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install TA-Lib

# Solution (macOS):
brew install ta-lib
pip install TA-Lib
```

**2. TensorFlow Import Error**

```bash
# Error: "No module named 'tensorflow'" after installation

# Solution: Verify Python version
python --version  # Must be 3.8-3.11

# Reinstall in venv
pip uninstall tensorflow
pip install tensorflow==2.14.0
```

**3. Alpaca API Connection Fails**

```python
# Error: "Unauthorized" or "Invalid API key"

# Check .env file
cat .env | grep ALPACA

# Verify API keys on Alpaca website
# Ensure using correct keys (paper vs live)
# Check base_url matches key type
```

**4. Database Locked Error**

```bash
# Error: "database is locked"

# Solution: Close other connections
# Ensure only one bot instance running
pkill -f "python src/main.py"

# Or delete lock file (safe if bot not running)
rm trading_bot.db-journal
```

**5. Port Already in Use (Dashboard)**

```bash
# Error: "Address already in use"

# Find process using port 5000
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Kill process
kill -9 <PID>

# Or use different port
FLASK_PORT=5001 python src/dashboard/app.py
```

### Performance Optimization

**1. Speed Up Model Training**

```python
# Use GPU if available
import tensorflow as tf
print(tf.config.list_physical_devices('GPU'))

# Reduce model complexity
# Fewer LSTM units or layers
# Smaller batch size for faster iteration
```

**2. Reduce API Calls**

```python
# Cache market data locally
from functools import lru_cache

@lru_cache(maxsize=100)
def fetch_price_cached(symbol: str, timestamp: int):
    # Round timestamp to nearest minute
    return fetch_price(symbol)
```

**3. Optimize Database Queries**

```sql
-- Add indices
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_predictions_timestamp ON predictions(timestamp);
```

## Future Technical Enhancements

### Planned Improvements

1. **PostgreSQL Migration** (if needed for multi-user)
2. **Redis Caching** (for high-frequency trading)
3. **Docker Containerization** (easier deployment)
4. **Grafana Dashboard** (advanced metrics)
5. **Prometheus Monitoring** (system health)
6. **CI/CD Pipeline** (automated testing/deployment)
7. **GPU Support** (faster model training)
8. **WebSocket Real-time Updates** (dashboard)

### Technology Upgrade Path

**Phase 1**: Core system working (current)
**Phase 2**: Add monitoring and alerting
**Phase 3**: Containerize with Docker
**Phase 4**: Add advanced ML models (Transformer, etc.)
**Phase 5**: Scale to multiple strategies/symbols
