"""
Trading Cycle Orchestrator

Orchestrates the complete trading workflow from data collection through
prediction generation to signal execution.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from src.bot_types.trading_types import BotConfig, TradingSignal
from src.database.db_manager import DatabaseManager


class TradingCycleOrchestrator:
    """
    Orchestrates the complete trading cycle workflow.
    
    Workflow:
    1. Fetch market data
    2. Calculate technical indicators
    3. Generate ML predictions
    4. Create trading signals
    5. Validate against risk rules
    6. Execute or queue signals
    
    Single Responsibility: Coordinate trading workflow execution.
    Does NOT manage lifecycle, scheduling, or position monitoring.
    """
    
    def __init__(self, modules: Dict[str, Any], config: BotConfig, db: DatabaseManager):
        """
        Initialize trading cycle orchestrator.
        
        Args:
            modules: Dict of bot module instances
            config: Bot configuration
            db: Database manager instance
        """
        # Extract required modules
        self.data_fetcher = modules['data_fetcher']
        self.feature_engineer = modules['feature_engineer']
        self.data_validator = modules['data_validator']
        self.predictor = modules['predictor']
        self.ensemble = modules['ensemble']
        self.signal_generator = modules['signal_generator']
        self.signal_queue = modules['signal_queue']
        self.risk_calculator = modules['risk_calculator']
        self.portfolio_monitor = modules['portfolio_monitor']
        self.order_manager = modules['order_manager']
        self.position_manager = modules['position_manager']
        
        self.config = config
        self.db = db
    
    def run(self):
        """
        Execute one complete trading cycle.
        
        Processes each configured symbol through the trading workflow.
        """
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
        """
        Process trading logic for a single symbol.
        
        Args:
            symbol: Stock symbol to process
        """
        try:
            logger.info(f"Processing {symbol}...")
            
            # Step 1: Fetch market data
            logger.debug(f"Fetching market data for {symbol}...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            historical_data = self.data_fetcher.fetch_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
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
            self.db.save_prediction(
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
            risk_metrics = self.portfolio_monitor.get_risk_metrics()
            current_positions = self.position_manager.get_all_positions()
            
            is_valid, reason = self.risk_calculator.validate_trade(
                signal=signal,
                portfolio=risk_metrics,
                current_positions=current_positions
            )
            
            if not is_valid:
                logger.warning(f"Trade rejected: {reason}")
                # Save signal as rejected
                self.db.save_signal(
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
                self.db.save_signal(
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
            risk_metrics = self.portfolio_monitor.get_risk_metrics()
            quantity = self.risk_calculator.calculate_position_size(
                signal=signal,
                portfolio_value=risk_metrics['portfolio_value'],
                current_price=signal.entry_price
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
                self.db.save_signal(
                    symbol=signal.symbol,
                    signal_type=signal.signal_type.value,
                    confidence=signal.confidence,
                    entry_price=signal.entry_price,
                    quantity=quantity,
                    status="executed",
                    reasoning=signal.reasoning
                )
                
                # Update bot state
                state = self.db.get_bot_state()
                if state:
                    self.db.update_bot_state({
                        'trading_mode': self.config.trading_mode.value,
                        'is_running': True,
                        'total_trades_today': state.get('total_trades_today', 0) + 1
                    })
                
                return True
            else:
                logger.error(f"Failed to execute signal: {signal.symbol}")
                return False
                
        except Exception as e:
            logger.exception(f"Error executing signal: {e}")
            return False
    
    def process_signal_approval(self, signal_id: str) -> bool:
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
            risk_metrics = self.portfolio_monitor.get_risk_metrics()
            current_positions = self.position_manager.get_all_positions()
            is_valid, reason = self.risk_calculator.validate_trade(
                signal=signal,
                portfolio=risk_metrics,
                current_positions=current_positions
            )
            
            if not is_valid:
                logger.warning(f"Signal no longer valid: {reason}")
                self.signal_queue.remove_signal(signal_id)
                # Update signal status in database
                self.db.update_signal_status(signal_id, "rejected", reason)
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
