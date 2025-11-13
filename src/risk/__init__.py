"""
Risk management module.

This module provides comprehensive risk management functionality including:
- Position sizing based on 2% risk rule
- Trade validation against risk limits
- Portfolio state monitoring
- Automated stop loss management

Key Components:
- RiskCalculator: Position sizing and trade validation
- PortfolioMonitor: Real-time portfolio tracking and metrics
- StopLossManager: Automated stop loss execution
"""

from .risk_calculator import RiskCalculator
from .portfolio_monitor import PortfolioMonitor, PortfolioState
from .stop_loss_manager import StopLossManager

__all__ = [
    'RiskCalculator',
    'PortfolioMonitor',
    'PortfolioState',
    'StopLossManager'
]
