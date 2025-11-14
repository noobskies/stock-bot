"""
Bot Coordinator

Central coordinator that wires all bot components together.
Provides unified interface for bot operations while delegating to specialized orchestrators.
"""

from typing import Dict, Any, Optional
from datetime import datetime, time as dtime
from loguru import logger

from src.bot.lifecycle import BotLifecycle
from src.bot.scheduler import TaskScheduler
from src.orchestrators.trading_cycle import TradingCycleOrchestrator
from src.orchestrators.position_monitor import PositionMonitorOrchestrator
from src.orchestrators.risk_monitor import RiskMonitorOrchestrator
from src.orchestrators.market_close import MarketCloseHandler


class BotCoordinator:
    """
    Central coordinator for all bot operations.
    
    Wires together lifecycle management, scheduling, and orchestrators.
    Provides clean public API while delegating to specialized components.
    
    Single Responsibility: Coordinate components and provide unified interface.
    Does NOT implement business logic - delegates to orchestrators.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - only one bot coordinator allowed."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize bot coordinator (only once due to singleton)."""
        if self._initialized:
            return
        
        # Core components
        self.lifecycle: Optional[BotLifecycle] = None
        self.scheduler: Optional[TaskScheduler] = None
        
        # Orchestrators
        self.trading_cycle: Optional[TradingCycleOrchestrator] = None
        self.position_monitor: Optional[PositionMonitorOrchestrator] = None
        self.risk_monitor: Optional[RiskMonitorOrchestrator] = None
        self.market_close: Optional[MarketCloseHandler] = None
        
        self._initialized = True
    
    def initialize(self) -> bool:
        """
        Initialize all bot components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing bot coordinator...")
            
            # Step 1: Create and initialize lifecycle manager
            self.lifecycle = BotLifecycle()
            if not self.lifecycle.initialize():
                logger.error("Failed to initialize bot lifecycle")
                return False
            
            # Step 2: Get module instances from lifecycle
            modules = self.lifecycle.get_modules()
            config = self.lifecycle.config
            db = self.lifecycle.db_manager
            
            # Step 3: Create orchestrators with dependency injection
            logger.info("Creating orchestrators...")
            self.trading_cycle = TradingCycleOrchestrator(modules, config, db)
            self.position_monitor = PositionMonitorOrchestrator(modules, config, db)
            self.risk_monitor = RiskMonitorOrchestrator(
                modules['portfolio_monitor'], 
                config, 
                db,
                position_manager=modules['position_manager'],
                executor=modules['executor']
            )
            self.market_close = MarketCloseHandler(modules, config, db)
            logger.debug("Orchestrators created successfully")
            
            # Step 4: Create and configure task scheduler
            logger.info("Setting up task scheduler...")
            self.scheduler = TaskScheduler(timezone_str='America/New_York')
            self.scheduler.configure_jobs(
                trading_cycle_func=self._run_trading_cycle_with_checks,
                position_monitor_func=self._run_position_monitor_with_checks,
                market_close_func=self.market_close.handle_market_close
            )
            
            logger.success("Bot coordinator initialized successfully!")
            return True
            
        except Exception as e:
            logger.exception(f"Error initializing bot coordinator: {e}")
            return False
    
    def start(self) -> bool:
        """
        Start the bot.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Bot is already running")
            return True
        
        if not self.lifecycle or not self.lifecycle.config:
            logger.error("Bot not initialized. Call initialize() first.")
            return False
        
        try:
            logger.info("Starting bot...")
            
            # Update lifecycle state
            self.lifecycle.is_running = True
            
            # Update bot state in database
            self.lifecycle.db_manager.update_bot_state({
                'trading_mode': self.lifecycle.config.trading_mode.value,
                'is_running': True
            })
            
            # Start scheduler
            if not self.scheduler.start():
                logger.error("Failed to start scheduler")
                self.lifecycle.is_running = False
                return False
            
            logger.success("Bot started successfully!")
            logger.info(f"Mode: {self.lifecycle.config.trading_mode.value}")
            logger.info(f"Symbols: {', '.join(self.lifecycle.config.symbols)}")
            logger.info(f"Max positions: {self.lifecycle.config.max_positions}")
            logger.info(f"Risk per trade: {self.lifecycle.config.risk_per_trade*100}%")
            
            # Initial position sync
            self._run_position_monitor_with_checks()
            
            return True
            
        except Exception as e:
            logger.exception(f"Error starting bot: {e}")
            self.lifecycle.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the bot gracefully.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("Bot is not running")
            return True
        
        try:
            logger.info("Stopping bot...")
            
            # Stop scheduler
            if self.scheduler:
                self.scheduler.stop()
            
            # Update lifecycle state
            self.lifecycle.is_running = False
            
            # Update bot state in database
            self.lifecycle.db_manager.update_bot_state({
                'trading_mode': self.lifecycle.config.trading_mode.value,
                'is_running': False
            })
            
            logger.success("Bot stopped successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Error stopping bot: {e}")
            return False
    
    def _run_trading_cycle_with_checks(self):
        """Run trading cycle with market hours check."""
        if not self.is_running:
            logger.debug("Skipping trading cycle - bot not running")
            return
        
        if not self.is_market_hours():
            logger.debug("Skipping trading cycle - outside market hours")
            return
        
        # Run trading cycle
        self.trading_cycle.run()
        
        # Check risk limits after trading cycle
        risk_ok = self.risk_monitor.check_risk_limits()
        if not risk_ok:
            logger.critical("Circuit breaker triggered - stopping bot")
            self.stop()
    
    def _run_position_monitor_with_checks(self):
        """Run position monitor with market hours check."""
        if not self.is_running:
            return
        
        if not self.is_market_hours():
            return
        
        # Update positions
        self.position_monitor.update_positions()
    
    def is_market_hours(self) -> bool:
        """
        Check if current time is during market hours (9:30 AM - 4:00 PM ET).
        
        Returns:
            bool: True if market is open, False otherwise
        """
        try:
            return self.lifecycle.data_fetcher.is_market_open()
        except Exception as e:
            logger.warning(f"Error checking market hours: {e}")
            # Fallback to manual check
            now = datetime.now(self.lifecycle.eastern_tz)
            market_open = dtime(9, 30)
            market_close = dtime(16, 0)
            return market_open <= now.time() <= market_close and now.weekday() < 5
    
    def sync_with_alpaca(self) -> Dict[str, Any]:
        """
        Manually trigger database-Alpaca synchronization.
        
        Returns:
            Dict with sync results
        """
        if not self.lifecycle:
            return {'error': 'Bot not initialized'}
        
        return self.lifecycle.sync_with_alpaca()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current bot status.
        
        Returns:
            Dict containing bot state and metrics
        """
        try:
            if not self.lifecycle:
                return {
                    'is_running': False,
                    'error': 'Bot not initialized'
                }
            
            pending_signal_count = 0
            if self.lifecycle.signal_queue:
                pending_signal_count = self.lifecycle.signal_queue.get_signal_count()
            
            open_positions = []
            if self.lifecycle.position_manager:
                open_positions = self.lifecycle.position_manager.get_all_positions()
            
            return {
                'is_running': self.is_running,
                'trading_mode': self.lifecycle.config.trading_mode.value if self.lifecycle.config else None,
                'symbols': self.lifecycle.config.symbols if self.lifecycle.config else [],
                'open_positions': len(open_positions),
                'pending_signals': pending_signal_count,
                'market_open': self.is_market_hours()
            }
            
        except Exception as e:
            logger.exception(f"Error getting status: {e}")
            return {
                'is_running': self.is_running,
                'error': str(e)
            }
    
    # Property accessors for dashboard compatibility
    
    @property
    def is_running(self) -> bool:
        """Check if bot is running."""
        return self.lifecycle.is_running if self.lifecycle else False
    
    @property
    def config(self):
        """Get bot configuration."""
        return self.lifecycle.config if self.lifecycle else None
    
    @property
    def executor(self):
        """Get Alpaca executor."""
        return self.lifecycle.executor if self.lifecycle else None
    
    @property
    def position_manager(self):
        """Get position manager."""
        return self.lifecycle.position_manager if self.lifecycle else None
    
    @property
    def stop_loss_manager(self):
        """Get stop loss manager."""
        return self.lifecycle.stop_loss_manager if self.lifecycle else None
    
    @property
    def risk_calculator(self):
        """Get risk calculator."""
        return self.lifecycle.risk_calculator if self.lifecycle else None
    
    @property
    def portfolio_monitor(self):
        """Get portfolio monitor."""
        return self.lifecycle.portfolio_monitor if self.lifecycle else None
    
    @property
    def signal_queue(self):
        """Get signal queue."""
        return self.lifecycle.signal_queue if self.lifecycle else None
    
    @property
    def db_manager(self):
        """Get database manager."""
        return self.lifecycle.db_manager if self.lifecycle else None
    
    def process_signal(self, signal_id: str) -> bool:
        """
        Process a signal approval (for manual/hybrid mode).
        
        Args:
            signal_id: Signal ID to process
            
        Returns:
            bool: True if processed successfully
        """
        if not self.trading_cycle:
            logger.error("Trading cycle orchestrator not initialized")
            return False
        
        return self.trading_cycle.process_signal_approval(signal_id)
