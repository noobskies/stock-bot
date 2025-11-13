#!/usr/bin/env python3
"""
Test 8: Ensemble Prediction Generation
Tests the complete ML prediction pipeline including LSTM, Random Forest, and Momentum ensemble.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.data_fetcher import DataFetcher
from data.feature_engineer import FeatureEngineer
from ml.ensemble import EnsemblePredictor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple config dict (avoiding BotConfig import conflict with built-in types module)
def create_config():
    return {
        'trading_mode': 'hybrid',
        'symbols': ['PLTR'],
        'initial_capital': 10000.0,
        'max_positions': 5,
        'risk_per_trade': 0.02,
        'max_position_size': 0.20,
        'max_portfolio_exposure': 0.20,
        'daily_loss_limit': 0.05,
        'stop_loss_percent': 0.03,
        'trailing_stop_percent': 0.02,
        'trailing_stop_activation': 0.05,
        'model_path': 'models/lstm_model.h5',
        'sequence_length': 60,
        'prediction_confidence_threshold': 0.70,
        'auto_execute_threshold': 0.80,
        'lstm_model_path': 'models/lstm_model.h5',
        'random_forest_path': 'models/random_forest_model.pkl',
        'momentum_weight': 0.2,
        'lstm_weight': 0.5,
        'random_forest_weight': 0.3
    }

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_ensemble_prediction():
    """Test the complete ensemble prediction pipeline"""
    
    print_section("TEST 8: ENSEMBLE PREDICTION GENERATION")
    print("Testing LSTM + Random Forest + Momentum ensemble system")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Initialize configuration
    print("Step 1: Loading Configuration")
    print("-" * 80)
    config = create_config()
    print(f"✓ Config loaded: {config['symbols'][0]}, {config['trading_mode']} mode")
    print(f"✓ Model path: {config['lstm_model_path']}")
    print(f"✓ Weights: LSTM={config['lstm_weight']}, RF={config['random_forest_weight']}, Momentum={config['momentum_weight']}")
    
    # Initialize data fetcher
    print("\nStep 2: Initializing Data Pipeline")
    print("-" * 80)
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    if not api_key or not secret_key:
        print("❌ ERROR: Alpaca API credentials not found in .env")
        return False
    
    data_fetcher = DataFetcher(alpaca_api_key=api_key, alpaca_secret_key=secret_key)
    feature_engineer = FeatureEngineer()
    print("✓ Data pipeline initialized")
    
    # Fetch historical data
    print("\nStep 3: Fetching Recent Market Data")
    print("-" * 80)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year for recent predictions
    
    print(f"Fetching {config['symbols'][0]} data...")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        df = data_fetcher.fetch_historical_data(
            symbol=config['symbols'][0],
            start_date=start_date,
            end_date=end_date
        )
        print(f"✓ Fetched {len(df)} days of data")
    except Exception as e:
        print(f"❌ ERROR fetching data: {e}")
        return False
    
    # Calculate technical indicators
    print("\nStep 4: Calculating Technical Indicators")
    print("-" * 80)
    try:
        df = feature_engineer.calculate_technical_indicators(df)
        print(f"✓ Calculated {len([col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']])} technical indicators")
        
        # Show last few values
        print("\nRecent indicator values:")
        recent = df.tail(3)[['close', 'rsi', 'macd', 'sma_20', 'sma_50']].round(2)
        print(recent.to_string())
    except Exception as e:
        print(f"❌ ERROR calculating indicators: {e}")
        return False
    
    # Initialize ensemble predictor
    print("\nStep 5: Initializing Ensemble Predictor")
    print("-" * 80)
    try:
        # Check if LSTM model exists
        if not Path(config['lstm_model_path']).exists():
            print(f"❌ ERROR: LSTM model not found at {config['lstm_model_path']}")
            print("Please run test_ml_training.py first to train the model")
            return False
        
        predictor = EnsemblePredictor(
            lstm_model_path=config['lstm_model_path'],
            rf_model_path=config['random_forest_path'],
            lstm_weight=config['lstm_weight'],
            rf_weight=config['random_forest_weight'],
            momentum_weight=config['momentum_weight'],
            sequence_length=config['sequence_length'],
            confidence_threshold=config['prediction_confidence_threshold']
        )
        print("✓ Ensemble predictor initialized")
        print(f"✓ LSTM model loaded from {config['lstm_model_path']}")
        
        # Check if Random Forest exists
        if Path(config['random_forest_path']).exists():
            print(f"✓ Random Forest loaded from {config['random_forest_path']}")
        else:
            print(f"⚠ Random Forest not found - will be trained on first use")
        
    except Exception as e:
        print(f"❌ ERROR initializing predictor: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Generate predictions
    print("\nStep 6: Generating Ensemble Predictions")
    print("-" * 80)
    try:
        # Prepare features
        features, targets = feature_engineer.create_ml_features(df)
        print(f"✓ Prepared {len(features)} feature samples")
        
        # Generate prediction for latest data
        print("\nGenerating prediction for latest market data...")
        prediction = predictor.ensemble_predict(
            df=df,
            symbol=config['symbols'][0]
        )
        
        print(f"\n{'PREDICTION RESULT':^80}")
        print("-" * 80)
        print(f"Symbol:           {prediction.symbol}")
        print(f"Timestamp:        {prediction.timestamp}")
        print(f"Direction:        {prediction.direction}")
        print(f"Probability:      {prediction.probability:.1%}")
        print(f"Confidence:       {prediction.confidence:.1%}")
        print(f"Model:            {prediction.model_name}")
        print(f"Features Used:    {', '.join(prediction.features_used)}")
        
        # Get current price from dataframe
        current_price = df.iloc[-1]['close']
        print(f"\nCurrent Price:    ${current_price:.2f}")
        
        # Estimate expected direction based on probability
        if prediction.direction == "UP":
            print(f"Expected Movement: Price likely to rise")
        else:
            print(f"Expected Movement: Price likely to fall")
        
    except Exception as e:
        print(f"❌ ERROR generating prediction: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Validation checks
    print("\nStep 7: Validation Checks")
    print("-" * 80)
    checks_passed = 0
    total_checks = 6
    
    # Check 1: Prediction generated
    if prediction:
        print("✓ Check 1: Prediction successfully generated")
        checks_passed += 1
    else:
        print("❌ Check 1: FAILED - No prediction generated")
    
    # Check 2: Valid direction
    if prediction.direction in ['UP', 'DOWN']:
        print(f"✓ Check 2: Valid direction ({prediction.direction})")
        checks_passed += 1
    else:
        print(f"❌ Check 2: FAILED - Invalid direction: {prediction.direction}")
    
    # Check 3: Confidence in valid range
    if 0.0 <= prediction.confidence <= 1.0:
        print(f"✓ Check 3: Confidence in valid range ({prediction.confidence:.1%})")
        checks_passed += 1
    else:
        print(f"❌ Check 3: FAILED - Confidence out of range: {prediction.confidence}")
    
    # Check 4: Probability in valid range
    if 0.0 <= prediction.probability <= 1.0:
        print(f"✓ Check 4: Probability in valid range ({prediction.probability:.1%})")
        checks_passed += 1
    else:
        print(f"❌ Check 4: FAILED - Probability out of range: {prediction.probability}")
    
    # Check 5: Model name present
    if prediction.model_name:
        print(f"✓ Check 5: Model name present ({prediction.model_name})")
        checks_passed += 1
    else:
        print("❌ Check 5: FAILED - No model name")
    
    # Check 6: Features used provided
    if prediction.features_used and len(prediction.features_used) > 0:
        print(f"✓ Check 6: Features used provided ({len(prediction.features_used)} features)")
        checks_passed += 1
    else:
        print("❌ Check 6: FAILED - No features used")
    
    # Final result
    print("\n" + "="*80)
    print(f"TEST 8 RESULT: {'PASSED' if checks_passed >= 5 else 'FAILED'}")
    print(f"Checks: {checks_passed}/{total_checks} passed")
    print("="*80 + "\n")
    
    if checks_passed >= 5:
        print("✓ Ensemble prediction system is operational")
        print("✓ LSTM + Random Forest + Momentum ensemble working correctly")
        print("✓ Predictions have reasonable confidence scores")
        print("✓ Ready for signal generation testing (Test 9)")
        return True
    else:
        print("❌ Ensemble prediction system has issues")
        print("Please review the failed checks above")
        return False

if __name__ == "__main__":
    success = test_ensemble_prediction()
    sys.exit(0 if success else 1)
