# Implementation Plan: DRY/SOLID Principles Refactoring

## [Overview]

Comprehensive refactoring to eliminate code duplication and apply SOLID principles across the 11,310-line trading bot codebase. This refactoring addresses five major areas: (1) error handling duplication across 89 try-catch blocks, (2) TradingBot God Class violating Single Responsibility Principle, (3) repeated Alpaca conversion logic in multiple modules, (4) DatabaseManager handling too many responsibilities, and (5) lack of dependency abstractions violating Dependency Inversion Principle.

The refactoring will improve maintainability, testability, and extensibility while preserving all existing functionality. All changes are non-breaking and will be validated through the existing test suite before deployment. The refactoring follows a progressive approach: first eliminate duplication (DRY), then separate concerns (SRP), and finally introduce abstractions (DIP).

## [Types]

New type system to support abstraction layers and shared functionality.

**Error Handling Types** (`src/common/error_types.py`):

```python
@dataclass
class ErrorContext:
    """Context information for error handling decorator"""
    operation: str  # e.g., "place_order", "fetch_data"
    module: str     # e.g., "executor", "data_fetcher"
    retry_count: int = 0
    max_retries: int = 3
    suppress_errors: bool = False

class RetryStrategy(Enum):
    """Retry strategies for failed operations"""
    EXPONENTIAL_BACKOFF = "exponential"
    FIXED_DELAY = "fixed"
    IMMEDIATE = "immediate"
    NO_RETRY = "none"
```

**Protocol Definitions** (`src/common/protocols.py`):

```python
from typing import Protocol, List, Optional, Dict, Any

class OrderExecutor(Protocol):
    """Protocol for order execution implementations"""
    def place_market_order(self, symbol: str, quantity: int, side: str) -> Tuple[bool, Optional[str], Optional[str]]: ...
    def place_limit_order(self, symbol: str, quantity: int, side: str, limit_price: float) -> Tuple[bool, Optional[str], Optional[str]]: ...
    def cancel_order(self, order_id: str) -> Tuple[bool, Optional[str]]: ...
    def get_open_positions(self) -> List[Position]: ...

class DataProvider(Protocol):
    """Protocol for market data providers"""
    def fetch_historical_data(self, symbol: str, days: int) -> Optional[pd.DataFrame]: ...
    def fetch_latest_price(self, symbol: str) -> Optional[float]: ...
    def is_market_open(self) -> bool: ...

class RepositoryProtocol(Protocol):
    """Protocol for data persistence implementations"""
    def save(self, entity: Dict[str, Any]) -> int: ...
    def update(self, id: int, updates: Dict[str, Any]) -> bool: ...
    def find_by_id(self, id: int) -> Optional[Dict[str, Any]]: ...
    def delete(self, id: int) -> bool: ...
```

**Converter Types** (`src/common/converter_types.py`):

```python
@dataclass
class AlpacaPositionDTO:
    """Data Transfer Object for Alpaca positions"""
    symbol: str
    qty: str
    avg_entry_price: str
    current_price: str
    market_value: str
    unrealized_pl: str
    unrealized_plpc: str

@dataclass
class AlpacaOrderDTO:
    """Data Transfer Object for Alpaca orders"""
    id: str
    symbol: str
    qty: str
    side: str
    type: str
    status: str
    filled_qty: Optional[str]
    filled_avg_price: Optional[str]
```

## [Files]

Detailed breakdown of file modifications, creations, and organizational changes.

**New Files to Create**:

1. `src/common/__init__.py` - Common utilities package initialization
2. `src/common/error_types.py` - Error handling type definitions (45 lines)
3. `src/common/protocols.py` - Protocol/interface definitions (120 lines)
4. `src/common/converter_types.py` - DTO type definitions (60 lines)
5. `src/common/decorators.py` - Reusable decorators including error handling (150 lines)
6. `src/common/converters.py` - Shared conversion utilities (200 lines)
7. `src/common/validators.py` - Shared validation logic (180 lines)
8. `src/orchestration/__init__.py` - Orchestration package initialization
9. `src/orchestration/trading_orchestrator.py` - Trading cycle orchestrator (250 lines)
10. `src/orchestration/position_orchestrator.py` - Position monitoring orchestrator (180 lines)
11. `src/orchestration/risk_orchestrator.py` - Risk management orchestrator (150 lines)
12. `src/orchestration/market_orchestrator.py` - Market hours and EOD orchestrator (120 lines)
13. `src/database/repositories/__init__.py` - Repository pattern package
14. `src/database/repositories/trade_repository.py` - Trade CRUD operations (120 lines)
15. `src/database/repositories/position_repository.py` - Position CRUD operations (100 lines)
16. `src/database/repositories/prediction_repository.py` - Prediction CRUD operations (90 lines)
17. `src/database/repositories/signal_repository.py` - Signal CRUD operations (80 lines)
18. `src/database/repositories/performance_repository.py` - Performance CRUD operations (70 lines)
19. `src/database/repositories/bot_state_repository.py` - Bot state CRUD operations (60 lines)
20. `src/database/analytics_service.py` - Analytics and reporting service (180 lines)

