"""
Position Manager - Track and manage open trading positions.

This module manages the lifecycle of trading positions, including tracking
entry/exit, P&L calculation, and position updates. It integrates with the
stop loss manager for automated risk management.

Key Features:
- Position tracking and updates
- Real-time P&L calculation
- Position lifecycle management
- Integration with stop loss manager
- Historical position tracking
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from loguru import logger

from src.types.trading_types import Position, PositionStatus, TradeRecord
from src.trading.executor import AlpacaExecutor
from src.risk.stop_loss_manager import StopLossManager


class PositionManager:
    """
    Manage open trading positions and their lifecycle.
    
    This class tracks all open positions, updates their prices and P&L,
    and coordinates with the stop loss manager for automated risk management.
    
    Attributes:
        executor: Alpaca API executor for position data
        stop_loss_manager: Stop loss manager for risk management
        positions: Dictionary of symbol: Position
    """
    
    def __init__(
        self,
        executor: AlpacaExecutor,
        stop_loss_manager: Optional[StopLossManager] = None
    ):
        """
        Initialize position manager.
        
        Args:
            executor: Alpaca API executor
            stop_loss_manager: Stop loss manager (optional)
        """
        self.executor = executor
        self.stop_loss_manager = stop_loss_manager
        self.positions: Dict[str, Position] = {}
        
        logger.info("PositionManager initialized")
    
    def sync_positions(self) -> int:
        """
        Sync positions from Alpaca broker.
        
        This fetches all open positions from Alpaca and updates the local
        position dictionary. Should be called on startup and periodically
        to ensure consistency.
        
        Returns:
            Number of positions synced
        """
        try:
            # Get positions from Alpaca
            alpaca_positions = self.executor.get_open_positions()
            
            # Update local positions
            synced_count = 0
            for position in alpaca_positions:
                symbol = position.symbol
                
                # If position exists locally, update it
                if symbol in self.positions:
                    self._update_position(symbol, position)
                else:
                    # New position, add it
                    self.positions[symbol] = position
                    
                    # Register with stop loss manager
                    if self.stop_loss_manager:
                        self.stop_loss_manager.register_position(position)
                
                synced_count += 1
            
            # Remove positions that no longer exist in Alpaca
            local_symbols = set(self.positions.keys())
            alpaca_symbols = {p.symbol for p in alpaca_positions}
            removed_symbols = local_symbols - alpaca_symbols
            
            for symbol in removed_symbols:
                logger.info(f"Position {symbol} no longer exists in broker - removing")
                self.close_position(symbol, auto_closed=True)
            
            logger.info(f"Synced {synced_count} positions from Alpaca")
            return synced_count
            
        except Exception as e:
            logger.error(f"Failed to sync positions: {e}")
            return 0
    
    def add_position(
        self,
        symbol: str,
        quantity: int,
        entry_price: float,
        entry_time: datetime,
        stop_loss_price: Optional[float] = None
    ) -> Position:
        """
        Add a new position to tracking.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            entry_price: Entry price per share
            entry_time: Time position was opened
            stop_loss_price: Initial stop loss price
        
        Returns:
            Created Position object
        """
        position = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            market_value=entry_price * quantity,
            unrealized_pnl=0.0,
            unrealized_pnl_percent=0.0,
            status=PositionStatus.OPEN,
            entry_time=entry_time,
            stop_loss_price=stop_loss_price,
            trailing_stop_price=None
        )
        
        self.positions[symbol] = position
        
        # Register with stop loss manager
        if self.stop_loss_manager and stop_loss_price:
            self.stop_loss_manager.register_position(position)
        
        logger.info(
            f"Position added: {symbol} - {quantity} shares @ ${entry_price:.2f} "
            f"(Stop: ${stop_loss_price:.2f})" if stop_loss_price else
            f"Position added: {symbol} - {quantity} shares @ ${entry_price:.2f}"
        )
        
        return position
    
    def update_position_prices(self) -> Dict[str, float]:
        """
        Update current prices for all open positions.
        
        This fetches latest prices from Alpaca and updates P&L calculations.
        Should be called periodically (every 30-60 seconds during market hours).
        
        Returns:
            Dictionary of symbol: current_price
        """
        updated_prices = {}
        
        for symbol in list(self.positions.keys()):
            try:
                # Get current price from executor
                current_price = self.executor.get_latest_price(symbol)
                
                if current_price is None:
                    logger.warning(f"Could not get current price for {symbol}")
                    continue
                
                # Update position
                position = self.positions[symbol]
                position.current_price = current_price
                position.market_value = current_price * position.quantity
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
                position.unrealized_pnl_percent = (
                    (current_price - position.entry_price) / position.entry_price * 100
                )
                
                updated_prices[symbol] = current_price
                
                # Update stop loss manager
                if self.stop_loss_manager:
                    self.stop_loss_manager.update_position_price(symbol, current_price)
                
            except Exception as e:
                logger.error(f"Failed to update price for {symbol}: {e}")
        
        if updated_prices:
            logger.debug(f"Updated prices for {len(updated_prices)} positions")
        
        return updated_prices
    
    def _update_position(self, symbol: str, new_position: Position):
        """
        Update an existing position with new data.
        
        Args:
            symbol: Stock symbol
            new_position: Updated position data
        """
        old_position = self.positions[symbol]
        
        # Preserve stop loss and trailing stop from old position
        new_position.stop_loss_price = old_position.stop_loss_price
        new_position.trailing_stop_price = old_position.trailing_stop_price
        new_position.entry_time = old_position.entry_time
        
        self.positions[symbol] = new_position
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get a position by symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Position object or None if not found
        """
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """
        Get all open positions.
        
        Returns:
            List of Position objects
        """
        return list(self.positions.values())
    
    def has_position(self, symbol: str) -> bool:
        """
        Check if a position exists for a symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            True if position exists
        """
        return symbol in self.positions
    
    def get_position_count(self) -> int:
        """
        Get number of open positions.
        
        Returns:
            Count of open positions
        """
        return len(self.positions)
    
    def get_total_market_value(self) -> float:
        """
        Get total market value of all positions.
        
        Returns:
            Sum of all position market values
        """
        return sum(p.market_value for p in self.positions.values())
    
    def get_total_unrealized_pnl(self) -> float:
        """
        Get total unrealized P&L across all positions.
        
        Returns:
            Sum of unrealized P&L
        """
        return sum(p.unrealized_pnl for p in self.positions.values())
    
    def close_position(
        self,
        symbol: str,
        exit_price: Optional[float] = None,
        exit_time: Optional[datetime] = None,
        auto_closed: bool = False
    ) -> Optional[TradeRecord]:
        """
        Close a position and create trade record.
        
        Args:
            symbol: Stock symbol to close
            exit_price: Exit price (if None, uses current price)
            exit_time: Exit time (if None, uses now)
            auto_closed: Whether position was auto-closed (e.g., by broker)
        
        Returns:
            TradeRecord or None if position not found
        """
        position = self.positions.get(symbol)
        if not position:
            logger.warning(f"Cannot close position - not found: {symbol}")
            return None
        
        # Use current price if not provided
        if exit_price is None:
            exit_price = position.current_price
        
        if exit_time is None:
            exit_time = datetime.now(timezone.utc)
        
        # Calculate final P&L
        realized_pnl = (exit_price - position.entry_price) * position.quantity
        realized_pnl_percent = (exit_price - position.entry_price) / position.entry_price * 100
        
        # Create trade record
        trade_record = TradeRecord(
            symbol=symbol,
            entry_time=position.entry_time,
            exit_time=exit_time,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            side='long',  # We only do long positions
            realized_pnl=realized_pnl,
            realized_pnl_percent=realized_pnl_percent,
            commission=0.0,  # Alpaca is commission-free
            hold_time=(exit_time - position.entry_time).total_seconds()
        )
        
        # Remove position
        del self.positions[symbol]
        
        # Unregister from stop loss manager
        if self.stop_loss_manager:
            self.stop_loss_manager.unregister_position(symbol)
        
        logger.info(
            f"Position closed: {symbol} - "
            f"P&L: ${realized_pnl:.2f} ({realized_pnl_percent:.2f}%)"
        )
        
        return trade_record
    
    def close_all_positions(self) -> List[TradeRecord]:
        """
        Close all open positions.
        
        This is typically used at end of day or during emergency stop.
        
        Returns:
            List of TradeRecord for closed positions
        """
        trade_records = []
        symbols_to_close = list(self.positions.keys())
        
        for symbol in symbols_to_close:
            trade_record = self.close_position(symbol)
            if trade_record:
                trade_records.append(trade_record)
        
        logger.info(f"Closed {len(trade_records)} positions")
        return trade_records
    
    def set_stop_loss(self, symbol: str, stop_price: float):
        """
        Set or update stop loss for a position.
        
        Args:
            symbol: Stock symbol
            stop_price: Stop loss price
        """
        position = self.positions.get(symbol)
        if not position:
            logger.warning(f"Cannot set stop loss - position not found: {symbol}")
            return
        
        position.stop_loss_price = stop_price
        
        # Update stop loss manager
        if self.stop_loss_manager:
            self.stop_loss_manager.update_stop_loss(symbol, stop_price)
        
        logger.info(f"Stop loss set: {symbol} @ ${stop_price:.2f}")
    
    def set_trailing_stop(self, symbol: str, trailing_price: float):
        """
        Set or update trailing stop for a position.
        
        Args:
            symbol: Stock symbol
            trailing_price: Trailing stop price
        """
        position = self.positions.get(symbol)
        if not position:
            logger.warning(f"Cannot set trailing stop - position not found: {symbol}")
            return
        
        position.trailing_stop_price = trailing_price
        
        # Update stop loss manager
        if self.stop_loss_manager:
            self.stop_loss_manager.update_trailing_stop(symbol, trailing_price)
        
        logger.info(f"Trailing stop set: {symbol} @ ${trailing_price:.2f}")
    
    def get_position_summary(self) -> Dict:
        """
        Get summary statistics for all positions.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.positions:
            return {
                'position_count': 0,
                'total_market_value': 0.0,
                'total_unrealized_pnl': 0.0,
                'avg_unrealized_pnl_percent': 0.0,
                'winning_positions': 0,
                'losing_positions': 0
            }
        
        total_market_value = self.get_total_market_value()
        total_unrealized_pnl = self.get_total_unrealized_pnl()
        
        winning_positions = sum(1 for p in self.positions.values() if p.unrealized_pnl > 0)
        losing_positions = sum(1 for p in self.positions.values() if p.unrealized_pnl < 0)
        
        avg_pnl_percent = sum(
            p.unrealized_pnl_percent for p in self.positions.values()
        ) / len(self.positions)
        
        return {
            'position_count': len(self.positions),
            'total_market_value': total_market_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'avg_unrealized_pnl_percent': avg_pnl_percent,
            'winning_positions': winning_positions,
            'losing_positions': losing_positions
        }


# Example usage
if __name__ == "__main__":
    """
    Example usage of PositionManager.
    
    This demonstrates:
    - Initializing the position manager
    - Adding and tracking positions
    - Updating prices and P&L
    - Closing positions
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize executor and position manager
    executor = AlpacaExecutor(is_paper=True)
    stop_loss_manager = StopLossManager()
    position_manager = PositionManager(executor, stop_loss_manager)
    
    print("\n=== Position Manager Demo ===")
    
    # Sync positions from Alpaca
    print("\nSyncing positions from Alpaca...")
    synced = position_manager.sync_positions()
    print(f"Synced {synced} positions")
    
    # Get all positions
    positions = position_manager.get_all_positions()
    if positions:
        print(f"\n=== Open Positions ({len(positions)}) ===")
        for position in positions:
            print(f"\n{position.symbol}:")
            print(f"  Quantity: {position.quantity}")
            print(f"  Entry: ${position.entry_price:.2f}")
            print(f"  Current: ${position.current_price:.2f}")
            print(f"  Market Value: ${position.market_value:.2f}")
            print(f"  Unrealized P&L: ${position.unrealized_pnl:.2f} ({position.unrealized_pnl_percent:.2f}%)")
            if position.stop_loss_price:
                print(f"  Stop Loss: ${position.stop_loss_price:.2f}")
    else:
        print("\nNo open positions")
    
    # Update prices
    print("\n=== Updating Prices ===")
    updated_prices = position_manager.update_position_prices()
    for symbol, price in updated_prices.items():
        print(f"{symbol}: ${price:.2f}")
    
    # Get summary
    print("\n=== Position Summary ===")
    summary = position_manager.get_position_summary()
    print(f"Total Positions: {summary['position_count']}")
    print(f"Total Market Value: ${summary['total_market_value']:.2f}")
    print(f"Total Unrealized P&L: ${summary['total_unrealized_pnl']:.2f}")
    print(f"Average P&L %: {summary['avg_unrealized_pnl_percent']:.2f}%")
    print(f"Winning: {summary['winning_positions']}, Losing: {summary['losing_positions']}")
