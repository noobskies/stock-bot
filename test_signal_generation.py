#!/usr/bin/env python3
"""
Integration Test 9: Signal Generation
Tests the SignalGenerator and SignalQueue functionality.

Verifies:
1. Signal generation from ML predictions
2. Confidence-based filtering
3. Mode-based execution logic (auto/manual/hybrid)
4. Signal queue management
5. Position-aware signal generation
6. Clear reasoning for all decisions
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import yaml

# Import only what we need from specific modules to avoid types conflict
from trading.signal_generator import SignalGenerator, SignalQueue
from database.db_manager import DatabaseManager

# Import the enums and dataclasses we need
import sys
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'types'))
from trading_types import ModelPrediction, SignalType, TradingMode, Position, PositionStatus
sys.path.pop(0)  # Remove types from path


def load_config() -> dict:
    """Load configuration from config.yaml"""
    config_path = Path('config/config.yaml')
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    # Return dict config to avoid BotConfig import issues
    return {
        'trading_mode': config_dict['trading']['mode'],
        'symbols': config_dict['trading']['symbols'],
        'prediction_confidence_threshold': config_dict['ml']['prediction_confidence_threshold'],
        'auto_execute_threshold': config_dict['ml']['auto_execute_threshold'],
        'database_path': config_dict['database']['path'],
    }


def create_mock_prediction(
    symbol: str,
    direction: str,
    confidence: float,
    current_price: float
) -> ModelPrediction:
    """Create a mock prediction for testing"""
    predicted_price = current_price * 1.02 if direction == "UP" else current_price * 0.98
    
    return ModelPrediction(
        symbol=symbol,
        predicted_price=predicted_price,
        direction=direction,
        confidence=confidence,
        features_used=['RSI', 'MACD', 'BB', 'SMA_20', 'Volume'],
        timestamp=datetime.now(),
        model_name='ensemble',
        metadata={'current_price': current_price}
    )


def create_mock_position(symbol: str, quantity: int, entry_price: float) -> Position:
    """Create a mock position for testing"""
    return Position(
        symbol=symbol,
        quantity=quantity,
        entry_price=entry_price,
        current_price=entry_price,
        entry_time=datetime.now(),
        status=PositionStatus.OPEN,
        stop_loss=entry_price * 0.97,  # 3% stop loss
        unrealized_pnl=0.0
    )


def test_signal_generation():
    """Test signal generation functionality"""
    
    print("=" * 80)
    print("TEST 9: SIGNAL GENERATION")
    print("=" * 80)
    
    # Step 1: Setup
    print("\n[Step 1] Loading Configuration")
    config = load_config()
    trading_mode = TradingMode(config['trading_mode'])
    print(f"✓ Trading Mode: {trading_mode.value}")
    print(f"✓ Confidence Threshold: {config['prediction_confidence_threshold'] * 100}%")
    print(f"✓ Auto Execute Threshold: {config['auto_execute_threshold'] * 100}%")
    
    print("\n[Step 2] Initializing Modules")
    # Ensure proper SQLAlchemy URL format
    db_path = config['database_path']
    if not db_path.startswith('sqlite:///'):
        db_path = f"sqlite:///{db_path}"
    db = DatabaseManager(db_path)
    signal_generator = SignalGenerator(
        confidence_threshold=config['prediction_confidence_threshold'],
        auto_threshold=config['auto_execute_threshold'],
        trading_mode=trading_mode
    )
    signal_queue = SignalQueue()
    print("✓ SignalGenerator initialized")
    print("✓ SignalQueue initialized")
    
    # Step 2: Create Mock Predictions
    print("\n[Step 3] Creating Mock Predictions")
    current_price = 172.14
    predictions = [
        ("High confidence UP (85%)", create_mock_prediction("PLTR", "UP", 0.85, current_price)),
        ("Medium confidence UP (75%)", create_mock_prediction("PLTR", "UP", 0.75, current_price)),
        ("Low confidence UP (65%)", create_mock_prediction("PLTR", "UP", 0.65, current_price)),
        ("High confidence DOWN (82%)", create_mock_prediction("PLTR", "DOWN", 0.82, current_price)),
        ("Medium confidence DOWN (72%)", create_mock_prediction("PLTR", "DOWN", 0.72, current_price)),
    ]
    
    for desc, pred in predictions:
        print(f"  • {desc}: {pred.direction} ${pred.predicted_price:.2f}")
    
    # Step 3: Generate Signals
    print("\n[Step 4] Generating Signals from Predictions")
    signals = []
    
    for desc, prediction in predictions:
        print(f"\n  Testing: {desc}")
        signal = signal_generator.generate_signal(
            prediction,
            current_price=current_price,
            current_position=None
        )
        
        if signal:
            print(f"    ✓ Signal generated: {signal.signal_type.value} {signal.symbol}")
            print(f"      Confidence: {signal.confidence * 100:.1f}%")
            print(f"      Reasoning: {signal.reasoning[:100]}...")
            signals.append((desc, signal))
        else:
            print(f"    ✗ Signal rejected (confidence {prediction.confidence * 100:.1f}% < threshold {config['prediction_confidence_threshold'] * 100:.1f}%)")
    
    print(f"\n  Generated {len(signals)} signals from {len(predictions)} predictions")
    
    # Step 4: Test Execution Logic
    print("\n[Step 5] Testing Execution Logic (Mode-Based)")
    
    # Test in HYBRID mode (current config)
    print(f"\n  Mode: {trading_mode.value.upper()}")
    for desc, signal in signals:
        should_execute = signal_generator.should_execute_trade(signal)
        auto_status = "AUTO EXECUTE" if should_execute else "MANUAL APPROVAL REQUIRED"
        print(f"    • {desc} ({signal.confidence * 100:.1f}%): {auto_status}")
    
    # Test other modes
    print("\n  Testing AUTO Mode:")
    signal_generator.trading_mode = TradingMode.AUTO
    for desc, signal in signals[:2]:  # Test first 2 signals
        should_execute = signal_generator.should_execute_trade(signal)
        auto_status = "AUTO EXECUTE" if should_execute else "MANUAL APPROVAL REQUIRED"
        print(f"    • {desc} ({signal.confidence * 100:.1f}%): {auto_status}")
    
    print("\n  Testing MANUAL Mode:")
    signal_generator.trading_mode = TradingMode.MANUAL
    for desc, signal in signals[:2]:  # Test first 2 signals
        should_execute = signal_generator.should_execute_trade(signal)
        auto_status = "AUTO EXECUTE" if should_execute else "MANUAL APPROVAL REQUIRED"
        print(f"    • {desc} ({signal.confidence * 100:.1f}%): {auto_status}")
    
    # Reset to hybrid
    signal_generator.trading_mode = TradingMode.HYBRID
    
    # Step 5: Test Signal Queue
    print("\n[Step 6] Testing Signal Queue Management")
    
    # Add signals to queue
    for desc, signal in signals:
        signal_queue.add_signal(signal)
    print(f"  ✓ Added {len(signals)} signals to queue")
    
    # Get pending signals
    pending = signal_queue.get_pending_signals()
    print(f"  ✓ Retrieved {len(pending)} pending signals")
    
    # Filter by symbol (manually)
    pltr_signals = {k: v for k, v in pending.items() if v.symbol == "PLTR"}
    print(f"  ✓ Filtered signals for PLTR: {len(pltr_signals)}")
    
    # Approve first signal
    if pending:
        first_signal_id = list(pending.keys())[0]
        approved = signal_queue.approve_signal(first_signal_id)
        print(f"  ✓ Approved signal {first_signal_id}: {approved is not None}")
        
        # Verify it's no longer pending
        pending_after = signal_queue.get_pending_signals()
        print(f"  ✓ Pending signals after approval: {len(pending_after)}")
    
    # Reject second signal
    if len(pending) > 1:
        second_signal_id = list(pending.keys())[1]
        rejected = signal_queue.reject_signal(second_signal_id)
        print(f"  ✓ Rejected signal {second_signal_id}: {rejected}")
        
        # Verify it's no longer pending
        pending_after = signal_queue.get_pending_signals()
        print(f"  ✓ Pending signals after rejection: {len(pending_after)}")
    
    # Step 6: Test With Existing Position
    print("\n[Step 7] Testing Position-Aware Signal Generation")
    
    # Create mock LONG position
    mock_position = create_mock_position("PLTR", 100, 170.00)
    print(f"  • Mock position: LONG {mock_position.quantity} shares @ ${mock_position.entry_price:.2f}")
    
    # Generate DOWN signal with existing position
    down_prediction = create_mock_prediction("PLTR", "DOWN", 0.78, current_price)
    exit_signal = signal_generator.generate_signal(
        down_prediction,
        current_price=current_price,
        current_position=mock_position
    )
    
    if exit_signal:
        print(f"  ✓ Generated signal: {exit_signal.signal_type.value}")
        print(f"    Confidence: {exit_signal.confidence * 100:.1f}%")
        print(f"    Reasoning: {exit_signal.reasoning[:80]}...")
    
    # Step 7: Validation Checks
    print("\n[Step 8] Validation Checks")
    print("=" * 80)
    
    checks_passed = 0
    total_checks = 6
    
    # Check 1: High confidence signals trigger auto execution in hybrid mode
    signal_generator.trading_mode = TradingMode.HYBRID
    high_conf_signals = [s for desc, s in signals if s.confidence >= config['auto_execute_threshold']]
    auto_execute_count = sum(1 for s in high_conf_signals if signal_generator.should_execute_trade(s))
    
    if auto_execute_count == len(high_conf_signals):
        print("✓ Check 1: High confidence signals (≥80%) trigger auto execution in hybrid mode")
        checks_passed += 1
    else:
        print(f"✗ Check 1: Expected {len(high_conf_signals)} auto executions, got {auto_execute_count}")
    
    # Check 2: Medium confidence signals require manual approval
    med_conf_signals = [s for desc, s in signals if config['prediction_confidence_threshold'] <= s.confidence < config['auto_execute_threshold']]
    manual_count = sum(1 for s in med_conf_signals if not signal_generator.should_execute_trade(s))
    
    if manual_count == len(med_conf_signals):
        print("✓ Check 2: Medium confidence signals (70-80%) require manual approval in hybrid mode")
        checks_passed += 1
    else:
        print(f"✗ Check 2: Expected {len(med_conf_signals)} manual approvals, got {manual_count}")
    
    # Check 3: Low confidence signals are rejected
    total_signals_generated = len(signals)
    total_predictions = len(predictions)
    rejected_count = total_predictions - total_signals_generated
    
    if rejected_count > 0:
        print(f"✓ Check 3: Low confidence signals rejected ({rejected_count} rejected)")
        checks_passed += 1
    else:
        print("✗ Check 3: No signals were rejected")
    
    # Check 4: Signal reasoning is clear
    all_have_reasoning = all(len(s.reasoning) > 20 for desc, s in signals)
    
    if all_have_reasoning:
        print("✓ Check 4: All signals have clear, informative reasoning")
        checks_passed += 1
    else:
        print("✗ Check 4: Some signals lack proper reasoning")
    
    # Check 5: Signal queue properly manages pending signals
    queue_works = len(pending) > 0 and len(pending_after) < len(pending)
    
    if queue_works:
        print("✓ Check 5: Signal queue properly manages approval/rejection")
        checks_passed += 1
    else:
        print("✗ Check 5: Signal queue management issues detected")
    
    # Check 6: Existing positions affect signal generation
    if exit_signal:
        # Compare by value since SignalType might be different instances
        position_aware = exit_signal.signal_type.value == "sell"
        if position_aware:
            print("✓ Check 6: Position-aware signal generation (EXIT signals for existing positions)")
            checks_passed += 1
        else:
            print(f"✗ Check 6: Signal type mismatch - got {exit_signal.signal_type.value}, expected 'sell'")
    else:
        print("✗ Check 6: No exit signal generated for existing position")
    
    # Final Summary
    print("\n" + "=" * 80)
    print(f"VALIDATION RESULT: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("✅ TEST 9 PASSED: Signal generation system operational")
        return True
    else:
        print(f"⚠️  TEST 9 PARTIAL: {total_checks - checks_passed} checks failed")
        return False


if __name__ == "__main__":
    try:
        success = test_signal_generation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST 9 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