**Existing Files to Modify**:

1. `src/main.py` - Reduce from 1000+ to ~400 lines by delegating to orchestrators

   - Remove: Direct signal processing, position monitoring, risk checking implementations
   - Keep: Initialization, start/stop, scheduler setup, high-level coordination
   - Add: Orchestrator instantiation and delegation

2. `src/trading/executor.py` - Apply error handling decorator, use converters

   - Remove: 15+ try-catch blocks (~180 lines)
   - Add: @handle_broker_error decorator usage
   - Modify: Position/order conversion to use AlpacaConverter

3. `src/trading/position_manager.py` - Use shared converters

   - Remove: Duplicate Alpaca position conversion logic (~40 lines)
   - Add: Import and use AlpacaConverter.to_position()

4. `src/trading/order_manager.py` - Apply error handling decorator

   - Remove: 8 try-catch blocks (~90 lines)
   - Add: @handle_trading_error decorator usage

5. `src/data/data_fetcher.py` - Apply error handling decorator

   - Remove: 12 try-catch blocks (~120 lines)
   - Add: @handle_data_error decorator usage

6. `src/data/feature_engineer.py` - Apply error handling decorator

   - Remove: 6 try-catch blocks (~60 lines)
   - Add: @handle_calculation_error decorator usage

7. `src/data/data_validator.py` - Use shared validators

   - Remove: Duplicate validation patterns (~80 lines)
   - Add: Import from common.validators

8. `src/ml/predictor.py` - Apply error handling decorator

   - Remove: 8 try-catch blocks (~80 lines)
   - Add: @handle_ml_error decorator usage

9. `src/ml/ensemble.py` - Apply error handling decorator

   - Remove: 5 try-catch blocks (~50 lines)
   - Add: @handle_ml_error decorator usage

10. `src/risk/risk_calculator.py` - Extract to validator

    - Remove: Inline validation logic (~60 lines)
    - Add: Use TradeValidator from common.validators

11. `src/database/db_manager.py` - Split into repositories + analytics service

    - Remove: All CRUD methods (~600 lines)
    - Keep: Session management, initialization (~150 lines)
    - Add: Repository delegation pattern

12. `src/dashboard/app.py` - Use protocol types for loose coupling
    - Modify: Type hints to use OrderExecutor, DataProvider protocols
    - Remove: Direct TradingBot coupling where possible

**Configuration File Updates**:

1. `config/config.yaml` - Add error handling configuration section:

```yaml
error_handling:
  max_retries: 3
  retry_strategy: exponential
  base_delay_seconds: 1
  max_delay_seconds: 30
  log_all_errors: true
```

## [Functions]

Detailed breakdown of new functions, modifications, and removals.

**New Functions**:

1. `src/common/decorators.py`:

   - `handle_broker_error(retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF, max_retries=3)` - Decorator for Alpaca API calls
   - `handle_data_error(fallback_value=None, log_level="ERROR")` - Decorator for data fetching operations
   - `handle_ml_error(fallback_to_baseline=False)` - Decorator for ML operations
   - `handle_trading_error(circuit_breaker=True)` - Decorator for trading operations
   - `log_execution_time(threshold_seconds=1.0)` - Performance logging decorator
   - `validate_inputs(**validation_rules)` - Input validation decorator

