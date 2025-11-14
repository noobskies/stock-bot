"""
Market Close Handler

Handles end-of-day operations at market close (4:00 PM ET).
"""

from typing import Dict, Any
from loguru import logger

from src.bot_types.trading_types import BotConfig
from src.database.db_manager import DatabaseManager


class MarketCloseHandler:
    """
    Handles end-of-day market close operations.
    
    Workflow:
    1. Close all positions (if configured)
    2. Calculate daily performance
    3. Save performance metrics
    4. Reset daily counters
    
    Single Responsibility: Execute EOD operations.
    Does NOT handle trading cycle or position monitoring.
    """
    
    def __init__(self, modules: Dict[str, Any], config: BotConfig, db: DatabaseManager):
        """
        Initialize market close handler.
        
        Args:
            modules: Dict of bot module instances
            config: Bot configuration
            db: Database manager instance
        """
        self.position_manager = modules['position_manager']
        self.config = config
        self.db = db
    
    def handle_market_close(self):
        """
        Execute end-of-day market close tasks.
        
        This is called by the scheduler at 4:00 PM ET daily.
        """
        try:
            logger.info("=" * 80)
            logger.info("Market close - executing end-of-day tasks...")
            
            # Close positions if configured
            if self.config.close_positions_eod:
                logger.info("Closing all positions (EOD setting enabled)...")
                positions = self.position_manager.get_open_positions()
                
                for position in positions:
                    logger.info(f"Closing position: {position.symbol}")
                    success = self.position_manager.close_position(position.symbol)
                    
                    if success:
                        logger.info(f"Position closed: {position.symbol}")
                    else:
                        logger.error(f"Failed to close position: {position.symbol}")
            
            # Calculate daily performance
            logger.info("Calculating daily performance...")
            daily_perf = self.db.calculate_daily_performance()
            
            if daily_perf:
                logger.info(f"Daily performance: P&L=${daily_perf['total_pnl']:.2f}")
                logger.info(f"Trades today: {daily_perf['num_trades']}")
                logger.info(f"Win rate: {daily_perf['win_rate']:.1%}")
                
                # Save performance metrics
                self.db.save_performance_metrics(
                    total_pnl=daily_perf['total_pnl'],
                    num_trades=daily_perf['num_trades'],
                    win_rate=daily_perf['win_rate'],
                    sharpe_ratio=0.0,  # Calculate from historical data
                    max_drawdown=0.0   # Calculate from historical data
                )
            
            # Reset daily counters
            self.db.update_bot_state({
                'trading_mode': self.config.trading_mode.value,
                'daily_pnl': 0.0,
                'total_trades_today': 0
            })
            
            logger.info("End-of-day tasks complete")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.exception(f"Error handling market close: {e}")
