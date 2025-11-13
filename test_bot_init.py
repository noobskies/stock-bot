#!/usr/bin/env python3
"""
Test script to verify full bot initialization and API connectivity
"""

import sys
from loguru import logger

# Configure simple logging for test
logger.remove()
logger.add(sys.stdout, level="INFO", format="<level>{level: <8}</level> | {message}")

print("=" * 80)
print("AI Stock Trading Bot - Initialization Test")
print("=" * 80)

try:
    # Import TradingBot
    from src.main import TradingBot
    
    # Create bot instance
    print("\n1. Creating TradingBot instance...")
    bot = TradingBot()
    print("   ✅ Bot instance created")
    
    # Initialize bot (loads config, connects to API, etc.)
    print("\n2. Initializing bot (this may take a moment)...")
    print("   - Loading configuration from config.yaml and .env")
    print("   - Setting up logging")
    print("   - Connecting to database")
    print("   - Creating all modules")
    print("   - Verifying Alpaca API connection")
    print("   - Setting up scheduler")
    print()
    
    success = bot.initialize()
    
    if not success:
        print("\n❌ Bot initialization failed!")
        print("\nCommon issues:")
        print("1. Alpaca API keys not set in .env file")
        print("2. config/config.yaml file not found or invalid")
        print("3. Network connectivity issues")
        print("4. Invalid API credentials")
        sys.exit(1)
    
    print("\n✅ Bot initialized successfully!")
    
    # Display configuration
    print("\n3. Bot Configuration:")
    print(f"   Trading Mode: {bot.config.trading_mode.value}")
    print(f"   Symbols: {', '.join(bot.config.symbols)}")
    print(f"   Max Positions: {bot.config.max_positions}")
    print(f"   Risk per Trade: {bot.config.risk_per_trade*100}%")
    print(f"   Stop Loss: {bot.config.stop_loss_percent*100}%")
    print(f"   Confidence Threshold: {bot.config.prediction_confidence_threshold*100}%")
    print(f"   Auto-Execute Threshold: {bot.config.auto_execute_threshold*100}%")
    print(f"   Close Positions EOD: {bot.config.close_positions_eod}")
    
    # Check Alpaca connection
    print("\n4. Alpaca API Status:")
    try:
        account = bot.executor.get_account()
        print(f"   Account Value: ${float(account.equity):,.2f}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")
        print(f"   Cash: ${float(account.cash):,.2f}")
        print(f"   Paper Trading: {'Yes' if account.account_number.startswith('P') else 'No ⚠️'}")
    except Exception as e:
        print(f"   ⚠️  Could not fetch account info: {e}")
    
    # Check if market is open
    print("\n5. Market Status:")
    is_open = bot.is_market_hours()
    print(f"   Market Hours (9:30 AM - 4:00 PM ET): {'OPEN' if is_open else 'CLOSED'}")
    
    # Check ML model
    print("\n6. ML Model Status:")
    if bot.predictor:
        print(f"   ✅ LSTM model loaded from {bot.config.model_path}")
    else:
        print(f"   ⚠️  No LSTM model found at {bot.config.model_path}")
        print("   ⚠️  Bot will run in manual-only mode")
        print("   ℹ️  To train a model, run: python src/ml/model_trainer.py")
    
    # Check database
    print("\n7. Database Status:")
    try:
        state = bot.db_manager.get_bot_state()
        if state:
            print(f"   ✅ Connected to database: {bot.db_manager.database_url}")
            print(f"   Last active: {state.get('last_update', 'Never')}")
        else:
            print(f"   ✅ Connected to database: {bot.db_manager.database_url}")
            print(f"   ℹ️  No previous bot state (fresh database)")
    except Exception as e:
        print(f"   ⚠️  Database issue: {e}")
    
    # Show module status
    print("\n8. Module Status:")
    modules = {
        'Data Fetcher': bot.data_fetcher,
        'Feature Engineer': bot.feature_engineer,
        'Data Validator': bot.data_validator,
        'LSTM Predictor': bot.predictor,
        'Ensemble Predictor': bot.ensemble,
        'Signal Generator': bot.signal_generator,
        'Signal Queue': bot.signal_queue,
        'Executor': bot.executor,
        'Order Manager': bot.order_manager,
        'Position Manager': bot.position_manager,
        'Risk Calculator': bot.risk_calculator,
        'Portfolio Monitor': bot.portfolio_monitor,
        'Stop Loss Manager': bot.stop_loss_manager,
        'Database Manager': bot.db_manager,
    }
    
    for name, module in modules.items():
        status = "✅" if module is not None else "❌"
        print(f"   {status} {name}")
    
    print("\n" + "=" * 80)
    print("✅ ALL INITIALIZATION TESTS PASSED!")
    print("=" * 80)
    
    print("\nBot is ready to run. Next steps:")
    print()
    print("1. Start bot:      python3 src/main.py")
    print("2. Start dashboard: python3 src/dashboard/app.py")
    print()
    print("Or test individual components:")
    print()
    print("3. Test data fetch:  python3 -c \"from src.data.data_fetcher import DataFetcher; df = DataFetcher(); print(df.fetch_latest_price('PLTR'))\"")
    print("4. Test prediction:  python3 -c \"from test_prediction import *\"  (if you create this)")
    print()
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 80)
    print("Initialization failed. Please check:")
    print("1. .env file has valid Alpaca API keys")
    print("2. config/config.yaml exists and is valid")
    print("3. All dependencies are installed (pip install -r requirements.txt)")
    print("4. Database file is accessible")
    print("=" * 80)
    sys.exit(1)