2. `src/common/converters.py`:

   - `AlpacaConverter.to_position(alpaca_position) -> Position` - Convert Alpaca position to internal Position
   - `AlpacaConverter.to_order_status(alpaca_order) -> OrderStatus` - Convert Alpaca order to OrderStatus
   - `AlpacaConverter.from_position(position) -> AlpacaPositionDTO` - Convert internal to Alpaca DTO
   - `DatabaseConverter.position_to_dict(position) -> Dict` - Convert Position to database dict
   - `DatabaseConverter.dict_to_position(data) -> Position` - Convert database dict to Position
   - `DatabaseConverter.trade_to_dict(trade) -> Dict` - Convert TradeRecord to database dict

3. `src/common/validators.py`:

   - `TradeValidator.validate_signal(signal, portfolio, positions) -> ValidationResult` - Extracted from RiskCalculator
   - `DataValidator.validate_price_bounds(price, symbol) -> bool` - Price sanity check
   - `DataValidator.validate_quantity(quantity, max_allowed) -> bool` - Quantity validation
   - `PositionValidator.validate_stop_loss(entry, stop, min_distance) -> bool` - Stop loss validation

4. `src/orchestration/trading_orchestrator.py`:

   - `TradingOrchestrator.__init__(config, modules)` - Initialize with dependencies
   - `TradingOrchestrator.run_cycle()` - Execute full trading cycle (extracted from main.py)
   - `TradingOrchestrator._process_symbol(symbol)` - Process single symbol (extracted)
   - `TradingOrchestrator._execute_signal(signal)` - Execute trading signal (extracted)

5. `src/orchestration/position_orchestrator.py`:

   - `PositionOrchestrator.__init__(config, modules)` - Initialize with dependencies
   - `PositionOrchestrator.update_positions()` - Update all positions (extracted from main.py)
   - `PositionOrchestrator._execute_stop_loss(symbol, reason)` - Execute stop (extracted)
   - `PositionOrchestrator._update_trailing_stops()` - Update trailing stops

6. `src/orchestration/risk_orchestrator.py`:

   - `RiskOrchestrator.__init__(config, modules)` - Initialize with dependencies
   - `RiskOrchestrator.check_limits()` - Check all risk limits (extracted from main.py)
   - `RiskOrchestrator._activate_circuit_breaker()` - Activate circuit breaker (extracted)
   - `RiskOrchestrator.calculate_portfolio_risk() -> RiskMetrics` - Calculate current risk

7. `src/database/repositories/trade_repository.py`:
   - `TradeRepository.__init__(session_factory)` - Initialize repository
   - `TradeRepository.save(trade_data) -> int` - Save trade (extracted from db_manager)
   - `TradeRepository.update(trade_id, updates) -> bool` - Update trade (extracted)
   - `TradeRepository.find_by_id(trade_id) -> Optional[Dict]` - Find trade (extracted)
   - `TradeRepository.find_by_symbol(symbol) -> List[Dict]` - Find by symbol (extracted)

**Modified Functions**:

1. `src/main.py`:

   - `TradingBot._create_modules()` - Add orchestrator instantiation
   - `TradingBot.run_trading_cycle()` - Delegate to TradingOrchestrator (reduce from 180 to 15 lines)
   - `TradingBot.update_positions()` - Delegate to PositionOrchestrator (reduce from 120 to 15 lines)
   - `TradingBot.check_risk_limits()` - Delegate to RiskOrchestrator (reduce from 80 to 12 lines)
   - `TradingBot._execute_signal()` - Delegate to TradingOrchestrator (remove, becomes orchestrator method)
   - `TradingBot._process_symbol()` - Delegate to TradingOrchestrator (remove, becomes orchestrator method)

2. `src/trading/executor.py`:

   - `AlpacaExecutor.place_market_order()` - Add @handle_broker_error decorator, remove try-catch
   - `AlpacaExecutor.place_limit_order()` - Add @handle_broker_error decorator, remove try-catch
   - `AlpacaExecutor.get_open_positions()` - Use AlpacaConverter.to_position(), remove conversion logic
   - `AlpacaExecutor.get_position()` - Use AlpacaConverter.to_position(), remove conversion logic

3. `src/database/db_manager.py`:
   - `DatabaseManager.save_trade()` - Delegate to TradeRepository (wrapper method)
   - `DatabaseManager.get_trade_history()` - Delegate to TradeRepository (wrapper method)
   - `DatabaseManager.save_position()` - Delegate to PositionRepository (wrapper method)
   - `DatabaseManager.calculate_daily_performance()` - Delegate to AnalyticsService (wrapper method)

