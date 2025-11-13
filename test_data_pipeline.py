#!/usr/bin/env python3
"""
Test 6: Data Pipeline
Tests historical data fetching, technical indicator calculation, and data validation.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_data_pipeline():
    """Test the complete data pipeline."""
    print("\n" + "="*80)
    print("TEST 6: DATA PIPELINE")
    print("="*80)
    
    try:
        # Import modules
        print("\n[1/5] Importing data modules...")
        from data.data_fetcher import DataFetcher
        from data.feature_engineer import FeatureEngineer
        from data.data_validator import DataValidator
        print("✅ All data modules imported successfully")
        
        # Initialize modules
        print("\n[2/5] Initializing data modules...")
        
        # Get API keys from environment
        alpaca_api_key = os.getenv('ALPACA_API_KEY')
        alpaca_secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        if not alpaca_api_key or not alpaca_secret_key:
            print("❌ Missing Alpaca API credentials in .env file")
            return False
        
        # Initialize data fetcher (alpaca-py SDK auto-detects paper vs live from keys)
        data_fetcher = DataFetcher(
            alpaca_api_key=alpaca_api_key,
            alpaca_secret_key=alpaca_secret_key
        )
        
        feature_engineer = FeatureEngineer()
        data_validator = DataValidator()
        
        print("✅ All modules initialized")
        
        # Test 1: Fetch historical data (2 years for PLTR)
        print("\n[3/5] Fetching historical PLTR data (2 years)...")
        symbol = "PLTR"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)  # ~2 years
        
        print(f"   Symbol: {symbol}")
        print(f"   Start: {start_date.strftime('%Y-%m-%d')}")
        print(f"   End: {end_date.strftime('%Y-%m-%d')}")
        
        df = data_fetcher.fetch_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe="1Day"
        )
        
        if df is None or df.empty:
            print(f"❌ Failed to fetch historical data for {symbol}")
            return False
        
        print(f"✅ Fetched {len(df)} days of historical data")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Sample data (latest):")
        print(df.tail(3))
        
        # Test 2: Validate data quality
        print("\n[4/5] Validating data quality...")
        
        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            print(f"⚠️  Found missing values: {missing[missing > 0].to_dict()}")
        else:
            print("✅ No missing values")
        
        # Validate price data structure
        is_valid, message = data_validator.validate_price_data(df)
        if is_valid:
            print(f"✅ Price data validation passed")
        else:
            print(f"❌ Price data validation failed: {message}")
            return False
        
        # Check for outliers
        outliers = data_validator.detect_outliers(df, method='iqr')
        outlier_count = outliers.sum().sum()
        if outlier_count > 0:
            print(f"⚠️  Found {outlier_count} potential outliers (normal for volatile stock)")
        else:
            print("✅ No significant outliers detected")
        
        # Test 3: Calculate technical indicators
        print("\n[5/5] Calculating technical indicators...")
        
        df_with_indicators = feature_engineer.calculate_technical_indicators(df)
        
        if df_with_indicators is None or df_with_indicators.empty:
            print("❌ Failed to calculate technical indicators")
            return False
        
        # Check which indicators were added
        new_columns = set(df_with_indicators.columns) - set(df.columns)
        print(f"✅ Calculated {len(new_columns)} technical indicators:")
        
        indicator_groups = {
            'RSI': [col for col in new_columns if 'rsi' in col.lower()],
            'MACD': [col for col in new_columns if 'macd' in col.lower()],
            'Bollinger Bands': [col for col in new_columns if 'bb' in col.lower()],
            'Moving Averages': [col for col in new_columns if 'sma' in col.lower() or 'ema' in col.lower()],
            'Volume': [col for col in new_columns if 'volume' in col.lower()],
            'Other': []
        }
        
        # Categorize indicators
        categorized = set()
        for group, indicators in indicator_groups.items():
            if indicators:
                print(f"   {group}: {', '.join(indicators)}")
                categorized.update(indicators)
        
        # Show uncategorized indicators
        uncategorized = new_columns - categorized
        if uncategorized:
            indicator_groups['Other'] = list(uncategorized)
            print(f"   Other: {', '.join(uncategorized)}")
        
        # Show sample indicator values (latest)
        print(f"\n   Sample indicator values (latest):")
        sample_indicators = ['rsi', 'macd', 'bb_upper', 'bb_lower', 'sma_20', 'sma_50']
        available_indicators = [col for col in sample_indicators if col in df_with_indicators.columns]
        if available_indicators:
            print(df_with_indicators[available_indicators].tail(3))
        
        # Check for NaN values after indicator calculation
        missing_after = df_with_indicators.isnull().sum()
        total_missing = missing_after.sum()
        if total_missing > 0:
            print(f"\n   ⚠️  {total_missing} NaN values after indicators (expected for first ~50 rows)")
            # Show which indicators have missing values
            indicators_with_nan = missing_after[missing_after > 0]
            for indicator, count in indicators_with_nan.items():
                if count > 60:  # More than expected warmup period
                    print(f"      ⚠️  {indicator}: {count} NaN values (more than expected)")
        else:
            print("   ✅ All indicator values calculated successfully")
        
        # Test 4: Create ML features
        print("\n   Testing ML feature creation...")
        
        X, y = feature_engineer.create_ml_features(df_with_indicators)
        
        if X is None or y is None:
            print("   ❌ Failed to create ML feature matrix")
            return False
        
        print(f"   ✅ Created feature matrix: {X.shape[0]} samples × {X.shape[1]} features")
        print(f"      Target distribution: Up={np.sum(y==1)}, Down={np.sum(y==0)}")
        
        # Test 5: Create LSTM sequences
        print("\n   Testing LSTM sequence creation...")
        
        sequences, targets = feature_engineer.create_sequences(
            X, y,
            sequence_length=60
        )
        
        if sequences is None or targets is None:
            print("   ❌ Failed to create LSTM sequences")
            return False
        
        print(f"   ✅ Created LSTM sequences:")
        print(f"      Sequences shape: {sequences.shape}")
        print(f"      Targets shape: {targets.shape}")
        print(f"      Sequence length: 60 days")
        print(f"      Total sequences: {len(sequences)}")
        
        # Summary
        print("\n" + "="*80)
        print("TEST 6 RESULTS: DATA PIPELINE")
        print("="*80)
        print("✅ Historical data fetching: PASSED")
        print(f"   - Fetched {len(df)} days of PLTR data")
        print("✅ Data validation: PASSED")
        print(f"   - No critical data quality issues")
        print("✅ Technical indicators: PASSED")
        print(f"   - Calculated {len(new_columns)} indicators")
        print("✅ ML feature engineering: PASSED")
        print(f"   - Created {X.shape[1]} features")
        print("✅ LSTM sequences: PASSED")
        print(f"   - Created {len(sequences)} training sequences")
        print("\n✅ TEST 6: DATA PIPELINE - PASSED")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 6 FAILED with exception:")
        print(f"   Error: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<level>{message}</level>",
        level="WARNING"  # Only show warnings and errors to keep output clean
    )
    
    success = test_data_pipeline()
    sys.exit(0 if success else 1)
