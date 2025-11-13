"""
ML Model Trainer - Build, train, and evaluate LSTM models for stock prediction.

This module handles:
- LSTM neural network architecture creation
- Model training with validation
- Performance evaluation
- Model persistence (save/load)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from datetime import datetime
from loguru import logger

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


class LSTMModelTrainer:
    """Train and evaluate LSTM models for stock price prediction."""
    
    def __init__(
        self,
        sequence_length: int = 60,
        lstm_units_1: int = 64,
        lstm_units_2: int = 32,
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001,
        batch_size: int = 32,
        epochs: int = 100,
        validation_split: float = 0.2,
        random_state: int = 42
    ):
        """
        Initialize the LSTM model trainer.
        
        Args:
            sequence_length: Number of time steps in each input sequence
            lstm_units_1: Number of units in first LSTM layer
            lstm_units_2: Number of units in second LSTM layer
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for Adam optimizer
            batch_size: Batch size for training
            epochs: Maximum number of training epochs
            validation_split: Fraction of data to use for validation
            random_state: Random seed for reproducibility
        """
        self.sequence_length = sequence_length
        self.lstm_units_1 = lstm_units_1
        self.lstm_units_2 = lstm_units_2
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.validation_split = validation_split
        self.random_state = random_state
        
        self.model: Optional[keras.Model] = None
        self.history: Optional[keras.callbacks.History] = None
        self.feature_names: Optional[list] = None
        
        # Set random seeds for reproducibility
        np.random.seed(random_state)
        tf.random.set_seed(random_state)
        
        logger.info(
            f"Initialized LSTMModelTrainer: seq_len={sequence_length}, "
            f"lstm=[{lstm_units_1},{lstm_units_2}], dropout={dropout_rate}"
        )
    
    def build_lstm_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """
        Build LSTM neural network architecture.
        
        Architecture:
        - LSTM layer 1: 64 units, return sequences
        - Dropout: 0.2
        - LSTM layer 2: 32 units
        - Dropout: 0.2
        - Dense: 1 unit with sigmoid activation (binary classification)
        
        Args:
            input_shape: Shape of input data (sequence_length, n_features)
            
        Returns:
            Compiled Keras model
        """
        logger.info(f"Building LSTM model with input shape: {input_shape}")
        
        model = keras.Sequential([
            # First LSTM layer - captures long-term dependencies
            layers.LSTM(
                self.lstm_units_1,
                return_sequences=True,
                input_shape=input_shape,
                name='lstm_1'
            ),
            layers.Dropout(self.dropout_rate, name='dropout_1'),
            
            # Second LSTM layer - refines patterns
            layers.LSTM(
                self.lstm_units_2,
                return_sequences=False,
                name='lstm_2'
            ),
            layers.Dropout(self.dropout_rate, name='dropout_2'),
            
            # Output layer - binary classification (up/down)
            layers.Dense(1, activation='sigmoid', name='output')
        ])
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='binary_crossentropy',
            metrics=[
                'accuracy',
                keras.metrics.Precision(name='precision'),
                keras.metrics.Recall(name='recall'),
                keras.metrics.AUC(name='auc')
            ]
        )
        
        logger.info("Model architecture:")
        model.summary(print_fn=logger.info)
        
        self.model = model
        return model
    
    def train_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        feature_names: Optional[list] = None,
        verbose: int = 1
    ) -> Dict[str, Any]:
        """
        Train the LSTM model.
        
        Args:
            X_train: Training features (n_samples, sequence_length, n_features)
            y_train: Training labels (n_samples,) - 1 for up, 0 for down
            X_val: Validation features (optional, will split from training if not provided)
            y_val: Validation labels (optional)
            feature_names: Names of features (optional, for tracking)
            verbose: Verbosity level (0=silent, 1=progress bar, 2=one line per epoch)
            
        Returns:
            Dictionary with training history and metrics
        """
        if self.model is None:
            # Auto-build model from input shape
            input_shape = (X_train.shape[1], X_train.shape[2])
            self.build_lstm_model(input_shape)
        
        self.feature_names = feature_names
        
        # Split validation set if not provided
        if X_val is None or y_val is None:
            X_train, X_val, y_train, y_val = train_test_split(
                X_train, y_train,
                test_size=self.validation_split,
                random_state=self.random_state,
                stratify=y_train  # Maintain class balance
            )
            logger.info(
                f"Split data: train={len(X_train)}, val={len(X_val)}, "
                f"stratified by class"
            )
        
        logger.info(
            f"Training LSTM model: train_samples={len(X_train)}, "
            f"val_samples={len(X_val)}, epochs={self.epochs}, "
            f"batch_size={self.batch_size}"
        )
        
        # Callbacks
        callbacks = [
            # Early stopping - stop if validation loss doesn't improve
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            
            # Reduce learning rate on plateau
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            ),
            
            # Save best model
            ModelCheckpoint(
                'models/best_model.h5',
                monitor='val_loss',
                save_best_only=True,
                verbose=0
            )
        ]
        
        # Train model
        start_time = datetime.now()
        
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.epochs,
            batch_size=self.batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
        
        training_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Training completed in {training_time:.1f} seconds")
        
        # Evaluate on validation set
        val_metrics = self.evaluate_model(X_val, y_val)
        
        # Prepare training summary
        training_summary = {
            'training_time_seconds': training_time,
            'epochs_trained': len(self.history.history['loss']),
            'final_train_loss': float(self.history.history['loss'][-1]),
            'final_val_loss': float(self.history.history['val_loss'][-1]),
            'final_train_accuracy': float(self.history.history['accuracy'][-1]),
            'final_val_accuracy': float(self.history.history['val_accuracy'][-1]),
            'validation_metrics': val_metrics,
            'best_epoch': int(np.argmin(self.history.history['val_loss'])) + 1
        }
        
        logger.info(f"Training summary: {training_summary}")
        
        return training_summary
    
    def evaluate_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        threshold: float = 0.5
    ) -> Dict[str, float]:
        """
        Evaluate model performance.
        
        Args:
            X: Features (n_samples, sequence_length, n_features)
            y: True labels (n_samples,)
            threshold: Probability threshold for classification
            
        Returns:
            Dictionary with evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not built or loaded. Train or load a model first.")
        
        logger.info(f"Evaluating model on {len(X)} samples")
        
        # Get predictions
        y_pred_proba = self.model.predict(X, verbose=0).flatten()
        y_pred = (y_pred_proba >= threshold).astype(int)
        
        # Calculate metrics
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, zero_division=0)
        recall = recall_score(y, y_pred, zero_division=0)
        f1 = f1_score(y, y_pred, zero_division=0)
        
        # Confusion matrix
        cm = confusion_matrix(y, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        # Directional accuracy (most important for trading)
        # What percentage of up/down predictions were correct
        up_mask = y == 1
        down_mask = y == 0
        up_accuracy = accuracy_score(y[up_mask], y_pred[up_mask]) if up_mask.sum() > 0 else 0.0
        down_accuracy = accuracy_score(y[down_mask], y_pred[down_mask]) if down_mask.sum() > 0 else 0.0
        
        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp),
            'up_accuracy': float(up_accuracy),
            'down_accuracy': float(down_accuracy),
            'n_samples': len(y),
            'threshold': threshold
        }
        
        logger.info(
            f"Evaluation metrics: accuracy={accuracy:.3f}, precision={precision:.3f}, "
            f"recall={recall:.3f}, f1={f1:.3f}, up_acc={up_accuracy:.3f}, "
            f"down_acc={down_accuracy:.3f}"
        )
        
        return metrics
    
    def save_model(self, filepath: str) -> None:
        """
        Save trained model to disk.
        
        Args:
            filepath: Path to save model file (.h5 or .keras)
        """
        if self.model is None:
            raise ValueError("No model to save. Train a model first.")
        
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Save model
        self.model.save(filepath)
        logger.info(f"Model saved to: {filepath}")
        
        # Save metadata
        metadata_path = Path(filepath).with_suffix('.json')
        metadata = {
            'sequence_length': self.sequence_length,
            'lstm_units_1': self.lstm_units_1,
            'lstm_units_2': self.lstm_units_2,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate,
            'feature_names': self.feature_names,
            'trained_at': datetime.now().isoformat()
        }
        
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Model metadata saved to: {metadata_path}")
    
    def load_model(self, filepath: str) -> keras.Model:
        """
        Load trained model from disk.
        
        Args:
            filepath: Path to model file (.h5 or .keras)
            
        Returns:
            Loaded Keras model
        """
        logger.info(f"Loading model from: {filepath}")
        
        # Load model
        self.model = keras.models.load_model(filepath)
        
        # Load metadata if available
        metadata_path = Path(filepath).with_suffix('.json')
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.sequence_length = metadata.get('sequence_length', self.sequence_length)
            self.feature_names = metadata.get('feature_names')
            logger.info(f"Loaded model metadata: {metadata}")
        
        logger.info("Model loaded successfully")
        return self.model
    
    def get_training_history(self) -> Optional[Dict[str, list]]:
        """
        Get training history.
        
        Returns:
            Dictionary with training metrics by epoch (loss, accuracy, etc.)
        """
        if self.history is None:
            logger.warning("No training history available")
            return None
        
        return self.history.history


