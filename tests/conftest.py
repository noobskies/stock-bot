"""Shared pytest fixtures for all tests."""
import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def test_config():
    """Provide test configuration."""
    return {
        "trading": {
            "mode": "manual",
            "symbols": ["PLTR"],
            "initial_capital": 10000,
            "max_positions": 5,
            "close_positions_eod": True
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.20,
            "max_portfolio_exposure": 0.20,
            "daily_loss_limit": 0.05,
            "stop_loss_percent": 0.03,
            "trailing_stop_percent": 0.02,
            "trailing_stop_activation": 0.05
        },
        "ml": {
            "model_path": "models/lstm_model.h5",
            "sequence_length": 60,
            "prediction_confidence_threshold": 0.70,
            "auto_execute_threshold": 0.80
        }
    }

@pytest.fixture
def mock_alpaca_api():
    """Mock Alpaca API for testing.
    
    TODO: Implement comprehensive mock for Alpaca API
    to enable unit tests without actual API calls.
    """
    # Placeholder for future implementation
    pass

@pytest.fixture
def test_database():
    """Provide test database.
    
    TODO: Implement test database setup/teardown
    - Create temporary test database
    - Initialize schema
    - Cleanup after tests
    """
    # Placeholder for future implementation
    pass

@pytest.fixture
def sample_market_data():
    """Provide sample market data for testing."""
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Generate 60 days of sample OHLCV data
    dates = [datetime.now() - timedelta(days=i) for i in range(60, 0, -1)]
    data = {
        'timestamp': dates,
        'open': [30.0 + i * 0.1 for i in range(60)],
        'high': [30.5 + i * 0.1 for i in range(60)],
        'low': [29.5 + i * 0.1 for i in range(60)],
        'close': [30.0 + i * 0.1 for i in range(60)],
        'volume': [1000000 + i * 10000 for i in range(60)]
    }
    
    return pd.DataFrame(data)

@pytest.fixture
def sample_position():
    """Provide sample position for testing."""
    from datetime import datetime
    
    return {
        'symbol': 'PLTR',
        'quantity': 50,
        'entry_price': 30.00,
        'current_price': 31.50,
        'stop_loss': 29.10,
        'trailing_stop': None,
        'entry_time': datetime.now(),
        'side': 'long'
    }

@pytest.fixture
def sample_trade():
    """Provide sample trade for testing."""
    from datetime import datetime
    
    return {
        'symbol': 'PLTR',
        'action': 'BUY',
        'quantity': 50,
        'price': 30.00,
        'timestamp': datetime.now(),
        'order_id': 'test-order-123',
        'status': 'filled'
    }
