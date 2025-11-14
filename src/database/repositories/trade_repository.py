"""
Trade Repository for database operations.

Handles all CRUD operations for Trade entities.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from loguru import logger

from src.database.repositories.base_repository import BaseRepository
from src.database.schema import Trade


class TradeRepository(BaseRepository):
    """Repository for Trade entity operations."""
    
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
