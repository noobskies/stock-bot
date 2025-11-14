"""
Data conversion utilities for transforming between different data formats.

This module provides converter classes that eliminate duplicate conversion logic
throughout the codebase, particularly for Alpaca API responses and database entities.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from src.bot_types.trading_types import Position, OrderStatus
from src.common.converter_types import AlpacaPositionDTO, AlpacaOrderDTO


class AlpacaConverter:
    """
    Converter for Alpaca API responses to internal data types.
    
    Centralizes all Alpaca-to-internal conversions to eliminate duplicate
    conversion logic found in executor.py and position_manager.py.
    """
    
    @staticmethod
    def to_position(alpaca_position: Any) -> Position:
        """
        Convert Alpaca position object to internal Position type.
        
        Args:
            alpaca_position: Alpaca position object (can be dict or object)
            
        Returns:
            Position object with converted data
            
        Example:
            position = AlpacaConverter.to_position(alpaca_api_response)
        """
        # Handle both dict and object responses from Alpaca
        if isinstance(alpaca_position, dict):
            symbol = alpaca_position.get('symbol', '')
            quantity = int(alpaca_position.get('qty', 0))
            entry_price = float(alpaca_position.get('avg_entry_price', 0.0))
            current_price = float(alpaca_position.get('current_price', 0.0))
            unrealized_pl = float(alpaca_position.get('unrealized_pl', 0.0))
            unrealized_plpc = float(alpaca_position.get('unrealized_plpc', 0.0))
        else:
            # Object with attributes
            symbol = getattr(alpaca_position, 'symbol', '')
            quantity = int(getattr(alpaca_position, 'qty', 0))
            entry_price = float(getattr(alpaca_position, 'avg_entry_price', 0.0))
            current_price = float(getattr(alpaca_position, 'current_price', 0.0))
            unrealized_pl = float(getattr(alpaca_position, 'unrealized_pl', 0.0))
            unrealized_plpc = float(getattr(alpaca_position, 'unrealized_plpc', 0.0))
        
        # Calculate market value
        market_value = current_price * quantity
        
        return Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price,
            market_value=market_value,
            unrealized_pl=unrealized_pl,
            unrealized_plpc=unrealized_plpc,
            stop_loss=entry_price * 0.97,  # Default 3% stop loss
            trailing_stop=None,
            entry_time=datetime.now(),
        )
    
    @staticmethod
    def to_order_status(alpaca_order: Any) -> OrderStatus:
        """
        Convert Alpaca order object to internal OrderStatus type.
        
        Args:
            alpaca_order: Alpaca order object (can be dict or object)
            
        Returns:
            OrderStatus enum value
            
        Example:
            status = AlpacaConverter.to_order_status(alpaca_order_response)
        """
        # Handle both dict and object responses
        if isinstance(alpaca_order, dict):
            status_str = alpaca_order.get('status', '').lower()
        else:
            status_str = getattr(alpaca_order, 'status', '').lower()
        
        # Map Alpaca statuses to internal OrderStatus enum
        status_mapping = {
            'new': OrderStatus.PENDING,
            'pending_new': OrderStatus.PENDING,
            'accepted': OrderStatus.PENDING,
            'partially_filled': OrderStatus.PARTIAL,
            'filled': OrderStatus.FILLED,
            'done_for_day': OrderStatus.FILLED,
            'canceled': OrderStatus.CANCELED,
            'cancelled': OrderStatus.CANCELED,
            'expired': OrderStatus.CANCELED,
            'replaced': OrderStatus.CANCELED,
            'pending_cancel': OrderStatus.CANCELED,
            'pending_replace': OrderStatus.PENDING,
            'rejected': OrderStatus.FAILED,
            'suspended': OrderStatus.FAILED,
        }
        
        return status_mapping.get(status_str, OrderStatus.FAILED)
    
    @staticmethod
    def from_position(position: Position) -> AlpacaPositionDTO:
        """
        Convert internal Position to Alpaca DTO format.
        
        Args:
            position: Internal Position object
            
        Returns:
            AlpacaPositionDTO with string-formatted values
            
        Example:
            dto = AlpacaConverter.from_position(position)
        """
        return AlpacaPositionDTO(
            symbol=position.symbol,
            qty=str(position.quantity),
            avg_entry_price=f"{position.entry_price:.2f}",
            current_price=f"{position.current_price:.2f}",
            market_value=f"{position.market_value:.2f}",
            unrealized_pl=f"{position.unrealized_pl:.2f}",
            unrealized_plpc=f"{position.unrealized_plpc:.4f}",
        )
    
    @staticmethod
    def extract_order_details(alpaca_order: Any) -> Dict[str, Any]:
        """
        Extract order details from Alpaca order response.
        
        Args:
            alpaca_order: Alpaca order object
            
        Returns:
            Dictionary with order details
        """
        # Handle both dict and object responses
        if isinstance(alpaca_order, dict):
            return {
                'order_id': alpaca_order.get('id', ''),
                'symbol': alpaca_order.get('symbol', ''),
                'quantity': int(alpaca_order.get('qty', 0)),
                'side': alpaca_order.get('side', ''),
                'type': alpaca_order.get('type', ''),
                'status': alpaca_order.get('status', ''),
                'filled_qty': int(alpaca_order.get('filled_qty', 0)),
                'filled_avg_price': float(alpaca_order.get('filled_avg_price', 0.0)) if alpaca_order.get('filled_avg_price') else None,
            }
        else:
            return {
                'order_id': getattr(alpaca_order, 'id', ''),
                'symbol': getattr(alpaca_order, 'symbol', ''),
                'quantity': int(getattr(alpaca_order, 'qty', 0)),
                'side': getattr(alpaca_order, 'side', ''),
                'type': getattr(alpaca_order, 'type', ''),
                'status': getattr(alpaca_order, 'status', ''),
                'filled_qty': int(getattr(alpaca_order, 'filled_qty', 0)),
                'filled_avg_price': float(getattr(alpaca_order, 'filled_avg_price', 0.0)) if getattr(alpaca_order, 'filled_avg_price', None) else None,
            }


class DatabaseConverter:
    """
    Converter for database entities to internal data types.
    
    Centralizes all database-to-internal conversions to eliminate duplicate
    logic in db_manager.py and various modules.
    """
    
    @staticmethod
    def position_to_dict(position: Position) -> Dict[str, Any]:
        """
        Convert Position object to database dictionary.
        
        Args:
            position: Position object to convert
            
        Returns:
            Dictionary suitable for database insertion
            
        Example:
            data = DatabaseConverter.position_to_dict(position)
            db.save_position(data)
        """
        return {
            'symbol': position.symbol,
            'quantity': position.quantity,
            'entry_price': position.entry_price,
            'current_price': position.current_price,
            'market_value': position.market_value,
            'unrealized_pl': position.unrealized_pl,
            'unrealized_plpc': position.unrealized_plpc,
            'stop_loss': position.stop_loss,
            'trailing_stop': position.trailing_stop,
            'entry_time': position.entry_time,
        }
    
    @staticmethod
    def dict_to_position(data: Dict[str, Any]) -> Position:
        """
        Convert database dictionary to Position object.
        
        Args:
            data: Dictionary from database query
            
        Returns:
            Position object with data from dictionary
            
        Example:
            position = DatabaseConverter.dict_to_position(db_result)
        """
        return Position(
            symbol=data.get('symbol', ''),
            quantity=data.get('quantity', 0),
            entry_price=data.get('entry_price', 0.0),
            current_price=data.get('current_price', 0.0),
            market_value=data.get('market_value', 0.0),
            unrealized_pl=data.get('unrealized_pl', 0.0),
            unrealized_plpc=data.get('unrealized_plpc', 0.0),
            stop_loss=data.get('stop_loss'),
            trailing_stop=data.get('trailing_stop'),
            entry_time=data.get('entry_time', datetime.now()),
        )
    
    @staticmethod
    def trade_to_dict(
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Convert trade parameters to database dictionary.
        
        Args:
            symbol: Stock symbol
            action: "buy" or "sell"
            quantity: Number of shares
            price: Execution price
            **kwargs: Additional trade details
            
        Returns:
            Dictionary suitable for database insertion
            
        Example:
            data = DatabaseConverter.trade_to_dict("PLTR", "buy", 50, 30.0)
            db.save_trade(data)
        """
        base_dict = {
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'timestamp': kwargs.get('timestamp', datetime.now()),
        }
        
        # Add optional fields if provided
        optional_fields = [
            'order_id', 'confidence', 'stop_loss', 'take_profit',
            'profit_loss', 'exit_price', 'exit_time', 'exit_reason'
        ]
        
        for field in optional_fields:
            if field in kwargs:
                base_dict[field] = kwargs[field]
        
        return base_dict


class ConverterRegistry:
    """
    Registry for custom converter functions.
    
    Allows registering domain-specific converters for extensibility.
    """
    
    _converters: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, name: str, converter: Any) -> None:
        """
        Register a custom converter.
        
        Args:
            name: Name for the converter
            converter: Converter function or class
        """
        cls._converters[name] = converter
    
    @classmethod
    def get(cls, name: str) -> Optional[Any]:
        """
        Get a registered converter by name.
        
        Args:
            name: Name of the converter
            
        Returns:
            Converter function/class or None if not found
        """
        return cls._converters.get(name)
    
    @classmethod
    def list_converters(cls) -> list[str]:
        """
        List all registered converter names.
        
        Returns:
            List of converter names
        """
        return list(cls._converters.keys())
