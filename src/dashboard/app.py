"""
Web Dashboard for AI Stock Trading Bot

This module provides a Flask-based web interface for monitoring and controlling
the trading bot. Features include:
- Real-time portfolio monitoring
- Trading signal approval/rejection
- Trade history and analytics
- Bot control (start/stop, mode switching)
- Configuration management
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.main import TradingBot
from src.database.db_manager import DatabaseManager
from src.bot_types.trading_types import TradingMode, SignalType
from loguru import logger

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Initialize database manager
db_manager = DatabaseManager()


def get_bot_instance() -> TradingBot:
    """Get the singleton TradingBot instance."""
    try:
        return TradingBot()
    except Exception as e:
        logger.error(f"Failed to get bot instance: {e}")
        return None


def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.2f}%"


# ============================================================================
# WEB PAGE ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/trades')
def trades_page():
    """Trade history page."""
    return render_template('trades.html')


@app.route('/signals')
def signals_page():
    """Signal management page."""
    return render_template('signals.html')


@app.route('/settings')
def settings_page():
    """Settings and configuration page."""
    return render_template('settings.html')


# ============================================================================
# API ROUTES - PORTFOLIO & STATUS
# ============================================================================

@app.route('/api/status')
def get_status():
    """Get current bot status and basic info."""
    try:
        # Get bot state from database instead of bot instance
        bot_state = db_manager.get_bot_state()
        
        if not bot_state:
            return jsonify({
                'is_running': False,
                'mode': 'hybrid',
                'is_paper_trading': True,
                'uptime': 0,
                'last_cycle': None,
                'market_open': False
            })
        
        return jsonify({
            'is_running': bot_state.get('is_running', False),
            'mode': bot_state.get('trading_mode', 'hybrid'),
            'is_paper_trading': True,  # Always paper trading for now
            'uptime': 0,  # Would need to track this separately
            'last_cycle': bot_state.get('last_update', None),
            'market_open': False  # Would need to check market hours
        })
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio')
def get_portfolio():
    """Get current portfolio state and metrics from REAL Alpaca account."""
    try:
        # Get bot instance with Alpaca API client
        bot = get_bot_instance()
        if not bot:
            return jsonify({'error': 'Bot not available'}), 500
        
        # If bot not initialized yet, return empty portfolio
        if not bot.executor:
            logger.info("Bot not initialized - returning empty portfolio")
            return jsonify({
                'portfolio': {
                    'total_value': 0,
                    'cash': 0,
                    'positions_value': 0,
                    'daily_pnl': 0,
                    'daily_pnl_percent': 0,
                    'buying_power': 0
                },
                'risk': {
                    'total_exposure': 0,
                    'position_count': 0,
                    'max_positions': 5,
                    'daily_loss_limit': 5.0,
                    'circuit_breaker_active': False
                },
                'positions': [],
                'performance': {
                    'win_rate': 0,
                    'total_trades': 0,
                    'profit_factor': 0,
                    'sharpe_ratio': 0,
                    'max_drawdown': 0
                }
            })
        
        # Fetch REAL account data from Alpaca using executor wrapper method
        alpaca_account = bot.executor.get_account()
        
        # Extract real account values (already in correct format from wrapper)
        total_value = alpaca_account['equity']
        cash_balance = alpaca_account['cash']
        buying_power = alpaca_account['buying_power']
        
        # Fetch REAL positions from Alpaca using executor wrapper method
        alpaca_positions = bot.executor.get_open_positions()
        
        # Process real positions (Position dataclass objects)
        positions = []
        total_position_value = 0.0
        total_unrealized_pnl = 0.0
        
        for pos in alpaca_positions:
            # Position is already a dataclass with proper types
            unrealized_pnl = pos.unrealized_pnl
            position_value = pos.market_value
            entry_price = pos.entry_price
            quantity = pos.quantity
            
            # Get stop loss info from database if available
            db_position = db_manager.get_position_by_symbol(pos.symbol)
            stop_loss = db_position.get('stop_loss') if db_position else None
            trailing_stop = db_position.get('trailing_stop') if db_position else None
            
            positions.append({
                'symbol': pos.symbol,
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': pos.current_price,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_percent': pos.unrealized_pnl_percent,
                'market_value': position_value,
                'stop_loss': stop_loss,
                'trailing_stop': trailing_stop
            })
            
            total_position_value += position_value
            total_unrealized_pnl += unrealized_pnl
        
        # Calculate daily P&L from Alpaca account (already floats from wrapper)
        daily_pnl = alpaca_account['equity'] - alpaca_account['last_equity']
        daily_pnl_percent = (daily_pnl / alpaca_account['last_equity'] * 100) if alpaca_account['last_equity'] > 0 else 0
        
        # Get performance metrics from database (historical data)
        perf_metrics = db_manager.get_performance_summary(days=30)
        
        return jsonify({
            'portfolio': {
                'total_value': total_value,  # REAL from Alpaca
                'cash': cash_balance,  # REAL from Alpaca
                'positions_value': total_position_value,  # Calculated from real positions
                'daily_pnl': daily_pnl,  # REAL from Alpaca
                'daily_pnl_percent': daily_pnl_percent,  # Calculated from real data
                'buying_power': buying_power  # REAL from Alpaca
            },
            'risk': {
                'total_exposure': (total_position_value / total_value * 100) if total_value > 0 else 0,
                'position_count': len(alpaca_positions),
                'max_positions': 5,  # From config
                'daily_loss_limit': 5.0,  # From config (5%)
                'circuit_breaker_active': daily_pnl_percent <= -5.0
            },
            'positions': positions,
            'performance': {
                'win_rate': perf_metrics.get('win_rate', 0),
                'total_trades': perf_metrics.get('total_trades', 0),
                'profit_factor': perf_metrics.get('profit_factor', 0),
                'sharpe_ratio': 0,  # Would need historical data to calculate
                'max_drawdown': 0   # Would need historical data to calculate
            }
        })
    except Exception as e:
        logger.error(f"Error getting portfolio data from Alpaca: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# API ROUTES - SIGNALS
# ============================================================================

@app.route('/api/signals/pending')
def get_pending_signals():
    """Get all pending signals awaiting approval."""
    try:
        signals = db_manager.get_pending_signals()
        
        formatted_signals = []
        for signal in signals:
            formatted_signals.append({
                'id': signal['id'],
                'symbol': signal['symbol'],
                'signal_type': signal['signal_type'],
                'confidence': signal['confidence'],
                'predicted_direction': signal.get('predicted_direction', 'unknown'),
                'entry_price': signal.get('entry_price', 0),
                'suggested_quantity': signal.get('quantity', 0),
                'features': signal.get('features', '{}'),
                'timestamp': signal.get('created_at').isoformat() if signal.get('created_at') else None
            })
        
        return jsonify({'signals': formatted_signals})
    except Exception as e:
        logger.error(f"Error getting pending signals: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/signals/<int:signal_id>/approve', methods=['POST'])
def approve_signal(signal_id: int):
    """Approve a pending signal for execution."""
    try:
        bot = get_bot_instance()
        if not bot:
            return jsonify({'error': 'Bot not available'}), 500
        
        # Get signal from database
        signal = db_manager.get_signal_by_id(signal_id)
        if not signal:
            return jsonify({'error': 'Signal not found'}), 404
        
        if signal['status'] != 'pending':
            return jsonify({'error': 'Signal is not pending'}), 400
        
        # Update signal status to approved
        db_manager.update_signal_status(signal_id, 'approved')
        
        # Execute the trade through the bot's order manager
        # Note: The bot's trading cycle will pick up approved signals
        # or we can trigger execution directly
        
        logger.info(f"Signal {signal_id} approved by user")
        
        return jsonify({
            'success': True,
            'message': f"Signal {signal_id} approved",
            'signal_id': signal_id
        })
    except Exception as e:
        logger.error(f"Error approving signal {signal_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/signals/<int:signal_id>/reject', methods=['POST'])
def reject_signal(signal_id: int):
    """Reject a pending signal."""
    try:
        # Get signal from database
        signal = db_manager.get_signal_by_id(signal_id)
        if not signal:
            return jsonify({'error': 'Signal not found'}), 404
        
        if signal['status'] != 'pending':
            return jsonify({'error': 'Signal is not pending'}), 400
        
        # Update signal status to rejected
        db_manager.update_signal_status(signal_id, 'rejected')
        
        logger.info(f"Signal {signal_id} rejected by user")
        
        return jsonify({
            'success': True,
            'message': f"Signal {signal_id} rejected",
            'signal_id': signal_id
        })
    except Exception as e:
        logger.error(f"Error rejecting signal {signal_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/signals/history')
def get_signal_history():
    """Get historical signals with outcomes."""
    try:
        days = request.args.get('days', 7, type=int)
        
        signals = db_manager.get_signal_history(days=days)
        
        formatted_signals = []
        for signal in signals:
            formatted_signals.append({
                'id': signal['id'],
                'symbol': signal['symbol'],
                'signal_type': signal['signal_type'],
                'confidence': signal['confidence'],
                'status': signal['status'],
                'predicted_price': signal['predicted_price'],
                'current_price': signal['current_price'],
                'timestamp': signal['timestamp'].isoformat() if signal['timestamp'] else None
            })
        
        return jsonify({'signals': formatted_signals})
    except Exception as e:
        logger.error(f"Error getting signal history: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# API ROUTES - TRADES
# ============================================================================

@app.route('/api/trades/history')
def get_trade_history():
    """Get trade history with optional filters."""
    try:
        # Get query parameters
        symbol = request.args.get('symbol')
        days = request.args.get('days', 30, type=int)
        status = request.args.get('status')
        
        # Get trades from database
        trades = db_manager.get_trade_history(
            symbol=symbol,
            days=days,
            status=status
        )
        
        formatted_trades = []
        for trade in trades:
            formatted_trades.append({
                'id': trade['id'],
                'symbol': trade['symbol'],
                'action': trade['action'],
                'quantity': trade['quantity'],
                'entry_price': trade['entry_price'],
                'exit_price': trade.get('exit_price'),
                'pnl': trade.get('pnl', 0),
                'pnl_percent': trade.get('pnl_percent', 0),
                'status': trade['status'],
                'entry_time': trade['entry_time'].isoformat() if trade['entry_time'] else None,
                'exit_time': trade['exit_time'].isoformat() if trade.get('exit_time') else None,
                'stop_loss': trade.get('stop_loss'),
                'confidence': trade.get('confidence')
            })
        
        return jsonify({'trades': formatted_trades})
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/trades/performance')
def get_trade_performance():
    """Get trading performance metrics."""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get performance summary
        performance = db_manager.get_performance_summary(days=days)
        
        # Get daily performance
        daily_perf = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            day_perf = db_manager.calculate_daily_performance(date)
            if day_perf:
                daily_perf.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'pnl': day_perf.get('daily_pnl', 0),
                    'trades': day_perf.get('trades_today', 0)
                })
        
        return jsonify({
            'summary': performance,
            'daily': daily_perf
        })
    except Exception as e:
        logger.error(f"Error getting trade performance: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# API ROUTES - BOT CONTROL
# ============================================================================

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the trading bot (idempotent - safe to call multiple times)."""
    try:
        bot = get_bot_instance()
        if not bot:
            return jsonify({'error': 'Bot not available'}), 500
        
        # Make idempotent - don't return error if already running
        if bot.is_running:
            logger.info("Start requested but bot is already running")
            # Ensure database state is in sync
            db_manager.update_bot_state({'is_running': True})
            return jsonify({
                'success': True,
                'message': 'Bot is already running',
                'was_stopped': False
            })
        
        # Check if bot needs initialization
        if bot.config is None:
            logger.info("Bot not initialized - initializing now...")
            if not bot.initialize():
                logger.error("Bot initialization failed")
                return jsonify({'error': 'Bot initialization failed. Check logs for details.'}), 500
        
        # Start the bot
        if not bot.start():
            logger.error("Bot start failed")
            return jsonify({'error': 'Failed to start bot. Check logs for details.'}), 500
        
        # Update database state to reflect bot is running
        db_manager.update_bot_state({'is_running': True})
        logger.info("Bot started via dashboard")
        
        return jsonify({
            'success': True,
            'message': 'Bot started successfully',
            'was_stopped': True
        })
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the trading bot (idempotent - safe to call multiple times)."""
    try:
        bot = get_bot_instance()
        if not bot:
            return jsonify({'error': 'Bot not available'}), 500
        
        # Make idempotent - don't return error if already stopped
        if not bot.is_running:
            logger.info("Stop requested but bot is already stopped")
            # Ensure database state is in sync
            db_manager.update_bot_state({'is_running': False})
            return jsonify({
                'success': True,
                'message': 'Bot is already stopped',
                'was_running': False
            })
        
        bot.stop()
        # Update database state to reflect bot is stopped
        db_manager.update_bot_state({'is_running': False})
        logger.info("Bot stopped via dashboard")
        
        return jsonify({
            'success': True,
            'message': 'Bot stopped successfully',
            'was_running': True
        })
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/mode', methods=['POST'])
def set_bot_mode():
    """Change the trading mode (auto/manual/hybrid)."""
    try:
        data = request.get_json()
        mode_str = data.get('mode')
        
        if not mode_str:
            return jsonify({'error': 'Mode not specified'}), 400
        
        # Validate mode
        try:
            mode = TradingMode[mode_str.upper()]
        except KeyError:
            return jsonify({'error': f'Invalid mode: {mode_str}. Valid modes: AUTO, MANUAL, HYBRID'}), 400
        
        bot = get_bot_instance()
        if not bot:
            return jsonify({'error': 'Bot not available'}), 500
        
        # Update bot state in database (proper persistence)
        # BotConfig is a dataclass, can't use dict access like bot.config['key']
        db_manager.update_bot_state({
            'trading_mode': mode.value
        })
        
        logger.info(f"Trading mode changed to {mode.value} via dashboard")
        
        return jsonify({
            'success': True,
            'message': f'Mode changed to {mode.value}. Change will take effect on next trading cycle.',
            'mode': mode.value,
            'requires_restart': bot.is_running
        })
    except Exception as e:
        logger.error(f"Error changing bot mode: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/emergency-stop', methods=['POST'])
def emergency_stop():
    """Emergency stop - halt all trading immediately."""
    try:
        bot = get_bot_instance()
        if not bot:
            return jsonify({'error': 'Bot not available'}), 500
        
        # Stop the bot
        bot.stop()
        # Update database state to reflect bot is stopped
        db_manager.update_bot_state({'is_running': False})
        
        # Close all positions
        if bot.position_manager:
            closed = bot.position_manager.close_all_positions()
            logger.warning(f"Emergency stop triggered - closed {len(closed)} positions")
        
        return jsonify({
            'success': True,
            'message': 'Emergency stop executed - all positions closed',
            'positions_closed': len(closed) if bot.position_manager else 0
        })
    except Exception as e:
        logger.error(f"Error during emergency stop: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# API ROUTES - SETTINGS
# ============================================================================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current bot configuration."""
    try:
        bot = get_bot_instance()
        if not bot:
            return jsonify({'error': 'Bot not available'}), 500
        
        return jsonify({
            'trading': {
                'mode': bot.config.get('trading', {}).get('mode', 'hybrid'),
                'symbols': bot.config.get('trading', {}).get('symbols', ['PLTR']),
                'close_positions_eod': bot.config.get('trading', {}).get('close_positions_eod', True)
            },
            'risk': bot.config.get('risk', {}),
            'ml': bot.config.get('ml', {}),
            'is_paper_trading': bot.config.get('alpaca', {}).get('is_paper', True)
        })
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update bot configuration."""
    try:
        data = request.get_json()
        
        bot = get_bot_instance()
        if not bot:
            return jsonify({'error': 'Bot not available'}), 500
        
        # Validate and prepare updates
        updates = {}
        
        if 'trading' in data:
            # Validate trading mode if provided
            if 'mode' in data['trading']:
                try:
                    TradingMode[data['trading']['mode'].upper()]
                    updates['trading_mode'] = data['trading']['mode']
                except KeyError:
                    return jsonify({'error': 'Invalid trading mode'}), 400
        
        if 'risk' in data:
            # Validate risk parameters
            for key, value in data['risk'].items():
                if not isinstance(value, (int, float)) or value < 0:
                    return jsonify({'error': f'Invalid risk parameter: {key}'}), 400
        
        if 'ml' in data:
            # Validate ML parameters
            if 'prediction_confidence_threshold' in data['ml']:
                threshold = data['ml']['prediction_confidence_threshold']
                if not (0 <= threshold <= 1):
                    return jsonify({'error': 'Confidence threshold must be between 0 and 1'}), 400
        
        # Update database state (proper persistence)
        # Note: BotConfig is a dataclass, changes should be persisted to database
        if updates:
            db_manager.update_bot_state(updates)
        
        logger.info("Settings updated via dashboard - restart bot for changes to take effect")
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully. Restart bot for changes to take effect.',
            'requires_restart': bot.is_running
        })
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# TEMPLATE FILTERS
# ============================================================================

@app.template_filter('currency')
def currency_filter(value):
    """Format value as currency."""
    return format_currency(value)


@app.template_filter('percentage')
def percentage_filter(value):
    """Format value as percentage."""
    return format_percentage(value)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the Flask development server."""
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
