"""
Database Repositories Package.

Provides specialized repository classes for database operations following
the Repository pattern and Single Responsibility Principle.
"""

from src.database.repositories.base_repository import BaseRepository
from src.database.repositories.trade_repository import TradeRepository
from src.database.repositories.position_repository import PositionRepository
from src.database.repositories.prediction_repository import PredictionRepository
from src.database.repositories.signal_repository import SignalRepository
from src.database.repositories.performance_repository import PerformanceMetricsRepository
from src.database.repositories.bot_state_repository import BotStateRepository
from src.database.repositories.analytics_service import AnalyticsService

__all__ = [
    'BaseRepository',
    'TradeRepository',
    'PositionRepository',
    'PredictionRepository',
    'SignalRepository',
    'PerformanceMetricsRepository',
    'BotStateRepository',
    'AnalyticsService',
]