**Removed Functions** (moved to appropriate locations):

1. From `src/database/db_manager.py` - Move to repositories:

   - All `save_*()` methods → respective repositories
   - All `update_*()` methods → respective repositories
   - All `get_*()` methods → respective repositories
   - All `find_*()` methods → respective repositories
   - All analytics methods → AnalyticsService

2. From `src/main.py` - Move to orchestrators:
   - `_execute_signal()` → TradingOrchestrator
   - `_process_symbol()` → TradingOrchestrator
   - `_execute_stop_loss()` → PositionOrchestrator
   - `_activate_circuit_breaker()` → RiskOrchestrator

## [Classes]

Detailed breakdown of new classes, modifications, and removals.

**New Classes**:

1. `src/common/decorators.py`:

   - `ErrorHandler` - Base class for error handling strategies
   - `RetryableError` - Custom exception for retryable operations
   - `CircuitBreakerError` - Custom exception when circuit breaker activates

2. `src/common/converters.py`:

   - `AlpacaConverter` - Static methods for Alpaca ↔ internal conversions
   - `DatabaseConverter` - Static methods for Database ↔ internal conversions
   - `ConverterRegistry` - Registry pattern for custom converters

3. `src/common/validators.py`:

   - `TradeValidator` - Trade validation logic (extracted from RiskCalculator)
   - `DataValidator` - Data validation logic (shared across modules)
   - `PositionValidator` - Position validation logic
   - `ValidationResult` - Dataclass for validation results with reason

4. `src/orchestration/trading_orchestrator.py`:

   - `TradingOrchestrator` - Manages trading cycle workflow
     - Key methods: `run_cycle()`, `_process_symbol()`, `_execute_signal()`
     - Dependencies: DataFetcher, FeatureEngineer, Predictor, SignalGenerator, OrderManager
     - Responsibility: Single concern - orchestrate trading decisions

5. `src/orchestration/position_orchestrator.py`:

   - `PositionOrchestrator` - Manages position monitoring workflow
     - Key methods: `update_positions()`, `_execute_stop_loss()`, `_update_trailing_stops()`
     - Dependencies: PositionManager, StopLossManager, DataFetcher, Executor
     - Responsibility: Single concern - monitor and manage positions

6. `src/orchestration/risk_orchestrator.py`:

   - `RiskOrchestrator` - Manages risk monitoring and enforcement
     - Key methods: `check_limits()`, `_activate_circuit_breaker()`, `calculate_portfolio_risk()`
     - Dependencies: PortfolioMonitor, RiskCalculator, DatabaseManager
     - Responsibility: Single concern - enforce risk rules

7. `src/orchestration/market_orchestrator.py`:

   - `MarketOrchestrator` - Manages market hours and EOD handling
     - Key methods: `handle_market_close()`, `is_market_hours()`, `get_next_trading_day()`
     - Dependencies: DataFetcher, PositionManager, DatabaseManager
     - Responsibility: Single concern - market scheduling

8. `src/database/repositories/trade_repository.py`:

   - `TradeRepository` - CRUD operations for trades
     - Inheritance: Implements RepositoryProtocol
     - Key methods: `save()`, `update()`, `find_by_id()`, `find_by_symbol()`, `get_open_trades()`
     - Responsibility: Single concern - trade data persistence

9. `src/database/repositories/position_repository.py`:

   - `PositionRepository` - CRUD operations for positions
     - Inheritance: Implements RepositoryProtocol
     - Key methods: `save()`, `update()`, `find_by_symbol()`, `get_active_positions()`, `delete()`
     - Responsibility: Single concern - position data persistence

10. `src/database/repositories/base_repository.py`:

    - `BaseRepository` - Abstract base class for repositories
      - Key methods: `_entity_to_dict()`, `_dict_to_entity()`, `_execute_query()`
      - Responsibility: Common repository functionality

11. `src/database/analytics_service.py`:
    - `AnalyticsService` - Analytics and reporting
      - Key methods: `calculate_daily_performance()`, `get_win_rate()`, `get_sharpe_ratio()`
      - Dependencies: All repositories
      - Responsibility: Single concern - analytics calculations

**Modified Classes**:

