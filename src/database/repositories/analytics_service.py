"""
Analytics Service for complex database queries and calculations.

Handles analytics, reporting, and complex queries across multiple entities.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from sqlalchemy import and_
from loguru import logger

from src.database.repositories.base_repository import BaseRepository
from src.database.schema import Trade


class AnalyticsService(BaseRepository):
    """Service for analytics and complex database queries."""
    
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
