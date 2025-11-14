"""
Alpaca API Executor - Order execution via Alpaca broker API.

This module handles all broker interactions for order placement, cancellation,
and status tracking. It wraps the Alpaca API to provide a clean interface for
the trading bot.

Key Features:
- Market and limit order execution
- Order status tracking
- Position querying
- Account information retrieval
- Paper and live trading support
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    GetOrdersRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus as AlpacaOrderStatus, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from loguru import logger

from src.bot_types.trading_types import OrderStatus, Position, PositionStatus


class AlpacaExecutor:
    """
    Alpaca API wrapper for order execution and position management.
    
    This class provides a clean interface for interacting with the Alpaca
    broker API, handling authentication, order placement, and error handling.
    
    Attributes:
        is_paper: Whether using paper trading (True) or live trading (False)
        trading_client: Alpaca trading client for orders and positions
        data_client: Alpaca data client for market data
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        is_paper: bool = True
    ):
        """
        Initialize Alpaca API executor.
        
        Args:
            api_key: Alpaca API key (if None, loads from environment)
            secret_key: Alpaca secret key (if None, loads from environment)
            is_paper: Use paper trading (True) or live trading (False)
        
        Raises:
            ValueError: If API credentials are missing
        """
        # Load credentials from environment if not provided
        if api_key is None:
            api_key = os.getenv('ALPACA_API_KEY')
        if secret_key is None:
            secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        if not api_key or not secret_key:
            raise ValueError(
                "Alpaca API credentials not found. Set ALPACA_API_KEY and "
                "ALPACA_SECRET_KEY environment variables or pass them explicitly."
            )
        
        self.is_paper = is_paper
        
        # Initialize Alpaca trading client
        self.trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=is_paper
        )
        
        # Initialize Alpaca data client (no auth needed for free tier)
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
        
        logger.info(
            f"AlpacaExecutor initialized - "
            f"Mode: {'PAPER' if is_paper else 'LIVE'} trading"
        )
    
    def get_account(self) -> Dict:
        """
        Get account information including buying power and equity.
        
        Returns:
            Dict with account details:
                - buying_power: Available buying power
                - equity: Total account equity
                - cash: Cash balance
                - portfolio_value: Total portfolio value
                - pattern_day_trader: PDT status
        
        Raises:
            Exception: If API call fails
        """
        try:
            account = self.trading_client.get_account()
            
            return {
                'buying_power': float(account.buying_power),
                'equity': float(account.equity),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'pattern_day_trader': account.pattern_day_trader,
                'daytrade_count': account.daytrade_count,
                'last_equity': float(account.last_equity)
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    def place_market_order(
        self,
        symbol: str,
        quantity: int,
        side: str,
        time_in_force: str = 'day'
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Place a market order.
        
        Args:
            symbol: Stock symbol (e.g., 'PLTR')
            quantity: Number of shares
            side: 'buy' or 'sell'
            time_in_force: Order duration ('day', 'gtc', 'ioc', 'fok')
        
        Returns:
            Tuple of (success, order_id, error_message)
        
        Example:
            success, order_id, error = executor.place_market_order(
                'PLTR', 10, 'buy'
            )
        """
        try:
            # Convert side to Alpaca enum
            order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
            
            # Convert time_in_force to Alpaca enum
            tif_map = {
                'day': TimeInForce.DAY,
                'gtc': TimeInForce.GTC,
                'ioc': TimeInForce.IOC,
                'fok': TimeInForce.FOK
            }
            tif = tif_map.get(time_in_force.lower(), TimeInForce.DAY)
            
            # Create market order request
            request = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=tif
            )
            
            # Submit order
            order = self.trading_client.submit_order(request)
            
            logger.info(
                f"Market order placed: {side.upper()} {quantity} {symbol} "
                f"(Order ID: {order.id})"
            )
            
            return True, order.id, None
            
        except Exception as e:
            error_msg = f"Failed to place market order: {e}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def place_limit_order(
        self,
        symbol: str,
        quantity: int,
        side: str,
        limit_price: float,
        time_in_force: str = 'day'
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Place a limit order.
        
        Args:
            symbol: Stock symbol (e.g., 'PLTR')
            quantity: Number of shares
            side: 'buy' or 'sell'
            limit_price: Limit price for the order
            time_in_force: Order duration ('day', 'gtc', 'ioc', 'fok')
        
        Returns:
            Tuple of (success, order_id, error_message)
        
        Example:
            success, order_id, error = executor.place_limit_order(
                'PLTR', 10, 'buy', 30.50
            )
        """
        try:
            # Convert side to Alpaca enum
            order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
            
            # Convert time_in_force to Alpaca enum
            tif_map = {
                'day': TimeInForce.DAY,
                'gtc': TimeInForce.GTC,
                'ioc': TimeInForce.IOC,
                'fok': TimeInForce.FOK
            }
            tif = tif_map.get(time_in_force.lower(), TimeInForce.DAY)
            
            # Create limit order request
            request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=tif,
                limit_price=limit_price
            )
            
            # Submit order
            order = self.trading_client.submit_order(request)
            
            logger.info(
                f"Limit order placed: {side.upper()} {quantity} {symbol} "
                f"@ ${limit_price:.2f} (Order ID: {order.id})"
            )
            
            return True, order.id, None
            
        except Exception as e:
            error_msg = f"Failed to place limit order: {e}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def cancel_order(self, order_id: str) -> Tuple[bool, Optional[str]]:
        """
        Cancel a pending order.
        
        Args:
            order_id: Alpaca order ID
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True, None
        except Exception as e:
            error_msg = f"Failed to cancel order {order_id}: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_order_status(self, order_id: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Get status of an order.
        
        Args:
            order_id: Alpaca order ID
        
        Returns:
            Tuple of (status, order_details)
            status: One of 'pending', 'filled', 'cancelled', 'rejected', 'expired'
            order_details: Dict with order information
        """
        try:
            order = self.trading_client.get_order_by_id(order_id)
            
            # Map Alpaca status to our OrderStatus enum
            status_map = {
                AlpacaOrderStatus.NEW: 'pending',
                AlpacaOrderStatus.PARTIALLY_FILLED: 'pending',
                AlpacaOrderStatus.FILLED: 'filled',
                AlpacaOrderStatus.DONE_FOR_DAY: 'pending',
                AlpacaOrderStatus.CANCELED: 'cancelled',
                AlpacaOrderStatus.EXPIRED: 'expired',
                AlpacaOrderStatus.REPLACED: 'pending',
                AlpacaOrderStatus.PENDING_CANCEL: 'cancelled',
                AlpacaOrderStatus.PENDING_REPLACE: 'pending',
                AlpacaOrderStatus.ACCEPTED: 'pending',
                AlpacaOrderStatus.PENDING_NEW: 'pending',
                AlpacaOrderStatus.ACCEPTED_FOR_BIDDING: 'pending',
                AlpacaOrderStatus.STOPPED: 'cancelled',
                AlpacaOrderStatus.REJECTED: 'rejected',
                AlpacaOrderStatus.SUSPENDED: 'cancelled',
                AlpacaOrderStatus.CALCULATED: 'pending',
            }
            
            status = status_map.get(order.status, 'pending')
            
            # Build order details dictionary
            details = {
                'order_id': order.id,
                'symbol': order.symbol,
                'quantity': int(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'status': status,
                'filled_qty': int(order.filled_qty) if order.filled_qty else 0,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None,
                'limit_price': float(order.limit_price) if order.limit_price else None,
                'stop_price': float(order.stop_price) if order.stop_price else None,
                'submitted_at': order.submitted_at,
                'filled_at': order.filled_at,
                'cancelled_at': order.cancelled_at,
                'expired_at': order.expired_at,
                'time_in_force': order.time_in_force.value
            }
            
            return status, details
            
        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            return None, None
    
    def get_open_positions(self) -> List[Position]:
        """
        Get all open positions from Alpaca.
        
        Returns:
            List of Position objects
        """
        try:
            positions = self.trading_client.get_all_positions()
            
            position_list = []
            for pos in positions:
                position = Position(
                    symbol=pos.symbol,
                    quantity=int(pos.qty),
                    entry_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price),
                    market_value=float(pos.market_value),
                    unrealized_pnl=float(pos.unrealized_pl),
                    unrealized_pnl_percent=float(pos.unrealized_plpc) * 100,
                    status=PositionStatus.OPEN,
                    entry_time=datetime.now(timezone.utc),  # Alpaca doesn't provide this
                    stop_loss_price=None,  # Set separately by stop_loss_manager
                    trailing_stop_price=None
                )
                position_list.append(position)
            
            logger.info(f"Retrieved {len(position_list)} open positions")
            return position_list
            
        except Exception as e:
            logger.error(f"Failed to get open positions: {e}")
            return []
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get a specific position by symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'PLTR')
        
        Returns:
            Position object or None if not found
        """
        try:
            pos = self.trading_client.get_open_position(symbol)
            
            position = Position(
                symbol=pos.symbol,
                quantity=int(pos.qty),
                entry_price=float(pos.avg_entry_price),
                current_price=float(pos.current_price),
                market_value=float(pos.market_value),
                unrealized_pnl=float(pos.unrealized_pl),
                unrealized_pnl_percent=float(pos.unrealized_plpc) * 100,
                status=PositionStatus.OPEN,
                entry_time=datetime.now(timezone.utc),
                stop_loss_price=None,
                trailing_stop_price=None
            )
            
            return position
            
        except Exception as e:
            # Position not found is not an error
            if "position does not exist" in str(e).lower():
                return None
            logger.error(f"Failed to get position for {symbol}: {e}")
            return None
    
    def close_position(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Close an entire position (market sell all shares).
        
        Args:
            symbol: Stock symbol (e.g., 'PLTR')
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Alpaca provides a convenient close_position endpoint
            self.trading_client.close_position(symbol)
            logger.info(f"Position closed: {symbol}")
            return True, None
        except Exception as e:
            error_msg = f"Failed to close position {symbol}: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_open_orders(self) -> List[Dict]:
        """
        Get all open (pending) orders.
        
        Returns:
            List of order dictionaries
        """
        try:
            # Create request for open orders only
            request = GetOrdersRequest(
                status=QueryOrderStatus.OPEN
            )
            orders = self.trading_client.get_orders(request)
            
            order_list = []
            for order in orders:
                order_dict = {
                    'order_id': order.id,
                    'symbol': order.symbol,
                    'quantity': int(order.qty),
                    'side': order.side.value,
                    'type': order.type.value,
                    'limit_price': float(order.limit_price) if order.limit_price else None,
                    'stop_price': float(order.stop_price) if order.stop_price else None,
                    'submitted_at': order.submitted_at,
                    'time_in_force': order.time_in_force.value
                }
                order_list.append(order_dict)
            
            logger.info(f"Retrieved {len(order_list)} open orders")
            return order_list
            
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    def cancel_all_orders(self) -> Tuple[bool, Optional[str]]:
        """
        Cancel all open orders.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.trading_client.cancel_orders()
            logger.info("All orders cancelled")
            return True, None
        except Exception as e:
            error_msg = f"Failed to cancel all orders: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest price for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'PLTR')
        
        Returns:
            Latest price or None if unavailable
        """
        try:
            # Try to get from open position first (faster)
            position = self.get_position(symbol)
            if position:
                return position.current_price
            
            # Otherwise get latest trade from data client
            # This requires using the data API which we'll keep simple
            from alpaca.data.requests import StockLatestQuoteRequest
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self.data_client.get_stock_latest_quote(request)
            
            if symbol in quote:
                return float(quote[symbol].ask_price)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest price for {symbol}: {e}")
            return None


# Example usage
if __name__ == "__main__":
    """
    Example usage of the AlpacaExecutor.
    
    This demonstrates:
    - Initializing the executor
    - Getting account information
    - Placing orders
    - Checking order status
    - Managing positions
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize executor (paper trading by default)
    executor = AlpacaExecutor(is_paper=True)
    
    # Get account info
    print("\n=== Account Information ===")
    account = executor.get_account()
    print(f"Buying Power: ${account['buying_power']:,.2f}")
    print(f"Portfolio Value: ${account['portfolio_value']:,.2f}")
    print(f"Cash: ${account['cash']:,.2f}")
    print(f"Pattern Day Trader: {account['pattern_day_trader']}")
    
    # Place a market order (example - commented out for safety)
    # success, order_id, error = executor.place_market_order('PLTR', 1, 'buy')
    # if success:
    #     print(f"\nOrder placed successfully: {order_id}")
    #     
    #     # Wait a moment for order to process
    #     import time
    #     time.sleep(2)
    #     
    #     # Check order status
    #     status, details = executor.get_order_status(order_id)
    #     print(f"Order status: {status}")
    #     print(f"Filled quantity: {details['filled_qty']}")
    #     print(f"Filled price: ${details['filled_avg_price']}")
    # else:
    #     print(f"\nOrder failed: {error}")
    
    # Get open positions
    print("\n=== Open Positions ===")
    positions = executor.get_open_positions()
    if positions:
        for pos in positions:
            print(f"\n{pos.symbol}:")
            print(f"  Quantity: {pos.quantity}")
            print(f"  Entry: ${pos.entry_price:.2f}")
            print(f"  Current: ${pos.current_price:.2f}")
            print(f"  P&L: ${pos.unrealized_pnl:.2f} ({pos.unrealized_pnl_percent:.2f}%)")
    else:
        print("No open positions")
    
    # Get open orders
    print("\n=== Open Orders ===")
    orders = executor.get_open_orders()
    if orders:
        for order in orders:
            print(f"\n{order['symbol']} - {order['side'].upper()}:")
            print(f"  Quantity: {order['quantity']}")
            print(f"  Type: {order['type']}")
            print(f"  Limit Price: ${order['limit_price']:.2f}" if order['limit_price'] else "  Market Order")
    else:
        print("No open orders")
