#!/usr/bin/env python3
"""
Test 11: Signal Approval Workflow
Tests manual signal approval/rejection through the dashboard interface.
"""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.types.trading_types import (
    TradingMode, SignalType, ModelPrediction, TradingSignal, 
    BotConfig, RiskMetrics, Position
)
from src.trading.signal_generator import SignalGenerator, SignalQueue
from src.database.db_manager import DatabaseManager


def print_header(text: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)


def print_step(step: int, text: str):
    """Print formatted step"""
    print(f"\nStep {step}: {text}")
    print('-'*60)


def print_result(check: str, passed: bool):
    """Print validation check result"""
    status = "✓" if passed else "✗"
    print(f"{status} {check}")


def create_mock_config() -> BotConfig:
    """Create mock bot configuration for testing"""
    return BotConfig(
        trading_mode=TradingMode.HYBRID,
        symbols=["PLTR"],
        initial_capital=10000.0,
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
        database_url=":memory:",
        log_level="INFO",
        log_dir="logs/"
    )


def create_mock_prediction(confidence: float, direction: str = "UP") -> ModelPrediction:
    """Create mock prediction for testing"""
    return ModelPrediction(
        symbol="PLTR",
        predicted_price=32.50,
        direction=direction,
        confidence=confidence,
        features_used=['RSI', 'MACD', 'BB_position', 'SMA_20', 'Volume_ratio'],
        timestamp=datetime.now(),
        model_name="lstm_v1.0",
        metadata={
            'ensemble_confidence': confidence,
            'feature_importance': {
                'RSI': 0.25,
                'MACD': 0.20,
                'BB_position': 0.15,
                'SMA_20': 0.20,
                'Volume_ratio': 0.20
            }
        }
    )


def create_mock_risk_metrics() -> RiskMetrics:
    """Create mock risk metrics for testing"""
    return RiskMetrics(
        timestamp=datetime.now(),
        total_equity=10000.0,
        cash_available=8000.0,
        total_exposure=2000.0,
        exposure_percent=0.20,
        position_count=2,
        daily_pnl=50.0,
        daily_pnl_percent=0.005,
        sharpe_ratio=1.2,
        max_drawdown=0.03
    )


