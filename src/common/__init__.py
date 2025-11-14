"""
Common utilities package for the trading bot.

This package provides shared functionality used across multiple modules:
- Error handling decorators
- Data converters (Alpaca ↔ internal types)
- Data validators
- Protocol definitions for loose coupling
"""

from src.common.decorators import (
    handle_broker_error,
    handle_data_error,
    handle_ml_error,
    handle_trading_error,
    log_execution_time,
    validate_inputs,
)

from src.common.converters import (
    AlpacaConverter,
    DatabaseConverter,
)

from src.common.validators import (
    TradeValidator,
    DataValidator,
    PositionValidator,
    ValidationResult,
)

from src.common.protocols import (
    OrderExecutor,
    DataProvider,
    RepositoryProtocol,
)

__all__ = [
    # Decorators
    'handle_broker_error',
    'handle_data_error',
    'handle_ml_error',
    'handle_trading_error',
    'log_execution_time',
    'validate_inputs',
    # Converters
    'AlpacaConverter',
    'DatabaseConverter',
    # Validators
    'TradeValidator',
    'DataValidator',
    'PositionValidator',
    'ValidationResult',
    # Protocols
    'OrderExecutor',
    'DataProvider',
    'RepositoryProtocol',
]
