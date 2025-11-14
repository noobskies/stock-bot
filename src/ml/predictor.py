"""
ML Predictor - Generate predictions using trained LSTM models.

This module handles:
- Loading trained models
- Making single predictions
- Calculating confidence scores
- Feature importance analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from datetime import datetime
from loguru import logger

from tensorflow import keras
from src.bot_types.trading_types import ModelPrediction
from src.data.feature_engineer import FeatureEngineer
from src.common.decorators import handle_ml_error


class LSTMPredictor:
    """Generate predictions using trained LSTM models."""
    
    def __init__(
        self,
        model_path: str,
        sequence_length: int = 60,
        confidence_threshold: float = 0.70
    ):
        """
        Initialize the LSTM predictor.
        
        Args:
            model_path: Path to trained model file (.h5 or .keras)
            sequence_length: Number of time steps in input sequence
            confidence_threshold: Minimum confidence for valid prediction
        """
        self.model_path = model_path
        self.sequence_length = sequence_length
        self.confidence_threshold = confidence_threshold
        
        self.model: Optional[keras.Model] = None
        self.feature_engineer: Optional[FeatureEngineer] = None
        self.feature_names: Optional[List[str]] = None
        
        # Load model
        self._load_model()
        
        logger.info(
            f"Initialized LSTMPredictor: model={model_path}, "
            f"seq_len={sequence_length}, threshold={confidence_threshold}"
        )
    
    @handle_ml_error()
    def _load_model(self) -> None:
        """Load trained model from disk."""
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        logger.info(f"Loading model from: {self.model_path}")
        self.model = keras.models.load_model(self.model_path)
        
        # Load metadata if available
        metadata_path = Path(self.model_path).with_suffix('.json')
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.sequence_length = metadata.get('sequence_length', self.sequence_length)
            self.feature_names = metadata.get('feature_names')
            logger.info(f"Loaded model metadata: trained_at={metadata.get('trained_at')}")
        
        logger.info("Model loaded successfully")
    
    @handle_ml_error()
    def predict_next_day(
        self,
        df: pd.DataFrame,
        symbol: str = "PLTR"
    ) -> Optional[ModelPrediction]:
        """
        Predict next day price direction.
        
        Args:
            df: DataFrame with historical OHLCV data (must have at least sequence_length rows)
            symbol: Stock symbol
            
        Returns:
            ModelPrediction with direction, confidence, and probability, or None if prediction fails
        """
        if len(df) < self.sequence_length:
            raise ValueError(
                f"Insufficient data: need {self.sequence_length} rows, got {len(df)}"
            )
        
        logger.info(f"Predicting next day direction for {symbol}")
        
        # Initialize feature engineer if needed
        if self.feature_engineer is None:
            self.feature_engineer = FeatureEngineer()
        
        # Calculate technical indicators
        df_features = self.feature_engineer.calculate_technical_indicators(df.copy())
        
        # Create ML features
        features_df = self.feature_engineer.create_ml_features(df_features)
        
        # Normalize features
        features_normalized = self.feature_engineer.normalize_features(features_df)
        
        # Create sequence (last sequence_length rows)
        sequence = features_normalized.values[-self.sequence_length:]
        sequence = sequence.reshape(1, self.sequence_length, -1)  # (1, seq_len, n_features)
        
        # Make prediction
        probability = float(self.model.predict(sequence, verbose=0)[0][0])
        
        # Determine direction
        direction = "UP" if probability > 0.5 else "DOWN"
        
        # Calculate confidence score (distance from 0.5)
        # More extreme probabilities = higher confidence
        confidence = abs(probability - 0.5) * 2.0  # Scale to [0, 1]
        
        # Calculate predicted price based on probability
        current_price = df.iloc[-1]['close']
        # Use probability to estimate price movement magnitude
        if direction == "UP":
            # For UP direction, use probability above 0.5 to scale the move
            move_percent = (probability - 0.5) * 0.04  # 0.5-1.0 -> 0-2%
            predicted_price = current_price * (1 + move_percent)
        else:
            # For DOWN direction, use probability below 0.5 to scale the move
            move_percent = (0.5 - probability) * 0.04  # 0.5-0.0 -> 0-2%
            predicted_price = current_price * (1 - move_percent)
        
        # Create prediction object
        prediction = ModelPrediction(
            symbol=symbol,
            predicted_price=predicted_price,
            direction=direction,
            confidence=confidence,
            features_used=self.feature_names or list(features_df.columns),
            timestamp=datetime.now(),
            model_name="LSTM",
            metadata={
                'probability': probability,
                'current_price': current_price
            }
        )
        
        logger.info(
            f"Prediction: {direction} with probability={probability:.3f}, "
            f"confidence={confidence:.3f}"
        )
        
        # Check if confidence meets threshold
        if confidence < self.confidence_threshold:
            logger.warning(
                f"Low confidence prediction: {confidence:.3f} < {self.confidence_threshold}"
            )
        
        return prediction
    
    @handle_ml_error()
    def predict_batch(
        self,
        sequences: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make batch predictions.
        
        Args:
            sequences: Array of sequences (n_samples, sequence_length, n_features)
            
        Returns:
            Tuple of (probabilities, confidences), or empty arrays if prediction fails
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        logger.info(f"Making batch predictions on {len(sequences)} samples")
        
        # Predict
        probabilities = self.model.predict(sequences, verbose=0).flatten()
        
        # Calculate confidences
        confidences = np.abs(probabilities - 0.5) * 2.0
        
        logger.info(
            f"Batch predictions complete: mean_prob={probabilities.mean():.3f}, "
            f"mean_conf={confidences.mean():.3f}"
        )
        
        return probabilities, confidences
    
    def calculate_confidence(
        self,
        probability: float,
        method: str = "distance"
    ) -> float:
        """
        Calculate confidence score from probability.
        
        Args:
            probability: Model output probability (0-1)
            method: Method to calculate confidence
                - "distance": Distance from 0.5 (default)
                - "entropy": Based on entropy of prediction
                
        Returns:
            Confidence score (0-1)
        """
        if method == "distance":
            # Distance from 0.5, scaled to [0, 1]
            confidence = abs(probability - 0.5) * 2.0
        
        elif method == "entropy":
            # Entropy-based confidence
            # Lower entropy = higher confidence
            epsilon = 1e-7  # Avoid log(0)
            p = np.clip(probability, epsilon, 1 - epsilon)
            entropy = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
            confidence = 1 - entropy  # Invert so higher is better
        
        else:
            raise ValueError(f"Unknown confidence method: {method}")
        
        return float(np.clip(confidence, 0.0, 1.0))
    
    @handle_ml_error()
    def get_feature_importance(
        self,
        df: pd.DataFrame,
        method: str = "permutation",
        n_samples: int = 100
    ) -> Dict[str, float]:
        """
        Estimate feature importance.
        
        Note: LSTM models don't have built-in feature importance like tree models.
        This uses approximation methods.
        
        Args:
            df: DataFrame with historical data for analysis
            method: Method to estimate importance
                - "permutation": Permutation importance (slower but more accurate)
                - "variance": Based on feature variance
            n_samples: Number of samples to use for permutation importance
            
        Returns:
            Dictionary mapping feature names to importance scores, or empty dict if fails
        """
        logger.info(f"Calculating feature importance using {method} method")
        
        if self.feature_engineer is None:
            self.feature_engineer = FeatureEngineer()
        
        # Prepare features
        df_features = self.feature_engineer.calculate_technical_indicators(df.copy())
        features_df = self.feature_engineer.create_ml_features(df_features)
        features_normalized = self.feature_engineer.normalize_features(features_df)
        
        # Get feature names
        feature_names = list(features_df.columns)
        
        if method == "permutation":
            # Permutation importance: shuffle each feature and measure prediction change
            importance_scores = {}
            
            # Create sequences
            sequences = []
            for i in range(self.sequence_length, len(features_normalized)):
                seq = features_normalized.values[i-self.sequence_length:i]
                sequences.append(seq)
            
            sequences = np.array(sequences)
            
            # Limit number of samples for speed
            if len(sequences) > n_samples:
                indices = np.random.choice(len(sequences), n_samples, replace=False)
                sequences = sequences[indices]
            
            # Baseline predictions
            baseline_probs = self.model.predict(sequences, verbose=0).flatten()
            baseline_variance = np.var(baseline_probs)
            
            # Shuffle each feature and measure change
            for feat_idx, feat_name in enumerate(feature_names):
                # Create copy of sequences
                shuffled_sequences = sequences.copy()
                
                # Shuffle this feature across all time steps
                for seq_idx in range(len(shuffled_sequences)):
                    for time_step in range(self.sequence_length):
                        shuffled_sequences[seq_idx, time_step, feat_idx] = np.random.permutation(
                            shuffled_sequences[:, time_step, feat_idx]
                        )[seq_idx]
                
                # Get predictions with shuffled feature
                shuffled_probs = self.model.predict(shuffled_sequences, verbose=0).flatten()
                
                # Importance = change in prediction variance
                # (If feature is important, shuffling it should change predictions)
                shuffled_variance = np.var(shuffled_probs)
                importance = abs(baseline_variance - shuffled_variance)
                importance_scores[feat_name] = float(importance)
            
            # Normalize to sum to 1
            total = sum(importance_scores.values())
            if total > 0:
                importance_scores = {k: v/total for k, v in importance_scores.items()}
        
        elif method == "variance":
            # Simple variance-based importance
            variances = features_normalized.var().to_dict()
            total = sum(variances.values())
            importance_scores = {k: v/total for k, v in variances.items()} if total > 0 else variances
        
        else:
            raise ValueError(f"Unknown importance method: {method}")
        
        # Sort by importance
        importance_scores = dict(sorted(
            importance_scores.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        logger.info(f"Top 5 important features: {list(importance_scores.keys())[:5]}")
        
        return importance_scores
    
    def get_prediction_explanation(
        self,
        prediction: ModelPrediction,
        df: pd.DataFrame
    ) -> Dict[str, any]:
        """
        Generate explanation for a prediction.
        
        Args:
            prediction: ModelPrediction to explain
            df: DataFrame with historical data used for prediction
            
        Returns:
            Dictionary with explanation details
        """
        logger.info(f"Generating explanation for {prediction.direction} prediction")
        
        # Get current technical indicators
        if self.feature_engineer is None:
            self.feature_engineer = FeatureEngineer()
        
        df_features = self.feature_engineer.calculate_technical_indicators(df.copy())
        latest = df_features.iloc[-1]
        
        # Key indicators
        explanation = {
            'prediction': prediction.direction,
            'probability': prediction.metadata.get('probability', 0.5),
            'confidence': prediction.confidence,
            'timestamp': prediction.timestamp.isoformat(),
            'technical_indicators': {
                'RSI': float(latest.get('RSI', 0)),
                'MACD': float(latest.get('MACD', 0)),
                'MACD_signal': float(latest.get('MACD_signal', 0)),
                'BB_position': float(latest.get('BB_position', 0)),
                'SMA_20': float(latest.get('SMA_20', 0)),
                'SMA_50': float(latest.get('SMA_50', 0)),
                'volume_ratio': float(latest.get('volume_ratio', 1.0)),
                'price_change_pct': float(latest.get('price_change_pct', 0))
            },
            'interpretation': self._interpret_indicators(latest)
        }
        
        return explanation
    
    def _interpret_indicators(self, indicators: pd.Series) -> Dict[str, str]:
        """
        Interpret technical indicators.
        
        Args:
            indicators: Series with indicator values
            
        Returns:
            Dictionary with human-readable interpretations
        """
        interpretation = {}
        
        # RSI
        rsi = indicators.get('RSI', 50)
        if rsi > 70:
            interpretation['RSI'] = "Overbought - bearish signal"
        elif rsi < 30:
            interpretation['RSI'] = "Oversold - bullish signal"
        else:
            interpretation['RSI'] = "Neutral"
        
        # MACD
        macd = indicators.get('MACD', 0)
        macd_signal = indicators.get('MACD_signal', 0)
        if macd > macd_signal:
            interpretation['MACD'] = "Bullish crossover"
        elif macd < macd_signal:
            interpretation['MACD'] = "Bearish crossover"
        else:
            interpretation['MACD'] = "Neutral"
        
        # Bollinger Bands
        bb_position = indicators.get('BB_position', 0.5)
        if bb_position > 0.8:
            interpretation['BB'] = "Near upper band - potential reversal"
        elif bb_position < 0.2:
            interpretation['BB'] = "Near lower band - potential bounce"
        else:
            interpretation['BB'] = "Within bands - normal"
        
        # Moving Averages
        sma_20 = indicators.get('SMA_20', 0)
        sma_50 = indicators.get('SMA_50', 0)
        close = indicators.get('close', 0)
        
        if close > sma_20 > sma_50:
            interpretation['MA'] = "Strong uptrend"
        elif close < sma_20 < sma_50:
            interpretation['MA'] = "Strong downtrend"
        else:
            interpretation['MA'] = "Mixed signals"
        
        return interpretation


# Example usage
if __name__ == "__main__":
    from loguru import logger
    import sys
    
    # Configure logging
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    print("\n=== LSTM Predictor Example ===\n")
    
    # Note: This example requires a trained model
    model_path = "models/lstm_model.h5"
    
    if not Path(model_path).exists():
        print(f"Model not found: {model_path}")
        print("Please train a model first using model_trainer.py")
        print("\nCreating demo prediction with mock model...")
        
        # Create mock prediction for demonstration
        mock_prediction = ModelPrediction(
            symbol="PLTR",
            predicted_price=30.50,
            direction="UP",
            confidence=0.50,
            features_used=["RSI", "MACD", "BB_position", "SMA_20", "volume_ratio"],
            timestamp=datetime.now(),
            model_name="LSTM",
            metadata={'probability': 0.75, 'current_price': 30.00}
        )
        
        print("\nMock Prediction:")
        print(f"  Symbol: {mock_prediction.symbol}")
        print(f"  Direction: {mock_prediction.direction}")
        print(f"  Predicted Price: ${mock_prediction.predicted_price:.2f}")
        print(f"  Confidence: {mock_prediction.confidence:.3f}")
        print(f"  Timestamp: {mock_prediction.timestamp}")
        if mock_prediction.metadata:
            print(f"  Probability: {mock_prediction.metadata.get('probability', 0):.3f}")
        
    else:
        print(f"Loading model from: {model_path}")
        
        # Initialize predictor
        predictor = LSTMPredictor(
            model_path=model_path,
            sequence_length=60,
            confidence_threshold=0.70
        )
        
        # Create sample data (normally would come from data_fetcher)
        print("\nCreating sample data...")
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        sample_df = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 30,
            'high': np.random.randn(100).cumsum() + 31,
            'low': np.random.randn(100).cumsum() + 29,
            'close': np.random.randn(100).cumsum() + 30,
            'volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
        
        print(f"Sample data shape: {sample_df.shape}")
        
        # Make prediction
        print("\nMaking prediction...")
        prediction = predictor.predict_next_day(sample_df, symbol="PLTR")
        
        print("\nPrediction Results:")
        print(f"  Symbol: {prediction.symbol}")
        print(f"  Direction: {prediction.direction}")
        print(f"  Predicted Price: ${prediction.predicted_price:.2f}")
        print(f"  Confidence: {prediction.confidence:.3f}")
        print(f"  Model: {prediction.model_name}")
        print(f"  Timestamp: {prediction.timestamp}")
        if prediction.metadata:
            print(f"  Probability: {prediction.metadata.get('probability', 0):.3f}")
        
        # Get explanation
        print("\nGenerating explanation...")
        explanation = predictor.get_prediction_explanation(prediction, sample_df)
        
        print("\nTechnical Indicators:")
        for indicator, value in explanation['technical_indicators'].items():
            print(f"  {indicator}: {value:.2f}")
        
        print("\nInterpretation:")
        for indicator, interp in explanation['interpretation'].items():
            print(f"  {indicator}: {interp}")
    
    print("\n=== Demo Complete ===")
