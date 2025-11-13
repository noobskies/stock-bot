"""
Trading Bot Main Application

This module contains the TradingBot orchestrator class that coordinates all
components of the AI stock trading system. It manages the complete trading
workflow from data collection through ML prediction to order execution and
position monitoring.

The bot operates during market hours with the following main tasks:
- Trading cycle: Every 5 minutes - Generate predictions and signals
- Position monitoring: Every 30 seconds - Update prices and check stops
- Market close: 4:00 PM ET - Close positions and calculate daily performance
"""

import os
import sys
import time
import yaml
import signal
from datetime import datetime, time as dtime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# Data pipeline modules
from src.data.data_fetcher import DataFetcher
from src.data.feature_engineer import FeatureEngineer
from src.data.data_validator import DataValidator

# ML modules
from src.ml.predictor import LSTMPredictor
from src.ml.ensemble import EnsemblePredictor

# Trading modules
from src.trading.signal_generator import SignalGenerator, SignalQueue
from src.trading.executor import AlpacaExecutor
from src.trading.order_manager import OrderManager
from src.trading.position_manager import PositionManager

# Risk modules
from src.risk.risk_calculator import RiskCalculator
from src.risk.portfolio_monitor import PortfolioMonitor
from src.risk.stop_loss_manager import StopLossManager

# Database module
from src.database.db_manager import DatabaseManager

# Type definitions
from src.types.trading_types import (
    TradingMode,
    TradingSignal,
    SignalType,
    Position,
    BotConfig
)


