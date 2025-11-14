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
            positions = self.position_manager.sync_positions()
            
            if not positions:
                return
            
            logger.debug(f"Monitoring {len(positions)} positions...")
            
            for position in positions:
                # Get current price
                current_price = self.data_fetcher.fetch_latest_price(position.symbol)
                if current_price is None:
                    logger.warning(f"Could not fetch price for {position.symbol}")
                    continue
                
                # Update position price
                self.position_manager.update_position_price(
                    symbol=position.symbol,
                    current_price=current_price
                )
                
                # Register with stop loss manager if not already registered
                if not self.stop_loss_manager.is_registered(position.symbol):
                    self.stop_loss_manager.register_position(
                        symbol=position.symbol,
                        entry_price=position.entry_price,
                        quantity=position.quantity,
                        side=position.side,
                        stop_loss_percent=self.config.stop_loss_percent
                    )
                
                # Update stop loss manager with current price
                self.stop_loss_manager.update_price(position.symbol, current_price)
                
                # Check if stop loss triggered
                triggered, reason = self.stop_loss_manager.check_stop_triggered(position.symbol)
                
                if triggered:
                    logger.warning(f"Stop loss triggered for {position.symbol}: {reason}")
                    self._execute_stop_loss(position.symbol, reason)
            
            # Update portfolio state
            account = self.executor.get_account()
            if account:
                cash = float(account.get('cash', 0)) if isinstance(account, dict) else float(account.cash)
                self.portfolio_monitor.update_state(
                    cash=cash,
                    positions=positions
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
