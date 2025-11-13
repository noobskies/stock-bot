"""
Portfolio monitoring and risk tracking.

This module tracks portfolio state in real-time and monitors for
risk limit violations, providing the data needed for risk validation.
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from loguru import logger

from ..types.trading_types import (
    Position,
    RiskMetrics,
    PerformanceMetrics,
    BotConfig,
    PositionStatus
)


@dataclass
class PortfolioState:
    """
    Complete portfolio state snapshot.
    
    Attributes:
        portfolio_value: Total value (cash + positions)
        cash: Available cash
        positions_value: Total value of positions
        open_positions: List of open positions
        daily_pnl: Profit/loss since market open
        start_of_day_value: Portfolio value at market open
        timestamp: When state was captured
    """
    portfolio_value: float
    cash: float
    positions_value: float
    open_positions: List[Position]
    daily_pnl: float
    start_of_day_value: float
    timestamp: datetime


class PortfolioMonitor:
    """
    Monitor portfolio state and track risk metrics in real-time.
    
    This class maintains current portfolio state and calculates
    risk metrics needed for trade validation.
    """
    
    def __init__(self, config: BotConfig, initial_capital: float):
        """
        Initialize portfolio monitor.
        
        Args:
            config: Bot configuration
            initial_capital: Starting capital
        """
        self.config = config
        self.initial_capital = initial_capital
        self.start_of_day_value = initial_capital
        self.portfolio_history: List[PortfolioState] = []
        
        logger.info(
            f"PortfolioMonitor initialized with ${initial_capital:.2f} capital"
        )
    
    def update_portfolio_state(
        self,
        current_positions: List[Position],
        cash_available: float
    ) -> PortfolioState:
        """
        Update portfolio state with current data.
        
        Args:
            current_positions: List of current positions
            cash_available: Available cash in account
        
        Returns:
            Current portfolio state
        """
        # Calculate positions value
        positions_value = sum(
            pos.quantity * pos.current_price
            for pos in current_positions
            if pos.status == PositionStatus.OPEN
        )
        
        # Calculate total portfolio value
        portfolio_value = cash_available + positions_value
        
        # Calculate daily P&L
        daily_pnl = portfolio_value - self.start_of_day_value
        
        # Create state snapshot
        state = PortfolioState(
            portfolio_value=portfolio_value,
            cash=cash_available,
            positions_value=positions_value,
            open_positions=[
                pos for pos in current_positions
                if pos.status == PositionStatus.OPEN
            ],
            daily_pnl=daily_pnl,
            start_of_day_value=self.start_of_day_value,
            timestamp=datetime.now()
        )
        
        # Add to history
        self.portfolio_history.append(state)
        
        logger.debug(
            f"Portfolio updated: ${portfolio_value:.2f} "
            f"(cash: ${cash_available:.2f}, positions: ${positions_value:.2f})"
        )
        
        return state
    
    def get_risk_metrics(
        self,
        portfolio_state: PortfolioState
    ) -> RiskMetrics:
        """
        Calculate current risk metrics.
        
        Args:
            portfolio_state: Current portfolio state
        
        Returns:
            Risk metrics for validation
        """
        # Calculate exposure
        total_exposure = portfolio_state.positions_value
        exposure_percent = (
            total_exposure / portfolio_state.portfolio_value
            if portfolio_state.portfolio_value > 0 else 0
        )
        
        # Calculate daily P&L percentage
        daily_pnl_percent = (
            portfolio_state.daily_pnl / portfolio_state.start_of_day_value
            if portfolio_state.start_of_day_value > 0 else 0
        )
        
        # Check if daily loss limit reached
        daily_loss_limit_reached = (
            daily_pnl_percent <= -self.config.daily_loss_limit
        )
        
        # Calculate max position size
        max_position_size = (
            portfolio_state.portfolio_value * self.config.max_position_size
        )
        
        # Calculate available positions
        positions_used = len(portfolio_state.open_positions)
        available_positions = self.config.max_positions - positions_used
        
        # Calculate portfolio risk (sum of all position risks)
        portfolio_risk_percent = self._calculate_portfolio_risk(
            portfolio_state.open_positions,
            portfolio_state.portfolio_value
        )
        
        metrics = RiskMetrics(
            portfolio_value=portfolio_state.portfolio_value,
            cash_available=portfolio_state.cash,
            total_exposure=total_exposure,
            total_exposure_percent=exposure_percent,
            daily_pnl=portfolio_state.daily_pnl,
            daily_pnl_percent=daily_pnl_percent,
            max_position_size=max_position_size,
            available_positions=available_positions,
            positions_used=positions_used,
            daily_loss_limit_reached=daily_loss_limit_reached,
            portfolio_risk_percent=portfolio_risk_percent
        )
        
        logger.debug(
            f"Risk metrics: Exposure {exposure_percent:.1%}, "
            f"Daily P&L {daily_pnl_percent:.1%}, "
            f"Positions {positions_used}/{self.config.max_positions}"
        )
        
        if daily_loss_limit_reached:
            logger.warning(
                f"⚠️ DAILY LOSS LIMIT REACHED: {daily_pnl_percent:.2%} "
                f"(limit: {self.config.daily_loss_limit:.2%})"
            )
        
        return metrics
    
    def _calculate_portfolio_risk(
        self,
        positions: List[Position],
        portfolio_value: float
    ) -> float:
        """
        Calculate total portfolio risk as percentage.
        
        Sum of all position risks (distance to stop loss).
        
        Args:
            positions: List of open positions
            portfolio_value: Current portfolio value
        
        Returns:
            Portfolio risk as percentage
        """
        if portfolio_value <= 0:
            return 0.0
        
        total_risk = sum(
            (pos.current_price - pos.stop_loss) * pos.quantity
            for pos in positions
        )
        
        risk_percent = total_risk / portfolio_value
        
        return risk_percent
    
    def check_daily_loss_limit(
        self,
        portfolio_state: PortfolioState
    ) -> tuple[bool, float]:
        """
        Check if daily loss limit has been exceeded.
        
        Args:
            portfolio_state: Current portfolio state
        
        Returns:
            Tuple of (limit_exceeded, current_loss_percent)
        """
        daily_pnl_percent = (
            portfolio_state.daily_pnl / portfolio_state.start_of_day_value
            if portfolio_state.start_of_day_value > 0 else 0
        )
        
        limit_exceeded = daily_pnl_percent <= -self.config.daily_loss_limit
        
        if limit_exceeded:
            logger.critical(
                f"🛑 CIRCUIT BREAKER TRIGGERED: "
                f"Daily loss {daily_pnl_percent:.2%} exceeds limit "
                f"of {self.config.daily_loss_limit:.2%}"
            )
        
        return limit_exceeded, daily_pnl_percent
    
    def reset_daily_tracking(self, current_portfolio_value: float):
        """
        Reset daily tracking for new trading day.
        
        Call this at market open.
        
        Args:
            current_portfolio_value: Portfolio value at market open
        """
        self.start_of_day_value = current_portfolio_value
        
        logger.info(
            f"Daily tracking reset. Start of day value: "
            f"${current_portfolio_value:.2f}"
        )
    
    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sharpe ratio (risk-adjusted returns).
        
        Sharpe Ratio = (Mean Return - Risk Free Rate) / Std Dev of Returns
        
        Args:
            returns: List of daily returns (as decimals)
            risk_free_rate: Annual risk-free rate (default: 2%)
        
        Returns:
            Sharpe ratio (annualized)
        """
        if len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        
        # Calculate metrics
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array)
        
        if std_return == 0:
            return 0.0
        
        # Daily risk-free rate
        daily_rf_rate = risk_free_rate / 252  # 252 trading days
        
        # Calculate Sharpe ratio
        sharpe = (mean_return - daily_rf_rate) / std_return
        
        # Annualize (multiply by sqrt of trading days)
        sharpe_annualized = sharpe * np.sqrt(252)
        
        return round(sharpe_annualized, 2)
    
    def calculate_max_drawdown(
        self,
        portfolio_values: List[float]
    ) -> tuple[float, float]:
        """
        Calculate maximum drawdown from peak.
        
        Args:
            portfolio_values: Historical portfolio values
        
        Returns:
            Tuple of (max_drawdown_dollars, max_drawdown_percent)
        """
        if len(portfolio_values) < 2:
            return 0.0, 0.0
        
        values = np.array(portfolio_values)
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(values)
        
        # Calculate drawdowns
        drawdowns = values - running_max
        
        # Find maximum drawdown
        max_dd = np.min(drawdowns)
        
        # Find the peak it came from
        max_dd_index = np.argmin(drawdowns)
        peak_value = running_max[max_dd_index]
        
        # Calculate percentage
        max_dd_percent = max_dd / peak_value if peak_value > 0 else 0.0
        
        return round(max_dd, 2), round(max_dd_percent, 4)
    
    def calculate_performance_metrics(
        self,
        trades: List[Dict]
    ) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            trades: List of completed trade records
        
        Returns:
            Performance metrics
        """
        if not trades:
            return PerformanceMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                average_win=0.0,
                average_loss=0.0,
                largest_win=0.0,
                largest_loss=0.0,
                total_pnl=0.0,
                total_pnl_percent=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_percent=0.0,
                current_streak=0,
                longest_win_streak=0,
                longest_loss_streak=0
            )
        
        # Separate winning and losing trades
        winning_trades = [t for t in trades if t.get('realized_pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('realized_pnl', 0) < 0]
        
        # Calculate basic metrics
        total_trades = len(trades)
        num_winning = len(winning_trades)
        num_losing = len(losing_trades)
        win_rate = num_winning / total_trades if total_trades > 0 else 0.0
        
        # Calculate P&L metrics
        total_pnl = sum(t.get('realized_pnl', 0) for t in trades)
        
        avg_win = (
            np.mean([t['realized_pnl'] for t in winning_trades])
            if winning_trades else 0.0
        )
        avg_loss = (
            np.mean([t['realized_pnl'] for t in losing_trades])
            if losing_trades else 0.0
        )
        
        largest_win = (
            max(t['realized_pnl'] for t in winning_trades)
            if winning_trades else 0.0
        )
        largest_loss = (
            min(t['realized_pnl'] for t in losing_trades)
            if losing_trades else 0.0
        )
        
        # Calculate returns for Sharpe ratio
        returns = [
            t.get('realized_pnl', 0) / (t.get('entry_price', 1) * t.get('quantity', 1))
            for t in trades
        ]
        sharpe_ratio = self.calculate_sharpe_ratio(returns)
        
        # Calculate drawdown from portfolio values
        if self.portfolio_history:
            portfolio_values = [s.portfolio_value for s in self.portfolio_history]
            max_dd, max_dd_pct = self.calculate_max_drawdown(portfolio_values)
        else:
            max_dd, max_dd_pct = 0.0, 0.0
        
        # Calculate streaks
        current_streak = self._calculate_current_streak(trades)
        longest_win, longest_loss = self._calculate_longest_streaks(trades)
        
        # Total P&L percent
        total_pnl_percent = (
            total_pnl / self.initial_capital
            if self.initial_capital > 0 else 0.0
        )
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=num_winning,
            losing_trades=num_losing,
            win_rate=round(win_rate, 4),
            average_win=round(avg_win, 2),
            average_loss=round(avg_loss, 2),
            largest_win=round(largest_win, 2),
            largest_loss=round(largest_loss, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_percent=round(total_pnl_percent, 4),
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_dd,
            max_drawdown_percent=max_dd_pct,
            current_streak=current_streak,
            longest_win_streak=longest_win,
            longest_loss_streak=longest_loss
        )
    
    def _calculate_current_streak(self, trades: List[Dict]) -> int:
        """Calculate current winning/losing streak."""
        if not trades:
            return 0
        
        # Sort by exit time
        sorted_trades = sorted(
            trades,
            key=lambda t: t.get('exit_time', datetime.min)
        )
        
        streak = 0
        last_result = None
        
        for trade in reversed(sorted_trades):
            pnl = trade.get('realized_pnl', 0)
            current_result = 'win' if pnl > 0 else 'loss'
            
            if last_result is None:
                last_result = current_result
                streak = 1
            elif current_result == last_result:
                streak += 1
            else:
                break
        
        # Negative for losing streak
        return streak if last_result == 'win' else -streak
    
    def _calculate_longest_streaks(
        self,
        trades: List[Dict]
    ) -> tuple[int, int]:
        """Calculate longest winning and losing streaks."""
        if not trades:
            return 0, 0
        
        sorted_trades = sorted(
            trades,
            key=lambda t: t.get('exit_time', datetime.min)
        )
        
        longest_win = 0
        longest_loss = 0
        current_win = 0
        current_loss = 0
        
        for trade in sorted_trades:
            pnl = trade.get('realized_pnl', 0)
            
            if pnl > 0:
                current_win += 1
                current_loss = 0
                longest_win = max(longest_win, current_win)
            else:
                current_loss += 1
                current_win = 0
                longest_loss = max(longest_loss, current_loss)
        
        return longest_win, longest_loss
    
    def get_portfolio_summary(self, portfolio_state: PortfolioState) -> Dict:
        """
        Get human-readable portfolio summary.
        
        Args:
            portfolio_state: Current portfolio state
        
        Returns:
            Dictionary with formatted summary
        """
        risk_metrics = self.get_risk_metrics(portfolio_state)
        
        return {
            'portfolio_value': f"${portfolio_state.portfolio_value:,.2f}",
            'cash': f"${portfolio_state.cash:,.2f}",
            'positions_value': f"${portfolio_state.positions_value:,.2f}",
            'open_positions': len(portfolio_state.open_positions),
            'daily_pnl': f"${portfolio_state.daily_pnl:,.2f}",
            'daily_pnl_percent': f"{risk_metrics.daily_pnl_percent:.2%}",
            'exposure_percent': f"{risk_metrics.total_exposure_percent:.2%}",
            'risk_percent': f"{risk_metrics.portfolio_risk_percent:.2%}",
            'available_positions': risk_metrics.available_positions,
            'daily_loss_limit_reached': risk_metrics.daily_loss_limit_reached
        }


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
    
    # Initialize monitor
    monitor = PortfolioMonitor(config, initial_capital=10000)
    
    # Example 1: Update portfolio state
    positions = [
        Position(
            symbol="PLTR",
            quantity=50,
            entry_price=30.0,
            current_price=31.5,
            stop_loss=29.1,
            unrealized_pnl=75.0,
            status=PositionStatus.OPEN,
            entry_time=datetime.now(),
            unrealized_pnl_percent=0.05
        )
    ]
    
    state = monitor.update_portfolio_state(
        current_positions=positions,
        cash_available=8500
    )
    
    print("\n1. Portfolio State:")
    print(f"   Value: ${state.portfolio_value:.2f}")
    print(f"   Cash: ${state.cash:.2f}")
    print(f"   Positions: ${state.positions_value:.2f}")
    print(f"   Daily P&L: ${state.daily_pnl:.2f}")
    
    # Example 2: Get risk metrics
    metrics = monitor.get_risk_metrics(state)
    print(f"\n2. Risk Metrics:")
    print(f"   Exposure: {metrics.total_exposure_percent:.1%}")
    print(f"   Daily P&L: {metrics.daily_pnl_percent:.2%}")
    print(f"   Positions: {metrics.positions_used}/{config.max_positions}")
    print(f"   Loss limit reached: {metrics.daily_loss_limit_reached}")
    
    # Example 3: Check daily loss limit
    limit_exceeded, loss_pct = monitor.check_daily_loss_limit(state)
    print(f"\n3. Daily Loss Check:")
    print(f"   Current loss: {loss_pct:.2%}")
    print(f"   Limit exceeded: {limit_exceeded}")
    
    # Example 4: Calculate Sharpe ratio
    returns = [0.01, -0.005, 0.02, 0.015, -0.01]
    sharpe = monitor.calculate_sharpe_ratio(returns)
    print(f"\n4. Sharpe Ratio: {sharpe:.2f}")
    
    # Example 5: Portfolio summary
    summary = monitor.get_portfolio_summary(state)
    print(f"\n5. Portfolio Summary:")
    for key, value in summary.items():
        print(f"   {key}: {value}")
