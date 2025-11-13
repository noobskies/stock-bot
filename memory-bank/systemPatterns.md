# System Patterns: AI Stock Trading Bot

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Trading Bot System                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐│
│  │   Web UI     │    │  Main Bot    │    │  External    ││
│  │  Dashboard   │◄───┤ Orchestrator │◄───┤   APIs       ││
│  │  (Flask)     │    │   (main.py)  │    │ (Alpaca/YF)  ││
│  └──────────────┘    └──────────────┘    └──────────────┘│
│         │                    │                             │
│         │                    │                             │
│  ┌──────▼────────────────────▼─────────────────────────┐  │
│  │              Database Layer (SQLite)                │  │
│  │  - Trades  - Predictions  - Signals  - Positions   │  │
│  └────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │              Core Processing Pipeline             │    │
│  ├───────────────────────────────────────────────────┤    │
│  │                                                   │    │
│  │  Data → Feature → ML Model → Signal → Risk       │    │
│  │  Fetch   Engine     LSTM     Gen     Check       │    │
│  │   ↓       ↓          ↓        ↓        ↓        │    │
│  │  [Data] [Feature] [Predict] [Signal] [Validate] │    │
│  │  Module   Module    Module   Module   Module     │    │
│  │                                                   │    │
│  └───────────────────────────────────────────────────┘    │
│                          │                                 │
│  ┌──────────────────────▼────────────────────────────┐    │
│  │           Trading Execution Layer                 │    │
│  ├───────────────────────────────────────────────────┤    │
│  │                                                   │    │
│  │  Order      Position     Stop Loss    Risk       │    │
│  │  Manager    Manager      Manager      Monitor    │    │
│  │                                                   │    │
│  └───────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Modular Component Design

The system follows a **modular architecture** with clear separation of concerns:

1. **Data Module** (`src/data/`)

   - Responsibility: Fetch and prepare market data
   - Independence: Can be tested/replaced without affecting ML or trading
   - Interface: Returns standardized pandas DataFrames

2. **ML Module** (`src/ml/`)

   - Responsibility: Train models and generate predictions
   - Independence: Isolated from trading logic and data fetching
   - Interface: Returns ModelPrediction dataclass

3. **Trading Module** (`src/trading/`)

   - Responsibility: Execute trades and manage orders
   - Independence: Works with any signal source, not tied to ML
   - Interface: Accepts TradingSignal, returns execution status

4. **Risk Module** (`src/risk/`)

   - Responsibility: Validate trades and monitor portfolio
   - Independence: Pure calculation logic, no external dependencies
   - Interface: Boolean validation with reason strings

5. **Database Module** (`src/database/`)

   - Responsibility: Persist all system data
   - Independence: Abstraction layer over SQLite
   - Interface: CRUD operations via db_manager

6. **Dashboard Module** (`src/dashboard/`)
   - Responsibility: Web UI for monitoring and control
   - Independence: Read-only view of system state
   - Interface: REST API + HTML templates

## Key Technical Decisions

### 1. Python as Primary Language

**Decision**: Use Python 3.10+ for entire system

**Rationale**:

- Best ML ecosystem (TensorFlow, scikit-learn, pandas)
- Excellent Alpaca SDK support
- Rich data processing libraries
- Fast development for solo project
- Strong typing with Python 3.10+ type hints

**Trade-offs**:

- ✅ Faster development, proven libraries
- ❌ Slower execution than compiled languages (acceptable for our use case)

### 2. LSTM Neural Networks for Predictions

**Decision**: Use LSTM as primary prediction model

**Rationale**:

- Time series data naturally fits sequential models
- LSTM handles long-term dependencies (market trends)
- Proven track record in financial prediction
- TensorFlow/Keras makes implementation straightforward

**Architecture**:

```python
LSTM(64 units) → Dropout(0.2) → LSTM(32 units) → Dropout(0.2) → Dense(1, sigmoid)
```

**Trade-offs**:

- ✅ Captures temporal patterns, handles sequences well
- ❌ Requires significant training data (2+ years)
- ❌ Slower inference than simple models (5 seconds acceptable)

### 3. Ensemble Approach for Confidence

**Decision**: Combine LSTM + Random Forest + Momentum for signal confidence

**Rationale**:

- Single model can overfit or miss patterns
- Ensemble reduces false positives
- Different models capture different patterns
- Confidence score more reliable when models agree

**Implementation**:

```python
final_confidence = (lstm_conf * 0.5) + (rf_conf * 0.3) + (momentum_conf * 0.2)
execute_if confidence > 0.70 (manual) or > 0.80 (auto)
```

**Trade-offs**:

- ✅ More robust predictions, fewer bad trades
- ❌ More complex to maintain and train

