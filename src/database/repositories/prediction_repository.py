"""
Prediction Repository for database operations.

Handles all CRUD operations for Prediction entities.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import and_
from loguru import logger

from src.database.repositories.base_repository import BaseRepository
from src.database.schema import Prediction


class PredictionRepository(BaseRepository):
    """Repository for Prediction entity operations."""
    
    def save_prediction(self, prediction_data: Dict[str, Any]) -> int:
        """
        Save an ML prediction.
        
        Args:
            prediction_data: Dictionary with prediction information
            
        Returns:
            int: Prediction ID
        """
        with self.get_session() as session:
            prediction = Prediction(**prediction_data)
            session.add(prediction)
            session.flush()
            prediction_id = prediction.id
            logger.debug(f"Saved prediction {prediction_id}: {prediction.symbol}")
            return prediction_id
    
    def update_prediction_actual(
        self, 
        prediction_id: int, 
        actual_price: float
    ) -> bool:
        """
        Update prediction with actual price (next day).
        
        Args:
            prediction_id: Prediction ID
            actual_price: Actual price that occurred
            
        Returns:
            bool: True if updated successfully
        """
        with self.get_session() as session:
            prediction = session.query(Prediction).filter(
                Prediction.id == prediction_id
            ).first()
            
            if not prediction:
                logger.warning(f"Prediction {prediction_id} not found")
                return False
            
            prediction.actual_price = actual_price
            
            # Calculate accuracy
            predicted_direction = prediction.direction
            actual_direction = 'up' if actual_price > prediction.predicted_price else 'down'
            prediction.accuracy = (predicted_direction == actual_direction)
            
            # Calculate error
            prediction.error = abs(actual_price - prediction.predicted_price)
            
            logger.debug(f"Updated prediction {prediction_id} with actual: {actual_price}")
            return True
    
    def get_predictions_by_symbol(
        self, 
        symbol: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get predictions for a specific symbol.
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of predictions to return
            
        Returns:
            List[Dict]: List of prediction dictionaries
        """
        with self.get_session() as session:
            predictions = session.query(Prediction).filter(
                Prediction.symbol == symbol
            ).order_by(Prediction.prediction_time.desc()).limit(limit).all()
            
            return [self._prediction_to_dict(p) for p in predictions]
    
    def get_recent_predictions(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get recent predictions within specified days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List[Dict]: List of prediction dictionaries
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self.get_session() as session:
            predictions = session.query(Prediction).filter(
                Prediction.prediction_time >= cutoff
            ).order_by(Prediction.prediction_time.desc()).all()
            
            return [self._prediction_to_dict(p) for p in predictions]
    
    def get_prediction_accuracy(self, days: int = 30) -> float:
        """
        Calculate prediction accuracy over a period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            float: Accuracy percentage (0-100)
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self.get_session() as session:
            total = session.query(Prediction).filter(
                and_(
                    Prediction.prediction_time >= cutoff,
                    Prediction.accuracy.isnot(None)
                )
            ).count()
            
            if total == 0:
                return 0.0
            
            correct = session.query(Prediction).filter(
                and_(
                    Prediction.prediction_time >= cutoff,
                    Prediction.accuracy == True
                )
            ).count()
            
            return (correct / total) * 100
    
    @staticmethod
    def _prediction_to_dict(prediction: Prediction) -> Dict[str, Any]:
        """Convert Prediction object to dictionary."""
        return {
            'id': prediction.id,
            'symbol': prediction.symbol,
            'predicted_price': prediction.predicted_price,
            'actual_price': prediction.actual_price,
            'direction': prediction.direction,
            'confidence': prediction.confidence,
            'model_name': prediction.model_name,
            'features_used': prediction.features_used,
            'prediction_time': prediction.prediction_time,
            'target_date': prediction.target_date,
            'accuracy': prediction.accuracy,
            'error': prediction.error,
            'prediction_metadata': prediction.prediction_metadata,
            'created_at': prediction.created_at
        }
