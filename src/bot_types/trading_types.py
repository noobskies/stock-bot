"""
Trading bot type definitions and data structures.

This module defines all enums, dataclasses, and type hints used throughout
the trading bot system.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


class TradingMode(Enum):
    """Trading execution modes."""
    AUTO = "auto"           # Full automation (confidence > 80%)
    MANUAL = "manual"       # All trades require approval
    HYBRID = "hybrid"       # Auto for high confidence, manual for medium


class SignalType(Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class OrderStatus(Enum):
    """Order lifecycle status."""
    PENDING = "pending"       # Signal generated, awaiting processing
    APPROVED = "approved"     # User approved (manual/hybrid mode)
    REJECTED = "rejected"     # User rejected signal
    EXECUTED = "executed"     # Order successfully executed
    FAILED = "failed"         # Order execution failed
    CANCELLED = "cancelled"   # Order cancelled


class PositionStatus(Enum):
    """Position lifecycle status."""
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class TradingSignal:
    """
    Trading signal generated from ML predictions.
    
    Attributes:
        symbol: Stock ticker symbol (e.g., 'PLTR')
        signal_type: BUY, SELL, or HOLD
        confidence: Prediction confidence (0.0 to 1.0)
        predicted_direction: 'up' or 'down'
        timestamp: When signal was generated
        features: Technical indicators used for prediction
        status: Current status of the signal
        quantity: Number of shares to trade (calculated by risk management)
        entry_price: Expected entry price
        stop_loss: Calculated stop loss price
    """
    symbol: str
    signal_type: SignalType
    confidence: float
    predicted_direction: str
    timestamp: datetime
    features: Dict[str, float]
    status: OrderStatus = OrderStatus.PENDING
    quantity: Optional[int] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None


@dataclass
class Position:
    """
    Active trading position.
    
    Attributes:
        symbol: Stock ticker symbol
        quantity: Number of shares held
        entry_price: Price at which position was entered
        current_price: Current market price
        stop_loss: Stop loss price (hard stop)
        trailing_stop: Trailing stop price (if activated)
        unrealized_pnl: Current profit/loss (not yet realized)
        unrealized_pnl_percent: P&L as percentage
        status: OPEN or CLOSED
        entry_time: When position was opened
        exit_time: When position was closed (if closed)
        exit_price: Price at which position was closed
        realized_pnl: Actual profit/loss after closing
    """
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    stop_loss: float
    unrealized_pnl: float
    status: PositionStatus
    entry_time: datetime
    trailing_stop: Optional[float] = None
    unrealized_pnl_percent: float = 0.0
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    realized_pnl: Optional[float] = None


@dataclass
class RiskMetrics:
    """
    Portfolio risk and exposure metrics.
    
    Attributes:
        portfolio_value: Total portfolio value (cash + positions)
        cash_available: Available buying power
        total_exposure: Total value of open positions
        total_exposure_percent: Exposure as percentage of portfolio
        daily_pnl: Today's profit/loss
        daily_pnl_percent: Today's P&L as percentage
        max_position_size: Maximum allowed position size ($)
        available_positions: Number of positions still allowed
        positions_used: Number of currently open positions
        daily_loss_limit_reached: Whether circuit breaker triggered
        portfolio_risk_percent: Current portfolio risk exposure
    """
    portfolio_value: float
    cash_available: float
    total_exposure: float
    total_exposure_percent: float
    daily_pnl: float
    daily_pnl_percent: float
    max_position_size: float
    available_positions: int
    positions_used: int
    daily_loss_limit_reached: bool
    portfolio_risk_percent: float


@dataclass
class ModelPrediction:
    """
    ML model prediction result.
    
    Attributes:
        symbol: Stock ticker symbol
        predicted_price: Predicted next-day price
        direction: 'up' or 'down'
        confidence: Model confidence (0.0 to 1.0)
        features_used: List of feature names used
        timestamp: When prediction was made
        model_name: Name of model that generated prediction
        metadata: Additional model-specific metadata
    """
    symbol: str
    predicted_price: float
    direction: str
    confidence: float
    features_used: List[str]
    timestamp: datetime
    model_name: str = "ensemble"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeRecord:
    """
    Complete trade record for database storage.
    
    Attributes:
        id: Unique trade ID (database primary key)
        symbol: Stock ticker symbol
        action: 'buy' or 'sell'
        quantity: Number of shares traded
        entry_price: Price at entry
        exit_price: Price at exit (if closed)
        stop_loss: Stop loss price
        trailing_stop: Trailing stop price (if activated)
        entry_time: When position opened
        exit_time: When position closed
        status: Position status
        unrealized_pnl: Current P&L (if open)
        realized_pnl: Final P&L (if closed)
        confidence_score: ML prediction confidence
        signal_id: Associated trading signal ID
    """
    symbol: str
    action: str
    quantity: int
    entry_price: float
    entry_time: datetime
    stop_loss: float
    status: str
    confidence_score: float
    id: Optional[int] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    trailing_stop: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    signal_id: Optional[int] = None


@dataclass
class PerformanceMetrics:
    """
    Trading performance metrics.
    
    Attributes:
        total_trades: Total number of trades executed
        winning_trades: Number of profitable trades
        losing_trades: Number of losing trades
        win_rate: Percentage of winning trades
        average_win: Average profit of winning trades
        average_loss: Average loss of losing trades
        largest_win: Largest single trade profit
        largest_loss: Largest single trade loss
        total_pnl: Total profit/loss
        total_pnl_percent: Total P&L as percentage
        sharpe_ratio: Risk-adjusted return metric
        max_drawdown: Maximum drawdown from peak
        max_drawdown_percent: Max drawdown as percentage
        current_streak: Current win/loss streak
        longest_win_streak: Longest winning streak
        longest_loss_streak: Longest losing streak
    """
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    total_pnl: float
    total_pnl_percent: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_percent: float
    current_streak: int
    longest_win_streak: int
    longest_loss_streak: int


@dataclass
class BotConfig:
    """
    Trading bot configuration.
    
    Loaded from config.yaml and environment variables.
    """
    # Trading configuration
    trading_mode: TradingMode
    symbols: List[str]
    initial_capital: float
    max_positions: int
    close_positions_eod: bool
    
    # Risk management
    risk_per_trade: float
    max_position_size: float
    max_portfolio_exposure: float
    daily_loss_limit: float
    stop_loss_percent: float
    trailing_stop_percent: float
    trailing_stop_activation: float
    
    # ML configuration
    model_path: str
    sequence_length: int
    prediction_confidence_threshold: float
    auto_execute_threshold: float
    
    # Database
    database_url: str
    
    # Logging
    log_level: str
    log_dir: str