class TradingBot:
    """
    Main trading bot orchestrator (Singleton).
    
    Coordinates all modules to execute automated trading strategy:
    1. Data collection and feature engineering
    2. ML predictions (LSTM + ensemble)
    3. Signal generation and risk validation
    4. Order execution and position management
    5. Stop loss monitoring and execution
    6. Performance tracking and reporting
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - only one bot instance allowed."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize bot state (only once due to singleton)."""
        if self._initialized:
            return
            
        # Bot state
        self.is_running = False
        self.is_initializing = False
        self.config: Optional[BotConfig] = None
        self.scheduler: Optional[BackgroundScheduler] = None
        
        # Module instances (created in initialize())
        self.data_fetcher: Optional[DataFetcher] = None
        self.feature_engineer: Optional[FeatureEngineer] = None
        self.data_validator: Optional[DataValidator] = None
        self.predictor: Optional[LSTMPredictor] = None
        self.ensemble: Optional[EnsemblePredictor] = None
        self.signal_generator: Optional[SignalGenerator] = None
        self.signal_queue: Optional[SignalQueue] = None
        self.executor: Optional[AlpacaExecutor] = None
        self.order_manager: Optional[OrderManager] = None
        self.position_manager: Optional[PositionManager] = None
        self.risk_calculator: Optional[RiskCalculator] = None
        self.portfolio_monitor: Optional[PortfolioMonitor] = None
        self.stop_loss_manager: Optional[StopLossManager] = None
        self.db_manager: Optional[DatabaseManager] = None
        
        # Timezone for market hours
        self.eastern_tz = pytz.timezone('America/New_York')
        
        self._initialized = True
    
    def initialize(self) -> bool:
        """
        Initialize all bot modules and verify connections.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self.is_initializing:
            logger.warning("Initialization already in progress")
            return False
            
        if self.is_running:
            logger.warning("Cannot initialize while bot is running")
            return False
        
        self.is_initializing = True
        logger.info("Starting bot initialization...")
        
        try:
            # Step 1: Load configuration
            logger.info("Loading configuration...")
            if not self._load_configuration():
                logger.error("Failed to load configuration")
                return False
            
            # Step 2: Setup logging
            logger.info("Configuring logging...")
            self._setup_logging()
            
            # Step 3: Initialize database
            logger.info("Initializing database connection...")
            self.db_manager = DatabaseManager()
            
            # Step 4: Create module instances
            logger.info("Creating module instances...")
            if not self._create_modules():
                logger.error("Failed to create modules")
                return False
            
            # Step 5: Verify Alpaca API connection
            logger.info("Verifying Alpaca API connection...")
            if not self._verify_api_connection():
                logger.error("Failed to connect to Alpaca API")
                return False
            
            # Step 6: Load or create bot state
            logger.info("Loading bot state from database...")
            self._load_bot_state()
            
            # Step 7: Setup scheduler
            logger.info("Setting up task scheduler...")
            self._setup_scheduler()
            
            logger.success("Bot initialization complete!")
            return True
            
        except Exception as e:
            logger.exception(f"Fatal error during initialization: {e}")
            return False
            
        finally:
            self.is_initializing = False
    
    def _load_configuration(self) -> bool:
        """Load configuration from config.yaml and .env files."""
        try:
            # Load environment variables
            load_dotenv()
            
            # Load config.yaml
            config_path = Path("config/config.yaml")
            if not config_path.exists():
                logger.error(f"Configuration file not found: {config_path}")
                return False
            
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            
            # Get environment variables
            alpaca_api_key = os.getenv('ALPACA_API_KEY')
            alpaca_secret_key = os.getenv('ALPACA_SECRET_KEY')
            alpaca_base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
            
            if not alpaca_api_key or not alpaca_secret_key:
                logger.error("Alpaca API credentials not found in .env file")
                return False
            
            # Parse trading mode
            trading_mode_str = config_dict.get('trading', {}).get('mode', 'hybrid')
            try:
                trading_mode = TradingMode[trading_mode_str.upper()]
            except KeyError:
                logger.error(f"Invalid trading mode: {trading_mode_str}")
                return False
            
            # Create BotConfig
            self.config = BotConfig(
                # Trading configuration
                trading_mode=trading_mode,
                symbols=config_dict.get('trading', {}).get('symbols', ['PLTR']),
                initial_capital=config_dict.get('trading', {}).get('initial_capital', 10000),
                max_positions=config_dict.get('trading', {}).get('max_positions', 5),
                close_positions_eod=config_dict.get('trading', {}).get('close_positions_eod', True),
                # Risk management
                risk_per_trade=config_dict.get('risk', {}).get('risk_per_trade', 0.02),
                max_position_size=config_dict.get('risk', {}).get('max_position_size', 0.20),
                max_portfolio_exposure=config_dict.get('risk', {}).get('max_portfolio_exposure', 0.20),
                daily_loss_limit=config_dict.get('risk', {}).get('daily_loss_limit', 0.05),
                stop_loss_percent=config_dict.get('risk', {}).get('stop_loss_percent', 0.03),
                trailing_stop_percent=config_dict.get('risk', {}).get('trailing_stop_percent', 0.02),
                trailing_stop_activation=config_dict.get('risk', {}).get('trailing_stop_activation', 0.05),
                # ML configuration
                model_path=config_dict.get('ml', {}).get('model_path', 'models/lstm_model.h5'),
                sequence_length=config_dict.get('ml', {}).get('sequence_length', 60),
                prediction_confidence_threshold=config_dict.get('ml', {}).get('prediction_confidence_threshold', 0.70),
                auto_execute_threshold=config_dict.get('ml', {}).get('auto_execute_threshold', 0.80),
                # Database
                database_url=os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db'),
                # Logging
                log_level=config_dict.get('logging', {}).get('level', 'INFO'),
                log_dir=config_dict.get('logging', {}).get('log_dir', 'logs/')
            )
            
            logger.info(f"Configuration loaded: mode={trading_mode_str}, symbols={self.config.symbols}")
            return True
            
        except Exception as e:
            logger.exception(f"Error loading configuration: {e}")
            return False
    
    def _setup_logging(self):
        """Configure loguru logging with rotation and multiple outputs."""
        # Remove default handler
        logger.remove()
        
        # Console output (colorized, INFO level)
        logger.add(
            sys.stdout,
            colorize=True,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level="INFO"
        )
        
        # Main log file (all INFO+ messages, daily rotation)
        logger.add(
            "logs/trading_bot_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
        )
        
        # Error log (ERROR+ only)
        logger.add(
            "logs/errors.log",
            level="ERROR",
            rotation="10 MB",
            retention="30 days",
            backtrace=True,
            diagnose=True,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}"
        )
        
        logger.info("Logging configured successfully")
    
    def _create_modules(self) -> bool:
        """Create instances of all bot modules."""
        try:
            # Data pipeline
            self.data_fetcher = DataFetcher()
            self.feature_engineer = FeatureEngineer()
            self.data_validator = DataValidator()
            logger.debug("Data pipeline modules created")
            
            # ML modules
            if Path(self.config.model_path).exists():
                self.predictor = LSTMPredictor()
                self.predictor.load_model(self.config.model_path)
                logger.info(f"Loaded LSTM model from {self.config.model_path}")
            else:
                logger.warning(f"Model file not found: {self.config.model_path}")
                logger.warning("Bot will run without ML predictions - manual mode only")
                self.predictor = None
            
            self.ensemble = EnsemblePredictor(
                lstm_model_path=self.config.model_path,
                lstm_weight=0.5,
                rf_weight=0.3,
                momentum_weight=0.2,
                sequence_length=self.config.sequence_length,
                confidence_threshold=self.config.prediction_confidence_threshold
            )
            logger.debug("ML modules created")
            
            # Risk modules (create before trading modules as they depend on risk_calculator)
            self.risk_calculator = RiskCalculator(config=self.config)
            self.portfolio_monitor = PortfolioMonitor(
                config=self.config,
                initial_capital=self.config.initial_capital
            )
            self.stop_loss_manager = StopLossManager(config=self.config)
            logger.debug("Risk modules created")
            
            # Trading modules
            self.signal_generator = SignalGenerator(
                confidence_threshold=self.config.prediction_confidence_threshold,
                auto_threshold=self.config.auto_execute_threshold,
                trading_mode=self.config.trading_mode
            )
            self.signal_queue = SignalQueue()
            self.executor = AlpacaExecutor()
            self.position_manager = PositionManager(self.executor)
            self.order_manager = OrderManager(
                executor=self.executor,
                position_manager=self.position_manager,
                risk_calculator=self.risk_calculator
            )
            logger.debug("Trading modules created")
            
            return True
            
        except Exception as e:
            logger.exception(f"Error creating modules: {e}")
            return False
    
    def _verify_api_connection(self) -> bool:
        """Verify Alpaca API connection and account access."""
        try:
            account = self.executor.get_account()
            if account:
                # Handle dict or object response
                if isinstance(account, dict):
                    equity = float(account.get('equity', 0))
                    buying_power = float(account.get('buying_power', 0))
                    # Paper accounts don't have account_number in dict
                    is_paper = os.getenv('ALPACA_IS_PAPER', 'true').lower() == 'true'
                else:
                    equity = float(account.equity)
                    buying_power = float(account.buying_power)
                    is_paper = account.account_number.startswith('P')
                
                logger.info(f"Connected to Alpaca: Account value=${equity:,.2f}")
                logger.info(f"Buying power: ${buying_power:,.2f}")
                logger.info(f"Paper trading: {is_paper}")
                return True
            else:
                logger.error("Failed to get account information")
                return False
                
        except Exception as e:
            logger.exception(f"Error verifying API connection: {e}")
            return False
    
    def _load_bot_state(self):
        """Load or create bot state in database."""
        try:
            state = self.db_manager.get_bot_state()
            if state:
                logger.info(f"Loaded bot state: mode={state.get('trading_mode', 'unknown')}")
            else:
                # Create initial state
                self.db_manager.update_bot_state(
                    trading_mode=self.config.trading_mode.value,
                    is_active=False,
                    daily_pnl=0.0,
                    total_trades_today=0
                )
                logger.info("Created initial bot state")
                
        except Exception as e:
            logger.warning(f"Could not load bot state (non-critical): {e}")
    
    def _setup_scheduler(self):
        """Setup APScheduler for automated tasks."""
        self.scheduler = BackgroundScheduler(timezone=self.eastern_tz)
        
        # Trading cycle every 5 minutes during market hours (9:30 AM - 4:00 PM ET)
        self.scheduler.add_job(
            func=self.run_trading_cycle,
            trigger='cron',
            day_of_week='mon-fri',
            hour='9-15',
            minute='*/5',
            id='trading_cycle',
            name='Trading Cycle'
        )
        
        # Also run at 9:30, 9:35, etc. (top of hour during market start)
        self.scheduler.add_job(
            func=self.run_trading_cycle,
            trigger='cron',
            day_of_week='mon-fri',
            hour=9,
            minute='30,35,40,45,50,55',
            id='trading_cycle_open',
            name='Trading Cycle (Market Open)'
        )
        
        # Position monitoring every 30 seconds (we'll check market hours in the function)
        self.scheduler.add_job(
            func=self.update_positions,
            trigger='interval',
            seconds=30,
            id='position_monitor',
            name='Position Monitor'
        )
        
        # Market close handler at 4:00 PM ET
        self.scheduler.add_job(
            func=self.handle_market_close,
            trigger='cron',
            day_of_week='mon-fri',
            hour=16,
            minute=0,
            id='market_close',
            name='Market Close Handler'
        )
        
        logger.info("Task scheduler configured")
    
    def start(self) -> bool:
        """
        Start the trading bot.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Bot is already running")
            return False
        
        if not self.config:
            logger.error("Bot not initialized. Call initialize() first.")
            return False
        
        try:
            logger.info("Starting trading bot...")
            
            # Update bot state in database
            self.db_manager.update_bot_state(
                trading_mode=self.config.trading_mode.value,
                is_active=True
            )
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.success("Trading bot started successfully!")
            logger.info(f"Mode: {self.config.trading_mode.value}")
            logger.info(f"Symbols: {', '.join(self.config.symbols)}")
            logger.info(f"Max positions: {self.config.max_positions}")
            logger.info(f"Risk per trade: {self.config.risk_per_trade*100}%")
            
            # Initial position sync
            self.update_positions()
            
            return True
            
        except Exception as e:
            logger.exception(f"Error starting bot: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the trading bot gracefully.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("Bot is not running")
            return False
        
        try:
            logger.info("Stopping trading bot...")
            
            # Stop scheduler
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=True)
            
            # Update bot state
            self.db_manager.update_bot_state(
                trading_mode=self.config.trading_mode.value,
                is_active=False
            )
            
            self.is_running = False
            logger.success("Trading bot stopped successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Error stopping bot: {e}")
            return False
    
    def is_market_hours(self) -> bool:
        """
        Check if current time is during market hours (9:30 AM - 4:00 PM ET).
        
        Returns:
            bool: True if market is open, False otherwise
        """
        try:
            return self.data_fetcher.is_market_open()
        except Exception as e:
            logger.warning(f"Error checking market hours: {e}")
            # Fallback to manual check
            now = datetime.now(self.eastern_tz)
            market_open = dtime(9, 30)
            market_close = dtime(16, 0)
            return market_open <= now.time() <= market_close and now.weekday() < 5
    
    def run_trading_cycle(self):
        """
        Execute one complete trading cycle.
        
        Workflow:
        1. Fetch latest market data
        2. Calculate technical indicators
        3. Generate ML predictions (ensemble)
        4. Create trading signals
        5. Validate against risk rules
        6. Execute or queue signal based on mode
        7. Persist to database
        """
        if not self.is_running:
            logger.debug("Skipping trading cycle - bot not running")
            return
        
        if not self.is_market_hours():
            logger.debug("Skipping trading cycle - outside market hours")
            return
        
        try:
            logger.info("=" * 80)
            logger.info("Starting trading cycle...")
            
            # Process each configured symbol
            for symbol in self.config.symbols:
                self._process_symbol(symbol)
            
            logger.info("Trading cycle complete")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.exception(f"Error in trading cycle: {e}")
    
    def _process_symbol(self, symbol: str):
        """Process trading logic for a single symbol."""
        try:
            logger.info(f"Processing {symbol}...")
            
            # Step 1: Fetch market data
            logger.debug(f"Fetching market data for {symbol}...")
            historical_data = self.data_fetcher.fetch_historical_data(
                symbol=symbol,
                days=90  # 90 days for technical indicators
            )
            
            if historical_data is None or historical_data.empty:
                logger.warning(f"No historical data available for {symbol}")
                return
            
            # Step 2: Validate data quality
            logger.debug("Validating data quality...")
            is_valid, issues = self.data_validator.validate_price_data(historical_data)
            if not is_valid:
                logger.warning(f"Data quality issues: {', '.join(issues)}")
                historical_data = self.data_validator.validate_and_clean(historical_data)
            
            # Step 3: Calculate technical indicators
            logger.debug("Calculating technical indicators...")
            data_with_indicators = self.feature_engineer.calculate_technical_indicators(
                historical_data
            )
            
            # Step 4: Create ML features
            logger.debug("Creating ML features...")
            features = self.feature_engineer.create_ml_features(data_with_indicators)
            
            if features is None or features.empty:
                logger.warning(f"Could not create ML features for {symbol}")
                return
            
            # Step 5: Generate ML prediction
            if self.predictor is None:
                logger.warning("No ML model loaded - skipping prediction")
                return
            
            logger.debug("Generating ML prediction...")
            prediction = self.ensemble.ensemble_predict(
                symbol=symbol,
                data=data_with_indicators,
                lstm_predictor=self.predictor,
                features=features
            )
            
            if prediction is None:
                logger.warning(f"Could not generate prediction for {symbol}")
                return
            
            logger.info(
                f"Prediction: direction={prediction.predicted_direction}, "
                f"confidence={prediction.confidence:.2%}, "
                f"price=${prediction.predicted_price:.2f}"
            )
            
            # Save prediction to database
            self.db_manager.save_prediction(
                symbol=prediction.symbol,
                predicted_direction=prediction.predicted_direction,
                predicted_price=prediction.predicted_price,
                confidence=prediction.confidence,
                model_type="ensemble"
            )
            
            # Step 6: Generate trading signal
            logger.debug("Generating trading signal...")
            current_price = self.data_fetcher.fetch_latest_price(symbol)
            
            # Check if we already have a position
            current_position = self.position_manager.get_position(symbol)
            
            signal = self.signal_generator.generate_signal(
                prediction=prediction,
                current_price=current_price,
                current_position=current_position
            )
            
            if signal is None:
                logger.info(f"No signal generated for {symbol}")
                return
            
            logger.info(
                f"Signal: {signal.signal_type.value} {symbol} @ ${signal.entry_price:.2f}, "
                f"confidence={signal.confidence:.2%}"
            )
            
            # Step 7: Validate against risk rules
            logger.debug("Validating trade against risk rules...")
            portfolio_state = self.portfolio_monitor.get_portfolio_state()
            
            is_valid, reason = self.risk_calculator.validate_trade(
                signal=signal,
                portfolio=portfolio_state
            )
            
            if not is_valid:
                logger.warning(f"Trade rejected: {reason}")
                # Save signal as rejected
                self.db_manager.save_signal(
                    symbol=signal.symbol,
                    signal_type=signal.signal_type.value,
                    confidence=signal.confidence,
                    entry_price=signal.entry_price,
                    quantity=signal.quantity,
                    status="rejected",
                    reasoning=f"Risk validation failed: {reason}"
                )
                return
            
            # Step 8: Determine execution path based on mode
            should_execute = self.signal_generator.should_execute_trade(signal)
            
            if should_execute:
                logger.info(f"Auto-executing signal (confidence {signal.confidence:.2%} > threshold)")
                self._execute_signal(signal)
            else:
                logger.info(f"Adding signal to queue for manual approval")
                self.signal_queue.add_signal(signal)
                # Save signal as pending
                self.db_manager.save_signal(
                    symbol=signal.symbol,
                    signal_type=signal.signal_type.value,
                    confidence=signal.confidence,
                    entry_price=signal.entry_price,
                    quantity=signal.quantity,
                    status="pending",
                    reasoning=signal.reasoning
                )
            
        except Exception as e:
            logger.exception(f"Error processing {symbol}: {e}")
    
    def _execute_signal(self, signal: TradingSignal) -> bool:
        """
        Execute a trading signal.
        
        Args:
            signal: TradingSignal to execute
            
        Returns:
            bool: True if executed successfully, False otherwise
        """
        try:
            logger.info(f"Executing signal: {signal.signal_type.value} {signal.symbol}")
            
            # Calculate position size based on risk
            portfolio_state = self.portfolio_monitor.get_portfolio_state()
            quantity = self.risk_calculator.calculate_position_size(
                signal=signal,
                portfolio=portfolio_state
            )
            
            if quantity <= 0:
                logger.warning("Position size calculated to 0 - cannot execute")
                return False
            
            # Update signal quantity
            signal.quantity = quantity
            
            # Execute order via order manager
            success = self.order_manager.submit_order(
                signal=signal,
                risk_calculator=self.risk_calculator,
                portfolio_monitor=self.portfolio_monitor
            )
            
            if success:
                logger.success(f"Signal executed successfully: {signal.signal_type.value} {quantity} {signal.symbol}")
                
                # Save signal as executed
                self.db_manager.save_signal(
                    symbol=signal.symbol,
                    signal_type=signal.signal_type.value,
                    confidence=signal.confidence,
                    entry_price=signal.entry_price,
                    quantity=quantity,
                    status="executed",
                    reasoning=signal.reasoning
                )
                
                # Update bot state
                state = self.db_manager.get_bot_state()
                if state:
                    self.db_manager.update_bot_state(
                        trading_mode=self.config.trading_mode.value,
                        is_active=True,
                        total_trades_today=state.get('total_trades_today', 0) + 1
                    )
                
                return True
            else:
                logger.error(f"Failed to execute signal: {signal.symbol}")
                return False
                
        except Exception as e:
            logger.exception(f"Error executing signal: {e}")
            return False
    
    def process_signal(self, signal_id: str) -> bool:
        """
        Process a signal from the queue (manual approval).
        
        Args:
            signal_id: Signal ID to process
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        try:
            signal = self.signal_queue.get_signal(signal_id)
            if signal is None:
                logger.warning(f"Signal not found: {signal_id}")
                return False
            
            # Re-validate risk rules (conditions may have changed)
            portfolio_state = self.portfolio_monitor.get_portfolio_state()
            is_valid, reason = self.risk_calculator.validate_trade(
                signal=signal,
                portfolio=portfolio_state
            )
            
            if not is_valid:
                logger.warning(f"Signal no longer valid: {reason}")
                self.signal_queue.remove_signal(signal_id)
                # Update signal status in database
                self.db_manager.update_signal_status(signal_id, "rejected", reason)
                return False
            
            # Execute signal
            success = self._execute_signal(signal)
            
            if success:
                self.signal_queue.remove_signal(signal_id)
                return True
            else:
                return False
                
        except Exception as e:
            logger.exception(f"Error processing signal: {e}")
            return False
    
    def update_positions(self):
        """
        Update all position prices and check stop losses.
        
        Runs every 30 seconds during market hours to:
        - Sync positions with Alpaca
        - Update current prices
        - Check stop losses
        - Update trailing stops
        - Execute stops if triggered
        """
        if not self.is_running:
            return
        
        if not self.is_market_hours():
            return
        
        try:
            # Sync positions with broker
            positions = self.position_manager.sync_positions()
            
            if not positions:
                return
            
            logger.debug(f"Monitoring {len(positions)} positions...")
            
            for position in positions:
                # Get current price
                current_price = self.data_fetcher.fetch_latest_price(position.symbol)
                if current_price is None:
                    logger.warning(f"Could not fetch price for {position.symbol}")
                    continue
                
                # Update position price
                self.position_manager.update_position_price(
                    symbol=position.symbol,
                    current_price=current_price
                )
                
                # Register with stop loss manager if not already registered
                if not self.stop_loss_manager.is_registered(position.symbol):
                    self.stop_loss_manager.register_position(
                        symbol=position.symbol,
                        entry_price=position.entry_price,
                        quantity=position.quantity,
                        side=position.side,
                        stop_loss_percent=self.config.stop_loss_percent
                    )
                
                # Update stop loss manager with current price
                self.stop_loss_manager.update_price(position.symbol, current_price)
                
                # Check if stop loss triggered
                triggered, reason = self.stop_loss_manager.check_stop_triggered(position.symbol)
                
                if triggered:
                    logger.warning(f"Stop loss triggered for {position.symbol}: {reason}")
                    self._execute_stop_loss(position.symbol, reason)
            
            # Update portfolio state
            self.portfolio_monitor.update_state(
                cash=float(self.executor.get_account().cash),
                positions=positions
            )
            
            # Check risk limits
            self.check_risk_limits()
            
        except Exception as e:
            logger.exception(f"Error updating positions: {e}")
    
    def _execute_stop_loss(self, symbol: str, reason: str):
        """Execute a stop loss order."""
        try:
            logger.info(f"Executing stop loss for {symbol}: {reason}")
            
            # Close position
            success = self.position_manager.close_position(symbol)
            
            if success:
                logger.success(f"Stop loss executed successfully for {symbol}")
                
                # Unregister from stop loss manager
                self.stop_loss_manager.unregister_position(symbol)
                
                # Update position in database
                # (position_manager should have already updated the trade record)
                
            else:
                logger.error(f"Failed to execute stop loss for {symbol}")
                
        except Exception as e:
            logger.exception(f"Error executing stop loss: {e}")
    
    def check_risk_limits(self):
        """
        Check portfolio risk limits and activate circuit breaker if needed.
        
        Monitors:
        - Daily P&L (circuit breaker at 5% loss)
        - Position count
        - Portfolio exposure
        """
        try:
            # Get current risk metrics
            risk_metrics = self.portfolio_monitor.get_risk_metrics()
            
            # Check daily loss limit (5%)
            daily_loss_limit = 0.05  # 5%
            if risk_metrics['daily_pnl_percent'] <= -daily_loss_limit:
                logger.critical(
                    f"CIRCUIT BREAKER TRIGGERED: Daily loss limit exceeded "
                    f"({risk_metrics['daily_pnl_percent']:.2%})"
                )
                self._activate_circuit_breaker()
                return
            
            # Log risk metrics periodically
            if risk_metrics['position_count'] > 0:
                logger.info(
                    f"Risk metrics: positions={risk_metrics['position_count']}, "
                    f"exposure={risk_metrics['total_exposure_percent']:.1%}, "
                    f"daily_pnl={risk_metrics['daily_pnl_percent']:.2%}"
                )
                
        except Exception as e:
            logger.exception(f"Error checking risk limits: {e}")
    
    def _activate_circuit_breaker(self):
        """Activate circuit breaker - stop all trading."""
        try:
            logger.critical("Activating circuit breaker - stopping all trading")
            
            # Stop the bot
            self.stop()
            
            # Update bot state
            self.db_manager.update_bot_state(
                trading_mode=self.config.trading_mode.value,
                is_active=False,
                circuit_breaker_active=True
            )
            
            logger.critical("Circuit breaker active - bot stopped")
            
        except Exception as e:
            logger.exception(f"Error activating circuit breaker: {e}")
    
    def handle_market_close(self):
        """
        Handle end-of-day market close.
        
        Tasks:
        - Close all positions (if configured)
        - Calculate daily performance
        - Save performance metrics
        - Reset daily counters
        """
        if not self.is_running:
            return
        
        try:
            logger.info("=" * 80)
            logger.info("Market close - executing end-of-day tasks...")
            
            # Close positions if configured
            if self.config.close_positions_eod:
                logger.info("Closing all positions (EOD setting enabled)...")
                positions = self.position_manager.get_open_positions()
                
                for position in positions:
                    logger.info(f"Closing position: {position.symbol}")
                    success = self.position_manager.close_position(position.symbol)
                    
                    if success:
                        logger.info(f"Position closed: {position.symbol}")
                    else:
                        logger.error(f"Failed to close position: {position.symbol}")
            
            # Calculate daily performance
            logger.info("Calculating daily performance...")
            daily_perf = self.db_manager.calculate_daily_performance()
            
            if daily_perf:
                logger.info(f"Daily performance: P&L=${daily_perf['total_pnl']:.2f}")
                logger.info(f"Trades today: {daily_perf['num_trades']}")
                logger.info(f"Win rate: {daily_perf['win_rate']:.1%}")
                
                # Save performance metrics
                self.db_manager.save_performance_metrics(
                    total_pnl=daily_perf['total_pnl'],
                    num_trades=daily_perf['num_trades'],
                    win_rate=daily_perf['win_rate'],
                    sharpe_ratio=0.0,  # Calculate from historical data
                    max_drawdown=0.0   # Calculate from historical data
                )
            
            # Reset daily counters
            self.db_manager.update_bot_state(
                trading_mode=self.config.trading_mode.value,
                is_active=self.is_running,
                daily_pnl=0.0,
                total_trades_today=0
            )
            
            logger.info("End-of-day tasks complete")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.exception(f"Error handling market close: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current bot status.
        
        Returns:
            Dict containing bot state and metrics
        """
        try:
            portfolio_state = self.portfolio_monitor.get_portfolio_state()
            risk_metrics = self.portfolio_monitor.get_risk_metrics()
            pending_signals = self.signal_queue.get_all_signals()
            
            return {
                'is_running': self.is_running,
                'trading_mode': self.config.trading_mode.value if self.config else None,
                'symbols': self.config.symbols if self.config else [],
                'portfolio': portfolio_state,
                'risk_metrics': risk_metrics,
                'pending_signals': len(pending_signals),
                'market_open': self.is_market_hours()
            }
            
        except Exception as e:
            logger.exception(f"Error getting status: {e}")
            return {
                'is_running': self.is_running,
                'error': str(e)
            }


def main():
    """Main entry point for the trading bot."""
    # Setup signal handlers for graceful shutdown
    bot = TradingBot()
    
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum} - shutting down...")
        bot.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize bot
    logger.info("Initializing trading bot...")
    if not bot.initialize():
        logger.error("Failed to initialize bot - exiting")
        sys.exit(1)
    
    # Start bot
    logger.info("Starting trading bot...")
    if not bot.start():
        logger.error("Failed to start bot - exiting")
        sys.exit(1)
    
    # Keep main thread alive
    logger.info("Bot running - Press Ctrl+C to stop")
    try:
        while bot.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt - stopping bot...")
        bot.stop()
    
    logger.info("Bot shutdown complete")


if __name__ == "__main__":
    main()
