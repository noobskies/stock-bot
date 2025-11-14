"""
Database Manager - Simplified Coordinator.

Provides a clean interface to all database operations through specialized repositories.
Follows Repository pattern and Single Responsibility Principle.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Any
import os
import shutil
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

from src.database.schema import Base
from src.database.repositories import (
    TradeRepository,
    PositionRepository,
    PredictionRepository,
    SignalRepository,
    PerformanceMetricsRepository,
    BotStateRepository,
    AnalyticsService
)

# Load environment variables
load_dotenv()


class DatabaseManager:
    """
    Simplified database manager that coordinates repository access.
    
    Provides access to specialized repositories for each domain entity
    and handles database-level operations like backup and maintenance.
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize database manager and all repositories.
        
        Args:
            database_url: Database connection string. If None, uses DATABASE_URL from .env
        """
        if database_url is None:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
        
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        # Initialize all repositories
        self._init_repositories()
        
        # Initialize bot state
        self.bot_state.init_bot_state()
        
        logger.info(f"Database manager initialized: {database_url}")
    
    def _init_repositories(self) -> None:
        """Initialize all repository instances."""
        self.trades = TradeRepository(self.SessionLocal)
        self.positions = PositionRepository(self.SessionLocal)
        self.predictions = PredictionRepository(self.SessionLocal)
        self.signals = SignalRepository(self.SessionLocal)
        self.performance = PerformanceMetricsRepository(self.SessionLocal)
        self.bot_state = BotStateRepository(self.SessionLocal)
        self.analytics = AnalyticsService(self.SessionLocal)
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.
        
        Automatically handles commit/rollback and session cleanup.
        Provided for backward compatibility with existing code.
        
        Usage:
            with db_manager.get_session() as session:
                # perform operations
                session.add(entity)
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    # ==================== BACKWARD COMPATIBILITY METHODS ====================
    # These methods delegate to the appropriate repository for backward compatibility
    
    def save_trade(self, trade_data: Dict[str, Any]) -> int:
        """Save a trade. Delegates to TradeRepository."""
        return self.trades.save_trade(trade_data)
    
    def update_trade(self, trade_id: int, updates: Dict[str, Any]) -> bool:
        """Update a trade. Delegates to TradeRepository."""
        return self.trades.update_trade(trade_id, updates)
    
    def get_trade_by_id(self, trade_id: int) -> Dict[str, Any]:
        """Get trade by ID. Delegates to TradeRepository."""
        return self.trades.get_trade_by_id(trade_id)
    
    def get_trades_by_symbol(self, symbol: str, status: str = None, limit: int = 100):
        """Get trades by symbol. Delegates to TradeRepository."""
        return self.trades.get_trades_by_symbol(symbol, status, limit)
    
    def get_recent_trades(self, days: int = 7, status: str = None):
        """Get recent trades. Delegates to TradeRepository."""
        return self.trades.get_recent_trades(days, status)
    
    def get_open_trades(self):
        """Get open trades. Delegates to TradeRepository."""
        return self.trades.get_open_trades()
    
    def close_trade(self, trade_id: int, exit_price: float, realized_pnl: float) -> bool:
        """Close a trade. Delegates to TradeRepository."""
        return self.trades.close_trade(trade_id, exit_price, realized_pnl)
    
    def save_position(self, position_data: Dict[str, Any]) -> int:
        """Save a position. Delegates to PositionRepository."""
        return self.positions.save_position(position_data)
    
    def update_position_price(self, symbol: str, current_price: float, 
                            unrealized_pnl: float, unrealized_pnl_percent: float) -> bool:
        """Update position price. Delegates to PositionRepository."""
        return self.positions.update_position_price(
            symbol, current_price, unrealized_pnl, unrealized_pnl_percent
        )
    
    def get_active_positions(self):
        """Get active positions. Delegates to PositionRepository."""
        return self.positions.get_active_positions()
    
    def get_position_by_symbol(self, symbol: str):
        """Get position by symbol. Delegates to PositionRepository."""
        return self.positions.get_position_by_symbol(symbol)
    
    def delete_position(self, symbol: str) -> bool:
        """Delete a position. Delegates to PositionRepository."""
        return self.positions.delete_position(symbol)
    
    def save_prediction(self, prediction_data: Dict[str, Any]) -> int:
        """Save a prediction. Delegates to PredictionRepository."""
        return self.predictions.save_prediction(prediction_data)
    
    def update_prediction_actual(self, prediction_id: int, actual_price: float) -> bool:
        """Update prediction with actual price. Delegates to PredictionRepository."""
        return self.predictions.update_prediction_actual(prediction_id, actual_price)
    
    def get_predictions_by_symbol(self, symbol: str, limit: int = 100):
        """Get predictions by symbol. Delegates to PredictionRepository."""
        return self.predictions.get_predictions_by_symbol(symbol, limit)
    
    def get_recent_predictions(self, days: int = 7):
        """Get recent predictions. Delegates to PredictionRepository."""
        return self.predictions.get_recent_predictions(days)
    
    def get_prediction_accuracy(self, days: int = 30) -> float:
        """Get prediction accuracy. Delegates to PredictionRepository."""
        return self.predictions.get_prediction_accuracy(days)
    
    def save_signal(self, signal_data: Dict[str, Any]) -> int:
        """Save a signal. Delegates to SignalRepository."""
        return self.signals.save_signal(signal_data)
    
    def update_signal_status(self, signal_id: int, status: str, **kwargs) -> bool:
        """Update signal status. Delegates to SignalRepository."""
        return self.signals.update_signal_status(signal_id, status, **kwargs)
    
    def get_pending_signals(self):
        """Get pending signals. Delegates to SignalRepository."""
        return self.signals.get_pending_signals()
    
    def get_signal_history(self, days: int = 30, status: str = None):
        """Get signal history. Delegates to SignalRepository."""
        return self.signals.get_signal_history(days, status)
    
    def save_performance_metrics(self, metrics_data: Dict[str, Any]) -> int:
        """Save performance metrics. Delegates to PerformanceMetricsRepository."""
        return self.performance.save_performance_metrics(metrics_data)
    
    def get_latest_metrics(self):
        """Get latest metrics. Delegates to PerformanceMetricsRepository."""
        return self.performance.get_latest_metrics()
    
    def get_metrics_by_date_range(self, start_date: datetime, end_date: datetime):
        """Get metrics by date range. Delegates to PerformanceMetricsRepository."""
        return self.performance.get_metrics_by_date_range(start_date, end_date)
    
    def get_bot_state(self) -> Dict[str, Any]:
        """Get bot state. Delegates to BotStateRepository."""
        return self.bot_state.get_bot_state()
    
    def update_bot_state(self, updates: Dict[str, Any]) -> bool:
        """Update bot state. Delegates to BotStateRepository."""
        return self.bot_state.update_bot_state(updates)
    
    def get_trade_history(self, symbol: str = None, start_date: datetime = None,
                         end_date: datetime = None, status: str = None, limit: int = 1000):
        """Get trade history. Delegates to AnalyticsService."""
        return self.analytics.get_trade_history(symbol, start_date, end_date, status, limit)
    
    def calculate_daily_performance(self, date: datetime) -> Dict[str, Any]:
        """Calculate daily performance. Delegates to AnalyticsService."""
        return self.analytics.calculate_daily_performance(date)
    
    def get_win_rate(self, days: int = 30) -> float:
        """Get win rate. Delegates to AnalyticsService."""
        return self.analytics.get_win_rate(days)
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary. Delegates to AnalyticsService."""
        return self.analytics.get_performance_summary(days)
    
    # ==================== DATABASE MAINTENANCE ====================
    
    def backup_database(self, backup_dir: str = "backups") -> str:
        """
        Create a backup of the database.
        
        Args:
            backup_dir: Directory to store backups
            
        Returns:
            str: Path to backup file
        """
        # Only works with SQLite
        if not self.database_url.startswith('sqlite:///'):
            logger.warning("Backup only supported for SQLite databases")
            return None
        
        # Extract database file path
        db_path = self.database_url.replace('sqlite:///', '')
        
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return None
        
        # Create backup directory
        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_path / f"trading_bot_{timestamp}.db"
        
        # Copy database file
        shutil.copy2(db_path, backup_file)
        
        logger.info(f"Database backed up to: {backup_file}")
        return str(backup_file)
    
    def restore_database(self, backup_file: str) -> bool:
        """
        Restore database from a backup.
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            bool: True if restored successfully
        """
        # Only works with SQLite
        if not self.database_url.startswith('sqlite:///'):
            logger.warning("Restore only supported for SQLite databases")
            return False
        
        if not os.path.exists(backup_file):
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        # Extract database file path
        db_path = self.database_url.replace('sqlite:///', '')
        
        # Close all connections
        self.engine.dispose()
        
        # Restore backup
        shutil.copy2(backup_file, db_path)
        
        # Reconnect
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Reinitialize repositories
        self._init_repositories()
        
        logger.info(f"Database restored from: {backup_file}")
        return True
    
    def verify_database(self) -> Dict[str, Any]:
        """
        Verify database integrity and return statistics.
        
        Returns:
            Dict: Database statistics
        """
        with self.get_session() as session:
            from src.database.schema import (
                Trade, Position, Prediction, Signal, 
                PerformanceMetric, BotState
            )
            
            stats = {
                'total_trades': session.query(Trade).count(),
                'open_trades': session.query(Trade).filter(Trade.status == 'open').count(),
                'closed_trades': session.query(Trade).filter(Trade.status == 'closed').count(),
                'active_positions': session.query(Position).count(),
                'total_predictions': session.query(Prediction).count(),
                'pending_signals': session.query(Signal).filter(Signal.status == 'pending').count(),
                'total_signals': session.query(Signal).count(),
                'performance_records': session.query(PerformanceMetric).count(),
                'bot_state_exists': session.query(BotState).count() > 0
            }
        
        logger.info(f"Database verification: {stats}")
        return stats


