"""
Backtesting - Validate trading strategies on historical data.

This module handles:
- Running strategy simulations on historical data
- Calculating performance metrics
- Generating detailed reports
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from src.ml.ensemble import EnsemblePredictor
from src.data.data_fetcher import MarketDataFetcher
from src.data.feature_engineer import FeatureEngineer


class Backtester:
    """Backtest trading strategies on historical data."""
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        position_size_pct: float = 0.20,
        stop_loss_pct: float = 0.03,
        confidence_threshold: float = 0.70,
        commission_rate: float = 0.0  # Alpaca is commission-free
    ):
        """
        Initialize backtester.
        
        Args:
            initial_capital: Starting capital
            position_size_pct: Max position size as % of capital
            stop_loss_pct: Stop loss percentage (3% = 0.03)
            confidence_threshold: Minimum confidence to take trade
            commission_rate: Commission per trade (0 for Alpaca)
        """
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.stop_loss_pct = stop_loss_pct
        self.confidence_threshold = confidence_threshold
        self.commission_rate = commission_rate
        
        logger.info(
            f"Initialized Backtester: capital=${initial_capital:,.2f}, "
            f"pos_size={position_size_pct:.1%}, stop_loss={stop_loss_pct:.1%}"
        )
    
    def run_backtest(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        predictor: EnsemblePredictor,
        sequence_length: int = 60
    ) -> Dict:
        """
        Run backtest on historical data.
        
        Args:
            symbol: Stock symbol to backtest
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            predictor: Trained predictor model
            sequence_length: Days of history needed for prediction
            
        Returns:
            Dictionary with backtest results and metrics
        """
        logger.info(
            f"Running backtest for {symbol}: {start_date} to {end_date}"
        )
        
        # Fetch historical data (need extra for sequence)
        data_fetcher = MarketDataFetcher()
        start_extended = (
            pd.to_datetime(start_date) - timedelta(days=sequence_length + 30)
        ).strftime('%Y-%m-%d')
        
        df = data_fetcher.fetch_historical_data(
            symbol=symbol,
            start_date=start_extended,
            end_date=end_date
        )
        
        if df is None or len(df) == 0:
            raise ValueError(f"No data available for {symbol}")
        
        logger.info(f"Fetched {len(df)} days of historical data")
        
        # Initialize tracking
        capital = self.initial_capital
        position = None  # (entry_price, shares, stop_loss, entry_date)
        trades = []
        daily_values = []
        
        # Backtest date range
        test_dates = df.loc[start_date:end_date].index
        
        for current_date in test_dates:
            # Get historical data up to current date
            history = df.loc[:current_date]
            
            if len(history) < sequence_length:
                continue  # Not enough history yet
            
            current_price = history.iloc[-1]['close']
            
            # Update daily portfolio value
            if position is not None:
                entry_price, shares, stop_loss, entry_date = position
                position_value = shares * current_price
                total_value = capital + position_value
            else:
                total_value = capital
            
            daily_values.append({
                'date': current_date,
                'portfolio_value': total_value,
                'cash': capital,
                'position_value': position_value if position else 0
            })
            
            # Check stop loss if in position
            if position is not None:
                entry_price, shares, stop_loss, entry_date = position
                
                if current_price <= stop_loss:
                    # Stop loss triggered
                    exit_value = shares * current_price
                    commission = exit_value * self.commission_rate
                    capital += exit_value - commission
                    
                    pnl = exit_value - (entry_price * shares)
                    pnl_pct = (current_price / entry_price - 1) * 100
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'shares': shares,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': 'stop_loss',
                        'holding_days': (current_date - entry_date).days
                    })
                    
                    logger.debug(
                        f"Stop loss triggered: {symbol} at ${current_price:.2f}, "
                        f"P&L=${pnl:.2f} ({pnl_pct:.1f}%)"
                    )
                    
                    position = None
                    continue  # Don't generate new signal same day
            
            # Generate prediction
            try:
                prediction = predictor.ensemble_predict(history, symbol=symbol)
            except Exception as e:
                logger.error(f"Prediction failed on {current_date}: {e}")
                continue
            
            # Trading logic
            if position is None:
                # No position - check for entry signal
                if (prediction.direction == "UP" and 
                    prediction.confidence >= self.confidence_threshold):
                    
                    # Calculate position size
                    max_position_value = capital * self.position_size_pct
                    shares = int(max_position_value / current_price)
                    
                    if shares > 0:
                        entry_value = shares * current_price
                        commission = entry_value * self.commission_rate
                        
                        if entry_value + commission <= capital:
                            # Enter position
                            capital -= (entry_value + commission)
                            stop_loss_price = current_price * (1 - self.stop_loss_pct)
                            position = (current_price, shares, stop_loss_price, current_date)
                            
                            logger.debug(
                                f"Entered position: {shares} shares of {symbol} at "
                                f"${current_price:.2f}, stop=${stop_loss_price:.2f}"
                            )
            
            else:
                # In position - check for exit signal
                entry_price, shares, stop_loss, entry_date = position
                
                if (prediction.direction == "DOWN" and 
                    prediction.confidence >= self.confidence_threshold):
                    
                    # Exit position
                    exit_value = shares * current_price
                    commission = exit_value * self.commission_rate
                    capital += exit_value - commission
                    
                    pnl = exit_value - (entry_price * shares)
                    pnl_pct = (current_price / entry_price - 1) * 100
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'shares': shares,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': 'signal',
                        'holding_days': (current_date - entry_date).days
                    })
                    
                    logger.debug(
                        f"Exited position: {symbol} at ${current_price:.2f}, "
                        f"P&L=${pnl:.2f} ({pnl_pct:.1f}%)"
                    )
                    
                    position = None
        
        # Close any remaining position at end
        if position is not None:
            entry_price, shares, stop_loss, entry_date = position
            final_price = df.iloc[-1]['close']
            exit_value = shares * final_price
            capital += exit_value
            
            pnl = exit_value - (entry_price * shares)
            pnl_pct = (final_price / entry_price - 1) * 100
            
            trades.append({
                'symbol': symbol,
                'entry_date': entry_date,
                'exit_date': df.index[-1],
                'entry_price': entry_price,
                'exit_price': final_price,
                'shares': shares,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'exit_reason': 'end_of_test',
                'holding_days': (df.index[-1] - entry_date).days
            })
        
        # Calculate metrics
        final_value = capital
        metrics = self.calculate_metrics(trades, daily_values, self.initial_capital)
        
        logger.info(
            f"Backtest complete: {len(trades)} trades, "
            f"final_value=${final_value:,.2f}, "
            f"return={metrics['total_return_pct']:.1f}%"
        )
        
        return {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': self.initial_capital,
            'final_capital': final_value,
            'trades': trades,
            'daily_values': daily_values,
            'metrics': metrics
        }
    
    def calculate_metrics(
        self,
        trades: List[Dict],
        daily_values: List[Dict],
        initial_capital: float
    ) -> Dict:
        """
        Calculate performance metrics.
        
        Args:
            trades: List of trade dictionaries
            daily_values: List of daily portfolio values
            initial_capital: Starting capital
            
        Returns:
            Dictionary with performance metrics
        """
        if not trades:
            return {
                'total_return_pct': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown_pct': 0.0,
                'profit_factor': 0.0
            }
        
        # Basic stats
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        losing_trades = sum(1 for t in trades if t['pnl'] < 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # P&L stats
        total_pnl = sum(t['pnl'] for t in trades)
        wins = [t['pnl'] for t in trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in trades if t['pnl'] < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0
        
        # Return
        final_value = daily_values[-1]['portfolio_value'] if daily_values else initial_capital
        total_return_pct = (final_value / initial_capital - 1) * 100
        
        # Sharpe Ratio (daily returns)
        if len(daily_values) > 1:
            portfolio_values = [d['portfolio_value'] for d in daily_values]
            returns = np.diff(portfolio_values) / portfolio_values[:-1]
            
            if len(returns) > 0 and np.std(returns) > 0:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        # Maximum Drawdown
        if daily_values:
            portfolio_values = [d['portfolio_value'] for d in daily_values]
            peak = portfolio_values[0]
            max_drawdown = 0
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            max_drawdown_pct = max_drawdown * 100
        else:
            max_drawdown_pct = 0.0
        
        # Profit Factor
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        
        return {
            'total_return_pct': float(total_return_pct),
            'total_trades': int(total_trades),
            'winning_trades': int(winning_trades),
            'losing_trades': int(losing_trades),
            'win_rate': float(win_rate),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'largest_win': float(largest_win),
            'largest_loss': float(largest_loss),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown_pct': float(max_drawdown_pct),
            'profit_factor': float(profit_factor),
            'avg_holding_days': float(np.mean([t['holding_days'] for t in trades]))
        }
    
    def generate_report(self, results: Dict) -> str:
        """
        Generate text report from backtest results.
        
        Args:
            results: Backtest results dictionary
            
        Returns:
            Formatted report string
        """
        metrics = results['metrics']
        
        report = [
            "\n" + "="*60,
            f"BACKTEST REPORT: {results['symbol']}",
            "="*60,
            f"\nPeriod: {results['start_date']} to {results['end_date']}",
            f"Initial Capital: ${results['initial_capital']:,.2f}",
            f"Final Capital: ${results['final_capital']:,.2f}",
            f"Total Return: {metrics['total_return_pct']:.2f}%",
            f"\n{'TRADE STATISTICS':-^60}",
            f"Total Trades: {metrics['total_trades']}",
            f"Winning Trades: {metrics['winning_trades']}",
            f"Losing Trades: {metrics['losing_trades']}",
            f"Win Rate: {metrics['win_rate']:.1%}",
            f"Average Win: ${metrics['avg_win']:.2f}",
            f"Average Loss: ${metrics['avg_loss']:.2f}",
            f"Largest Win: ${metrics['largest_win']:.2f}",
            f"Largest Loss: ${metrics['largest_loss']:.2f}",
            f"Avg Holding Days: {metrics['avg_holding_days']:.1f}",
            f"\n{'RISK METRICS':-^60}",
            f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}",
            f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%",
            f"Profit Factor: {metrics['profit_factor']:.2f}",
            f"\n{'RECENT TRADES':-^60}"
        ]
        
        # Show last 5 trades
        recent_trades = results['trades'][-5:] if results['trades'] else []
        for trade in recent_trades:
            report.append(
                f"{trade['entry_date'].strftime('%Y-%m-%d')} → "
                f"{trade['exit_date'].strftime('%Y-%m-%d')}: "
                f"${trade['entry_price']:.2f} → ${trade['exit_price']:.2f} "
                f"| P&L: ${trade['pnl']:.2f} ({trade['pnl_pct']:+.1f}%) "
                f"| Reason: {trade['exit_reason']}"
            )
        
        report.append("="*60 + "\n")
        
        return "\n".join(report)


# Example usage
if __name__ == "__main__":
    from loguru import logger
    import sys
    
    # Configure logging
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    print("\n=== Backtester Example ===\n")
    
    # Check if ensemble model exists
    from pathlib import Path
    lstm_path = "models/lstm_model.h5"
    
    if not Path(lstm_path).exists():
        print(f"LSTM model not found: {lstm_path}")
        print("Please train an LSTM model first")
        print("\nGenerating mock backtest results...")
        
        # Create mock backtest results
        mock_results = {
            'symbol': 'PLTR',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'initial_capital': 10000.0,
            'final_capital': 12500.0,
            'trades': [
                {
                    'symbol': 'PLTR',
                    'entry_date': pd.Timestamp('2024-01-15'),
                    'exit_date': pd.Timestamp('2024-01-20'),
                    'entry_price': 30.0,
                    'exit_price': 32.0,
                    'shares': 100,
                    'pnl': 200.0,
                    'pnl_pct': 6.67,
                    'exit_reason': 'signal',
                    'holding_days': 5
                },
                {
                    'symbol': 'PLTR',
                    'entry_date': pd.Timestamp('2024-02-01'),
                    'exit_date': pd.Timestamp('2024-02-05'),
                    'entry_price': 31.0,
                    'exit_price': 29.5,
                    'shares': 100,
                    'pnl': -150.0,
                    'pnl_pct': -4.84,
                    'exit_reason': 'stop_loss',
                    'holding_days': 4
                }
            ],
            'daily_values': [
                {'date': pd.Timestamp('2024-01-15'), 'portfolio_value': 10000, 'cash': 7000, 'position_value': 3000},
                {'date': pd.Timestamp('2024-01-16'), 'portfolio_value': 10100, 'cash': 7000, 'position_value': 3100},
            ],
            'metrics': {
                'total_return_pct': 25.0,
                'total_trades': 2,
                'winning_trades': 1,
                'losing_trades': 1,
                'win_rate': 0.5,
                'avg_win': 200.0,
                'avg_loss': -150.0,
                'largest_win': 200.0,
                'largest_loss': -150.0,
                'sharpe_ratio': 1.2,
                'max_drawdown_pct': 5.0,
                'profit_factor': 1.33,
                'avg_holding_days': 4.5
            }
        }
        
        # Generate report
        backtester = Backtester()
        report = backtester.generate_report(mock_results)
        print(report)
        
    else:
        print("To run a full backtest, you need:")
        print("1. A trained LSTM model")
        print("2. Historical data (will be fetched automatically)")
        print("3. Valid Alpaca API keys for data fetching")
        print("\nExample code:")
        print("""
from src.ml.ensemble import EnsemblePredictor
from src.ml.backtest import Backtester

# Initialize predictor
predictor = EnsemblePredictor(
    lstm_model_path="models/lstm_model.h5"
)

# Run backtest
backtester = Backtester(
    initial_capital=10000,
    position_size_pct=0.20,
    stop_loss_pct=0.03,
    confidence_threshold=0.70
)

results = backtester.run_backtest(
    symbol="PLTR",
    start_date="2023-01-01",
    end_date="2024-01-01",
    predictor=predictor
)

# Generate report
report = backtester.generate_report(results)
print(report)
        """)
    
    print("\n=== Demo Complete ===")
