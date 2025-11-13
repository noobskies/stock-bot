"""
Order Manager - Order lifecycle management and execution coordination.

This module coordinates the complete order lifecycle from signal to execution,
integrating risk validation, position sizing, and broker execution.

Key Features:
- Order lifecycle management
- Risk validation integration
- Position sizing coordination
- Order tracking and status updates
- Execution confirmation
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from loguru import logger

from src.types.trading_types import (
    TradingSignal,
    SignalType,
    OrderStatus,
    Position,
    TradeRecord
)
from src.trading.executor import AlpacaExecutor
from src.trading.position_manager import PositionManager
from src.risk.risk_calculator import RiskCalculator


@dataclass
class OrderTracking:
    """
    Track an order through its lifecycle.
    
    Attributes:
        signal: Original trading signal
        order_id: Broker order ID
        symbol: Stock symbol
        quantity: Number of shares
        side: 'buy' or 'sell'
        order_type: 'market' or 'limit'
        limit_price: Limit price (for limit orders)
        status: Current order status
        submitted_at: When order was submitted
        filled_at: When order was filled (if filled)
        filled_price: Actual fill price
        filled_quantity: Actual fill quantity
    """
    signal: TradingSignal
    order_id: str
    symbol: str
    quantity: int
    side: str
    order_type: str = 'market'
    limit_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    submitted_at: datetime = None
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None
    filled_quantity: Optional[int] = None


class OrderManager:
    """
    Manage order execution and lifecycle.
    
    This class coordinates the complete order process from signal to execution,
    handling risk validation, position sizing, broker submission, and status
    tracking.
    
    Attributes:
        executor: Alpaca API executor
        position_manager: Position manager
        risk_calculator: Risk calculator
        active_orders: Dictionary of order_id: OrderTracking
    """
    
    def __init__(
        self,
        executor: AlpacaExecutor,
        position_manager: PositionManager,
        risk_calculator: RiskCalculator
    ):
        """
        Initialize order manager.
        
        Args:
            executor: Alpaca API executor
            position_manager: Position manager
            risk_calculator: Risk calculator
        """
        self.executor = executor
        self.position_manager = position_manager
        self.risk_calculator = risk_calculator
        self.active_orders: Dict[str, OrderTracking] = {}
        
        logger.info("OrderManager initialized")
    
    def execute_signal(
        self,
        signal: TradingSignal,
        portfolio_value: float,
        buying_power: float
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Execute a trading signal.
        
        This is the main entry point for signal execution, coordinating all
        steps from risk validation to broker submission.
        
        Args:
            signal: Trading signal to execute
            portfolio_value: Total portfolio value
            buying_power: Available buying power
        
        Returns:
            Tuple of (success, order_id, error_message)
        
        Example:
            success, order_id, error = order_manager.execute_signal(
                signal, 10000.0, 5000.0
            )
        """
        logger.info(
            f"Executing signal: {signal.signal_type.value} {signal.symbol} "
            f"(confidence: {signal.confidence:.2%})"
        )
        
        # Handle BUY and SELL differently
        if signal.signal_type == SignalType.BUY:
            return self._execute_buy_signal(signal, portfolio_value, buying_power)
        elif signal.signal_type == SignalType.SELL:
            return self._execute_sell_signal(signal)
        else:
            return False, None, f"Unknown signal type: {signal.signal_type}"
    
    def _execute_buy_signal(
        self,
        signal: TradingSignal,
        portfolio_value: float,
        buying_power: float
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Execute a BUY signal.
        
        Args:
            signal: Buy trading signal
            portfolio_value: Total portfolio value
            buying_power: Available buying power
        
        Returns:
            Tuple of (success, order_id, error_message)
        """
        # Calculate position size
        quantity = self.risk_calculator.calculate_position_size(
            signal.symbol,
            signal.entry_price,
            portfolio_value
        )
        
        if quantity <= 0:
            error_msg = "Position size calculation resulted in 0 shares"
            logger.warning(f"Cannot execute buy signal: {error_msg}")
            return False, None, error_msg
        
        # Validate buying power
        required_capital = signal.entry_price * quantity
        if required_capital > buying_power:
            error_msg = (
                f"Insufficient buying power: need ${required_capital:.2f}, "
                f"have ${buying_power:.2f}"
            )
            logger.warning(f"Cannot execute buy signal: {error_msg}")
            return False, None, error_msg
        
        # Submit market order
        success, order_id, error = self.executor.place_market_order(
            symbol=signal.symbol,
            quantity=quantity,
            side='buy'
        )
        
        if not success:
            return False, None, error
        
        # Track the order
        order_tracking = OrderTracking(
            signal=signal,
            order_id=order_id,
            symbol=signal.symbol,
            quantity=quantity,
            side='buy',
            order_type='market',
            status=OrderStatus.PENDING,
            submitted_at=datetime.now(timezone.utc)
        )
        self.active_orders[order_id] = order_tracking
        
        logger.info(
            f"Buy order submitted: {quantity} shares of {signal.symbol} "
            f"(Order ID: {order_id})"
        )
        
        return True, order_id, None
    
    def _execute_sell_signal(
        self,
        signal: TradingSignal
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Execute a SELL signal.
        
        Args:
            signal: Sell trading signal
        
        Returns:
            Tuple of (success, order_id, error_message)
        """
        # Get current position
        position = self.position_manager.get_position(signal.symbol)
        
        if not position:
            error_msg = f"No position found for {signal.symbol} to sell"
            logger.warning(f"Cannot execute sell signal: {error_msg}")
            return False, None, error_msg
        
        # Submit market order to close position
        success, order_id, error = self.executor.place_market_order(
            symbol=signal.symbol,
            quantity=position.quantity,
            side='sell'
        )
        
        if not success:
            return False, None, error
        
        # Track the order
        order_tracking = OrderTracking(
            signal=signal,
            order_id=order_id,
            symbol=signal.symbol,
            quantity=position.quantity,
            side='sell',
            order_type='market',
            status=OrderStatus.PENDING,
            submitted_at=datetime.now(timezone.utc)
        )
        self.active_orders[order_id] = order_tracking
        
        logger.info(
            f"Sell order submitted: {position.quantity} shares of {signal.symbol} "
            f"(Order ID: {order_id})"
        )
        
        return True, order_id, None
    
    def update_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """
        Update status of a tracked order.
        
        Args:
            order_id: Order ID to update
        
        Returns:
            Updated OrderStatus or None if not found
        """
        tracking = self.active_orders.get(order_id)
        if not tracking:
            logger.warning(f"Order not found for status update: {order_id}")
            return None
        
        # Get status from broker
        status_str, details = self.executor.get_order_status(order_id)
        
        if status_str is None:
            logger.error(f"Failed to get status for order {order_id}")
            return tracking.status
        
        # Update tracking based on status
        if status_str == 'filled':
            tracking.status = OrderStatus.FILLED
            tracking.filled_at = details.get('filled_at')
            tracking.filled_price = details.get('filled_avg_price')
            tracking.filled_quantity = details.get('filled_qty')
            
            logger.info(
                f"Order filled: {order_id} - {tracking.quantity} shares @ "
                f"${tracking.filled_price:.2f}"
            )
            
            # Update position manager if buy order
            if tracking.side == 'buy':
                self._handle_buy_fill(tracking)
            elif tracking.side == 'sell':
                self._handle_sell_fill(tracking)
                
        elif status_str == 'cancelled':
            tracking.status = OrderStatus.CANCELLED
            logger.info(f"Order cancelled: {order_id}")
            
        elif status_str == 'rejected':
            tracking.status = OrderStatus.REJECTED
            logger.warning(f"Order rejected: {order_id}")
            
        elif status_str == 'expired':
            tracking.status = OrderStatus.EXPIRED
            logger.info(f"Order expired: {order_id}")
            
        else:  # pending
            tracking.status = OrderStatus.PENDING
        
        return tracking.status
    
    def _handle_buy_fill(self, tracking: OrderTracking):
        """
        Handle a filled buy order.
        
        Args:
            tracking: Order tracking info
        """
        # Calculate stop loss
        stop_loss_price = self.risk_calculator.calculate_stop_loss(
            tracking.filled_price
        )
        
        # Add position to position manager
        position = self.position_manager.add_position(
            symbol=tracking.symbol,
            quantity=tracking.filled_quantity,
            entry_price=tracking.filled_price,
            entry_time=tracking.filled_at,
            stop_loss_price=stop_loss_price
        )
        
        logger.info(
            f"Position opened: {tracking.symbol} - "
            f"{tracking.filled_quantity} shares @ ${tracking.filled_price:.2f} "
            f"(Stop: ${stop_loss_price:.2f})"
        )
    
    def _handle_sell_fill(self, tracking: OrderTracking):
        """
        Handle a filled sell order.
        
        Args:
            tracking: Order tracking info
        """
        # Close position in position manager
        trade_record = self.position_manager.close_position(
            symbol=tracking.symbol,
            exit_price=tracking.filled_price,
            exit_time=tracking.filled_at
        )
        
        if trade_record:
            logger.info(
                f"Position closed: {tracking.symbol} - "
                f"P&L: ${trade_record.realized_pnl:.2f} "
                f"({trade_record.realized_pnl_percent:.2f}%)"
            )
    
    def update_all_orders(self) -> Dict[str, OrderStatus]:
        """
        Update status of all active orders.
        
        Returns:
            Dictionary of order_id: status
        """
        statuses = {}
        
        for order_id in list(self.active_orders.keys()):
            status = self.update_order_status(order_id)
            if status:
                statuses[order_id] = status
                
                # Remove completed orders from active tracking
                if status in [
                    OrderStatus.FILLED,
                    OrderStatus.CANCELLED,
                    OrderStatus.REJECTED,
                    OrderStatus.EXPIRED
                ]:
                    del self.active_orders[order_id]
        
        return statuses
    
    def get_active_orders(self) -> List[OrderTracking]:
        """
        Get all active orders.
        
        Returns:
            List of OrderTracking objects
        """
        return list(self.active_orders.values())
    
    def cancel_order(self, order_id: str) -> Tuple[bool, Optional[str]]:
        """
        Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            Tuple of (success, error_message)
        """
        tracking = self.active_orders.get(order_id)
        if not tracking:
            return False, f"Order not found: {order_id}"
        
        success, error = self.executor.cancel_order(order_id)
        
        if success:
            tracking.status = OrderStatus.CANCELLED
            del self.active_orders[order_id]
            logger.info(f"Order cancelled successfully: {order_id}")
        
        return success, error
    
    def cancel_all_orders(self) -> Tuple[bool, Optional[str]]:
        """
        Cancel all pending orders.
        
        Returns:
            Tuple of (success, error_message)
        """
        order_ids = list(self.active_orders.keys())
        
        if not order_ids:
            logger.info("No active orders to cancel")
            return True, None
        
        # Use executor's bulk cancel
        success, error = self.executor.cancel_all_orders()
        
        if success:
            # Update tracking
            for order_id in order_ids:
                if order_id in self.active_orders:
                    self.active_orders[order_id].status = OrderStatus.CANCELLED
            
            self.active_orders.clear()
            logger.info(f"Cancelled {len(order_ids)} orders")
        
        return success, error
    
    def get_order_summary(self) -> Dict:
        """
        Get summary of order activity.
        
        Returns:
            Dictionary with order statistics
        """
        active_count = len(self.active_orders)
        
        buy_count = sum(1 for o in self.active_orders.values() if o.side == 'buy')
        sell_count = sum(1 for o in self.active_orders.values() if o.side == 'sell')
        
        return {
            'active_orders': active_count,
            'buy_orders': buy_count,
            'sell_orders': sell_count
        }


# Example usage
if __name__ == "__main__":
    """
    Example usage of OrderManager.
    
    This demonstrates:
    - Initializing the order manager
    - Executing buy/sell signals
    - Tracking order status
    - Cancelling orders
    """
    from dotenv import load_dotenv
    from src.risk.stop_loss_manager import StopLossManager
    
    load_dotenv()
    
    # Initialize components
    executor = AlpacaExecutor(is_paper=True)
    stop_loss_manager = StopLossManager()
    position_manager = PositionManager(executor, stop_loss_manager)
    risk_calculator = RiskCalculator(
        initial_capital=10000.0,
        risk_per_trade=0.02,
        max_position_size=0.20,
        max_portfolio_exposure=0.20,
        daily_loss_limit=0.05
    )
    
    order_manager = OrderManager(
        executor=executor,
        position_manager=position_manager,
        risk_calculator=risk_calculator
    )
    
    print("\n=== Order Manager Demo ===")
    
    # Get account info
    account = executor.get_account()
    portfolio_value = account['portfolio_value']
    buying_power = account['buying_power']
    
    print(f"\nPortfolio Value: ${portfolio_value:,.2f}")
    print(f"Buying Power: ${buying_power:,.2f}")
    
    # Create a sample buy signal (commented out for safety)
    # from src.types.trading_types import TradingSignal, SignalType
    # signal = TradingSignal(
    #     symbol='PLTR',
    #     signal_type=SignalType.BUY,
    #     confidence=0.85,
    #     entry_price=30.50,
    #     timestamp=datetime.now(timezone.utc),
    #     model_prediction='UP',
    #     technical_indicators={},
    #     reasoning='Test buy signal',
    #     requires_approval=False
    # )
    # 
    # # Execute the signal
    # success, order_id, error = order_manager.execute_signal(
    #     signal, portfolio_value, buying_power
    # )
    # 
    # if success:
    #     print(f"\nOrder submitted: {order_id}")
    #     
    #     # Wait for order to process
    #     import time
    #     time.sleep(2)
    #     
    #     # Update order status
    #     status = order_manager.update_order_status(order_id)
    #     print(f"Order status: {status.value if status else 'Unknown'}")
    # else:
    #     print(f"\nOrder failed: {error}")
    
    # Show active orders
    print("\n=== Active Orders ===")
    active_orders = order_manager.get_active_orders()
    if active_orders:
        for order in active_orders:
            print(f"\n{order.symbol} - {order.side.upper()}:")
            print(f"  Order ID: {order.order_id}")
            print(f"  Quantity: {order.quantity}")
            print(f"  Status: {order.status.value}")
            print(f"  Submitted: {order.submitted_at}")
    else:
        print("No active orders")
    
    # Show summary
    print("\n=== Order Summary ===")
    summary = order_manager.get_order_summary()
    print(f"Active Orders: {summary['active_orders']}")
    print(f"Buy Orders: {summary['buy_orders']}")
    print(f"Sell Orders: {summary['sell_orders']}")
