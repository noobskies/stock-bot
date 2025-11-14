"""
Bot Lifecycle Management

Handles bot initialization, configuration loading, and module creation.
Separates lifecycle concerns from orchestration logic.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import yaml
from dotenv import load_dotenv
from loguru import logger
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
from src.bot_types.trading_types import TradingMode, BotConfig


class BotLifecycle:
    """
    Manages bot lifecycle: configuration, initialization, module creation.
    
    Single Responsibility: Initialize and wire up all bot components.
    Does NOT handle orchestration or trading logic.
    """
    
    def __init__(self):
        """Initialize lifecycle manager."""
        # State flags
        self.is_initializing = False
        self.is_running = False
        
        # Configuration
        self.config: Optional[BotConfig] = None
        self.eastern_tz = pytz.timezone('America/New_York')
        
        # Module instances (created in create_modules())
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
    
    def initialize(self) -> bool:
        """
        Initialize all bot components.
        
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
            if not self.load_configuration():
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
            if not self.create_modules():
                logger.error("Failed to create modules")
                return False
            
            # Step 5: Verify Alpaca API connection
            logger.info("Verifying Alpaca API connection...")
            if not self.verify_api_connection():
                logger.error("Failed to connect to Alpaca API")
                return False
            
            # Step 6: Load or create bot state
            logger.info("Loading bot state from database...")
            self._load_bot_state()
            
            # Step 7: Sync database with Alpaca reality
            logger.info("Synchronizing database with Alpaca...")
            sync_results = self.sync_with_alpaca()
            if 'error' not in sync_results:
                logger.info(
                    f"Sync: {sync_results['positions_synced']} updated, "
                    f"{sync_results['new_positions_imported']} imported, "
                    f"{sync_results['trades_archived']} archived"
                )
            
            logger.success("Bot initialization complete!")
            return True
            
        except Exception as e:
            logger.exception(f"Fatal error during initialization: {e}")
            return False
            
        finally:
            self.is_initializing = False
    
    def load_configuration(self) -> bool:
        """
        Load configuration from config.yaml and .env files.
        
        Returns:
            bool: True if successful, False otherwise
        """
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
    
    def create_modules(self) -> bool:
        """
        Create instances of all bot modules with proper dependency injection.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Data pipeline
            self.data_fetcher = DataFetcher()
            self.feature_engineer = FeatureEngineer()
            self.data_validator = DataValidator()
            logger.debug("Data pipeline modules created")
            
            # ML modules
            if Path(self.config.model_path).exists():
                self.predictor = LSTMPredictor(model_path=self.config.model_path)
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
    
    def verify_api_connection(self) -> bool:
        """
        Verify Alpaca API connection and account access.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            account = self.executor.get_account()
            if account:
                # Handle dict or object response
                if isinstance(account, dict):
                    equity = float(account.get('equity', 0))
                    buying_power = float(account.get('buying_power', 0))
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
                self.db_manager.update_bot_state({
                    'trading_mode': self.config.trading_mode.value,
                    'is_running': False,
                    'daily_pnl': 0.0,
                    'total_trades_today': 0
                })
                logger.info("Created initial bot state")
                
        except Exception as e:
            logger.warning(f"Could not load bot state (non-critical): {e}")
    
    def sync_with_alpaca(self) -> Dict[str, Any]:
        """
        Synchronize database with Alpaca reality (ensures 1:1 data consistency).
        
        Returns:
            Dict with sync results
        """
        try:
            logger.info("Starting database-Alpaca synchronization...")
            
            # Get current reality from Alpaca
            alpaca_positions = self.executor.get_open_positions()
            alpaca_orders = self.executor.get_open_orders()
            
            alpaca_symbols = {pos.symbol for pos in alpaca_positions}
            logger.info(f"Alpaca reality: {len(alpaca_positions)} positions, {len(alpaca_orders)} pending orders")
            
            # Get database state
            db_positions = self.db_manager.get_active_positions()
            db_symbols = {pos['symbol'] for pos in db_positions}
            logger.info(f"Database state: {len(db_positions)} active positions")
            
            # Track sync results
            positions_synced = 0
            positions_imported = 0
            trades_archived = 0
            
            # Step 1: Sync Alpaca positions → Database
            for alpaca_pos in alpaca_positions:
                db_pos = self.db_manager.get_position_by_symbol(alpaca_pos.symbol)
                
                if db_pos:
                    # Update existing position
                    self.db_manager.update_position(alpaca_pos.symbol, {
                        'current_price': alpaca_pos.current_price,
                        'market_value': alpaca_pos.market_value,
                        'unrealized_pnl': alpaca_pos.unrealized_pnl,
                        'unrealized_pnl_percent': alpaca_pos.unrealized_pnl_percent
                    })
                    positions_synced += 1
                else:
                    # Import new position
                    logger.info(f"Importing new position from Alpaca: {alpaca_pos.symbol}")
                    
                    self.db_manager.save_position(
                        symbol=alpaca_pos.symbol,
                        quantity=alpaca_pos.quantity,
                        entry_price=alpaca_pos.entry_price,
                        current_price=alpaca_pos.current_price,
                        side='buy',
                        status='open'
                    )
                    
                    self.db_manager.save_trade(
                        symbol=alpaca_pos.symbol,
                        action='buy',
                        quantity=alpaca_pos.quantity,
                        entry_price=alpaca_pos.entry_price,
                        stop_loss=alpaca_pos.entry_price * (1 - self.config.stop_loss_percent),
                        status='open',
                        confidence=0.0,
                        reasoning="Imported from Alpaca (manual trade or external system)"
                    )
                    
                    positions_imported += 1
            
            # Step 2: Archive database positions that don't exist in Alpaca
            for db_pos in db_positions:
                if db_pos['symbol'] not in alpaca_symbols:
                    logger.info(f"Archiving orphaned position: {db_pos['symbol']}")
                    
                    trades = self.db_manager.get_trade_history(
                        symbol=db_pos['symbol'],
                        status='open'
                    )
                    
                    for trade in trades:
                        self.db_manager.update_trade_status(
                            trade_id=trade['id'],
                            status='archived',
                            exit_price=db_pos.get('current_price', trade['entry_price']),
                            pnl=0.0,
                            pnl_percent=0.0
                        )
                        trades_archived += 1
                    
                    self.db_manager.delete_position(db_pos['symbol'])
            
            sync_results = {
                'positions_synced': positions_synced,
                'new_positions_imported': positions_imported,
                'trades_archived': trades_archived,
                'pending_orders': len(alpaca_orders),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.success(
                f"Sync complete: {positions_synced} updated, "
                f"{positions_imported} imported, {trades_archived} archived"
            )
            
            return sync_results
            
        except Exception as e:
            logger.exception(f"Error during Alpaca sync: {e}")
            return {
                'error': str(e),
                'positions_synced': 0,
                'new_positions_imported': 0,
                'trades_archived': 0
            }
    
    def get_modules(self) -> Dict[str, Any]:
        """
        Get all module instances for orchestrators.
        
        Returns:
            Dict of module instances
        """
        return {
            'data_fetcher': self.data_fetcher,
            'feature_engineer': self.feature_engineer,
            'data_validator': self.data_validator,
            'predictor': self.predictor,
            'ensemble': self.ensemble,
            'signal_generator': self.signal_generator,
            'signal_queue': self.signal_queue,
            'executor': self.executor,
            'order_manager': self.order_manager,
            'position_manager': self.position_manager,
            'risk_calculator': self.risk_calculator,
            'portfolio_monitor': self.portfolio_monitor,
            'stop_loss_manager': self.stop_loss_manager,
            'db_manager': self.db_manager
        }
