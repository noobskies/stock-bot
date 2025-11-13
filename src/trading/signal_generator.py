"""
Signal Generator - Convert ML predictions into trading signals.

This module takes ML predictions and determines whether they should be
converted into actionable trading signals based on confidence thresholds,
trading mode, and current portfolio state.

Key Features:
- Prediction-to-signal conversion
- Confidence-based filtering
- Mode-based execution decisions (auto/manual/hybrid)
- Signal validation and enrichment
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict
from enum import Enum

from loguru import logger

from src.types.trading_types import (
    ModelPrediction,
    TradingSignal,
    SignalType,
    TradingMode,
    Position
)


class SignalGenerator:
    """
    Generate trading signals from ML predictions.
    
    This class converts ML model predictions into actionable trading signals,
    applying confidence thresholds and trading mode logic to determine which
    signals should be executed automatically vs. requiring manual approval.
    
    Attributes:
        confidence_threshold: Minimum confidence for signal generation (default: 0.70)
        auto_threshold: Confidence threshold for auto-execution (default: 0.80)
        trading_mode: Current trading mode (auto/manual/hybrid)
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.70,
        auto_threshold: float = 0.80,
        trading_mode: TradingMode = TradingMode.HYBRID
    ):
        """
        Initialize signal generator.
        
        Args:
            confidence_threshold: Minimum confidence to generate signal (0.0-1.0)
            auto_threshold: Confidence for auto-execution (0.0-1.0)
            trading_mode: Trading mode (AUTO, MANUAL, HYBRID)
        """
        self.confidence_threshold = confidence_threshold
        self.auto_threshold = auto_threshold
        self.trading_mode = trading_mode
        
        logger.info(
            f"SignalGenerator initialized - Mode: {trading_mode.value}, "
            f"Confidence threshold: {confidence_threshold:.2f}, "
            f"Auto threshold: {auto_threshold:.2f}"
        )
    
    def generate_signal(
        self,
        prediction: ModelPrediction,
        current_price: float,
        current_position: Optional[Position] = None,
        account_value: float = 10000.0
    ) -> Optional[TradingSignal]:
        """
        Generate a trading signal from an ML prediction.
        
        Args:
            prediction: ML model prediction
            current_price: Current market price
            current_position: Existing position (if any)
            account_value: Total account value for position sizing
        
        Returns:
            TradingSignal or None if confidence too low
        
        Example:
            signal = generator.generate_signal(
                prediction=model_prediction,
                current_price=30.50,
                current_position=existing_position,
                account_value=10000.0
            )
        """
        # Check if confidence meets minimum threshold
        if prediction.confidence < self.confidence_threshold:
            logger.debug(
                f"Prediction confidence {prediction.confidence:.2f} below "
                f"threshold {self.confidence_threshold:.2f} - skipping"
            )
            return None
        
        # Determine signal type based on prediction and current position
        signal_type = self._determine_signal_type(
            prediction,
            current_position
        )
        
        if signal_type is None:
            logger.debug("No actionable signal generated")
            return None
        
        # Determine if signal should auto-execute
        should_auto_execute = self._should_auto_execute(prediction.confidence)
        
        # Create trading signal
        signal = TradingSignal(
            symbol=prediction.symbol,
            signal_type=signal_type,
            confidence=prediction.confidence,
            entry_price=current_price,
            timestamp=datetime.now(timezone.utc),
            model_prediction=prediction.predicted_direction,
            technical_indicators=prediction.feature_importance,
            reasoning=self._generate_reasoning(prediction, signal_type),
            requires_approval=not should_auto_execute
        )
        
        logger.info(
            f"Signal generated: {signal.signal_type.value} {signal.symbol} "
            f"(confidence: {signal.confidence:.2%}, "
            f"auto-execute: {not signal.requires_approval})"
        )
        
        return signal
    
    def _determine_signal_type(
        self,
        prediction: ModelPrediction,
        current_position: Optional[Position]
    ) -> Optional[SignalType]:
        """
        Determine signal type based on prediction and position.
        
        Args:
            prediction: ML model prediction
            current_position: Current position (if any)
        
        Returns:
            SignalType (BUY/SELL) or None
        
        Logic:
            - If no position and prediction UP → BUY
            - If no position and prediction DOWN → No signal
            - If long position and prediction UP → Hold (no signal)
            - If long position and prediction DOWN → SELL
        """
        predicted_direction = prediction.predicted_direction.upper()
        
        # No current position
        if current_position is None:
            if predicted_direction == 'UP':
                return SignalType.BUY
            else:
                # Don't generate short signals (not implemented)
                return None
        
        # Have a position
        else:
            if predicted_direction == 'DOWN':
                # Exit long position
                return SignalType.SELL
            else:
                # Continue holding (no signal needed)
                logger.debug(
                    f"Position {current_position.symbol} prediction UP - "
                    f"continue holding"
                )
                return None
    
    def _should_auto_execute(self, confidence: float) -> bool:
        """
        Determine if signal should auto-execute based on mode and confidence.
        
        Args:
            confidence: Signal confidence (0.0-1.0)
        
        Returns:
            True if should auto-execute, False if requires approval
        
        Logic:
            - AUTO mode: Always auto-execute (if confidence >= threshold)
            - MANUAL mode: Never auto-execute
            - HYBRID mode: Auto-execute if confidence >= auto_threshold
        """
        if self.trading_mode == TradingMode.AUTO:
            return True
        elif self.trading_mode == TradingMode.MANUAL:
            return False
        else:  # HYBRID
            return confidence >= self.auto_threshold
    
    def _generate_reasoning(
        self,
        prediction: ModelPrediction,
        signal_type: SignalType
    ) -> str:
        """
        Generate human-readable reasoning for the signal.
        
        Args:
            prediction: ML model prediction
            signal_type: Type of signal (BUY/SELL)
        
        Returns:
            Reasoning string explaining the signal
        """
        direction = prediction.predicted_direction.upper()
        confidence = prediction.confidence
        
        reasoning = (
            f"ML model predicts {direction} movement with "
            f"{confidence:.1%} confidence. "
        )
        
        # Add top technical indicators if available
        if prediction.feature_importance:
            top_features = sorted(
                prediction.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            if top_features:
                reasoning += "Key indicators: "
                indicator_strings = [
                    f"{name} ({importance:.2f})"
                    for name, importance in top_features
                ]
                reasoning += ", ".join(indicator_strings) + ". "
        
        # Add action recommendation
        if signal_type == SignalType.BUY:
            reasoning += "Recommend opening long position."
        elif signal_type == SignalType.SELL:
            reasoning += "Recommend closing position to lock in gains/limit losses."
        
        return reasoning
    
    def generate_exit_signal(
        self,
        position: Position,
        reason: str,
        current_price: float
    ) -> TradingSignal:
        """
        Generate an exit signal for an existing position.
        
        This is used by stop loss manager or other risk management components
        to force exit a position.
        
        Args:
            position: Position to exit
            reason: Reason for exit (e.g., "Stop loss triggered")
            current_price: Current market price
        
        Returns:
            TradingSignal for selling the position
        """
        signal = TradingSignal(
            symbol=position.symbol,
            signal_type=SignalType.SELL,
            confidence=1.0,  # Risk management exits are always high confidence
            entry_price=current_price,
            timestamp=datetime.now(timezone.utc),
            model_prediction='FORCED_EXIT',
            technical_indicators={},
            reasoning=reason,
            requires_approval=False  # Risk exits never require approval
        )
        
        logger.info(
            f"Exit signal generated: {signal.symbol} - {reason}"
        )
        
        return signal
    
    def filter_signals(
        self,
        signals: List[TradingSignal],
        max_positions: int = 5,
        current_position_count: int = 0
    ) -> List[TradingSignal]:
        """
        Filter signals based on portfolio constraints.
        
        Args:
            signals: List of generated signals
            max_positions: Maximum allowed concurrent positions
            current_position_count: Number of current open positions
        
        Returns:
            Filtered list of signals that can be executed
        """
        # Separate buy and sell signals
        buy_signals = [s for s in signals if s.signal_type == SignalType.BUY]
        sell_signals = [s for s in signals if s.signal_type == SignalType.SELL]
        
        # Sell signals are always allowed (closing positions)
        filtered = sell_signals.copy()
        
        # For buy signals, check position limit
        available_slots = max_positions - current_position_count
        
        if available_slots <= 0:
            logger.warning(
                f"Maximum positions ({max_positions}) reached - "
                f"skipping {len(buy_signals)} buy signals"
            )
        else:
            # Sort buy signals by confidence (highest first)
            buy_signals.sort(key=lambda s: s.confidence, reverse=True)
            
            # Take only signals that fit available slots
            filtered.extend(buy_signals[:available_slots])
            
            if len(buy_signals) > available_slots:
                logger.info(
                    f"Limited to {available_slots} buy signals due to "
                    f"position limits (skipped {len(buy_signals) - available_slots})"
                )
        
        return filtered
    
    def set_trading_mode(self, mode: TradingMode):
        """
        Update the trading mode.
        
        Args:
            mode: New trading mode (AUTO/MANUAL/HYBRID)
        """
        old_mode = self.trading_mode
        self.trading_mode = mode
        logger.info(f"Trading mode changed: {old_mode.value} → {mode.value}")
    
    def set_thresholds(
        self,
        confidence_threshold: Optional[float] = None,
        auto_threshold: Optional[float] = None
    ):
        """
        Update confidence thresholds.
        
        Args:
            confidence_threshold: Minimum confidence for signal generation
            auto_threshold: Confidence threshold for auto-execution
        """
        if confidence_threshold is not None:
            old = self.confidence_threshold
            self.confidence_threshold = confidence_threshold
            logger.info(
                f"Confidence threshold changed: {old:.2f} → {confidence_threshold:.2f}"
            )
        
        if auto_threshold is not None:
            old = self.auto_threshold
            self.auto_threshold = auto_threshold
            logger.info(
                f"Auto threshold changed: {old:.2f} → {auto_threshold:.2f}"
            )


class SignalQueue:
    """
    Queue for managing pending signals awaiting approval.
    
    This class maintains a queue of signals that require manual approval
    before execution, providing methods to approve, reject, or modify them.
    """
    
    def __init__(self):
        """Initialize empty signal queue."""
        self.pending_signals: Dict[str, TradingSignal] = {}
        self._signal_counter = 0
    
    def add_signal(self, signal: TradingSignal) -> str:
        """
        Add a signal to the pending queue.
        
        Args:
            signal: Trading signal requiring approval
        
        Returns:
            Signal ID for tracking
        """
        self._signal_counter += 1
        signal_id = f"SIG-{self._signal_counter:04d}"
        self.pending_signals[signal_id] = signal
        
        logger.info(
            f"Signal added to queue: {signal_id} - "
            f"{signal.signal_type.value} {signal.symbol} "
            f"(confidence: {signal.confidence:.2%})"
        )
        
        return signal_id
    
    def get_pending_signals(self) -> Dict[str, TradingSignal]:
        """
        Get all pending signals.
        
        Returns:
            Dictionary of signal_id: TradingSignal
        """
        return self.pending_signals.copy()
    
    def approve_signal(self, signal_id: str) -> Optional[TradingSignal]:
        """
        Approve a signal for execution.
        
        Args:
            signal_id: ID of signal to approve
        
        Returns:
            Approved signal or None if not found
        """
        signal = self.pending_signals.pop(signal_id, None)
        if signal:
            logger.info(f"Signal approved: {signal_id}")
        else:
            logger.warning(f"Signal not found for approval: {signal_id}")
        return signal
    
    def reject_signal(self, signal_id: str) -> bool:
        """
        Reject a signal (remove from queue).
        
        Args:
            signal_id: ID of signal to reject
        
        Returns:
            True if signal was found and rejected
        """
        signal = self.pending_signals.pop(signal_id, None)
        if signal:
            logger.info(
                f"Signal rejected: {signal_id} - "
                f"{signal.signal_type.value} {signal.symbol}"
            )
            return True
        else:
            logger.warning(f"Signal not found for rejection: {signal_id}")
            return False
    
    def clear_queue(self):
        """Clear all pending signals."""
        count = len(self.pending_signals)
        self.pending_signals.clear()
        logger.info(f"Signal queue cleared - {count} signals removed")
    
    def get_signal_count(self) -> int:
        """Get number of pending signals."""
        return len(self.pending_signals)


# Example usage
if __name__ == "__main__":
    """
    Example usage of SignalGenerator and SignalQueue.
    
    This demonstrates:
    - Creating a signal generator
    - Generating signals from predictions
    - Managing signal queue for manual approval
    """
    from datetime import datetime, timezone
    
    # Create signal generator (hybrid mode)
    generator = SignalGenerator(
        confidence_threshold=0.70,
        auto_threshold=0.80,
        trading_mode=TradingMode.HYBRID
    )
    
    # Create mock prediction
    prediction = ModelPrediction(
        symbol='PLTR',
        timestamp=datetime.now(timezone.utc),
        predicted_direction='UP',
        confidence=0.75,
        model_type='LSTM',
        feature_importance={
            'RSI': 0.25,
            'MACD': 0.20,
            'SMA_20': 0.15,
            'Volume': 0.10
        }
    )
    
    # Generate signal
    print("\n=== Generating Signal ===")
    signal = generator.generate_signal(
        prediction=prediction,
        current_price=30.50,
        current_position=None,
        account_value=10000.0
    )
    
    if signal:
        print(f"Signal Type: {signal.signal_type.value}")
        print(f"Symbol: {signal.symbol}")
        print(f"Confidence: {signal.confidence:.2%}")
        print(f"Entry Price: ${signal.entry_price:.2f}")
        print(f"Requires Approval: {signal.requires_approval}")
        print(f"Reasoning: {signal.reasoning}")
    
    # Demonstrate signal queue
    print("\n=== Signal Queue ===")
    queue = SignalQueue()
    
    if signal and signal.requires_approval:
        signal_id = queue.add_signal(signal)
        print(f"Signal added to queue: {signal_id}")
        print(f"Pending signals: {queue.get_signal_count()}")
        
        # Approve the signal
        approved = queue.approve_signal(signal_id)
        if approved:
            print(f"Signal approved and ready for execution")
            print(f"Remaining pending signals: {queue.get_signal_count()}")
    
    # Demonstrate high-confidence signal (auto-execute)
    print("\n=== High Confidence Signal ===")
    high_conf_prediction = ModelPrediction(
        symbol='PLTR',
        timestamp=datetime.now(timezone.utc),
        predicted_direction='UP',
        confidence=0.85,  # Above auto threshold
        model_type='LSTM',
        feature_importance={'RSI': 0.30, 'MACD': 0.25}
    )
    
    high_conf_signal = generator.generate_signal(
        prediction=high_conf_prediction,
        current_price=30.75,
        current_position=None,
        account_value=10000.0
    )
    
    if high_conf_signal:
        print(f"Confidence: {high_conf_signal.confidence:.2%}")
        print(f"Auto-execute: {not high_conf_signal.requires_approval}")