def prepare_training_data(
    df: pd.DataFrame,
    target_column: str = 'target',
    sequence_length: int = 60,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list]:
    """
    Prepare data for LSTM training from a DataFrame.
    
    Args:
        df: DataFrame with features and target
        target_column: Name of target column (1=up, 0=down)
        sequence_length: Number of time steps in each sequence
        test_size: Fraction of data to use for testing
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test, feature_names)
    """
    logger.info(f"Preparing training data from DataFrame with {len(df)} rows")
    
    # Separate features and target
    y = df[target_column].values
    X = df.drop(columns=[target_column])
    feature_names = X.columns.tolist()
    X = X.values
    
    # Create sequences
    X_sequences = []
    y_sequences = []
    
    for i in range(sequence_length, len(X)):
        X_sequences.append(X[i-sequence_length:i])
        y_sequences.append(y[i])
    
    X_sequences = np.array(X_sequences)
    y_sequences = np.array(y_sequences)
    
    logger.info(
        f"Created {len(X_sequences)} sequences of length {sequence_length}, "
        f"with {len(feature_names)} features"
    )
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_sequences, y_sequences,
        test_size=test_size,
        random_state=random_state,
        stratify=y_sequences  # Maintain class balance
    )
    
    logger.info(
        f"Split into train={len(X_train)}, test={len(X_test)}, "
        f"stratified by target"
    )
    
    # Log class distribution
    train_up_pct = (y_train == 1).mean() * 100
    test_up_pct = (y_test == 1).mean() * 100
    logger.info(
        f"Class distribution: train_up={train_up_pct:.1f}%, "
        f"test_up={test_up_pct:.1f}%"
    )
    
    return X_train, X_test, y_train, y_test, feature_names


