"""
Bot State Repository for database operations.

Handles all CRUD operations for BotState entity.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from loguru import logger

from src.database.repositories.base_repository import BaseRepository
from src.database.schema import BotState


class BotStateRepository(BaseRepository):
    """Repository for BotState entity operations."""
    
    def init_bot_state(self) -> None:
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
