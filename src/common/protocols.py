"""
Protocol definitions for loose coupling and dependency inversion.

This module defines Protocol classes (structural subtyping) that allow
components to depend on abstractions rather than concrete implementations.
This follows the Dependency Inversion Principle (SOLID).
"""

from typing import Protocol, List, Optional, Dict, Any, Tuple
import pandas as pd
from src.bot_types.trading_types import Position, TradingSignal


class OrderExecutor(Protocol):
    """
    Protocol for order execution implementations.
    
    Any class that implements these methods can be used as an order executor,
    enabling easy swapping between different brokers or testing with mocks.
    """
    
    def place_market_order(
        self, 
        symbol: str, 
        quantity: int, 
        side: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Place a market order.
        
        Args:
            symbol: Stock symbol (e.g., "PLTR")
            quantity: Number of shares to trade
            side: "buy" or "sell"
            
        Returns:
            Tuple of (success, order_id, error_message)
        """
        ...
    
    def place_limit_order(
        self, 
        symbol: str, 
        quantity: int, 
        side: str, 
        limit_price: float
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Place a limit order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            side: "buy" or "sell"
            limit_price: Limit price for the order
            
        Returns:
            Tuple of (success, order_id, error_message)
        """
        ...
    
    def cancel_order(self, order_id: str) -> Tuple[bool, Optional[str]]:
        """
        Cancel an open order.
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            Tuple of (success, error_message)
        """
        ...
    
    def get_open_positions(self) -> List[Position]:
        """
        Get all open positions.
        
        Returns:
            List of Position objects
        """
        ...


class DataProvider(Protocol):
    """
    Protocol for market data provider implementations.
    
    Allows swapping between different data sources (Alpaca, Yahoo Finance, etc.)
    without changing dependent code.
    """
    
    def fetch_historical_data(
        self, 
        symbol: str, 
        days: int
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV data.
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data
            
        Returns:
            DataFrame with columns: open, high, low, close, volume, timestamp
            or None if fetch fails
        """
        ...
    
    def fetch_latest_price(self, symbol: str) -> Optional[float]:
        """
        Fetch the latest price for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest price or None if unavailable
        """
        ...
    
    def is_market_open(self) -> bool:
        """
        Check if the market is currently open.
        
        Returns:
            True if market is open, False otherwise
        """
        ...


class RepositoryProtocol(Protocol):
    """
    Protocol for data persistence implementations.
    
    Defines the standard interface for repository pattern,
    allowing different storage backends (SQLite, PostgreSQL, etc.)
    """
    
    def save(self, entity: Dict[str, Any]) -> int:
        """
        Save a new entity to the repository.
        
        Args:
            entity: Dictionary representing the entity
            
        Returns:
            ID of the saved entity
        """
        ...
    
    def update(self, id: int, updates: Dict[str, Any]) -> bool:
        """
        Update an existing entity.
        
        Args:
            id: Entity ID
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        ...
    
    def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Find an entity by its ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Entity dictionary or None if not found
        """
        ...
    
    def delete(self, id: int) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            id: Entity ID
            
        Returns:
            True if successful, False otherwise
        """
        ...
