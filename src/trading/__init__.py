"""
Trading Module - Order execution and signal management.

This module provides the complete trading execution layer, from signal
generation to order placement and position management.

Key Components:
- AlpacaExecutor: Broker API integration
- SignalGenerator: Convert ML predictions to trading signals
- SignalQueue: Manage pending signals for approval
- PositionManager: Track open positions and P&L
- OrderManager: Order lifecycle management
"""

from src.trading.executor import AlpacaExecutor
from src.trading.signal_generator import SignalGenerator, SignalQueue
from src.trading.position_manager import PositionManager
from src.trading.order_manager import OrderManager, OrderTracking

__all__ = [
    'AlpacaExecutor',
    'SignalGenerator',
    'SignalQueue',
    'PositionManager',
    'OrderManager',
    'OrderTracking'
]
