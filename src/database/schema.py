"""
Database schema definitions using SQLAlchemy ORM.

Defines all database tables and their relationships for the trading bot.
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create declarative base
Base = declarative_base()


class Trade(Base):
    """
    Trade records table.
    
    Stores complete information about each trade executed by the bot.
    """
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # 'buy' or 'sell'
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=False)
    trailing_stop = Column(Float, nullable=True)
    entry_time = Column(DateTime, nullable=False, index=True)
    exit_time = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, index=True)  # 'open' or 'closed'
    unrealized_pnl = Column(Float, nullable=True)
    realized_pnl = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=False)
    signal_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, action={self.action}, status={self.status})>"


class Position(Base):
    """
    Active positions table.
    
    Tracks currently open positions for real-time monitoring.
    """
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, unique=True, index=True)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    trailing_stop = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=False)
    unrealized_pnl_percent = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=False)
    trade_id = Column(Integer, nullable=True)  # Link to trades table
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Position(symbol={self.symbol}, quantity={self.quantity}, pnl={self.unrealized_pnl})>"


class Prediction(Base):
    """
    ML model predictions table.
    
    Stores all predictions made by the ML model for analysis and backtesting.
    """
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    predicted_price = Column(Float, nullable=False)
    actual_price = Column(Float, nullable=True)  # Filled in next day
    direction = Column(String(10), nullable=False)  # 'up' or 'down'
    confidence = Column(Float, nullable=False)
    model_name = Column(String(50), nullable=False)
    features_used = Column(Text, nullable=False)  # JSON string of features
    prediction_time = Column(DateTime, nullable=False, index=True)
    target_date = Column(DateTime, nullable=False)  # Date being predicted
    accuracy = Column(Boolean, nullable=True)  # True if prediction was correct
    error = Column(Float, nullable=True)  # Prediction error
    metadata = Column(Text, nullable=True)  # JSON string of additional data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Prediction(symbol={self.symbol}, direction={self.direction}, confidence={self.confidence})>"


class Signal(Base):
    """
    Trading signals table.
    
    Stores all trading signals generated, both executed and rejected.
    """
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    signal_type = Column(String(10), nullable=False)  # 'buy', 'sell', 'hold'
    confidence = Column(Float, nullable=False)
    predicted_direction = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False, index=True)  # 'pending', 'approved', 'rejected', 'executed'
    quantity = Column(Integer, nullable=True)
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    features = Column(Text, nullable=False)  # JSON string of technical indicators
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    rejected_reason = Column(Text, nullable=True)
    trade_id = Column(Integer, nullable=True)  # Link to trades table if executed
    
    def __repr__(self):
        return f"<Signal(symbol={self.symbol}, type={self.signal_type}, confidence={self.confidence}, status={self.status})>"


class PerformanceMetric(Base):
    """
    Performance metrics table.
    
    Stores daily/weekly/monthly performance statistics.
    """
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    portfolio_value = Column(Float, nullable=False)
    cash_available = Column(Float, nullable=False)
    total_exposure = Column(Float, nullable=False)
    daily_pnl = Column(Float, nullable=False)
    daily_pnl_percent = Column(Float, nullable=False)
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    win_rate = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    max_drawdown_percent = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PerformanceMetric(date={self.date}, pnl={self.daily_pnl}, win_rate={self.win_rate})>"


class BotState(Base):
    """
    Bot state table.
    
    Stores current bot operational state (singleton table with one row).
    """
    __tablename__ = 'bot_state'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    is_running = Column(Boolean, nullable=False, default=False)
    trading_mode = Column(String(20), nullable=False, default='hybrid')
    last_trading_cycle = Column(DateTime, nullable=True)
    last_position_update = Column(DateTime, nullable=True)
    daily_loss_limit_reached = Column(Boolean, nullable=False, default=False)
    circuit_breaker_triggered = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<BotState(running={self.is_running}, mode={self.trading_mode})>"


def create_database(database_url: str = None) -> tuple:
    """
    Create database and all tables.
    
    Args:
        database_url: Database connection string. If None, uses DATABASE_URL from .env
        
    Returns:
        tuple: (engine, Session) - SQLAlchemy engine and session maker
    """
    if database_url is None:
        database_url = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
    
    # Create engine
    engine = create_engine(database_url, echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session maker
    Session = sessionmaker(bind=engine)
    
    print(f"✅ Database created successfully at {database_url}")
    print(f"✅ Created tables: {', '.join(Base.metadata.tables.keys())}")
    
    return engine, Session


def init_bot_state(session) -> None:
    """
    Initialize bot state if not exists.
    
    Args:
        session: SQLAlchemy session
    """
    state = session.query(BotState).first()
    if not state:
        state = BotState(
            is_running=False,
            trading_mode='hybrid',
            daily_loss_limit_reached=False,
            circuit_breaker_triggered=False
        )
        session.add(state)
        session.commit()
        print("✅ Bot state initialized")


if __name__ == "__main__":
    """
    Run this script directly to create the database and tables.
    
    Usage:
        python src/database/schema.py
    """
    print("🚀 Initializing database...")
    
    # Create database
    engine, Session = create_database()
    
    # Initialize bot state
    session = Session()
    try:
        init_bot_state(session)
        print("✅ Database initialization complete!")
        print("\nYou can now run the trading bot with: python src/main.py")
    except Exception as e:
        print(f"❌ Error initializing bot state: {e}")
        session.rollback()
    finally:
        session.close()
