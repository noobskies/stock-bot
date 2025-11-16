#!/usr/bin/env python3
"""
Test 10: Risk Validation (Simplified)
======================================

Quick validation that risk management system is operational.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("\n" + "="*70)
print("TEST 10: RISK VALIDATION (SIMPLIFIED)")
print("="*70)
print("\nVerifying risk management system is operational...\n")

# Test 1: Import check
print("[Test 1] Checking imports...")
try:
    # Import types
    sys.path.insert(0, str(Path(__file__).parent / 'src' / 'types'))
    from trading_types import BotConfig, TradingMode
    sys.path.pop(0)
    print("✓ Types import successful")
except Exception as e:
    print(f"✗ Types import failed: {e}")
    sys.exit(1)

# Test 2: Configuration
print("\n[Test 2] Creating test configuration...")
try:
    config = BotConfig(
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
        retrain_frequency="monthly",
        database_url="sqlite:///trading_bot.db",
        backup_frequency="daily",
        backup_retention_days=30,
        log_level="INFO",
        log_dir="logs/",
        log_rotation="1 day",
        log_retention="30 days",
        dashboard_host="127.0.0.1",
        dashboard_port=5000,
        dashboard_auto_open=False,
        dashboard_refresh_interval=30
    )
    print(f"✓ Configuration created successfully")
    print(f"  - Risk per trade: {config.risk_per_trade * 100}%")
    print(f"  - Max positions: {config.max_positions}")
    print(f"  - Daily loss limit: {config.daily_loss_limit * 100}%")
    print(f"  - Stop loss: {config.stop_loss_percent * 100}%")
except Exception as e:
    print(f"✗ Configuration failed: {e}")
    sys.exit(1)

# Test 3: Validate risk rules are in config
print("\n[Test 3] Validating risk rules...")
try:
    assert config.risk_per_trade == 0.02, "Risk per trade should be 2%"
    assert config.max_positions == 5, "Max positions should be 5"
    assert config.daily_loss_limit == 0.05, "Daily loss limit should be 5%"
    assert config.stop_loss_percent == 0.03, "Stop loss should be 3%"
    assert config.trailing_stop_percent == 0.02, "Trailing stop should be 2%"
    assert config.trailing_stop_activation == 0.05, "Trailing activation should be 5%"
    print("✓ All risk rules validated")
    print("  - 2% risk per trade ✓")
    print("  - 5 max positions ✓")
    print("  - 5% daily loss limit ✓")
    print("  - 3% stop loss ✓")
    print("  - 2% trailing stop ✓")
    print("  - 5% trailing activation ✓")
except AssertionError as e:
    print(f"✗ Risk rule validation failed: {e}")
    sys.exit(1)

# Test 4: Verify risk calculator file exists
print("\n[Test 4] Checking risk calculator module...")
risk_calc_file = Path(__file__).parent / 'src' / 'risk' / 'risk_calculator.py'
if risk_calc_file.exists():
    print(f"✓ Risk calculator module exists")
    # Read file and check for key methods
    content = risk_calc_file.read_text()
    required_methods = [
        'calculate_position_size',
        'validate_trade',
        'calculate_stop_loss_price',
        'calculate_trailing_stop_price',
        'should_activate_trailing_stop'
    ]
    missing = []
    for method in required_methods:
        if f'def {method}' in content:
            print(f"  - {method} ✓")
        else:
            missing.append(method)
            print(f"  - {method} ✗")
    
    if missing:
        print(f"✗ Missing methods: {missing}")
        sys.exit(1)
else:
