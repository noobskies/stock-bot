"""
Position Monitor Orchestrator

Orchestrates position monitoring and stop loss execution.
Runs continuously during market hours.
"""

from typing import Dict, Any
from loguru import logger

from src.bot_types.trading_types import BotConfig
from src.database.db_manager import DatabaseManager


class PositionMonitorOrchestrator:
    """
    Monitors open positions and manages stop losses.
    
    Workflow:
    1. Sync positions with broker
    2. Update current prices
    3. Check stop losses
    4. Update trailing stops
    5. Execute stops if triggered
    
    Single Responsibility: Monitor positions and execute stops.
    Does NOT handle trading cycle or risk limit checking.
    """
    
    def __init__(self, modules: Dict[str, Any], config: BotConfig, db: DatabaseManager):
        """
        Initialize position monitor orchestrator.
        
        Args:
            modules: Dict of bot module instances
            config: Bot configuration
            db: Database manager instance
        """
        self.position_manager = modules['position_manager']
        self.stop_loss_manager = modules['stop_loss_manager']
        self.portfolio_monitor = modules['portfolio_monitor']
        self.data_fetcher = modules['data_fetcher']
        self.executor = modules['executor']
        
        self.config = config
        self.db = db
    
    def update_positions(self):
        """
        Update all position prices and check stop losses.
        
        This is the main entry point called by the scheduler every 30 seconds.
        """
        try:
            # Sync positions with broker
            self.position_manager.sync_positions()
            
            # Update all position prices at once (batch update)
            updated_prices = self.position_manager.update_position_prices()
            
            # Get all positions for monitoring
            positions = self.position_manager.get_all_positions()
            
            if not positions:
                return
            
            logger.debug(f"Monitoring {len(positions)} positions...")
            
            # Register any new positions with stop loss manager
            for position in positions:
                # Check if position is registered (returns None if not)
                if self.stop_loss_manager.get_stop_info(position.symbol) is None:
                    # Pass entire Position object
                    self.stop_loss_manager.register_position(position)
            
            # Check ALL stops at once (batch operation)
            # StopLossManager internally updates trailing stops based on position.current_price
            triggered_stops = self.stop_loss_manager.check_stops(positions)
            
            # Execute any triggered stops
            for position, reason in triggered_stops:
                logger.warning(f"Stop loss triggered for {position.symbol}: {reason}")
                self._execute_stop_loss(position.symbol, reason)
            
            # Update portfolio state
            account = self.executor.get_account()
            if account:
                cash = float(account.get('cash', 0)) if isinstance(account, dict) else float(account.cash)
                self.portfolio_monitor.update_portfolio_state(
                    current_positions=positions,
                    cash_available=cash
                )
            
        except Exception as e:
            logger.exception(f"Error updating positions: {e}")
    
    def _execute_stop_loss(self, symbol: str, reason: str):
        """
        Execute a stop loss order.
        
        Args:
            symbol: Symbol to close
            reason: Reason for stop loss
        """
        try:
            logger.info(f"Executing stop loss for {symbol}: {reason}")
            
            # Close position
            success = self.position_manager.close_position(symbol)
            
            if success:
                logger.success(f"Stop loss executed successfully for {symbol}")
                
                # Unregister from stop loss manager
                self.stop_loss_manager.unregister_position(symbol)
                
            else:
                logger.error(f"Failed to execute stop loss for {symbol}")
                
        except Exception as e:
            logger.exception(f"Error executing stop loss: {e}")
