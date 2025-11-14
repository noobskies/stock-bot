"""
Data validation utilities for trade and position validation.

This module provides validator classes that extract and centralize validation
logic previously scattered across RiskCalculator and other modules.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.bot_types.trading_types import TradingSignal, Position


@dataclass
class ValidationResult:
    """
    Result of a validation operation.
    
    Attributes:
        is_valid: Whether validation passed
        reason: Explanation if validation failed
        details: Additional details about the validation
    """
    
    is_valid: bool
    reason: str = ""
    details: Optional[Dict[str, Any]] = None
    
    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.is_valid


class TradeValidator:
    """
    Validator for trade signals and execution decisions.
    
    Extracted from RiskCalculator to separate validation logic
    from calculation logic (Single Responsibility Principle).
    """
    
    @staticmethod
    def validate_signal(
        signal: TradingSignal,
        portfolio_value: float,
        current_positions: List[Position],
        daily_loss: float,
        config: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate a trading signal against risk rules.
        
        This replaces the inline validation logic previously in RiskCalculator.
        
        Args:
            signal: Trading signal to validate
            portfolio_value: Current portfolio value
            current_positions: List of currently open positions
            daily_loss: Daily loss amount (positive value)
            config: Configuration with risk parameters
            
        Returns:
            ValidationResult with validation outcome
            
        Example:
            result = TradeValidator.validate_signal(signal, 10000, [], 0, config)
            if result.is_valid:
                execute_trade(signal)
            else:
                logger.warning(f"Trade rejected: {result.reason}")
        """
        # Extract config parameters
        max_positions = config.get('max_positions', 5)
        max_portfolio_exposure = config.get('max_portfolio_exposure', 0.20)
        daily_loss_limit = config.get('daily_loss_limit', 0.05)
        risk_per_trade = config.get('risk_per_trade', 0.02)
        
        # Rule 1: Check daily loss limit
        daily_loss_pct = daily_loss / portfolio_value if portfolio_value > 0 else 0
        if daily_loss_pct >= daily_loss_limit:
            return ValidationResult(
                is_valid=False,
                reason=f"Daily loss limit exceeded: {daily_loss_pct:.2%} >= {daily_loss_limit:.2%}",
                details={'daily_loss': daily_loss, 'limit': daily_loss_limit}
            )
        
        # Rule 2: Check maximum position count (only for BUY signals)
        if signal.action.upper() == "BUY":
            if len(current_positions) >= max_positions:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Maximum positions reached: {len(current_positions)} >= {max_positions}",
                    details={'current': len(current_positions), 'max': max_positions}
                )
        
        # Rule 3: Check total portfolio exposure (only for BUY signals)
        if signal.action.upper() == "BUY":
            total_exposure = sum(pos.market_value for pos in current_positions)
            position_value = signal.quantity * signal.entry_price
            new_exposure = (total_exposure + position_value) / portfolio_value if portfolio_value > 0 else 0
            
            if new_exposure > max_portfolio_exposure:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Portfolio exposure too high: {new_exposure:.2%} > {max_portfolio_exposure:.2%}",
                    details={'new_exposure': new_exposure, 'limit': max_portfolio_exposure}
                )
        
        # Rule 4: Check position size (risk per trade)
        position_value = signal.quantity * signal.entry_price
        position_pct = position_value / portfolio_value if portfolio_value > 0 else 0
        
        if position_pct > risk_per_trade * 2:  # Allow up to 2x risk per trade
            return ValidationResult(
                is_valid=False,
                reason=f"Position size too large: {position_pct:.2%} > {risk_per_trade * 2:.2%}",
                details={'position_pct': position_pct, 'max': risk_per_trade * 2}
            )
        
        # Rule 5: Check sufficient buying power (only for BUY signals)
        if signal.action.upper() == "BUY":
            # Assuming 50% buying power (conservative estimate)
            available_cash = portfolio_value * 0.5 - sum(pos.market_value for pos in current_positions)
            if position_value > available_cash:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Insufficient buying power: ${position_value:.2f} > ${available_cash:.2f}",
                    details={'required': position_value, 'available': available_cash}
                )
        
        # All checks passed
        return ValidationResult(
            is_valid=True,
            reason="All validation checks passed",
            details={
                'daily_loss_pct': daily_loss_pct,
                'position_count': len(current_positions),
                'position_pct': position_pct,
            }
        )


