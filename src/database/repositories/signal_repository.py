"""
Signal Repository for database operations.

Handles all CRUD operations for Signal entities.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from loguru import logger

from src.database.repositories.base_repository import BaseRepository
from src.database.schema import Signal


class SignalRepository(BaseRepository):
    """Repository for Signal entity operations."""
    
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