### 4. Alpaca API for Brokerage

**Decision**: Use Alpaca Markets as exclusive broker

**Rationale**:

- Commission-free trading (critical for small accounts)
- Excellent Python SDK
- Free paper trading account (perfect for testing)
- RESTful API easy to work with
- Real-time market data included

**Alternatives Rejected**:

- Interactive Brokers: Complex API, high minimum
- TD Ameritrade: Being acquired, uncertain future
- Robinhood: Poor API, limited features

**Trade-offs**:

- ✅ Free, excellent SDK, paper trading
- ❌ US stocks only, no options trading
- ❌ Pattern day trading rules still apply

### 5. SQLite for Database

**Decision**: Use SQLite instead of PostgreSQL/MySQL

**Rationale**:

- Personal project with single user
- No concurrent write requirements
- Zero configuration/maintenance
- File-based portability
- Sufficient performance (<1000 trades/year)

**Trade-offs**:

- ✅ Simple, portable, zero maintenance
- ❌ Cannot scale to multi-user (not needed)
- ❌ Limited concurrent writes (not an issue)

### 6. Flask for Web Dashboard

**Decision**: Use Flask instead of Django/FastAPI

**Rationale**:

- Lightweight, minimal boilerplate
- Proven for small applications
- Easy to integrate with existing Python code
- Template system sufficient for UI needs
- Large community and documentation

**Trade-offs**:

