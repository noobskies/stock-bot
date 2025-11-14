"""
Stop loss management and automated execution.

This module monitors positions for stop loss triggers and executes
automatic sell orders to limit losses and protect profits.

Key Features:
- Initial stop loss (3% below entry)
- Trailing stop loss (2% trail after 5% profit)
- Automatic execution without hesitation
- No exceptions - stops always execute
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from loguru import logger

from src.bot_types.trading_types import (
    Position,
    BotConfig,
    PositionStatus
)


class StopLossManager:
    """
    Manage stop losses for all positions.
    
    Monitors prices continuously and executes stops automatically
    when triggered, without hesitation or delay.
    """
    
    def __init__(self, config: BotConfig):
        """
        Initialize stop loss manager.
        
        Args:
            config: Bot configuration with stop loss parameters
        """
        self.config = config
        self.stop_registry: Dict[str, Dict] = {}  # symbol -> stop info
        
        logger.info("StopLossManager initialized")
        logger.info(f"  Initial stop: {config.stop_loss_percent * 100}%")
        logger.info(f"  Trailing stop: {config.trailing_stop_percent * 100}%")
        logger.info(
            f"  Trailing activation: {config.trailing_stop_activation * 100}%"
        )
    
    def register_position(self, position: Position):
        """
        Register a position for stop loss monitoring.
        
        Args:
            position: Position to monitor
        """
        self.stop_registry[position.symbol] = {
            'entry_price': position.entry_price,
            'quantity': position.quantity,
            'initial_stop': position.stop_loss,
            'trailing_stop': position.trailing_stop,
            'trailing_activated': position.trailing_stop is not None,
            'last_price': position.current_price,
            'entry_time': position.entry_time
        }
        
        logger.info(
            f"Position registered for {position.symbol}: "
            f"{position.quantity} shares at ${position.entry_price:.2f}, "
            f"stop: ${position.stop_loss:.2f}"
        )
    
    def unregister_position(self, symbol: str):
        """
        Unregister a position (after closing).
        
        Args:
            symbol: Stock symbol
        """
        if symbol in self.stop_registry:
            del self.stop_registry[symbol]
            logger.info(f"Position unregistered: {symbol}")
    
    def update_position_price(self, symbol: str, current_price: float):
        """
        Update current price for position.
        
        Args:
            symbol: Stock symbol
            current_price: Current market price
        """
        if symbol in self.stop_registry:
            self.stop_registry[symbol]['last_price'] = current_price
    
    def check_stops(
        self,
        positions: List[Position]
    ) -> List[Tuple[Position, str]]:
        """
        Check all positions for stop loss triggers.
        
        Args:
            positions: List of open positions
        
        Returns:
            List of (position, reason) tuples for positions to close
        """
        triggered_stops = []
        
        for position in positions:
            if position.status != PositionStatus.OPEN:
                continue
            
            # Update trailing stop if needed
            self._update_trailing_stop(position)
            
            # Check for stop trigger
            stop_triggered, reason = self._check_stop_triggered(position)
            
            if stop_triggered:
                triggered_stops.append((position, reason))
                logger.warning(
                    f"🛑 STOP LOSS TRIGGERED: {position.symbol} - {reason}"
                )
        
        return triggered_stops
    
    def _check_stop_triggered(
        self,
        position: Position
    ) -> Tuple[bool, str]:
        """
        Check if stop loss has been triggered for a position.
        
        Args:
            position: Position to check
        
        Returns:
            Tuple of (is_triggered, reason)
        """
        current_price = position.current_price
        
        # Check trailing stop first (if activated)
        if position.trailing_stop is not None:
            if current_price <= position.trailing_stop:
                return True, (
                    f"Trailing stop hit: ${current_price:.2f} <= "
                    f"${position.trailing_stop:.2f}"
                )
        
        # Check initial stop loss
        if current_price <= position.stop_loss:
            return True, (
                f"Initial stop hit: ${current_price:.2f} <= "
                f"${position.stop_loss:.2f}"
            )
        
        return False, ""
    
    def _update_trailing_stop(self, position: Position):
        """
        Update trailing stop if profit threshold reached.
        
        Trailing stop activates at 5% profit and trails by 2%.
        
        Args:
            position: Position to update
        """
        current_price = position.current_price
        entry_price = position.entry_price
        
        # Calculate profit percentage
        profit_percent = (current_price - entry_price) / entry_price
        
        # Check if we should activate trailing stop
        should_activate = (
            profit_percent >= self.config.trailing_stop_activation
        )
        
        if not should_activate:
            return
        
        # Calculate new trailing stop price
        new_trailing_stop = current_price * (
            1 - self.config.trailing_stop_percent
        )
        
        # Only update if new trailing stop is higher than current
        if position.trailing_stop is None:
            # First time activation
            position.trailing_stop = round(new_trailing_stop, 2)
            
            logger.info(
                f"✓ Trailing stop ACTIVATED for {position.symbol}: "
                f"${position.trailing_stop:.2f} "
                f"(profit: {profit_percent * 100:.1f}%)"
            )
            
            # Update registry
            if position.symbol in self.stop_registry:
                self.stop_registry[position.symbol]['trailing_stop'] = (
                    position.trailing_stop
                )
                self.stop_registry[position.symbol]['trailing_activated'] = True
        
        elif new_trailing_stop > position.trailing_stop:
            # Update existing trailing stop (price rose)
            old_stop = position.trailing_stop
            position.trailing_stop = round(new_trailing_stop, 2)
            
            logger.info(
                f"↑ Trailing stop RAISED for {position.symbol}: "
                f"${old_stop:.2f} -> ${position.trailing_stop:.2f}"
            )
            
            # Update registry
            if position.symbol in self.stop_registry:
                self.stop_registry[position.symbol]['trailing_stop'] = (
                    position.trailing_stop
                )
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        stop_percent: Optional[float] = None
    ) -> float:
        """
        Calculate initial stop loss price.
        
        Args:
            entry_price: Entry price
            stop_percent: Stop percentage (default: from config)
        
        Returns:
            Stop loss price
        """
        if stop_percent is None:
            stop_percent = self.config.stop_loss_percent
        
        stop_price = entry_price * (1 - stop_percent)
        
        return round(stop_price, 2)
    
    def calculate_trailing_stop(
        self,
        current_price: float,
        trail_percent: Optional[float] = None
    ) -> float:
        """
        Calculate trailing stop price.
        
        Args:
            current_price: Current market price
            trail_percent: Trailing percentage (default: from config)
        
        Returns:
            Trailing stop price
        """
        if trail_percent is None:
            trail_percent = self.config.trailing_stop_percent
        
        trailing_price = current_price * (1 - trail_percent)
        
        return round(trailing_price, 2)
    
    def should_activate_trailing_stop(
        self,
        entry_price: float,
        current_price: float
    ) -> Tuple[bool, float]:
        """
        Check if trailing stop should be activated.
        
        Args:
            entry_price: Original entry price
            current_price: Current market price
        
        Returns:
            Tuple of (should_activate, profit_percent)
        """
        profit_percent = (current_price - entry_price) / entry_price
        
        should_activate = (
            profit_percent >= self.config.trailing_stop_activation
        )
        
        return should_activate, profit_percent
    
    def get_stop_info(self, symbol: str) -> Optional[Dict]:
        """
        Get stop loss information for a symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Stop info dictionary or None
        """
        return self.stop_registry.get(symbol)
    
    def get_all_stops(self) -> Dict[str, Dict]:
        """
        Get stop information for all positions.
        
        Returns:
            Dictionary of symbol -> stop info
        """
        return self.stop_registry.copy()
    
    def calculate_potential_loss(
        self,
        position: Position
    ) -> Tuple[float, float]:
        """
        Calculate potential loss if stop is hit.
        
        Args:
            position: Position to calculate for
        
        Returns:
            Tuple of (loss_dollars, loss_percent)
        """
        # Use trailing stop if active, otherwise initial stop
        stop_price = (
            position.trailing_stop
            if position.trailing_stop is not None
            else position.stop_loss
        )
        
        # Calculate loss
        loss_per_share = position.entry_price - stop_price
        total_loss = loss_per_share * position.quantity
        loss_percent = loss_per_share / position.entry_price
        
        return round(total_loss, 2), round(loss_percent, 4)
    
    def get_position_summary(self, position: Position) -> Dict:
        """
        Get human-readable summary of position stops.
        
        Args:
            position: Position to summarize
        
        Returns:
            Dictionary with formatted summary
        """
        potential_loss, loss_pct = self.calculate_potential_loss(position)
        
        summary = {
            'symbol': position.symbol,
            'entry_price': f"${position.entry_price:.2f}",
            'current_price': f"${position.current_price:.2f}",
            'initial_stop': f"${position.stop_loss:.2f}",
            'trailing_stop': (
                f"${position.trailing_stop:.2f}"
                if position.trailing_stop is not None
                else "Not activated"
            ),
            'potential_loss': f"${potential_loss:.2f}",
            'potential_loss_percent': f"{loss_pct:.2%}",
            'profit_percent': f"{((position.current_price - position.entry_price) / position.entry_price):.2%}"
        }
        
        return summary
    
    def validate_stop_loss(
        self,
        entry_price: float,
        stop_loss: float
    ) -> Tuple[bool, str]:
        """
        Validate that stop loss is properly set.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
        
        Returns:
            Tuple of (is_valid, reason)
        """
        # Stop loss must be below entry
        if stop_loss >= entry_price:
            return False, "Stop loss must be below entry price"
        
        # Calculate distance
        distance = (entry_price - stop_loss) / entry_price
        
        # Check if within reasonable range (1% to 10%)
        if distance < 0.01:
            return False, "Stop loss too tight (< 1%)"
        
        if distance > 0.10:
            return False, "Stop loss too wide (> 10%)"
        
        return True, ""


# Example usage
if __name__ == "__main__":
    from ..types.trading_types import TradingMode
    
    # Create config
    config = BotConfig(
        trading_mode=TradingMode.HYBRID,
        symbols=["PLTR"],
        initial_capital=10000,
        max_positions=5,
        close_positions_eod=True,
        risk_per_trade=0.02,
        max_position_size=0.20,
        max_portfolio_exposure=0.20,
        daily_loss_limit=0.05,
        stop_loss_percent=0.03,
        trailing_stop_percent=0.02,
        trailing_stop_activation=0.05,
        model_path="models/lstm_model.h5",
        sequence_length=60,
        prediction_confidence_threshold=0.70,
        auto_execute_threshold=0.80,
        database_url="sqlite:///trading_bot.db",
        log_level="INFO",
        log_dir="logs/"
    )
    
    # Initialize manager
    manager = StopLossManager(config)
    
    # Example 1: Calculate initial stop loss
    entry_price = 30.0
    stop_loss = manager.calculate_stop_loss(entry_price)
    print(f"\n1. Initial Stop Loss:")
    print(f"   Entry: ${entry_price:.2f}")
    print(f"   Stop: ${stop_loss:.2f}")
    print(f"   Distance: {((entry_price - stop_loss) / entry_price) * 100:.1f}%")
    
    # Example 2: Register a position
    position = Position(
        symbol="PLTR",
        quantity=50,
        entry_price=30.0,
        current_price=30.5,
        stop_loss=29.1,
        unrealized_pnl=25.0,
        status=PositionStatus.OPEN,
        entry_time=datetime.now(),
        unrealized_pnl_percent=0.017
    )
    
    manager.register_position(position)
    print(f"\n2. Position Registered:")
    print(f"   Symbol: {position.symbol}")
    print(f"   Stop: ${position.stop_loss:.2f}")
    
    # Example 3: Check if trailing stop should activate
    should_activate, profit = manager.should_activate_trailing_stop(
        entry_price=30.0,
        current_price=31.6  # 5.3% profit
    )
    print(f"\n3. Trailing Stop Check:")
    print(f"   Current profit: {profit * 100:.1f}%")
    print(f"   Should activate: {should_activate}")
    
    # Example 4: Update position and check trailing stop
    position.current_price = 31.6
    manager._update_trailing_stop(position)
    print(f"\n4. Trailing Stop Update:")
    print(f"   Trailing stop: ${position.trailing_stop:.2f}")
    
    # Example 5: Check for stop triggers
    position.current_price = 30.8  # Still above trailing stop
    triggered = manager.check_stops([position])
    print(f"\n5. Stop Check (price at $30.80):")
    print(f"   Triggered: {len(triggered) > 0}")
    
    # Example 6: Trigger stop
    position.current_price = 30.0  # Below trailing stop
    triggered = manager.check_stops([position])
    print(f"\n6. Stop Check (price at $30.00):")
    print(f"   Triggered: {len(triggered) > 0}")
    if triggered:
        pos, reason = triggered[0]
        print(f"   Reason: {reason}")
    
    # Example 7: Position summary
    position.current_price = 31.0
    summary = manager.get_position_summary(position)
    print(f"\n7. Position Summary:")
    for key, value in summary.items():
        print(f"   {key}: {value}")
