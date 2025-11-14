"""
Position Repository for database operations.

Handles all CRUD operations for Position entities.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from loguru import logger

from src.database.repositories.base_repository import BaseRepository
from src.database.schema import Position


class PositionRepository(BaseRepository):
    """Repository for Position entity operations."""
    
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
