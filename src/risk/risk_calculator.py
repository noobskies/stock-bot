"""
Risk calculator for position sizing and trade validation.

This module implements the core risk management rules that prevent
catastrophic losses and ensure disciplined trading.

Key Rules:
- Maximum 2% portfolio risk per trade
- Maximum 5 concurrent positions
- Maximum 20% in single position
- Maximum 20% total portfolio exposure
- Daily loss limit: 5% (circuit breaker)
"""

from typing import Tuple, Dict, Optional
from datetime import datetime
from loguru import logger

from src.bot_types.trading_types import (
    TradingSignal,
    Position,
    RiskMetrics,
    BotConfig
)


class RiskCalculator:
    """
    Calculate position sizes and validate trades against risk rules.
    
    All risk rules are HARD CONSTRAINTS - no trade executes if rules violated.
    """
    
    def __init__(self, config: BotConfig):
        """
        Initialize risk calculator.
        
        Args:
            config: Bot configuration with risk parameters
        """
        self.config = config
        logger.info("RiskCalculator initialized with rules:")
        logger.info(f"  Risk per trade: {config.risk_per_trade * 100}%")
        logger.info(f"  Max positions: {config.max_positions}")
        logger.info(f"  Max position size: {config.max_position_size * 100}%")
        logger.info(f"  Max portfolio exposure: {config.max_portfolio_exposure * 100}%")
        logger.info(f"  Daily loss limit: {config.daily_loss_limit * 100}%")
        logger.info(f"  Stop loss: {config.stop_loss_percent * 100}%")
    
    def calculate_position_size(
        self,
        signal: TradingSignal,
        portfolio_value: float,
        current_price: float
    ) -> int:
        """
        Calculate number of shares to buy based on 2% risk rule.
        
        Formula:
        1. Risk amount = portfolio_value * risk_per_trade (2%)
        2. Risk per share = current_price * stop_loss_percent (3%)
        3. Shares = risk_amount / risk_per_share
        4. Apply max position size limit (20% of portfolio)
        
        Args:
            signal: Trading signal
            portfolio_value: Total portfolio value
            current_price: Current stock price
        
        Returns:
            Number of shares to buy (0 if invalid)
        """
        # Calculate risk amount (2% of portfolio)
        risk_amount = portfolio_value * self.config.risk_per_trade
        
        # Calculate risk per share (stop loss distance)
        risk_per_share = current_price * self.config.stop_loss_percent
        
        if risk_per_share <= 0:
            logger.error(f"Invalid risk per share: {risk_per_share}")
            return 0
        
        # Calculate shares based on risk
        shares_by_risk = int(risk_amount / risk_per_share)
        
        # Calculate max shares based on position size limit (20% of portfolio)
        max_position_value = portfolio_value * self.config.max_position_size
        max_shares_by_limit = int(max_position_value / current_price)
        
        # Take minimum of both constraints
        shares = min(shares_by_risk, max_shares_by_limit)
        
        # Ensure at least 1 share (if affordable)
        if shares < 1 and current_price <= portfolio_value * self.config.max_position_size:
            shares = 1
        
        logger.info(
            f"Position size calculated for {signal.symbol}: "
            f"{shares} shares (${shares * current_price:.2f})"
        )
        logger.debug(
            f"  Risk amount: ${risk_amount:.2f}, "
            f"Risk per share: ${risk_per_share:.2f}, "
            f"Max by limit: {max_shares_by_limit} shares"
        )
        
        return shares
    
    def calculate_stop_loss_price(
        self,
        entry_price: float,
        stop_loss_percent: Optional[float] = None
    ) -> float:
        """
        Calculate stop loss price.
        
        Args:
            entry_price: Entry price of position
            stop_loss_percent: Stop loss percentage (default: from config)
        
        Returns:
            Stop loss price
        """
        if stop_loss_percent is None:
            stop_loss_percent = self.config.stop_loss_percent
        
        stop_price = entry_price * (1 - stop_loss_percent)
        
        logger.debug(
            f"Stop loss calculated: ${stop_price:.2f} "
            f"({stop_loss_percent * 100}% below ${entry_price:.2f})"
        )
        
        return round(stop_price, 2)
    
    def calculate_trailing_stop_price(
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
    
    def validate_trade(
        self,
        signal: TradingSignal,
        risk_metrics: RiskMetrics,
        current_positions: list[Position]
    ) -> Tuple[bool, str]:
        """
        Validate trade against all risk rules.
        
        This is the GATEKEEPER - no trade executes unless all checks pass.
        
        Args:
            signal: Trading signal to validate
            risk_metrics: Current portfolio risk metrics
            current_positions: List of open positions
        
        Returns:
            Tuple of (is_valid, reason)
            - is_valid: True if all checks pass
            - reason: Explanation for rejection (empty if valid)
        """
        # Check 1: Daily loss limit (circuit breaker)
        if risk_metrics.daily_loss_limit_reached:
            reason = (
                f"Daily loss limit reached: "
                f"{risk_metrics.daily_pnl_percent:.2f}% "
                f"(limit: {self.config.daily_loss_limit * 100}%)"
            )
            logger.warning(f"Trade rejected: {reason}")
            return False, reason
        
        # Check 2: Maximum positions limit
        if risk_metrics.positions_used >= self.config.max_positions:
            reason = (
                f"Maximum positions reached: {risk_metrics.positions_used} "
                f"(limit: {self.config.max_positions})"
            )
            logger.warning(f"Trade rejected: {reason}")
            return False, reason
        
        # Check 3: Already have position in this symbol
        for position in current_positions:
            if position.symbol == signal.symbol and position.status.value == "open":
                reason = f"Position already exists in {signal.symbol}"
                logger.warning(f"Trade rejected: {reason}")
                return False, reason
        
        # Check 4: Calculate position value and check limits
        if signal.entry_price and signal.quantity:
            position_value = signal.entry_price * signal.quantity
            
            # Check single position size limit (20% of portfolio)
            max_position_value = risk_metrics.portfolio_value * self.config.max_position_size
            if position_value > max_position_value:
                reason = (
                    f"Position too large: ${position_value:.2f} "
                    f"(limit: ${max_position_value:.2f}, "
                    f"{self.config.max_position_size * 100}%)"
                )
                logger.warning(f"Trade rejected: {reason}")
                return False, reason
            
            # Check total exposure limit (20% of portfolio)
            new_total_exposure = risk_metrics.total_exposure + position_value
            max_total_exposure = risk_metrics.portfolio_value * self.config.max_portfolio_exposure
            
            if new_total_exposure > max_total_exposure:
                reason = (
                    f"Portfolio exposure limit exceeded: "
                    f"${new_total_exposure:.2f} "
                    f"(limit: ${max_total_exposure:.2f}, "
                    f"{self.config.max_portfolio_exposure * 100}%)"
                )
                logger.warning(f"Trade rejected: {reason}")
                return False, reason
        
        # Check 5: Sufficient buying power
        if signal.entry_price and signal.quantity:
            required_capital = signal.entry_price * signal.quantity
            if required_capital > risk_metrics.cash_available:
                reason = (
                    f"Insufficient buying power: "
                    f"${required_capital:.2f} required, "
                    f"${risk_metrics.cash_available:.2f} available"
                )
                logger.warning(f"Trade rejected: {reason}")
                return False, reason
        
        # Check 6: Signal confidence meets threshold
        min_confidence = self.config.prediction_confidence_threshold
        if signal.confidence < min_confidence:
            reason = (
                f"Confidence too low: {signal.confidence:.2f} "
                f"(minimum: {min_confidence:.2f})"
            )
            logger.info(f"Trade rejected: {reason}")
            return False, reason
        
        # All checks passed
        logger.info(
            f"Trade validated for {signal.symbol}: "
            f"{signal.quantity} shares at ${signal.entry_price:.2f}"
        )
        return True, ""
    
    def calculate_risk_amount(
        self,
        entry_price: float,
        stop_loss: float,
        quantity: int
    ) -> float:
        """
        Calculate total risk amount for a trade.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            quantity: Number of shares
        
        Returns:
            Total risk in dollars
        """
        risk_per_share = entry_price - stop_loss
        total_risk = risk_per_share * quantity
        
        return round(total_risk, 2)
    
    def validate_buying_power(
        self,
        required_capital: float,
        available_cash: float
    ) -> Tuple[bool, str]:
        """
        Validate sufficient buying power.
        
        Args:
            required_capital: Amount needed for trade
            available_cash: Available cash in account
        
        Returns:
            Tuple of (is_valid, reason)
        """
        if required_capital > available_cash:
            return False, (
                f"Insufficient funds: ${required_capital:.2f} needed, "
                f"${available_cash:.2f} available"
            )
        
        return True, ""
    
    def get_max_shares_allowed(
        self,
        current_price: float,
        portfolio_value: float
    ) -> int:
        """
        Get maximum shares allowed based on position size limit.
        
        Args:
            current_price: Current stock price
            portfolio_value: Total portfolio value
        
        Returns:
            Maximum number of shares allowed
        """
        max_position_value = portfolio_value * self.config.max_position_size
        max_shares = int(max_position_value / current_price)
        
        return max_shares
    
    def should_activate_trailing_stop(
        self,
        entry_price: float,
        current_price: float
    ) -> bool:
        """
        Check if trailing stop should be activated.
        
        Trailing stop activates at 5% profit.
        
        Args:
            entry_price: Original entry price
            current_price: Current market price
        
        Returns:
            True if trailing stop should activate
        """
        profit_percent = (current_price - entry_price) / entry_price
        
        should_activate = profit_percent >= self.config.trailing_stop_activation
        
        if should_activate:
            logger.info(
                f"Trailing stop activation threshold reached: "
                f"{profit_percent * 100:.2f}% profit "
                f"(threshold: {self.config.trailing_stop_activation * 100}%)"
            )
        
        return should_activate


# Example usage
if __name__ == "__main__":
    from ..types.trading_types import SignalType, OrderStatus
    
    # Create sample config
    config = BotConfig(
        trading_mode="hybrid",
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
    
    # Initialize calculator
    calc = RiskCalculator(config)
    
    # Example 1: Calculate position size
    signal = TradingSignal(
        symbol="PLTR",
        signal_type=SignalType.BUY,
        confidence=0.75,
        predicted_direction="up",
        timestamp=datetime.now(),
        features={"rsi": 45.0, "macd": 0.5}
    )
    
    portfolio_value = 10000
    current_price = 30.0
    
    shares = calc.calculate_position_size(signal, portfolio_value, current_price)
    print(f"\n1. Position Size: {shares} shares")
    
    # Example 2: Calculate stop loss
    stop_loss = calc.calculate_stop_loss_price(entry_price=30.0)
    print(f"2. Stop Loss: ${stop_loss:.2f}")
    
    # Example 3: Validate trade
    signal.quantity = shares
    signal.entry_price = current_price
    signal.stop_loss = stop_loss
    
    risk_metrics = RiskMetrics(
        portfolio_value=10000,
        cash_available=5000,
        total_exposure=3000,
        total_exposure_percent=0.30,
        daily_pnl=-100,
        daily_pnl_percent=-0.01,
        max_position_size=2000,
        available_positions=3,
        positions_used=2,
        daily_loss_limit_reached=False,
        portfolio_risk_percent=0.04
    )
    
    is_valid, reason = calc.validate_trade(signal, risk_metrics, [])
    print(f"3. Trade Valid: {is_valid}")
    if not is_valid:
        print(f"   Reason: {reason}")
    
    # Example 4: Check trailing stop activation
    should_activate = calc.should_activate_trailing_stop(
        entry_price=30.0,
        current_price=31.60  # 5.3% profit
    )
    print(f"4. Activate Trailing Stop: {should_activate}")