1. `src/main.py::TradingBot`:

   - Current size: ~1000 lines with 15+ methods
   - Target size: ~400 lines with 8 core methods
   - Changes:
     - Remove: 7 implementation methods (moved to orchestrators)
     - Add: 4 orchestrator instance variables
     - Modify: Delegate to orchestrators instead of direct implementation
     - Keep: Initialization, start/stop, scheduler setup, status reporting

2. `src/trading/executor.py::AlpacaExecutor`:

   - Remove: All try-catch blocks (~15 blocks, 180 lines)
   - Add: Decorator usage (@handle_broker_error on all public methods)
   - Modify: Use AlpacaConverter for all position/order conversions
   - Impact: Reduce from ~480 lines to ~300 lines

3. `src/database/db_manager.py::DatabaseManager`:

   - Current size: ~800 lines with 30+ methods
   - Target size: ~200 lines with 10 wrapper methods
   - Changes:
     - Remove: All CRUD methods (moved to repositories)
     - Add: Repository instances (6 repositories)
     - Add: Delegation wrapper methods for backward compatibility
     - Add: Migration helper method for gradual transition

4. `src/risk/risk_calculator.py::RiskCalculator`:
   - Remove: Inline validation logic (~60 lines)
   - Add: Use TradeValidator.validate_signal()
   - Modify: Focus solely on calculations, not validation
   - Impact: Clearer separation between calculation and validation

**Class Relationship Changes**:

Before:

```
TradingBot (God Class)
  ├─ Direct: DataFetcher, FeatureEngineer, Predictor
  ├─ Direct: SignalGenerator, Executor, OrderManager
  ├─ Direct: PositionManager, StopLossManager
  ├─ Direct: RiskCalculator, PortfolioMonitor
  └─ Direct: DatabaseManager (God Class)
```

After:

```
TradingBot (Coordinator)
  ├─ TradingOrchestrator
  │   ├─ DataFetcher
  │   ├─ FeatureEngineer
  │   ├─ Predictor
  │   ├─ SignalGenerator
  │   └─ OrderManager
  ├─ PositionOrchestrator
  │   ├─ PositionManager
  │   ├─ StopLossManager
  │   └─ DataFetcher
  ├─ RiskOrchestrator
  │   ├─ RiskCalculator
  │   ├─ PortfolioMonitor
  │   └─ TradeValidator
  └─ MarketOrchestrator
      ├─ DataFetcher
      └─ PositionManager

DatabaseManager (Coordinator)
  ├─ TradeRepository
  ├─ PositionRepository
  ├─ PredictionRepository
  ├─ SignalRepository
  ├─ PerformanceRepository
  ├─ BotStateRepository
  └─ AnalyticsService (uses all repositories)
```

## [Dependencies]

No new external packages required. All refactoring uses Python standard library and existing dependencies.

**Existing Dependencies** (no changes):

- Python 3.12.3
- TensorFlow 2.19.1
- scikit-learn 1.3.2
- pandas 2.1.3
- alpaca-py (latest)
- Flask 3.0.0
- SQLAlchemy 2.0.23
- loguru 0.7.2
- APScheduler 3.10.4

**Internal Dependency Changes**:

1. Add imports across all modules:

```python
from src.common.decorators import handle_broker_error, handle_data_error
from src.common.converters import AlpacaConverter, DatabaseConverter
from src.common.validators import TradeValidator, DataValidator
from src.common.protocols import OrderExecutor, DataProvider
```

2. Update `src/main.py` imports:

```python
from src.orchestration.trading_orchestrator import TradingOrchestrator
from src.orchestration.position_orchestrator import PositionOrchestrator
from src.orchestration.risk_orchestrator import RiskOrchestrator
from src.orchestration.market_orchestrator import MarketOrchestrator
```

3. Update `src/database/db_manager.py` imports:

```python
from src.database.repositories.trade_repository import TradeRepository
from src.database.repositories.position_repository import PositionRepository
# ... all repositories
from src.database.analytics_service import AnalyticsService
```

## [Testing]

Comprehensive testing strategy to ensure refactoring maintains functionality.

**New Test Files**:

1. `tests/common/test_decorators.py` - Test error handling decorators (120 lines)

   - Test retry logic with exponential backoff
   - Test circuit breaker activation
   - Test error logging patterns
   - Test fallback value handling

