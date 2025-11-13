"""
Database Manager for Trading Bot.

Provides a clean interface for all database operations including CRUD operations,
queries for analytics, and database maintenance functions.
"""

from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import os
import json
import shutil
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

from src.database.schema import (
    Base, Trade, Position, Prediction, Signal, 
    PerformanceMetric, BotState
)
from src.types.trading_types import (
    TradingSignal, Position as PositionType, TradeRecord,
    PerformanceMetrics, ModelPrediction, SignalType, OrderStatus
)

# Load environment variables
load_dotenv()


class DatabaseManager:
    """
    Database manager for all bot data operations.
    
    Provides CRUD operations, queries, and maintenance functions for all database tables.
    Uses context managers for safe transaction handling.
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize database manager.
        
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
        
        # Initialize bot state if needed
        self._init_bot_state()
        
        logger.info(f"Database manager initialized: {database_url}")
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.
        
        Automatically handles commit/rollback and session cleanup.
        
        Usage:
            with db_manager.get_session() as session:
                # perform operations
                session.add(trade)
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
    
    def _init_bot_state(self) -> None:
        """Initialize bot state if not exists."""
        with self.get_session() as session:
            state = session.query(BotState).first()
            if not state:
                state = BotState(
                    is_running=False,
                    trading_mode='hybrid',
                    daily_loss_limit_reached=False,
                    circuit_breaker_triggered=False
                )
                session.add(state)
                logger.info("Bot state initialized")
    
    # ==================== TRADE OPERATIONS ====================
    
    def save_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        Save a new trade to database.
        
        Args:
            trade_data: Dictionary with trade information
            
        Returns:
            int: Trade ID
        """
        with self.get_session() as session:
            trade = Trade(**trade_data)
            session.add(trade)
            session.flush()  # Get ID before commit
            trade_id = trade.id
            logger.info(f"Saved trade {trade_id}: {trade.symbol} {trade.action}")
            return trade_id
    
    def update_trade(self, trade_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update an existing trade.
        
        Args:
            trade_id: Trade ID to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if updated successfully
        """
        with self.get_session() as session:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                logger.warning(f"Trade {trade_id} not found")
                return False
            
            for key, value in updates.items():
                setattr(trade, key, value)
            
            trade.updated_at = datetime.utcnow()
            logger.info(f"Updated trade {trade_id}: {updates}")
            return True
    
    def get_trade_by_id(self, trade_id: int) -> Optional[Dict[str, Any]]:
        """
        Get trade by ID.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            Optional[Dict]: Trade data or None if not found
        """
        with self.get_session() as session:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                return None
            return self._trade_to_dict(trade)
    
    def get_trades_by_symbol(
        self, 
        symbol: str, 
        status: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get trades for a specific symbol.
        
        Args:
            symbol: Stock symbol
            status: Filter by status ('open', 'closed', or None for all)
            limit: Maximum number of trades to return
            
        Returns:
            List[Dict]: List of trade dictionaries
        """
        with self.get_session() as session:
            query = session.query(Trade).filter(Trade.symbol == symbol)
            
            if status:
                query = query.filter(Trade.status == status)
            
            trades = query.order_by(Trade.entry_time.desc()).limit(limit).all()
            return [self._trade_to_dict(t) for t in trades]
    
    def get_recent_trades(
        self, 
        days: int = 7,
        status: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent trades within specified days.
        
        Args:
            days: Number of days to look back
            status: Filter by status (optional)
            
        Returns:
            List[Dict]: List of trade dictionaries
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self.get_session() as session:
            query = session.query(Trade).filter(Trade.entry_time >= cutoff)
            
            if status:
                query = query.filter(Trade.status == status)
            
            trades = query.order_by(Trade.entry_time.desc()).all()
            return [self._trade_to_dict(t) for t in trades]
    
    def get_open_trades(self) -> List[Dict[str, Any]]:
        """
        Get all open trades.
        
        Returns:
            List[Dict]: List of open trade dictionaries
        """
        with self.get_session() as session:
            trades = session.query(Trade).filter(Trade.status == 'open').all()
            return [self._trade_to_dict(t) for t in trades]
    
    def close_trade(
        self, 
        trade_id: int, 
        exit_price: float, 
        realized_pnl: float
    ) -> bool:
        """
        Close a trade with exit information.
        
        Args:
            trade_id: Trade ID to close
            exit_price: Exit price
            realized_pnl: Realized profit/loss
            
        Returns:
            bool: True if closed successfully
        """
        updates = {
            'status': 'closed',
            'exit_price': exit_price,
            'exit_time': datetime.utcnow(),
            'realized_pnl': realized_pnl
        }
        return self.update_trade(trade_id, updates)
    
    @staticmethod
    def _trade_to_dict(trade: Trade) -> Dict[str, Any]:
        """Convert Trade object to dictionary."""
        return {
            'id': trade.id,
            'symbol': trade.symbol,
            'action': trade.action,
            'quantity': trade.quantity,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'stop_loss': trade.stop_loss,
            'trailing_stop': trade.trailing_stop,
            'entry_time': trade.entry_time,
            'exit_time': trade.exit_time,
            'status': trade.status,
            'unrealized_pnl': trade.unrealized_pnl,
            'realized_pnl': trade.realized_pnl,
            'confidence_score': trade.confidence_score,
            'signal_id': trade.signal_id,
            'created_at': trade.created_at,
            'updated_at': trade.updated_at
        }
    
    # ==================== POSITION OPERATIONS ====================
    
    def save_position(self, position_data: Dict[str, Any]) -> int:
        """
        Save or update a position.
        
        Args:
            position_data: Dictionary with position information
            
        Returns:
            int: Position ID
        """
        with self.get_session() as session:
            # Check if position already exists for this symbol
            existing = session.query(Position).filter(
                Position.symbol == position_data['symbol']
            ).first()
            
            if existing:
                # Update existing position
                for key, value in position_data.items():
                    setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                position_id = existing.id
                logger.info(f"Updated position {position_id}: {existing.symbol}")
            else:
                # Create new position
                position = Position(**position_data)
                session.add(position)
                session.flush()
                position_id = position.id
                logger.info(f"Created position {position_id}: {position.symbol}")
            
            return position_id
    
    def update_position_price(
        self, 
        symbol: str, 
        current_price: float,
        unrealized_pnl: float,
        unrealized_pnl_percent: float
    ) -> bool:
        """
        Update position with current price and P&L.
        
        Args:
            symbol: Stock symbol
            current_price: Current market price
            unrealized_pnl: Unrealized profit/loss
            unrealized_pnl_percent: Unrealized P&L percentage
            
        Returns:
            bool: True if updated successfully
        """
        with self.get_session() as session:
            position = session.query(Position).filter(Position.symbol == symbol).first()
            if not position:
                logger.warning(f"Position {symbol} not found")
                return False
            
            position.current_price = current_price
            position.unrealized_pnl = unrealized_pnl
            position.unrealized_pnl_percent = unrealized_pnl_percent
            position.updated_at = datetime.utcnow()
            
            return True
    
    def get_active_positions(self) -> List[Dict[str, Any]]:
        """
        Get all active positions.
        
        Returns:
            List[Dict]: List of active position dictionaries
        """
        with self.get_session() as session:
            positions = session.query(Position).all()
            return [self._position_to_dict(p) for p in positions]
    
    def get_position_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Optional[Dict]: Position data or None if not found
        """
        with self.get_session() as session:
            position = session.query(Position).filter(Position.symbol == symbol).first()
            if not position:
                return None
            return self._position_to_dict(position)
    
    def delete_position(self, symbol: str) -> bool:
        """
        Delete a position (when closed).
        
        Args:
            symbol: Stock symbol
            
        Returns:
            bool: True if deleted successfully
        """
        with self.get_session() as session:
            position = session.query(Position).filter(Position.symbol == symbol).first()
            if not position:
                logger.warning(f"Position {symbol} not found")
                return False
            
            session.delete(position)
            logger.info(f"Deleted position: {symbol}")
            return True
    
    @staticmethod
    def _position_to_dict(position: Position) -> Dict[str, Any]:
        """Convert Position object to dictionary."""
        return {
            'id': position.id,
            'symbol': position.symbol,
            'quantity': position.quantity,
            'entry_price': position.entry_price,
            'current_price': position.current_price,
            'stop_loss': position.stop_loss,
            'trailing_stop': position.trailing_stop,
            'unrealized_pnl': position.unrealized_pnl,
            'unrealized_pnl_percent': position.unrealized_pnl_percent,
            'entry_time': position.entry_time,
            'trade_id': position.trade_id,
            'created_at': position.created_at,
            'updated_at': position.updated_at
        }
    
    # ==================== PREDICTION OPERATIONS ====================
    
    def save_prediction(self, prediction_data: Dict[str, Any]) -> int:
        """
        Save an ML prediction.
        
        Args:
            prediction_data: Dictionary with prediction information
            
        Returns:
            int: Prediction ID
        """
        with self.get_session() as session:
            prediction = Prediction(**prediction_data)
            session.add(prediction)
            session.flush()
            prediction_id = prediction.id
            logger.debug(f"Saved prediction {prediction_id}: {prediction.symbol}")
            return prediction_id
    
    def update_prediction_actual(
        self, 
        prediction_id: int, 
        actual_price: float
    ) -> bool:
        """
        Update prediction with actual price (next day).
        
        Args:
            prediction_id: Prediction ID
            actual_price: Actual price that occurred
            
        Returns:
            bool: True if updated successfully
        """
        with self.get_session() as session:
            prediction = session.query(Prediction).filter(
                Prediction.id == prediction_id
            ).first()
            
            if not prediction:
                logger.warning(f"Prediction {prediction_id} not found")
                return False
            
            prediction.actual_price = actual_price
            
            # Calculate accuracy
            predicted_direction = prediction.direction
            actual_direction = 'up' if actual_price > prediction.predicted_price else 'down'
            prediction.accuracy = (predicted_direction == actual_direction)
            
            # Calculate error
            prediction.error = abs(actual_price - prediction.predicted_price)
            
            logger.debug(f"Updated prediction {prediction_id} with actual: {actual_price}")
            return True
    
    def get_predictions_by_symbol(
        self, 
        symbol: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get predictions for a specific symbol.
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of predictions to return
            
        Returns:
            List[Dict]: List of prediction dictionaries
        """
        with self.get_session() as session:
            predictions = session.query(Prediction).filter(
                Prediction.symbol == symbol
            ).order_by(Prediction.prediction_time.desc()).limit(limit).all()
            
            return [self._prediction_to_dict(p) for p in predictions]
    
    def get_recent_predictions(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get recent predictions within specified days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List[Dict]: List of prediction dictionaries
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self.get_session() as session:
            predictions = session.query(Prediction).filter(
                Prediction.prediction_time >= cutoff
            ).order_by(Prediction.prediction_time.desc()).all()
            
            return [self._prediction_to_dict(p) for p in predictions]
    
    def get_prediction_accuracy(self, days: int = 30) -> float:
        """
        Calculate prediction accuracy over a period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            float: Accuracy percentage (0-100)
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self.get_session() as session:
            total = session.query(Prediction).filter(
                and_(
                    Prediction.prediction_time >= cutoff,
                    Prediction.accuracy.isnot(None)
                )
            ).count()
            
            if total == 0:
                return 0.0
            
            correct = session.query(Prediction).filter(
                and_(
                    Prediction.prediction_time >= cutoff,
                    Prediction.accuracy == True
                )
            ).count()
            
            return (correct / total) * 100
    
    @staticmethod
    def _prediction_to_dict(prediction: Prediction) -> Dict[str, Any]:
        """Convert Prediction object to dictionary."""
        return {
            'id': prediction.id,
            'symbol': prediction.symbol,
            'predicted_price': prediction.predicted_price,
            'actual_price': prediction.actual_price,
            'direction': prediction.direction,
            'confidence': prediction.confidence,
            'model_name': prediction.model_name,
            'features_used': prediction.features_used,
            'prediction_time': prediction.prediction_time,
            'target_date': prediction.target_date,
            'accuracy': prediction.accuracy,
            'error': prediction.error,
            'prediction_metadata': prediction.prediction_metadata,
            'created_at': prediction.created_at
        }
    
    # ==================== SIGNAL OPERATIONS ====================
    
    def save_signal(self, signal_data: Dict[str, Any]) -> int:
        """
        Save a trading signal.
        
        Args:
            signal_data: Dictionary with signal information
            
        Returns:
            int: Signal ID
        """
        with self.get_session() as session:
            signal = Signal(**signal_data)
            session.add(signal)
            session.flush()
            signal_id = signal.id
            logger.info(f"Saved signal {signal_id}: {signal.symbol} {signal.signal_type}")
            return signal_id
    
    def update_signal_status(
        self, 
        signal_id: int, 
        status: str,
        **kwargs
    ) -> bool:
        """
        Update signal status and related fields.
        
        Args:
            signal_id: Signal ID
            status: New status ('approved', 'rejected', 'executed')
            **kwargs: Additional fields to update
            
        Returns:
            bool: True if updated successfully
        """
        with self.get_session() as session:
            signal = session.query(Signal).filter(Signal.id == signal_id).first()
            if not signal:
                logger.warning(f"Signal {signal_id} not found")
                return False
            
            signal.status = status
            
            if status == 'approved':
                signal.approved_at = datetime.utcnow()
            elif status == 'executed':
                signal.executed_at = datetime.utcnow()
            
            # Update additional fields
            for key, value in kwargs.items():
                setattr(signal, key, value)
            
            logger.info(f"Updated signal {signal_id} to status: {status}")
            return True
    
    def get_pending_signals(self) -> List[Dict[str, Any]]:
        """
        Get all pending signals awaiting approval.
        
        Returns:
            List[Dict]: List of pending signal dictionaries
        """
        with self.get_session() as session:
            signals = session.query(Signal).filter(
                Signal.status == 'pending'
            ).order_by(Signal.created_at.desc()).all()
            
            return [self._signal_to_dict(s) for s in signals]
    
    def get_signal_history(
        self, 
        days: int = 30,
        status: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get signal history.
        
        Args:
            days: Number of days to look back
            status: Filter by status (optional)
            
        Returns:
            List[Dict]: List of signal dictionaries
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self.get_session() as session:
            query = session.query(Signal).filter(Signal.created_at >= cutoff)
            
            if status:
                query = query.filter(Signal.status == status)
            
            signals = query.order_by(Signal.created_at.desc()).all()
            return [self._signal_to_dict(s) for s in signals]
    
    @staticmethod
    def _signal_to_dict(signal: Signal) -> Dict[str, Any]:
        """Convert Signal object to dictionary."""
        return {
            'id': signal.id,
            'symbol': signal.symbol,
            'signal_type': signal.signal_type,
            'confidence': signal.confidence,
            'predicted_direction': signal.predicted_direction,
            'status': signal.status,
            'quantity': signal.quantity,
            'entry_price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'features': signal.features,
            'created_at': signal.created_at,
            'approved_at': signal.approved_at,
            'executed_at': signal.executed_at,
            'rejected_reason': signal.rejected_reason,
            'trade_id': signal.trade_id
        }
    
    # ==================== PERFORMANCE METRICS OPERATIONS ====================
    
    def save_performance_metrics(self, metrics_data: Dict[str, Any]) -> int:
        """
        Save daily performance metrics.
        
        Args:
            metrics_data: Dictionary with performance metrics
            
        Returns:
            int: Metric ID
        """
        with self.get_session() as session:
            # Check if metrics for this date already exist
            existing = session.query(PerformanceMetric).filter(
                PerformanceMetric.date == metrics_data['date']
            ).first()
            
            if existing:
                # Update existing metrics
                for key, value in metrics_data.items():
                    setattr(existing, key, value)
                metric_id = existing.id
                logger.info(f"Updated performance metrics for {metrics_data['date']}")
            else:
                # Create new metrics
                metric = PerformanceMetric(**metrics_data)
                session.add(metric)
                session.flush()
                metric_id = metric.id
                logger.info(f"Saved performance metrics for {metrics_data['date']}")
            
            return metric_id
    
    def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent performance metrics.
        
        Returns:
            Optional[Dict]: Latest metrics or None
        """
        with self.get_session() as session:
            metric = session.query(PerformanceMetric).order_by(
                PerformanceMetric.date.desc()
            ).first()
            
            if not metric:
                return None
            
            return self._metric_to_dict(metric)
    
    def get_metrics_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List[Dict]: List of metric dictionaries
        """
        with self.get_session() as session:
            metrics = session.query(PerformanceMetric).filter(
                and_(
                    PerformanceMetric.date >= start_date,
                    PerformanceMetric.date <= end_date
                )
            ).order_by(PerformanceMetric.date.asc()).all()
            
            return [self._metric_to_dict(m) for m in metrics]
    
    @staticmethod
    def _metric_to_dict(metric: PerformanceMetric) -> Dict[str, Any]:
        """Convert PerformanceMetric object to dictionary."""
        return {
            'id': metric.id,
            'date': metric.date,
            'portfolio_value': metric.portfolio_value,
            'cash_available': metric.cash_available,
            'total_exposure': metric.total_exposure,
            'daily_pnl': metric.daily_pnl,
            'daily_pnl_percent': metric.daily_pnl_percent,
            'total_trades': metric.total_trades,
            'winning_trades': metric.winning_trades,
            'losing_trades': metric.losing_trades,
            'win_rate': metric.win_rate,
            'sharpe_ratio': metric.sharpe_ratio,
            'max_drawdown': metric.max_drawdown,
            'max_drawdown_percent': metric.max_drawdown_percent,
            'created_at': metric.created_at
        }
    
    # ==================== BOT STATE OPERATIONS ====================
    
    def get_bot_state(self) -> Dict[str, Any]:
        """
        Get current bot state.
        
        Returns:
            Dict: Bot state dictionary
        """
        with self.get_session() as session:
            state = session.query(BotState).first()
            if not state:
                # Initialize if not exists
                state = BotState(
                    is_running=False,
                    trading_mode='hybrid',
                    daily_loss_limit_reached=False,
                    circuit_breaker_triggered=False
                )
                session.add(state)
                session.flush()
            
            return self._bot_state_to_dict(state)
    
    def update_bot_state(self, updates: Dict[str, Any]) -> bool:
        """
        Update bot state.
        
        Args:
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if updated successfully
        """
        with self.get_session() as session:
            state = session.query(BotState).first()
            if not state:
                logger.warning("Bot state not found")
                return False
            
            for key, value in updates.items():
                setattr(state, key, value)
            
            state.updated_at = datetime.utcnow()
            logger.info(f"Updated bot state: {updates}")
            return True
    
    @staticmethod
    def _bot_state_to_dict(state: BotState) -> Dict[str, Any]:
        """Convert BotState object to dictionary."""
        return {
            'id': state.id,
            'is_running': state.is_running,
            'trading_mode': state.trading_mode,
            'last_trading_cycle': state.last_trading_cycle,
            'last_position_update': state.last_position_update,
            'daily_loss_limit_reached': state.daily_loss_limit_reached,
            'circuit_breaker_triggered': state.circuit_breaker_triggered,
            'error_message': state.error_message,
            'created_at': state.created_at,
            'updated_at': state.updated_at
        }
    
    # ==================== ANALYTICS & QUERIES ====================
    
    def get_trade_history(
        self,
        symbol: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        status: str = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get trade history with flexible filtering.
        
        Args:
            symbol: Filter by symbol (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            status: Filter by status (optional)
            limit: Maximum number of trades
            
        Returns:
            List[Dict]: List of trade dictionaries
        """
        with self.get_session() as session:
            query = session.query(Trade)
            
            if symbol:
                query = query.filter(Trade.symbol == symbol)
            
            if start_date:
                query = query.filter(Trade.entry_time >= start_date)
            
            if end_date:
                query = query.filter(Trade.entry_time <= end_date)
            
            if status:
                query = query.filter(Trade.status == status)
            
            trades = query.order_by(Trade.entry_time.desc()).limit(limit).all()
            return [self._trade_to_dict(t) for t in trades]
    
    def calculate_daily_performance(self, date: datetime) -> Dict[str, Any]:
        """
        Calculate performance metrics for a specific day.
        
        Args:
            date: Date to calculate metrics for
            
        Returns:
            Dict: Performance metrics
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        with self.get_session() as session:
            # Get all trades that closed on this day
            closed_trades = session.query(Trade).filter(
                and_(
                    Trade.exit_time >= start_of_day,
                    Trade.exit_time < end_of_day,
                    Trade.status == 'closed'
                )
            ).all()
            
            total_trades = len(closed_trades)
            if total_trades == 0:
                return {
                    'date': date,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0
                }
            
            winning_trades = [t for t in closed_trades if t.realized_pnl > 0]
            losing_trades = [t for t in closed_trades if t.realized_pnl <= 0]
            
            total_pnl = sum(t.realized_pnl for t in closed_trades)
            avg_win = sum(t.realized_pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t.realized_pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            return {
                'date': date,
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': (len(winning_trades) / total_trades) * 100,
                'total_pnl': total_pnl,
                'avg_win': avg_win,
                'avg_loss': avg_loss
            }
    
    def get_win_rate(self, days: int = 30) -> float:
        """
        Calculate win rate over a period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            float: Win rate percentage (0-100)
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self.get_session() as session:
            total_trades = session.query(Trade).filter(
                and_(
                    Trade.exit_time >= cutoff,
                    Trade.status == 'closed'
                )
            ).count()
            
            if total_trades == 0:
                return 0.0
            
            winning_trades = session.query(Trade).filter(
                and_(
                    Trade.exit_time >= cutoff,
                    Trade.status == 'closed',
                    Trade.realized_pnl > 0
                )
            ).count()
            
            return (winning_trades / total_trades) * 100
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict: Performance summary with all key metrics
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self.get_session() as session:
            # Get all closed trades in period
            trades = session.query(Trade).filter(
                and_(
                    Trade.exit_time >= cutoff,
                    Trade.status == 'closed'
                )
            ).all()
            
            if not trades:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'profit_factor': 0.0,
                    'largest_win': 0.0,
                    'largest_loss': 0.0,
                    'avg_hold_time_hours': 0.0
                }
            
            # Calculate metrics
            winning_trades = [t for t in trades if t.realized_pnl > 0]
            losing_trades = [t for t in trades if t.realized_pnl <= 0]
            
            total_wins = sum(t.realized_pnl for t in winning_trades)
            total_losses = abs(sum(t.realized_pnl for t in losing_trades))
            
            # Hold time calculation
            hold_times = []
            for t in trades:
                if t.exit_time and t.entry_time:
                    duration = (t.exit_time - t.entry_time).total_seconds() / 3600
                    hold_times.append(duration)
            
            return {
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': (len(winning_trades) / len(trades)) * 100,
                'total_pnl': sum(t.realized_pnl for t in trades),
                'avg_win': total_wins / len(winning_trades) if winning_trades else 0,
                'avg_loss': total_losses / len(losing_trades) if losing_trades else 0,
                'profit_factor': total_wins / total_losses if total_losses > 0 else 0,
                'largest_win': max((t.realized_pnl for t in winning_trades), default=0),
                'largest_loss': min((t.realized_pnl for t in trades), default=0),
                'avg_hold_time_hours': sum(hold_times) / len(hold_times) if hold_times else 0
            }
    
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
        
        logger.info(f"Database restored from: {backup_file}")
        return True
    
    def verify_database(self) -> Dict[str, Any]:
        """
        Verify database integrity and return statistics.
        
        Returns:
            Dict: Database statistics
        """
        with self.get_session() as session:
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
    Example usage of DatabaseManager.
    
    Run this script to test database operations:
        python src/database/db_manager.py
    """
    from datetime import datetime
    import json
    
    print("🚀 Testing Database Manager...")
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Verify database
    print("\n📊 Database Statistics:")
    stats = db.verify_database()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test trade operations
    print("\n💰 Testing Trade Operations...")
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
    
    trade_id = db.save_trade(trade_data)
    print(f"  ✅ Created trade {trade_id}")
    
    # Update trade
    db.update_trade(trade_id, {'unrealized_pnl': 50.0})
    print(f"  ✅ Updated trade {trade_id}")
    
    # Get trade
    trade = db.get_trade_by_id(trade_id)
    print(f"  ✅ Retrieved trade: {trade['symbol']} @ ${trade['entry_price']}")
    
    # Test position operations
    print("\n📈 Testing Position Operations...")
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
    print(f"  ✅ Created position {position_id}")
    
    # Test signal operations
    print("\n🔔 Testing Signal Operations...")
    signal_data = {
        'symbol': 'PLTR',
        'signal_type': 'buy',
        'confidence': 0.85,
        'predicted_direction': 'up',
        'status': 'pending',
        'features': json.dumps({'rsi': 35, 'macd': 0.5})
    }
    
    signal_id = db.save_signal(signal_data)
    print(f"  ✅ Created signal {signal_id}")
    
    # Test prediction operations
    print("\n🔮 Testing Prediction Operations...")
    prediction_data = {
        'symbol': 'PLTR',
        'predicted_price': 32.00,
        'direction': 'up',
        'confidence': 0.85,
        'model_name': 'LSTM',
        'features_used': json.dumps(['rsi', 'macd', 'volume']),
        'prediction_time': datetime.utcnow(),
        'target_date': datetime.utcnow() + timedelta(days=1)
    }
    
    pred_id = db.save_prediction(prediction_data)
    print(f"  ✅ Created prediction {pred_id}")
    
    # Test bot state
    print("\n🤖 Testing Bot State...")
    state = db.get_bot_state()
    print(f"  Bot running: {state['is_running']}")
    print(f"  Trading mode: {state['trading_mode']}")
    
    db.update_bot_state({'is_running': True})
    state = db.get_bot_state()
    print(f"  ✅ Updated bot state: running={state['is_running']}")
    
    # Test analytics
    print("\n📊 Testing Analytics...")
    pending_signals = db.get_pending_signals()
    print(f"  Pending signals: {len(pending_signals)}")
    
    active_positions = db.get_active_positions()
    print(f"  Active positions: {len(active_positions)}")
    
    open_trades = db.get_open_trades()
    print(f"  Open trades: {len(open_trades)}")
    
    # Test backup
    print("\n💾 Testing Backup...")
    backup_file = db.backup_database()
    if backup_file:
        print(f"  ✅ Backup created: {backup_file}")
    
    print("\n✅ All tests completed successfully!")
    print("\nDatabase is ready for use with the trading bot.")
