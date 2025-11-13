"""
Ensemble Prediction - Combine multiple models for robust predictions.

This module handles:
- Combining LSTM + Random Forest + momentum signals
- Calculating aggregate confidence scores
- Weighted voting for final prediction
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime
from loguru import logger

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

from src.types.trading_types import ModelPrediction
from src.ml.predictor import LSTMPredictor
from src.data.feature_engineer import FeatureEngineer


class EnsemblePredictor:
    """Combine multiple prediction methods for robust trading signals."""
    
    def __init__(
        self,
        lstm_model_path: str,
        rf_model_path: Optional[str] = None,
        lstm_weight: float = 0.5,
        rf_weight: float = 0.3,
        momentum_weight: float = 0.2,
        sequence_length: int = 60,
        confidence_threshold: float = 0.70
    ):
        """
        Initialize the ensemble predictor.
        
        Args:
            lstm_model_path: Path to trained LSTM model
            rf_model_path: Path to trained Random Forest model (optional)
            lstm_weight: Weight for LSTM predictions (default: 0.5)
            rf_weight: Weight for Random Forest predictions (default: 0.3)
            momentum_weight: Weight for momentum signals (default: 0.2)
            sequence_length: Number of time steps for LSTM
            confidence_threshold: Minimum confidence for valid prediction
        """
        self.lstm_weight = lstm_weight
        self.rf_weight = rf_weight
        self.momentum_weight = momentum_weight
        self.sequence_length = sequence_length
        self.confidence_threshold = confidence_threshold
        
        # Validate weights sum to 1
        total_weight = lstm_weight + rf_weight + momentum_weight
        if not np.isclose(total_weight, 1.0):
            logger.warning(
                f"Weights don't sum to 1.0 (got {total_weight}), normalizing..."
            )
            self.lstm_weight /= total_weight
            self.rf_weight /= total_weight
            self.momentum_weight /= total_weight
        
        # Initialize models
        self.lstm_predictor: Optional[LSTMPredictor] = None
        self.rf_model: Optional[RandomForestClassifier] = None
        self.rf_scaler: Optional[StandardScaler] = None
        self.feature_engineer = FeatureEngineer()
        
        # Load LSTM model
        if Path(lstm_model_path).exists():
            self.lstm_predictor = LSTMPredictor(
                model_path=lstm_model_path,
                sequence_length=sequence_length,
                confidence_threshold=confidence_threshold
            )
            logger.info(f"Loaded LSTM model from: {lstm_model_path}")
        else:
            logger.warning(f"LSTM model not found: {lstm_model_path}")
        
        # Load Random Forest model if provided
        if rf_model_path and Path(rf_model_path).exists():
            self.rf_model = joblib.load(rf_model_path)
            scaler_path = Path(rf_model_path).with_suffix('.scaler')
            if scaler_path.exists():
                self.rf_scaler = joblib.load(scaler_path)
            logger.info(f"Loaded Random Forest model from: {rf_model_path}")
        else:
            logger.info("Random Forest model not loaded (optional)")
        
        logger.info(
            f"Initialized EnsemblePredictor: lstm_w={self.lstm_weight:.2f}, "
            f"rf_w={self.rf_weight:.2f}, momentum_w={self.momentum_weight:.2f}"
        )
    
    def ensemble_predict(
        self,
        df: pd.DataFrame,
        symbol: str = "PLTR"
    ) -> ModelPrediction:
        """
        Generate ensemble prediction combining all methods.
        
        Args:
            df: DataFrame with historical OHLCV data
            symbol: Stock symbol
            
        Returns:
            ModelPrediction with ensemble direction and confidence
        """
        logger.info(f"Generating ensemble prediction for {symbol}")
        
        predictions = {}
        weights = {}
        
        # 1. LSTM Prediction
        if self.lstm_predictor is not None:
            try:
                lstm_pred = self.lstm_predictor.predict_next_day(df, symbol)
                # Get probability from metadata (stored there to match ModelPrediction dataclass)
                lstm_probability = lstm_pred.metadata.get('probability', 0.5)
                predictions['lstm'] = lstm_probability
                weights['lstm'] = self.lstm_weight
                logger.info(
                    f"LSTM: direction={lstm_pred.direction}, "
                    f"prob={lstm_probability:.3f}, "
                    f"conf={lstm_pred.confidence:.3f}"
                )
            except Exception as e:
                logger.error(f"LSTM prediction failed: {e}")
                weights['lstm'] = 0.0
        else:
            logger.warning("LSTM predictor not available")
            weights['lstm'] = 0.0
        
        # 2. Random Forest Prediction
        if self.rf_model is not None:
            try:
                rf_prob = self._predict_random_forest(df)
                predictions['rf'] = rf_prob
                weights['rf'] = self.rf_weight
                rf_direction = "UP" if rf_prob > 0.5 else "DOWN"
                logger.info(
                    f"Random Forest: direction={rf_direction}, prob={rf_prob:.3f}"
                )
            except Exception as e:
                logger.error(f"Random Forest prediction failed: {e}")
                weights['rf'] = 0.0
        else:
            logger.info("Random Forest not available, redistributing weight")
            weights['rf'] = 0.0
        
        # 3. Momentum Signal
        try:
            momentum_prob = self._calculate_momentum_signal(df)
            predictions['momentum'] = momentum_prob
            weights['momentum'] = self.momentum_weight
            momentum_direction = "UP" if momentum_prob > 0.5 else "DOWN"
            logger.info(
                f"Momentum: direction={momentum_direction}, prob={momentum_prob:.3f}"
            )
        except Exception as e:
            logger.error(f"Momentum calculation failed: {e}")
            weights['momentum'] = 0.0
        
        # Normalize weights if some models failed
        total_weight = sum(weights.values())
        if total_weight == 0:
            raise RuntimeError("All prediction methods failed")
        
        if total_weight < 1.0:
            logger.warning(f"Normalizing weights (total={total_weight})")
            for key in weights:
                weights[key] /= total_weight
        
        # Calculate weighted ensemble probability
        ensemble_probability = sum(
            predictions.get(key, 0.5) * weights[key]
            for key in weights
        )
        
        # Determine direction
        direction = "UP" if ensemble_probability > 0.5 else "DOWN"
        
        # Calculate confidence
        # More agreement between models = higher confidence
        confidence = self._calculate_ensemble_confidence(predictions, weights)
        
        # Calculate predicted price based on ensemble probability
        current_price = df.iloc[-1]['close']
        # Use probability to estimate price movement magnitude
        # Higher probability = larger expected move
        if direction == "UP":
            # For UP direction, use probability above 0.5 to scale the move
            move_percent = (ensemble_probability - 0.5) * 0.04  # 0.5-1.0 -> 0-2%
            predicted_price = current_price * (1 + move_percent)
        else:
            # For DOWN direction, use probability below 0.5 to scale the move
            move_percent = (0.5 - ensemble_probability) * 0.04  # 0.5-0.0 -> 0-2%
            predicted_price = current_price * (1 - move_percent)
        
        # Create ensemble prediction
        prediction = ModelPrediction(
            symbol=symbol,
            predicted_price=predicted_price,
            direction=direction,
            confidence=confidence,
            features_used=["LSTM", "RandomForest", "Momentum"],
            timestamp=datetime.now(),
            model_name="Ensemble",
            metadata={
                'ensemble_probability': ensemble_probability,
                'lstm_weight': weights.get('lstm', 0),
                'rf_weight': weights.get('rf', 0),
                'momentum_weight': weights.get('momentum', 0),
                'current_price': current_price
            }
        )
        
        logger.info(
            f"Ensemble prediction: {direction} with "
            f"probability={ensemble_probability:.3f}, confidence={confidence:.3f}"
        )
        
        # Log individual contributions
        for model, prob in predictions.items():
            contribution = (prob - 0.5) * weights[model] * 2  # How much this model influenced result
            logger.debug(f"  {model}: prob={prob:.3f}, weight={weights[model]:.2f}, contribution={contribution:.3f}")
        
        return prediction
    
    def _predict_random_forest(self, df: pd.DataFrame) -> float:
        """
        Generate Random Forest prediction.
        
        Args:
            df: DataFrame with historical data
            
        Returns:
            Probability of up movement (0-1)
        """
        # Calculate features
        df_features = self.feature_engineer.calculate_technical_indicators(df.copy())
        features_df = self.feature_engineer.create_ml_features(df_features)
        
        # Get latest features (no sequences for RF)
        X = features_df.iloc[-1:].values
        
        # Scale if scaler available
        if self.rf_scaler is not None:
            X = self.rf_scaler.transform(X)
        
        # Predict
        probability = self.rf_model.predict_proba(X)[0, 1]  # Probability of class 1 (UP)
        
        return float(probability)
    
    def _calculate_momentum_signal(self, df: pd.DataFrame) -> float:
        """
        Calculate momentum-based signal.
        
        Simple momentum strategy:
        - Recent price trend
        - Volume confirmation
        - RSI levels
        
        Args:
            df: DataFrame with historical data
            
        Returns:
            Probability of up movement (0-1)
        """
        # Calculate technical indicators
        df_features = self.feature_engineer.calculate_technical_indicators(df.copy())
        latest = df_features.iloc[-1]
        
        signals = []
        
        # 1. Price momentum (20% weight)
        # Compare current price to moving averages
        close = latest['close']
        sma_20 = latest.get('SMA_20', close)
        sma_50 = latest.get('SMA_50', close)
        
        if close > sma_20 > sma_50:
            price_signal = 0.8  # Strong uptrend
        elif close > sma_20:
            price_signal = 0.65  # Moderate uptrend
        elif close < sma_20 < sma_50:
            price_signal = 0.2  # Strong downtrend
        elif close < sma_20:
            price_signal = 0.35  # Moderate downtrend
        else:
            price_signal = 0.5  # Neutral
        
        signals.append(('price_momentum', price_signal, 0.3))
        
        # 2. RSI signal (15% weight)
        rsi = latest.get('RSI', 50)
        
        if rsi < 30:
            rsi_signal = 0.7  # Oversold, likely to bounce
        elif rsi > 70:
            rsi_signal = 0.3  # Overbought, likely to drop
        elif 40 <= rsi <= 60:
            rsi_signal = 0.5  # Neutral
        elif rsi < 50:
            rsi_signal = 0.4  # Slightly bearish
        else:
            rsi_signal = 0.6  # Slightly bullish
        
        signals.append(('rsi', rsi_signal, 0.2))
        
        # 3. MACD signal (20% weight)
        macd = latest.get('MACD', 0)
        macd_signal = latest.get('MACD_signal', 0)
        
        if macd > macd_signal and macd > 0:
            macd_prob = 0.75  # Bullish above zero line
        elif macd > macd_signal:
            macd_prob = 0.65  # Bullish below zero line
        elif macd < macd_signal and macd < 0:
            macd_prob = 0.25  # Bearish below zero line
        elif macd < macd_signal:
            macd_prob = 0.35  # Bearish above zero line
        else:
            macd_prob = 0.5  # Neutral
        
        signals.append(('macd', macd_prob, 0.25))
        
        # 4. Volume confirmation (10% weight)
        volume_ratio = latest.get('volume_ratio', 1.0)
        
        if volume_ratio > 1.5:
            # High volume - amplifies the price signal
            volume_prob = 0.5 + (price_signal - 0.5) * 1.2  # Amplify
        elif volume_ratio < 0.7:
            # Low volume - dampens the signal
            volume_prob = 0.5 + (price_signal - 0.5) * 0.5  # Dampen
        else:
            volume_prob = price_signal  # Normal volume
        
        volume_prob = np.clip(volume_prob, 0, 1)
        signals.append(('volume', volume_prob, 0.15))
        
        # 5. Recent price change (10% weight)
        price_change_pct = latest.get('price_change_pct', 0)
        
        if price_change_pct > 0:
            change_prob = 0.5 + min(price_change_pct / 10, 0.3)  # Cap at 0.8
        else:
            change_prob = 0.5 + max(price_change_pct / 10, -0.3)  # Floor at 0.2
        
        signals.append(('price_change', change_prob, 0.1))
        
        # Calculate weighted average
        total_weight = sum(w for _, _, w in signals)
        momentum_probability = sum(p * w for _, p, w in signals) / total_weight
        
        # Log signal breakdown
        for name, prob, weight in signals:
            logger.debug(f"  Momentum {name}: {prob:.3f} (weight={weight:.2f})")
        
        return float(np.clip(momentum_probability, 0, 1))
    
    def _calculate_ensemble_confidence(
        self,
        predictions: Dict[str, float],
        weights: Dict[str, float]
    ) -> float:
        """
        Calculate ensemble confidence based on agreement between models.
        
        High confidence when:
        - All models agree on direction
        - Individual models have high confidence
        
        Low confidence when:
        - Models disagree
        - Individual models are uncertain
        
        Args:
            predictions: Dictionary of model predictions (probabilities)
            weights: Dictionary of model weights
            
        Returns:
            Confidence score (0-1)
        """
        if not predictions:
            return 0.0
        
        probs = list(predictions.values())
        
        # 1. Agreement score - how much do models agree?
        # Standard deviation of probabilities (lower = more agreement)
        std = np.std(probs)
        agreement_score = 1.0 - min(std * 2, 1.0)  # Normalize to [0, 1]
        
        # 2. Extremity score - how extreme are the predictions?
        # More extreme (close to 0 or 1) = higher confidence
        extremity_scores = [abs(p - 0.5) * 2 for p in probs]
        avg_extremity = np.mean(extremity_scores)
        
        # 3. Weighted combination
        # Agreement is more important than extremity
        confidence = (agreement_score * 0.6) + (avg_extremity * 0.4)
        
        logger.debug(
            f"Confidence breakdown: agreement={agreement_score:.3f}, "
            f"extremity={avg_extremity:.3f}, final={confidence:.3f}"
        )
        
        return float(np.clip(confidence, 0, 1))
    
    def train_random_forest(
        self,
        df: pd.DataFrame,
        target_column: str = 'target',
        save_path: str = 'models/random_forest.pkl',
        n_estimators: int = 100,
        max_depth: int = 10,
        random_state: int = 42
    ) -> Dict[str, float]:
        """
        Train Random Forest model.
        
        Args:
            df: DataFrame with features and target
            target_column: Name of target column
            save_path: Path to save trained model
            n_estimators: Number of trees
            max_depth: Maximum tree depth
            random_state: Random seed
            
        Returns:
            Dictionary with training metrics
        """
        logger.info("Training Random Forest model")
        
        # Prepare data
        y = df[target_column].values
        X = df.drop(columns=[target_column])
        feature_names = X.columns.tolist()
        X = X.values
        
        # Split train/test
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=random_state, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        rf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )
        
        rf.fit(X_train_scaled, y_train)
        
        # Evaluate
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        y_pred = rf.predict(X_test_scaled)
        
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, zero_division=0)),
            'f1_score': float(f1_score(y_test, y_pred, zero_division=0))
        }
        
        logger.info(f"Random Forest metrics: {metrics}")
        
        # Save model
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(rf, save_path)
        joblib.dump(scaler, Path(save_path).with_suffix('.scaler'))
        
        # Save feature names
        import json
        metadata = {
            'feature_names': feature_names,
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'trained_at': datetime.now().isoformat()
        }
        with open(Path(save_path).with_suffix('.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Random Forest model saved to: {save_path}")
        
        self.rf_model = rf
        self.rf_scaler = scaler
        
        return metrics


# Example usage
if __name__ == "__main__":
    from loguru import logger
    import sys
    
    # Configure logging
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    print("\n=== Ensemble Predictor Example ===\n")
    
    # Check if models exist
    lstm_path = "models/lstm_model.h5"
    rf_path = "models/random_forest.pkl"
    
    if not Path(lstm_path).exists():
        print(f"LSTM model not found: {lstm_path}")
        print("Please train an LSTM model first using model_trainer.py")
        print("\nCreating demo ensemble prediction...")
        
        # Create mock ensemble prediction
        mock_prediction = ModelPrediction(
            symbol="PLTR",
            predicted_price=32.50,
            direction="UP",
            confidence=0.65,
            features_used=["LSTM", "RandomForest", "Momentum"],
            timestamp=datetime.now(),
            model_name="Ensemble",
            metadata={'ensemble_probability': 0.72, 'current_price': 32.00}
        )
        
        print("\nMock Ensemble Prediction:")
        print(f"  Symbol: {mock_prediction.symbol}")
        print(f"  Direction: {mock_prediction.direction}")
        print(f"  Predicted Price: ${mock_prediction.predicted_price:.2f}")
        print(f"  Confidence: {mock_prediction.confidence:.3f}")
        print(f"  Model: {mock_prediction.model_name}")
        print(f"  Methods: {', '.join(mock_prediction.features_used)}")
        
    else:
        print("Initializing ensemble predictor...")
        
        # Initialize ensemble
        ensemble = EnsemblePredictor(
            lstm_model_path=lstm_path,
            rf_model_path=rf_path if Path(rf_path).exists() else None,
            lstm_weight=0.5,
            rf_weight=0.3,
            momentum_weight=0.2
        )
        
        # Create sample data
        print("\nCreating sample data...")
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        sample_df = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 30,
            'high': np.random.randn(100).cumsum() + 31,
            'low': np.random.randn(100).cumsum() + 29,
            'close': np.random.randn(100).cumsum() + 30,
            'volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
        
        # Make ensemble prediction
        print("\nGenerating ensemble prediction...")
        prediction = ensemble.ensemble_predict(sample_df, symbol="PLTR")
        
        print("\nEnsemble Prediction Results:")
        print(f"  Symbol: {prediction.symbol}")
        print(f"  Direction: {prediction.direction}")
        print(f"  Predicted Price: ${prediction.predicted_price:.2f}")
        print(f"  Confidence: {prediction.confidence:.3f}")
        print(f"  Model: {prediction.model_name}")
        print(f"  Timestamp: {prediction.timestamp}")
        if prediction.metadata:
            print(f"  Ensemble Probability: {prediction.metadata.get('ensemble_probability', 0):.3f}")
    
    print("\n=== Demo Complete ===")
