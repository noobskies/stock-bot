"""
Trading Bot Main Application

Simplified entry point that uses the BotCoordinator architecture.
All orchestration logic has been moved to specialized components.
"""

import sys
import time
import signal
from loguru import logger

from src.bot.coordinator import BotCoordinator


# Backward compatibility alias for dashboard
TradingBot = BotCoordinator


def main():
    """Main entry point for the trading bot."""
    # Create bot coordinator instance
    bot = BotCoordinator()
    
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum} - shutting down...")
        bot.stop()
        sys.exit(0)
    
    # Register signal handlers
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