2. `tests/common/test_converters.py` - Test conversion utilities (150 lines)

   - Test Alpaca → internal conversions
   - Test internal → database conversions
   - Test round-trip conversions (data integrity)
   - Test edge cases (None values, missing fields)

3. `tests/common/test_validators.py` - Test validation logic (100 lines)

   - Test TradeValidator rules
   - Test DataValidator bounds checking
   - Test PositionValidator constraints

4. `tests/orchestration/test_trading_orchestrator.py` - Test trading workflow (180 lines)

   - Test full cycle execution
   - Test signal processing
   - Test error handling
   - Mock all dependencies

5. `tests/orchestration/test_position_orchestrator.py` - Test position monitoring (120 lines)

   - Test position updates
   - Test stop loss execution
   - Test trailing stop logic
   - Mock all dependencies

6. `tests/orchestration/test_risk_orchestrator.py` - Test risk management (100 lines)

   - Test limit checking
   - Test circuit breaker activation
   - Test risk calculations
   - Mock all dependencies

7. `tests/database/repositories/test_trade_repository.py` - Test trade CRUD (80 lines)

   - Test save, update, find operations
   - Test query filtering
   - Use test database

8. `tests/database/test_analytics_service.py` - Test analytics (90 lines)
   - Test performance calculations
   - Test win rate calculations
   - Test metric aggregations
   - Mock repositories

**Modified Test Files**:

1. `tests/test_bot_init.py` - Update for orchestrator initialization

   - Add: Verify orchestrator instances created
   - Modify: Assertions for new module structure

2. `tests/test_risk_validation.py` - Update for TradeValidator

   - Modify: Import from common.validators instead of risk_calculator
   - Keep: All existing test cases (should pass unchanged)

3. `test_data_pipeline.py` - Update for decorators

   - Add: Verify error handling decorator behavior
   - Keep: All existing functionality tests

4. `test_ensemble_prediction.py` - Update for ML decorators
   - Add: Verify error handling in prediction failures
   - Keep: All existing prediction tests

**Existing Test Maintenance**:

All 14 existing integration tests must pass unchanged:

- Test 1-4: Bot Initialization
- Test 5: Dashboard Launch
- Test 6: Data Pipeline
- Test 7: ML Model Training
- Test 8: Ensemble Prediction
- Test 9: Signal Generation
- Test 10: Risk Validation
- Test 11: Signal Approval
- Test 12: Position Monitoring
- Test 13: Bot Control
- Test 14: 48-Hour Continuous Run

**Test Execution Strategy**:

1. **Phase 1**: Unit test new components

   - Run: `pytest tests/common/`
   - Run: `pytest tests/orchestration/`
   - Run: `pytest tests/database/repositories/`
   - Target: 100% coverage of new code

2. **Phase 2**: Integration test modified components

   - Run: `pytest tests/test_bot_init.py`
   - Run: `pytest tests/test_risk_validation.py`
   - Target: All existing tests pass

3. **Phase 3**: Full regression testing

   - Run: `pytest tests/`
   - Target: All 14 integration tests + new tests pass
   - Target: Overall coverage >80%

4. **Phase 4**: Manual testing
   - Test bot initialization
   - Test trading cycle execution
   - Test position monitoring
   - Test risk limit enforcement
   - Test dashboard functionality

**Mock Strategy**:

- Mock external dependencies (Alpaca API) using pytest fixtures
- Use test database for repository tests
- Mock time.sleep() for retry logic tests
- Use dependency injection for easier mocking in orchestrators

## [Implementation Order]

Numbered sequence to minimize conflicts and ensure successful integration.

**Phase 1: Foundation (Days 1-2) - DRY Improvements**

1. Create `src/common/` package structure

   - Create `src/common/__init__.py`
   - Create `src/common/error_types.py`
   - Create `src/common/protocols.py`
   - Create `src/common/converter_types.py`
   - Write unit tests for types

2. Implement error handling decorators

   - Create `src/common/decorators.py`
   - Implement `@handle_broker_error` decorator
   - Implement `@handle_data_error` decorator
   - Implement `@handle_ml_error` decorator
   - Write unit tests for decorators (tests/common/test_decorators.py)
   - Target: 100% test coverage

3. Implement conversion utilities

   - Create `src/common/converters.py`
   - Implement `AlpacaConverter` class
   - Implement `DatabaseConverter` class
   - Write unit tests (tests/common/test_converters.py)
   - Target: 100% test coverage

