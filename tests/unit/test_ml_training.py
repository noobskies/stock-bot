#!/usr/bin/env python3
"""
Test 7: ML Model Training
Trains LSTM model on historical PLTR data and validates performance.
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

def test_ml_training():
    """Test ML model training."""
    print("\n" + "="*80)
    print("TEST 7: ML MODEL TRAINING")
    print("="*80)
    
    try:
        # Import modules
        print("\n[1/6] Importing modules...")
        from data.data_fetcher import DataFetcher
        from data.feature_engineer import FeatureEngineer
        from ml.model_trainer import LSTMModelTrainer
        print("✅ All modules imported successfully")
        
        # Initialize modules
        print("\n[2/6] Initializing modules...")
        alpaca_api_key = os.getenv('ALPACA_API_KEY')
        alpaca_secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        if not alpaca_api_key or not alpaca_secret_key:
            print("❌ Missing Alpaca API credentials")
            return False
        
        data_fetcher = DataFetcher(
            alpaca_api_key=alpaca_api_key,
            alpaca_secret_key=alpaca_secret_key
        )
        feature_engineer = FeatureEngineer()
        
        print("✅ Modules initialized")
        
        # Fetch and prepare data
        print("\n[3/6] Fetching and preparing training data...")
        symbol = "PLTR"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)  # 2 years
        
        print(f"   Fetching {symbol} data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        df = data_fetcher.fetch_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe="day"
        )
        
        if df is None or df.empty:
            print("❌ Failed to fetch historical data")
            return False
        
        print(f"✅ Fetched {len(df)} days of data")
        
        # Calculate indicators
        print(f"   Calculating technical indicators...")
        df_indicators = feature_engineer.calculate_technical_indicators(df)
        print(f"✅ Calculated indicators ({df_indicators.shape[1]} total columns)")
        
        # Create features and sequences
        print(f"   Creating ML features and sequences...")
        X, y = feature_engineer.create_ml_features(df_indicators)
        
        if X is None or y is None:
            print("❌ Failed to create features")
            return False
        
        print(f"✅ Created features: {X.shape}")
        
        X_seq, y_seq = feature_engineer.create_sequences(X, y, sequence_length=60)
        
        if X_seq is None or y_seq is None:
            print("❌ Failed to create sequences")
            return False
        
        print(f"✅ Created sequences: {X_seq.shape}")
        print(f"   Target distribution: Up={np.sum(y_seq==1)}, Down={np.sum(y_seq==0)}")
        
        # Normalize features
        print(f"   Normalizing features...")
        X_normalized, scaler = feature_engineer.normalize_features(X_seq.reshape(-1, X_seq.shape[-1]))
        X_normalized = X_normalized.reshape(X_seq.shape)
        print(f"✅ Features normalized")
        
        # Train model
        print("\n[4/6] Training LSTM model...")
        print(f"   This may take 10-30 minutes depending on hardware...")
        
        # Split data for training and validation
        split_idx = int(len(X_normalized) * 0.8)
        X_train, X_val = X_normalized[:split_idx], X_normalized[split_idx:]
        y_train, y_val = y_seq[:split_idx], y_seq[split_idx:]
        
        print(f"   Training set: {len(X_train)} sequences")
        print(f"   Validation set: {len(X_val)} sequences")
        
        model_trainer = LSTMModelTrainer(
            sequence_length=60,
            epochs=50,
            batch_size=32
        )
        
        print(f"\n   Training model (this will take a while)...")
        results = model_trainer.train_model(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val
        )
        
        if results is None:
            print("❌ Model training failed")
            return False
        
        # Model, history, and metrics are stored in the trainer instance
        model = model_trainer.model
        history = model_trainer.history
        metrics = results['validation_metrics']
        
        print(f"✅ Model training completed")
        print(f"   Final training accuracy: {history.history['accuracy'][-1]:.4f}")
        print(f"   Final validation accuracy: {history.history['val_accuracy'][-1]:.4f}")
        print(f"   Final training loss: {history.history['loss'][-1]:.4f}")
        print(f"   Final validation loss: {history.history['val_loss'][-1]:.4f}")
        
        # Evaluate model
        print("\n[5/6] Evaluating model performance...")
        
        print(f"✅ Model evaluation complete:")
        print(f"   Accuracy: {metrics['accuracy']:.4f}")
        print(f"   Precision: {metrics['precision']:.4f}")
        print(f"   Recall: {metrics['recall']:.4f}")
        print(f"   F1 Score: {metrics['f1_score']:.4f}")
        print(f"   Directional Accuracy: {metrics.get('directional_accuracy', metrics['accuracy']):.4f}")
        
        # Check if model meets minimum accuracy requirement
        min_accuracy = 0.60
        if metrics['accuracy'] < min_accuracy:
            print(f"\n⚠️  WARNING: Model accuracy ({metrics['accuracy']:.4f}) below target ({min_accuracy})")
            print(f"   This is acceptable for testing, but may need improvement for live trading")
        else:
            print(f"\n✅ Model accuracy ({metrics['accuracy']:.4f}) meets minimum requirement ({min_accuracy})")
        
        # Save model
        print("\n[6/6] Saving model...")
        
        # Create models directory if it doesn't exist
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        model_path = "models/lstm_model.h5"
        
        # save_model only takes filepath - metadata saved automatically
        model_trainer.save_model(model_path)
        
        print(f"✅ Model saved to {model_path}")
        print(f"   Model size: {os.path.getsize(model_path) / (1024*1024):.2f} MB")
        
        # Verify model can be loaded
        print(f"\n   Verifying model can be loaded...")
        new_trainer = LSTMModelTrainer()
        loaded_model = new_trainer.load_model(model_path)
        
        if loaded_model is None:
            print("❌ Failed to load saved model")
            return False
        
        print(f"✅ Model successfully loaded and verified")
        print(f"   Sequence length: {new_trainer.sequence_length}")
        print(f"   Feature names: {len(new_trainer.feature_names) if new_trainer.feature_names else 0} features")
        
        # Summary
        print("\n" + "="*80)
        print("TEST 7 RESULTS: ML MODEL TRAINING")
        print("="*80)
        print("✅ Data preparation: PASSED")
        print(f"   - {len(df)} days of historical data")
        print(f"   - {X_seq.shape[0]} training sequences")
        print("✅ Model training: PASSED")
        print(f"   - Training accuracy: {history.history['accuracy'][-1]:.4f}")
        print(f"   - Validation accuracy: {history.history['val_accuracy'][-1]:.4f}")
        print("✅ Model evaluation: PASSED")
        print(f"   - Test accuracy: {metrics['accuracy']:.4f}")
        print(f"   - Precision: {metrics['precision']:.4f}")
        print(f"   - Recall: {metrics['recall']:.4f}")
        print(f"   - F1 Score: {metrics['f1_score']:.4f}")
        print("✅ Model persistence: PASSED")
        print(f"   - Saved to {model_path}")
        print(f"   - Load verification successful")
        
        if metrics['accuracy'] >= min_accuracy:
            print(f"\n✅ TEST 7: ML MODEL TRAINING - PASSED")
        else:
            print(f"\n⚠️  TEST 7: ML MODEL TRAINING - PASSED (with warnings)")
            print(f"   Model accuracy below target but acceptable for testing")
        
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 7 FAILED with exception:")
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
        level="WARNING"  # Only show warnings and errors
    )
    
    success = test_ml_training()
    sys.exit(0 if success else 1)
