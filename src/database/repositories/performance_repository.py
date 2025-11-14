"""
Performance Metrics Repository for database operations.

Handles all CRUD operations for PerformanceMetric entities.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import and_
from loguru import logger

from src.database.repositories.base_repository import BaseRepository
from src.database.schema import PerformanceMetric


class PerformanceMetricsRepository(BaseRepository):
    """Repository for PerformanceMetric entity operations."""
    
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
