"""
Data Transfer Object (DTO) type definitions for converters.

This module defines DTO classes used for converting between external
API formats (Alpaca) and internal data structures.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AlpacaPositionDTO:
    """
    Data Transfer Object for Alpaca position responses.
    
    Represents the structure of position data returned from Alpaca API.
    Used to standardize conversion to internal Position type.
    """
    
    symbol: str
    qty: str                    # Quantity as string (Alpaca format)
    avg_entry_price: str       # Average entry price as string
    current_price: str         # Current market price as string
    market_value: str          # Total market value as string
    unrealized_pl: str         # Unrealized P&L as string
    unrealized_plpc: str       # Unrealized P&L percentage as string
    
    # Optional fields that may be present
    side: Optional[str] = None          # "long" or "short"
    exchange: Optional[str] = None      # Exchange where position is held
    asset_id: Optional[str] = None      # Alpaca asset ID
    asset_class: Optional[str] = None   # "us_equity", etc.


@dataclass
class AlpacaOrderDTO:
    """
    Data Transfer Object for Alpaca order responses.
    
    Represents the structure of order data returned from Alpaca API.
    Used to standardize conversion to internal OrderStatus type.
    """
    
    id: str                    # Order ID
    symbol: str                # Stock symbol
    qty: str                   # Quantity as string
    side: str                  # "buy" or "sell"
    type: str                  # "market", "limit", "stop", "stop_limit"
    status: str                # "new", "filled", "canceled", etc.
    
    # Optional fields
    filled_qty: Optional[str] = None        # Filled quantity
    filled_avg_price: Optional[str] = None  # Average fill price
    limit_price: Optional[str] = None       # Limit price (if limit order)
    stop_price: Optional[str] = None        # Stop price (if stop order)
    time_in_force: Optional[str] = None     # "day", "gtc", "ioc", "fok"
    created_at: Optional[str] = None        # ISO timestamp
    updated_at: Optional[str] = None        # ISO timestamp
    filled_at: Optional[str] = None         # ISO timestamp
    canceled_at: Optional[str] = None       # ISO timestamp
    failed_at: Optional[str] = None         # ISO timestamp