- ✅ Simple, fast to develop, lightweight
- ❌ Fewer built-in features than Django (we don't need them)

### 7. Hybrid Trading Mode as Default

**Decision**: Default to Hybrid mode (auto >80% confidence, manual otherwise)

**Rationale**:

- Balances automation with human oversight
- User learns to trust bot gradually
- Prevents autopilot during uncertain conditions
- Easy to switch to full auto after confidence builds

**Mode Comparison**:

- Auto: Fast, hands-off, but risky if model fails
- Manual: Safe, slow, defeats automation purpose
- **Hybrid**: Best of both worlds for personal trading

### 8. Single Stock Focus (PLTR)

**Decision**: Start with single stock before expanding

**Rationale**:

- Simpler to debug and optimize
- Concentrated learning (model specialization)
- Easier risk management
- Can expand later after proven success

**Expansion Path**:

- Phase 1: PLTR only (tech growth stock)
- Phase 2: Add 2-3 similar stocks (tech sector)
- Phase 3: Expand to 5-10 stocks across sectors

**Trade-offs**:

- ✅ Focused development, easier debugging
- ❌ Less diversification (acceptable with strict risk limits)

### 9. No Overnight Positions (Initially)

**Decision**: Close all positions by market close

**Rationale**:

- Eliminates gap risk (news after hours)
- Simpler position management
- Daily reset for clean slate
- Reduces stress for user

**Future Enhancement**:

- Add "hold_overnight" flag per position
- Implement pre-market monitoring
- Add after-hours trading support

**Trade-offs**:

- ✅ Safer, simpler, no overnight worry
- ❌ Misses gap-up profits (worth it for safety)

### 10. Paper Trading First (Mandatory)

**Decision**: Require 2+ weeks paper trading before live

**Rationale**:

- Proves bot stability and reliability
- Validates risk management in real conditions
- Builds user confidence
- Identifies bugs without financial loss

**Trade-offs**:

- ✅ Safe, proven approach
- ❌ Delayed gratification (worth the wait)

## Design Patterns

### 1. Singleton Pattern - Trading Bot Instance

**Use Case**: Ensure only one bot instance runs at a time

```python
class TradingBot:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def start(self):
        if self.is_running:
            raise RuntimeError("Bot already running")
        self.is_running = True
```

**Why**: Prevents multiple bots from conflicting orders and state corruption

### 2. Strategy Pattern - Trading Modes

**Use Case**: Different execution strategies (auto/manual/hybrid)

```python
class ExecutionStrategy(ABC):
    @abstractmethod
    def should_execute(self, signal: TradingSignal) -> bool:
        pass

class AutoStrategy(ExecutionStrategy):
    def should_execute(self, signal: TradingSignal) -> bool:
        return signal.confidence > 0.80

class ManualStrategy(ExecutionStrategy):
    def should_execute(self, signal: TradingSignal) -> bool:
        return False  # Always require approval

class HybridStrategy(ExecutionStrategy):
    def should_execute(self, signal: TradingSignal) -> bool:
        return signal.confidence > 0.80  # Auto if high confidence
```

**Why**: Easy to add new trading modes without changing core logic

### 3. Observer Pattern - Position Monitoring

**Use Case**: Notify multiple components when positions change

```python
class PositionObserver(ABC):
    @abstractmethod
    def on_position_update(self, position: Position):
        pass

class StopLossManager(PositionObserver):
    def on_position_update(self, position: Position):
        if position.current_price <= position.stop_loss:
            self.execute_stop(position)

class DashboardUpdater(PositionObserver):
    def on_position_update(self, position: Position):
        self.update_ui(position)
```

**Why**: Decouples position tracking from reaction logic

### 4. Factory Pattern - Model Creation

**Use Case**: Create different ML models based on configuration

```python
class ModelFactory:
    @staticmethod
    def create_model(model_type: str, config: dict):
        if model_type == "lstm":
            return LSTMModel(config)
        elif model_type == "random_forest":
            return RandomForestModel(config)
        elif model_type == "ensemble":
            return EnsembleModel(config)
        else:
            raise ValueError(f"Unknown model: {model_type}")
```

**Why**: Simplifies model swapping for testing and comparison

### 5. Repository Pattern - Database Access

**Use Case**: Abstract database operations from business logic

```python
class TradeRepository:
    def save(self, trade: dict) -> int:
        return self.db.insert('trades', trade)

    def find_by_symbol(self, symbol: str) -> List[dict]:
        return self.db.query('trades', symbol=symbol)

    def find_recent(self, days: int) -> List[dict]:
        cutoff = datetime.now() - timedelta(days=days)
        return self.db.query('trades', timestamp__gt=cutoff)
```

**Why**: Easy to swap SQLite for PostgreSQL later without changing business logic

### 6. Command Pattern - Order Management

**Use Case**: Encapsulate order actions for undo/replay

```python
class OrderCommand(ABC):
    @abstractmethod
    def execute(self) -> bool:
        pass

    @abstractmethod
    def undo(self) -> bool:
        pass

class PlaceOrderCommand(OrderCommand):
    def execute(self) -> bool:
        self.order_id = self.executor.place_order(self.symbol, self.qty)
        return self.order_id is not None

    def undo(self) -> bool:
        return self.executor.cancel_order(self.order_id)
```

**Why**: Enables order replay for backtesting and debugging

## Component Relationships

### Data Flow Diagram

```
External APIs          Data Module          ML Module          Trading Module
─────────────         ─────────────        ─────────         ──────────────
     │                      │                   │                   │
     │ Historical Data      │                   │                   │
     ├─────────────────────►│                   │                   │
     │                      │                   │                   │
     │                      │ Features          │                   │
     │                      ├──────────────────►│                   │
     │                      │                   │                   │
     │                      │                   │ Prediction        │
     │                      │                   ├──────────────────►│
     │                      │                   │                   │
     │                      │                   │                   │ Signal
     │                      │                   │                   ├────────►
     │                      │                   │                   │
     │ Order Confirmation   │                   │                   │
     │◄─────────────────────────────────────────────────────────────┤
     │                      │                   │                   │

Risk Module validates before Trading Module executes
Dashboard reads from Database, never modifies trading state directly
```

### Module Dependencies

```
main.py (orchestrator)
  ├─► data.data_fetcher
  ├─► data.feature_engineer
  ├─► ml.predictor
  ├─► ml.ensemble
  ├─► trading.signal_generator
  ├─► trading.executor
  ├─► risk.risk_calculator
  ├─► risk.portfolio_monitor
  ├─► database.db_manager
  └─► dashboard.app (runs separately)

No circular dependencies
Each module can be tested independently
```

### Critical Implementation Paths

#### Path 1: Trade Execution Flow

```
1. main.py: run_trading_cycle()
2. data_fetcher: fetch_realtime_data("PLTR")
3. feature_engineer: calculate_technical_indicators(data)
4. predictor: predict_next_day("PLTR", model)
5. ensemble: ensemble_predict(lstm_pred, rf_pred, momentum)
6. signal_generator: generate_signal(prediction, current_position)
7. risk_calculator: validate_trade(signal, portfolio)
8. executor: place_market_order(signal.symbol, qty, side)
9. position_manager: track_position(order_result)
10. db_manager: save_trade(trade_data)
```

#### Path 2: Stop Loss Execution

```
1. position_manager: update_position_prices() [every 30s]
2. stop_loss_manager: check_stops()
3. stop_loss_manager: detect stop_loss triggered
4. executor: place_market_order(symbol, qty, "sell")
5. position_manager: close_position(symbol)
6. db_manager: update_trade_status(trade_id, "closed")
7. portfolio_monitor: update_daily_pnl()
```

#### Path 3: Dashboard Update Flow

```
1. dashboard.routes: @app.route('/api/portfolio')
2. db_manager: get_active_positions()
3. position_manager: get_open_positions() [from Alpaca]
4. portfolio_monitor: get_risk_metrics()
5. dashboard: render JSON response
6. JavaScript: update UI elements
```

### Error Handling Strategy

**Principle**: Fail gracefully, never silently

```python
# All external API calls wrapped in try/except
try:
    data = alpaca.get_positions()
except APIError as e:
    logger.error(f"Failed to fetch positions: {e}")
    return cached_positions  # Use last known good state

# All database operations wrapped
try:
    db.save_trade(trade)
except DatabaseError as e:
    logger.critical(f"Failed to save trade: {e}")
    # Log to backup file
    with open('trades_backup.log', 'a') as f:
        f.write(json.dumps(trade) + '\n')

# Risk validation always checked
result, reason = risk_calculator.validate_trade(signal, portfolio)
if not result:
    logger.warning(f"Trade rejected: {reason}")
    return False  # Never execute invalid trade
```

**Recovery Mechanisms**:

- API failures: Retry with exponential backoff (3 attempts)
- Database failures: Backup log file, manual recovery
- Model failures: Fall back to simpler rule-based signals
- Network issues: Queue orders for execution when reconnected

### Logging Strategy

**Levels**:

- **DEBUG**: Feature values, prediction details, timing
- **INFO**: Trade execution, position updates, signal generation
- **WARNING**: Risk limit approached, API retry, invalid data
- **ERROR**: Order failure, model error, data fetch failure
- **CRITICAL**: System shutdown, data loss, security issue

**Log Locations**:

- `logs/trading_bot.log`: Main application log (rotated daily)
- `logs/trades.log`: Trade execution details only
- `logs/predictions.log`: ML prediction details
- `logs/errors.log`: ERROR and CRITICAL only

**Loguru Configuration**:

```python
from loguru import logger

logger.add(
    "logs/trading_bot.log",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)

logger.add(
    "logs/errors.log",
    level="ERROR",
    backtrace=True,
    diagnose=True
)
```

## Performance Considerations

### Optimization Targets

1. **Dashboard Load Time**: <2 seconds

   - Cache position data (30s refresh)
   - Lazy load charts
   - Minimize database queries

2. **Prediction Latency**: <5 seconds

   - Model inference optimized
   - Feature calculation parallelized
   - Pre-compute indicators where possible

3. **Order Execution**: <1 second from signal

   - Direct Alpaca API calls
   - No unnecessary validation loops
   - Parallel position monitoring

4. **Database Performance**: <100ms for queries
   - Indices on frequently queried columns
   - Batch inserts for historical data
   - Query optimization for dashboard

### Scalability Considerations

**Current Limits** (designed for):

- 1 user
- 5 concurrent positions
- 1-5 symbols traded
- ~10 trades per day
- 1000 trades per year

**Future Scaling** (if needed):

- Multi-user: Separate portfolios in database
- More symbols: Parallel prediction processing
- Higher frequency: In-memory caching layer
- More trades: PostgreSQL migration

## Testing Strategy

### Unit Tests

- Each module tested independently
- Mock external dependencies (Alpaca API, database)
- Test edge cases (division by zero, null data)
- Target: >80% code coverage

### Integration Tests

- Test module interactions
- Use test database (separate from production)
- Mock Alpaca API responses
- Verify data flow end-to-end

### Backtesting

- Historical data validation
- Strategy performance metrics
- Risk management verification
- Time-travel simulation

### Paper Trading

- Real market conditions
- Real API integration
- No financial risk
- 2+ weeks minimum before live

## Development Workflow

### Documentation-Driven Development

**Context7 Integration**: The project uses Context7 MCP server for real-time library documentation access during development.

**When to Use Context7**:

- Before implementing new features: Verify current API patterns for TensorFlow, pandas, Alpaca, etc.
- During code review: Ensure code follows latest library best practices
- When encountering errors: Look up correct usage patterns and parameters
- For API verification: Confirm method signatures and return types

**Typical Workflow**:

1. Identify library/topic needed (e.g., "TensorFlow LSTM layers")
2. Use Context7 to fetch latest documentation
3. Review examples and best practices
4. Implement using verified patterns
5. Test implementation

**Benefits**:

- Always use current API patterns (especially important for TensorFlow)
- Avoid deprecated methods
- Follow library-specific best practices
- Reduce debugging time from API misuse

## Security Considerations

### API Key Management

- Stored in `.env` file (never committed)
- Loaded at runtime only
- Never logged or displayed
- Separate keys for paper/live

### Database Security

- Local file only (not exposed)
- No sensitive data in logs
- Regular backups
- Encrypted if storing on cloud

### Dashboard Security

- Localhost only (127.0.0.1)
- No external access
- Optional: Add authentication for future
- HTTPS if exposed (not planned)

### Code Security

- No hardcoded credentials
- Input validation on all user inputs
- SQL injection prevention (parameterized queries)
- XSS prevention (template escaping)