4. Implement validation utilities
   - Create `src/common/validators.py`
   - Extract validation logic from RiskCalculator
   - Implement `TradeValidator`, `DataValidator`, `PositionValidator`
   - Write unit tests (tests/common/test_validators.py)
   - Target: 100% test coverage

**Phase 2: Apply DRY (Days 3-4) - Eliminate Duplication**

5. Refactor `src/trading/executor.py`

   - Apply `@handle_broker_error` to all methods
   - Remove 15 try-catch blocks
   - Use `AlpacaConverter` for conversions
   - Remove duplicate conversion logic (40 lines)
   - Run existing tests to verify no regression

6. Refactor `src/trading/position_manager.py`

   - Use `AlpacaConverter.to_position()`
   - Remove duplicate conversion logic
   - Run existing tests to verify no regression

7. Refactor `src/trading/order_manager.py`

   - Apply `@handle_trading_error` decorator
   - Remove 8 try-catch blocks
   - Run existing tests to verify no regression

8. Refactor `src/data/` modules

   - Apply decorators to data_fetcher.py (remove 12 try-catch blocks)
   - Apply decorators to feature_engineer.py (remove 6 try-catch blocks)
   - Use shared validators in data_validator.py
   - Run existing tests to verify no regression

9. Refactor `src/ml/` modules

   - Apply `@handle_ml_error` to predictor.py (remove 8 try-catch blocks)
   - Apply `@handle_ml_error` to ensemble.py (remove 5 try-catch blocks)
   - Run existing tests to verify no regression

10. Refactor `src/risk/risk_calculator.py`
    - Use `TradeValidator.validate_signal()`
    - Remove inline validation logic
    - Update tests to import from common.validators
    - Run existing tests to verify no regression

**Phase 3: SRP - Database Split (Days 5-6)**

11. Create repository infrastructure

    - Create `src/database/repositories/__init__.py`
    - Create `src/database/repositories/base_repository.py`
    - Implement `BaseRepository` abstract class
    - Write base repository tests

12. Implement individual repositories

    - Create `trade_repository.py` - Extract from db_manager (120 lines)
    - Create `position_repository.py` - Extract from db_manager (100 lines)
    - Create `prediction_repository.py` - Extract from db_manager (90 lines)
    - Create `signal_repository.py` - Extract from db_manager (80 lines)
    - Create `performance_repository.py` - Extract from db_manager (70 lines)
    - Create `bot_state_repository.py` - Extract from db_manager (60 lines)
    - Write unit tests for each repository
    - Target: 100% coverage for CRUD operations

13. Create analytics service

    - Create `src/database/analytics_service.py`
    - Extract analytics methods from db_manager
    - Implement performance calculations using repositories
    - Write unit tests (tests/database/test_analytics_service.py)
    - Target: 100% test coverage

14. Refactor `src/database/db_manager.py`
    - Remove all CRUD methods (move to repositories)
    - Add repository instances as attributes
    - Add delegation wrapper methods for backward compatibility
    - Keep session management and initialization
    - Run existing tests to verify no regression

**Phase 4: SRP - Main Bot Split (Days 7-9)**

15. Create orchestration infrastructure

    - Create `src/orchestration/__init__.py`
    - Define orchestrator base patterns
    - Setup dependency injection helpers

16. Create TradingOrchestrator

    - Create `src/orchestration/trading_orchestrator.py`
    - Extract `_process_symbol()` from main.py
    - Extract `_execute_signal()` from main.py
    - Extract `run_trading_cycle()` logic from main.py
    - Write unit tests (tests/orchestration/test_trading_orchestrator.py)
    - Target: 100% test coverage with mocked dependencies

17. Create PositionOrchestrator

    - Create `src/orchestration/position_orchestrator.py`
    - Extract `update_positions()` logic from main.py
    - Extract `_execute_stop_loss()` from main.py
    - Add trailing stop update logic
    - Write unit tests (tests/orchestration/test_position_orchestrator.py)
    - Target: 100% test coverage with mocked dependencies

18. Create RiskOrchestrator

    - Create `src/orchestration/risk_orchestrator.py`
    - Extract `check_risk_limits()` logic from main.py
    - Extract `_activate_circuit_breaker()` from main.py
    - Add portfolio risk calculation
    - Write unit tests (tests/orchestration/test_risk_orchestrator.py)
    - Target: 100% test coverage with mocked dependencies

