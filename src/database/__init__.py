"""
Database module for trading bot.

Provides database schema, manager, and data persistence.
"""

from src.database.schema import (
    Base,
    Trade,
    Position,
    Prediction,
    Signal,
    PerformanceMetric,
    BotState,
    create_database
)
from src.database.db_manager import DatabaseManager

__all__ = [
    'Base',
    'Trade',
    'Position',
    'Prediction',
    'Signal',
    'PerformanceMetric',
    'BotState',
    'create_database',
    'DatabaseManager'
]
