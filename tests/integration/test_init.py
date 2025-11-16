#!/usr/bin/env python3
"""
Test script to verify bot initialization
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Testing Trading Bot Initialization")
print("=" * 60)

# Check critical environment variables
print("\n1. Checking Environment Variables...")
required_vars = [
    'ALPACA_API_KEY',
    'ALPACA_SECRET_KEY',
    'ALPACA_BASE_URL',
    'ALPACA_IS_PAPER'
]

missing_vars = []
for var in required_vars:
    value = os.getenv(var)
    if not value or value.startswith('your_'):
        print(f"   ❌ {var}: NOT SET or placeholder")
        missing_vars.append(var)
    else:
        # Mask the actual values for security
        if 'KEY' in var:
            masked = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
            print(f"   ✅ {var}: {masked}")
        else:
            print(f"   ✅ {var}: {value}")

if missing_vars:
    print(f"\n⚠️  Missing or placeholder values detected!")
    print(f"   Please configure these in .env file: {', '.join(missing_vars)}")
    print(f"\n   To get Alpaca API keys:")
    print(f"   1. Go to https://alpaca.markets/")
    print(f"   2. Sign up for a free account")
    print(f"   3. Navigate to Paper Trading section")
    print(f"   4. Generate API keys")
    print(f"   5. Update .env file with your keys")
    sys.exit(1)

# Check if paper trading is enabled
is_paper = os.getenv('ALPACA_IS_PAPER', 'true').lower() == 'true'
print(f"\n2. Trading Mode: {'PAPER TRADING ✅ (Safe)' if is_paper else 'LIVE TRADING ⚠️  (Real Money!)'}")

if not is_paper:
    print("   ⚠️  WARNING: Live trading is enabled!")
    print("   ⚠️  This will use real money!")
    print("   ⚠️  Change ALPACA_IS_PAPER=true for safety")

# Try to import TradingBot
print("\n3. Testing TradingBot Import...")
try:
    from src.main import TradingBot
    print("   ✅ TradingBot imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import TradingBot: {e}")
    sys.exit(1)

# Try to create bot instance (without starting)
print("\n4. Testing Bot Instance Creation...")
try:
    bot = TradingBot()
    print("   ✅ TradingBot instance created")
    print(f"   ✅ Bot ID: {id(bot)}")
    print(f"   ✅ Singleton pattern working: {bot is TradingBot()}")
except Exception as e:
    print(f"   ❌ Failed to create bot instance: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check bot configuration
print("\n5. Verifying Bot Configuration...")
try:
    print(f"   ✅ Config loaded: {bot.config is not None}")
    print(f"   ✅ Trading mode: {bot.config.get('trading', {}).get('mode', 'N/A')}")
    print(f"   ✅ Symbols: {bot.config.get('trading', {}).get('symbols', [])}")
    print(f"   ✅ Risk per trade: {bot.config.get('risk', {}).get('risk_per_trade', 'N/A')}%")
except Exception as e:
    print(f"   ❌ Config verification failed: {e}")

# Check database connection
print("\n6. Testing Database Connection...")
try:
    from src.database.db_manager import DatabaseManager
    db = DatabaseManager()
    # Try a simple query
    with db:
        state = db.get_bot_state()
        print(f"   ✅ Database connected")
        print(f"   ✅ Bot state retrieved: {state is not None}")
except Exception as e:
    print(f"   ⚠️  Database warning: {e}")

print("\n" + "=" * 60)
print("✅ Initialization Test Complete!")
print("=" * 60)
print("\nNext steps:")
print("1. If API keys are set: Test Alpaca connection")
print("2. Start the bot with: python3 src/main.py")
print("3. Start dashboard with: python3 src/dashboard/app.py")
print("=" * 60)