19. Create MarketOrchestrator

    - Create `src/orchestration/market_orchestrator.py`
    - Extract `handle_market_close()` logic from main.py
    - Extract `is_market_hours()` logic from main.py
    - Add market scheduling utilities
    - Write unit tests (tests/orchestration/test_market_orchestrator.py)
    - Target: 100% test coverage with mocked dependencies

20. Refactor `src/main.py::TradingBot`
    - Add orchestrator instantiation in `_create_modules()`
    - Replace `run_trading_cycle()` with delegation to TradingOrchestrator
    - Replace `update_positions()` with delegation to PositionOrchestrator
    - Replace `check_risk_limits()` with delegation to RiskOrchestrator
    - Replace `handle_market_close()` with delegation to MarketOrchestrator
    - Remove extracted private methods
    - Update tests (tests/test_bot_init.py, tests/test_bot_control.py)
    - Run all integration tests to verify no regression
    - Target: Reduce from 1000+ to ~400 lines

**Phase 5: Integration & Testing (Days 10-12)**

21. Full integration testing

    - Run all 14 existing integration tests
    - Verify all tests pass without modification
    - Fix any regressions discovered
    - Target: 100% of existing tests passing

22. New component testing

    - Run all new unit tests (common, orchestration, repositories)
    - Verify 100% coverage of new code
    - Fix any bugs discovered
    - Target: All new tests passing

23. Update test suite

    - Update `tests/test_bot_init.py` for orchestrators
    - Update `tests/test_risk_validation.py` for TradeValidator
    - Update other affected tests as needed
    - Document test changes in test files

24. Manual end-to-end testing
    - Initialize bot and verify all modules load
    - Run trading cycle and verify workflow
    - Test position monitoring and stop loss execution
    - Test risk limit enforcement
    - Test dashboard functionality
    - Document any issues found

**Phase 6: Documentation & Deployment (Days 13-14)**

25. Update code documentation

    - Update docstrings for modified classes/methods
    - Add docstrings for new classes/methods
    - Update inline comments where logic changed
    - Ensure all public APIs documented

26. Update Memory Bank

    - Update `systemPatterns.md` with new architecture
    - Update `techContext.md` with new module structure
    - Update `activeContext.md` with refactoring completion
    - Update `progress.md` with refactoring milestone

27. Create migration guide

    - Document breaking changes (if any)
    - Document new import paths
    - Document deprecated methods (with replacements)
    - Create before/after examples

28. Final validation
    - Run Test 14: 48-hour continuous run
    - Monitor for any errors or regressions
    - Verify performance metrics unchanged
    - Verify memory usage stable
    - Document results

**Phase 7: Optional Enhancements (Future)**

29. Add protocol-based dependency injection (if needed)

    - Replace concrete dependencies with protocols
    - Add dependency injection container
    - Update tests for easier mocking

30. Performance optimization (if needed)
    - Profile refactored code
    - Optimize hot paths discovered
    - Add caching where beneficial
    - Measure and document improvements

## Success Criteria

Refactoring is complete when:

1. ✅ All 20 new files created and tested
2. ✅ All 12 existing files refactored
3. ✅ Error handling decorators eliminate 80+ try-catch blocks
4. ✅ TradingBot reduced from 1000+ to ~400 lines
5. ✅ DatabaseManager reduced from 800 to ~200 lines
6. ✅ All 14 existing integration tests pass unchanged
7. ✅ All new unit tests pass with >80% coverage
8. ✅ Test 14 (48-hour run) completes successfully
9. ✅ Memory Bank updated with final architecture
10. ✅ Zero functional regressions detected

## Risk Mitigation

**Risk**: Refactoring breaks existing functionality
**Mitigation**: Progressive approach with testing after each phase

**Risk**: Integration issues between new components
**Mitigation**: Comprehensive integration testing in Phase 5

**Risk**: Performance degradation from abstractions
**Mitigation**: Profile before/after, optimize hot paths if needed

**Risk**: Incomplete test coverage
**Mitigation**: Target 100% coverage for new code, maintain existing coverage

**Risk**: Developer confusion from new structure
**Mitigation**: Clear documentation, migration guide, before/after examples