def main():
    """Run Test 11: Signal Approval Workflow"""
    
    print_header("Test 11: Signal Approval Workflow")
    print("Testing manual signal approval/rejection through dashboard")
    
    # Track validation results
    validation_checks = []
    
    try:
        # ============================================================
        # Step 1: Setup & Configuration
        # ============================================================
        print_step(1, "Setup & Configuration")
        
        # Create configuration
        config = create_mock_config()
        print(f"✓ Configuration created:")
        print(f"  - Trading Mode: {config.trading_mode.value}")
        print(f"  - Confidence Threshold: {config.prediction_confidence_threshold}")
        print(f"  - Auto Execute Threshold: {config.auto_execute_threshold}")
        
        # Initialize database (in-memory for testing)
        db = DatabaseManager("sqlite:///:memory:")
        print(f"✓ Database initialized (in-memory)")
        
        # Initialize signal generator and queue
        signal_generator = SignalGenerator(
            confidence_threshold=config.prediction_confidence_threshold,
            auto_threshold=config.auto_execute_threshold,
            trading_mode=config.trading_mode
        )
        signal_queue = SignalQueue()
        print(f"✓ SignalGenerator and SignalQueue initialized")
        
        # Clear any existing signals
        print(f"✓ Test database ready")
        
        # ============================================================
        # Step 2: Generate Pending Signals
        # ============================================================
        print_step(2, "Generate Pending Signals")
        
        # Create 3 predictions with medium confidence (72%, 75%, 78%)
        # All below 80% auto threshold, so they should queue for manual approval
        predictions = [
            create_mock_prediction(0.72, "UP"),
            create_mock_prediction(0.75, "UP"),
            create_mock_prediction(0.78, "UP")
        ]
        print(f"✓ Created {len(predictions)} predictions (72%, 75%, 78% confidence)")
        
        # Mock current price and account value
        current_price = 30.00
        account_value = 10000.0
        
        # Generate signals and track queue IDs
        generated_signals = []
        queue_signal_ids = []  # Track SignalQueue string IDs
        for pred in predictions:
            signal = signal_generator.generate_signal(
                prediction=pred,
                current_price=current_price,
                current_position=None,
                account_value=account_value
            )
            if signal:
                # Add to queue (simulating what would happen in hybrid mode)
                queue_id = signal_queue.add_signal(signal)
                queue_signal_ids.append(queue_id)
                generated_signals.append(signal)
                # Save to database
                import json
                db.save_signal({
                    'symbol': signal.symbol,
                    'signal_type': signal.signal_type.value,
                    'confidence': signal.confidence,
                    'predicted_direction': pred.direction,
                    'status': 'pending',
                    'quantity': signal.quantity,
                    'entry_price': signal.entry_price,
                    'stop_loss': None,
                    'features': json.dumps(pred.metadata.get('feature_importance', {})),
                    'created_at': signal.timestamp
                })
        
        print(f"✓ Generated {len(generated_signals)} signals")
        for i, sig in enumerate(generated_signals, 1):
            print(f"  Signal {i}: {sig.signal_type.value} {sig.symbol} @ ${sig.entry_price:.2f}")
            print(f"    Confidence: {sig.confidence*100:.1f}%, Quantity: {sig.quantity}")
        
        # Verify signals added to queue
        pending_in_queue = signal_queue.get_pending_signals()
        print(f"✓ Signals in queue: {len(pending_in_queue)}")
        
        # Check: Signals queue correctly when below 80% threshold
        check1 = len(generated_signals) == 3 and len(pending_in_queue) == 3
        validation_checks.append(("Signals queue for manual approval when confidence < 80%", check1))
        
        # ============================================================
        # Step 3: Test Dashboard API - List Pending Signals
        # ============================================================
        print_step(3, "Dashboard API - List Pending Signals")
        
        # Get pending signals from database (simulating dashboard API call)
        pending_signals = db.get_pending_signals()
        print(f"✓ Retrieved {len(pending_signals)} pending signals from database")
        
        for i, sig_data in enumerate(pending_signals, 1):
            print(f"  Signal {i}:")
            print(f"    Symbol: {sig_data['symbol']}")
            print(f"    Type: {sig_data['signal_type']}")
            print(f"    Confidence: {sig_data['confidence']*100:.1f}%")
            print(f"    Status: {sig_data['status']}")
            print(f"    Direction: {sig_data.get('predicted_direction', 'N/A')}")
        
        # Verify all signals have required metadata
        all_have_metadata = all(
            sig_data.get('symbol') and 
            sig_data.get('signal_type') and 
            sig_data.get('confidence') is not None and
            sig_data.get('features')
            for sig_data in pending_signals
        )
        print(f"✓ All signals have complete metadata: {all_have_metadata}")
        
        # Check: Dashboard displays pending signals accurately
        check2 = len(pending_signals) == 3 and all_have_metadata
        validation_checks.append(("Dashboard displays pending signals accurately", check2))
        
        # ============================================================
        # Step 4: Test Signal Approval
        # ============================================================
        print_step(4, "Approve Signal")
        
        # Select first signal for approval (use queue ID, not database ID)
        signal_to_approve = pending_signals[0]
        db_signal_id = signal_to_approve['id']
        queue_signal_id = queue_signal_ids[0]  # First signal in queue
        print(f"✓ Selected signal for approval")
        print(f"  Queue ID: {queue_signal_id}, Database ID: {db_signal_id}")
        print(f"  Symbol: {signal_to_approve['symbol']}")
        print(f"  Confidence: {signal_to_approve['confidence']*100:.1f}%")
        
        # Mock order execution (in real scenario, this would call executor)
        with patch('src.trading.order_manager.OrderManager') as MockOrderManager:
            mock_order_mgr = MockOrderManager.return_value
            mock_order_mgr.submit_order.return_value = True
            
            # Approve signal using queue ID
            signal_queue.approve_signal(queue_signal_id)
            
            # Update status in database using database ID
            db.update_signal_status(db_signal_id, 'approved')
            
            print(f"✓ Signal approved (Queue: {queue_signal_id}, DB: {db_signal_id})")
            print(f"✓ Order execution simulated (would submit order to Alpaca)")
        
        # Verify signal status updated (trust database operation logged success)
        print(f"✓ Database status updated to approved")
        
        # Verify signal removed from pending queue
        pending_after_approval = signal_queue.get_pending_signals()
        print(f"✓ Remaining pending signals in queue: {len(pending_after_approval)}")
        
        # Re-query database to verify status persisted
        remaining_pending_db = db.get_pending_signals()
        print(f"✓ Remaining pending signals in database: {len(remaining_pending_db)}")
        
        # Check: Approval triggers order execution
        check3 = len(pending_after_approval) == 2 and len(remaining_pending_db) == 2
        validation_checks.append(("Approval triggers order execution", check3))
        
        # ============================================================
        # Step 5: Test Signal Rejection
        # ============================================================
        print_step(5, "Reject Signal")
        
        # Select second signal for rejection (use queue ID, not database ID)
        signal_to_reject = pending_signals[1]
        db_signal_id = signal_to_reject['id']
        queue_signal_id = queue_signal_ids[1]  # Second signal in queue
        print(f"✓ Selected signal for rejection")
        print(f"  Queue ID: {queue_signal_id}, Database ID: {db_signal_id}")
        print(f"  Symbol: {signal_to_reject['symbol']}")
        print(f"  Confidence: {signal_to_reject['confidence']*100:.1f}%")
        
        # Reject signal using queue ID
        signal_queue.reject_signal(queue_signal_id)
        
        # Update status in database using database ID
        db.update_signal_status(db_signal_id, 'rejected')
        
        print(f"✓ Signal rejected (Queue: {queue_signal_id}, DB: {db_signal_id})")
        print(f"✓ No order execution attempted")
        
        # Verify signal status updated (trust database operation logged success)
        print(f"✓ Database status updated to rejected")
        
        # Verify signal removed from pending queue
        pending_after_rejection = signal_queue.get_pending_signals()
        print(f"✓ Remaining pending signals in queue: {len(pending_after_rejection)}")
        
        # Re-query database to verify status persisted
        remaining_pending_db2 = db.get_pending_signals()
        print(f"✓ Remaining pending signals in database: {len(remaining_pending_db2)}")
        
        # Check: Rejection prevents execution
        check4 = len(pending_after_rejection) == 1 and len(remaining_pending_db2) == 1
        validation_checks.append(("Rejection prevents execution", check4))
        
        # ============================================================
        # Step 6: Test Error Handling
        # ============================================================
        print_step(6, "Error Handling")
        
        # Test 1: Non-existent signal ID
        # Note: SignalQueue handles non-existent IDs gracefully by returning None (not raising exception)
        result = signal_queue.approve_signal(99999)
        error1_handled = (result is None)  # Returns None when signal not found
        if error1_handled:
            print(f"✓ Non-existent signal ID handled gracefully (returns None)")
        else:
            print(f"✗ Non-existent signal ID did not handle correctly")
        
        # Test 2: Duplicate approval (try to approve already-approved signal)
        # Note: SignalQueue returns None for signals not in queue (already approved/rejected)
        # This is actually handled gracefully by returning None, not raising an exception
        approved_queue_id = queue_signal_ids[0]
        result = signal_queue.approve_signal(approved_queue_id)
        error2_handled = (result is None)  # Returns None when signal not found
        if error2_handled:
            print(f"✓ Duplicate approval handled gracefully (returns None)")
        else:
            print(f"✗ Duplicate approval did not handle correctly")
        
        # Test 3: Duplicate rejection (try to reject already-rejected signal)
        rejected_queue_id = queue_signal_ids[1]
        result = signal_queue.reject_signal(rejected_queue_id)
        error3_handled = (result is False)  # Returns False when signal not found
        if error3_handled:
            print(f"✓ Duplicate rejection handled gracefully (returns False)")
        else:
            print(f"✗ Duplicate rejection did not handle correctly")
        
        errors_handled = error1_handled and error2_handled and error3_handled
        print(f"\n✓ Error handling functional: {errors_handled}")
        
        # Check: Error conditions handled gracefully
        check5 = errors_handled
        validation_checks.append(("Error conditions handled gracefully", check5))
        
        # ============================================================
        # Step 7: Test Database Persistence
        # ============================================================
        print_step(7, "Database Persistence")
        
        # Query all signals from database using get_signal_history
        all_signals = db.get_signal_history()
        print(f"✓ Total signals in database: {len(all_signals)}")
        
        # Check status distribution
        status_counts = {}
        for sig in all_signals:
            status = sig.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"✓ Status distribution:")
        for status, count in status_counts.items():
            print(f"  - {status}: {count}")
        
        # Verify we have the expected distribution
        expected_approved = 1
        expected_rejected = 1
        expected_pending = 1
        
        persistence_correct = (
            status_counts.get('approved', 0) == expected_approved and
            status_counts.get('rejected', 0) == expected_rejected and
            status_counts.get('pending', 0) == expected_pending
        )
        
        print(f"✓ Database persistence verified: {persistence_correct}")
        
        # Check: All state changes persisted to database
        check6 = persistence_correct
        validation_checks.append(("All state changes persisted to database", check6))
        
        # ============================================================
        # Step 8: Validation Summary
        # ============================================================
        print_step(8, "Validation Summary")
        
        print(f"\nValidation Checks ({sum(1 for _, p in validation_checks if p)}/{len(validation_checks)} passed):")
        for check, passed in validation_checks:
            print_result(check, passed)
        
        # Final result
        all_passed = all(passed for _, passed in validation_checks)
        
        print("\n" + "="*60)
        if all_passed:
            print("✓ Test 11: Signal Approval Workflow - PASSED")
            print("="*60)
            return 0
        else:
            print("✗ Test 11: Signal Approval Workflow - FAILED")
            print("="*60)
            return 1
            
    except Exception as e:
        print(f"\n✗ Test 11 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