# Example usage
if __name__ == "__main__":
    from loguru import logger
    import sys
    
    # Configure logging
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    print("\n=== LSTM Model Trainer Example ===\n")
    
    # Example: Create synthetic data
    print("Creating synthetic training data...")
    n_samples = 1000
    sequence_length = 60
    n_features = 10
    
    # Random features and target
    X = np.random.randn(n_samples, sequence_length, n_features)
    y = np.random.randint(0, 2, n_samples)  # Binary: 0 or 1
    
    feature_names = [f"feature_{i}" for i in range(n_features)]
    
    print(f"Data shape: X={X.shape}, y={y.shape}")
    print(f"Features: {feature_names}")
    
    # Initialize trainer
    print("\nInitializing trainer...")
    trainer = LSTMModelTrainer(
        sequence_length=sequence_length,
        lstm_units_1=32,  # Smaller for demo
        lstm_units_2=16,
        epochs=5,  # Fewer epochs for demo
        batch_size=32,
        validation_split=0.2
    )
    
    # Build model
    print("\nBuilding model...")
    input_shape = (sequence_length, n_features)
    trainer.build_lstm_model(input_shape)
    
    # Train model
    print("\nTraining model...")
    training_summary = trainer.train_model(
        X, y,
        feature_names=feature_names,
        verbose=0
    )
    
    print("\nTraining Summary:")
    for key, value in training_summary.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
    
    # Save model
    print("\nSaving model...")
    trainer.save_model("models/demo_lstm_model.h5")
    
    # Load model
    print("\nLoading model...")
    trainer_new = LSTMModelTrainer()
    trainer_new.load_model("models/demo_lstm_model.h5")
    
    # Make predictions
    print("\nMaking predictions on test data...")
    X_test = X[:10]  # First 10 samples
    predictions = trainer_new.model.predict(X_test, verbose=0)
    
    print("Predictions (probability of 'up'):")
    for i, pred in enumerate(predictions.flatten()[:5]):
        print(f"  Sample {i}: {pred:.3f} ({'UP' if pred > 0.5 else 'DOWN'})")
    
    print("\n=== Demo Complete ===")