# Example usage
if __name__ == "__main__":
    """
    Example usage of DatabaseManager with repositories.
    
    Run this script to test database operations:
        python src/database/db_manager.py
    """
    from datetime import datetime, timedelta
    import json
    
    print("🚀 Testing Database Manager with Repositories...")
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Verify database
    print("\n📊 Database Statistics:")
    stats = db.verify_database()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test using repositories directly
    print("\n💰 Testing Trade Operations (via repository)...")
    trade_data = {
        'symbol': 'PLTR',
        'action': 'buy',
        'quantity': 10,
        'entry_price': 30.50,
        'stop_loss': 29.59,
        'entry_time': datetime.utcnow(),
        'status': 'open',
        'confidence_score': 0.85
    }
    
    trade_id = db.trades.save_trade(trade_data)
    print(f"  ✅ Created trade {trade_id} via repository")
    
    # Test using backward compatibility methods
    print("\n📈 Testing Position Operations (via db manager)...")
    position_data = {
        'symbol': 'PLTR',
        'quantity': 10,
        'entry_price': 30.50,
        'current_price': 31.00,
        'stop_loss': 29.59,
        'unrealized_pnl': 5.0,
        'unrealized_pnl_percent': 1.64,
        'entry_time': datetime.utcnow(),
        'trade_id': trade_id
    }
    
    position_id = db.save_position(position_data)
    print(f"  ✅ Created position {position_id} via db manager")
    
    # Test analytics
    print("\n📊 Testing Analytics (via analytics service)...")
    summary = db.analytics.get_performance_summary(days=30)
    print(f"  Total trades: {summary['total_trades']}")
    print(f"  Win rate: {summary['win_rate']:.1f}%")
    
    # Test backup
    print("\n💾 Testing Backup...")
    backup_file = db.backup_database()
    if backup_file:
        print(f"  ✅ Backup created: {backup_file}")
    
    print("\n✅ All tests completed successfully!")
    print("\n📌 Repository Pattern Implementation:")
    print("  - db.trades → TradeRepository")
    print("  - db.positions → PositionRepository")
    print("  - db.predictions → PredictionRepository")
    print("  - db.signals → SignalRepository")
    print("  - db.performance → PerformanceMetricsRepository")
    print("  - db.bot_state → BotStateRepository")
    print("  - db.analytics → AnalyticsService")
