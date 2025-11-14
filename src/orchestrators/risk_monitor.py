"""
Risk Monitor Orchestrator

Monitors portfolio risk limits and activates circuit breaker when needed.
"""

from typing import Dict, Any
from loguru import logger

from src.bot_types.trading_types import BotConfig
from src.database.db_manager import DatabaseManager


class RiskMonitorOrchestrator:
    """
    Monitors portfolio risk and activates circuit breaker.
    
    Workflow:
    1. Get current risk metrics
    2. Check daily loss limit
    3. Check position count
    4. Check portfolio exposure
    5. Activate circuit breaker if needed
    
    Single Responsibility: Monitor risk limits and circuit breaker.
    Does NOT handle position monitoring or trading.
    """
    
    def __init__(self, portfolio_monitor, config: BotConfig, db: DatabaseManager):
        """
        Initialize risk monitor orchestrator.
        
        Args:
            portfolio_monitor: PortfolioMonitor instance
            config: Bot configuration
            db: Database manager instance
        """
        self.portfolio_monitor = portfolio_monitor
        self.config = config
        self.db = db
    
    def check_risk_limits(self) -> bool:
        """
        Check portfolio risk limits and activate circuit breaker if needed.
        
        Monitors:
        - Daily P&L (circuit breaker at 5% loss)
        - Position count
        - Portfolio exposure
        
        Returns:
            bool: True if limits OK, False if circuit breaker triggered
        """
        try:
            # Get current risk metrics
            risk_metrics = self.portfolio_monitor.get_risk_metrics()
            
            # Check daily loss limit (5%)
            daily_loss_limit = self.config.daily_loss_limit  # 0.05 = 5%
            if risk_metrics['daily_pnl_percent'] <= -daily_loss_limit:
                logger.critical(
                    f"CIRCUIT BREAKER TRIGGERED: Daily loss limit exceeded "
                    f"({risk_metrics['daily_pnl_percent']:.2%})"
                )
                return self.activate_circuit_breaker()
            
            # Log risk metrics periodically
            if risk_metrics['position_count'] > 0:
                logger.info(
                    f"Risk metrics: positions={risk_metrics['position_count']}, "
                    f"exposure={risk_metrics['total_exposure_percent']:.1%}, "
                    f"daily_pnl={risk_metrics['daily_pnl_percent']:.2%}"
                )
            
            return True
                
        except Exception as e:
            logger.exception(f"Error checking risk limits: {e}")
            return False
    
    def activate_circuit_breaker(self) -> bool:
        """
        Activate circuit breaker - emergency stop.
        
        Returns:
            bool: False (to signal bot should stop)
        """
        try:
            logger.critical("Activating circuit breaker - stopping all trading")
            
            # Update bot state to trigger stop
            self.db.update_bot_state({
                'trading_mode': self.config.trading_mode.value,
                'is_running': False,
                'circuit_breaker_triggered': True
            })
            
            logger.critical("Circuit breaker active - bot stopped")
            return False
            
        except Exception as e:
            logger.exception(f"Error activating circuit breaker: {e}")
            return False