class DataValidator:
    """
    Validator for market data and prices.
    
    Provides sanity checks for data quality and bounds.
    """
    
    @staticmethod
    def validate_price_bounds(
        price: float,
        symbol: str,
        min_price: float = 0.01,
        max_price: float = 10000.0,
    ) -> ValidationResult:
        """
        Validate that a price is within reasonable bounds.
        
        Args:
            price: Price to validate
            symbol: Stock symbol (for error messages)
            min_price: Minimum acceptable price
            max_price: Maximum acceptable price
            
        Returns:
            ValidationResult with validation outcome
        """
        if price <= 0:
            return ValidationResult(
                is_valid=False,
                reason=f"Invalid price for {symbol}: {price} <= 0",
            )
        
        if price < min_price:
            return ValidationResult(
                is_valid=False,
                reason=f"Price too low for {symbol}: {price} < {min_price}",
            )
        
        if price > max_price:
            return ValidationResult(
                is_valid=False,
                reason=f"Price too high for {symbol}: {price} > {max_price}",
            )
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def validate_quantity(
        quantity: int,
        max_quantity: int = 10000,
    ) -> ValidationResult:
        """
        Validate trade quantity.
        
        Args:
            quantity: Number of shares
            max_quantity: Maximum allowed quantity
            
        Returns:
            ValidationResult with validation outcome
        """
        if quantity <= 0:
            return ValidationResult(
                is_valid=False,
                reason=f"Invalid quantity: {quantity} <= 0",
            )
        
        if quantity > max_quantity:
            return ValidationResult(
                is_valid=False,
                reason=f"Quantity too large: {quantity} > {max_quantity}",
            )
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def validate_dataframe_required_columns(
        df: Any,  # pandas DataFrame
        required_columns: List[str],
    ) -> ValidationResult:
        """
        Validate that a DataFrame has required columns.
        
        Args:
            df: pandas DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            ValidationResult with validation outcome
        """
        if df is None or df.empty:
            return ValidationResult(
                is_valid=False,
                reason="DataFrame is None or empty",
            )
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return ValidationResult(
                is_valid=False,
                reason=f"Missing required columns: {missing_columns}",
                details={'missing': missing_columns, 'available': list(df.columns)}
            )
        
        return ValidationResult(is_valid=True)


class PositionValidator:
    """
    Validator for position management rules.
    
    Validates stop loss levels, position updates, and other position-related rules.
    """
    
    @staticmethod
    def validate_stop_loss(
        entry_price: float,
        stop_loss: float,
        min_distance_pct: float = 0.01,  # 1% minimum
    ) -> ValidationResult:
        """
        Validate stop loss level relative to entry price.
        
        Args:
            entry_price: Position entry price
            stop_loss: Proposed stop loss price
            min_distance_pct: Minimum distance as percentage of entry price
            
        Returns:
            ValidationResult with validation outcome
        """
        if stop_loss >= entry_price:
            return ValidationResult(
                is_valid=False,
                reason=f"Stop loss {stop_loss} must be below entry price {entry_price}",
            )
        
        distance_pct = (entry_price - stop_loss) / entry_price
        
        if distance_pct < min_distance_pct:
            return ValidationResult(
                is_valid=False,
                reason=f"Stop loss too close: {distance_pct:.2%} < {min_distance_pct:.2%}",
                details={'distance_pct': distance_pct, 'min': min_distance_pct}
            )
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def validate_trailing_stop(
        current_price: float,
        trailing_stop: float,
        entry_price: float,
    ) -> ValidationResult:
        """
        Validate trailing stop level.
        
        Args:
            current_price: Current market price
            trailing_stop: Proposed trailing stop price
            entry_price: Original entry price
            
        Returns:
            ValidationResult with validation outcome
        """
        # Trailing stop should be below current price
        if trailing_stop >= current_price:
            return ValidationResult(
                is_valid=False,
                reason=f"Trailing stop {trailing_stop} must be below current price {current_price}",
            )
        
        # Trailing stop should be above entry (in profit)
        if trailing_stop < entry_price:
            return ValidationResult(
                is_valid=False,
                reason=f"Trailing stop {trailing_stop} should be above entry {entry_price}",
            )
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def validate_position_update(
        position: Position,
        new_price: float,
    ) -> ValidationResult:
        """
        Validate a position price update.
        
        Args:
            position: Position to update
            new_price: New market price
            
        Returns:
            ValidationResult with validation outcome
        """
        # Price sanity check
        if new_price <= 0:
            return ValidationResult(
                is_valid=False,
                reason=f"Invalid price: {new_price} <= 0",
            )
        
        # Check for unreasonable price movement (>50% in one update)
        if position.current_price > 0:
            price_change_pct = abs(new_price - position.current_price) / position.current_price
            if price_change_pct > 0.50:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Unusual price movement: {price_change_pct:.2%} (possible data error)",
                    details={'old_price': position.current_price, 'new_price': new_price}
                )
        
        return ValidationResult(is_valid=True)
