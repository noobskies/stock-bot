"""
Data Fetcher Module

Responsible for fetching market data from Alpaca and Yahoo Finance.
Provides historical and real-time stock price data.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
import pandas as pd
from loguru import logger

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import yfinance as yf

from src.common.decorators import handle_data_error


class DataFetcher:
    """Fetches market data from Alpaca and Yahoo Finance APIs."""
    
    def __init__(
        self,
        alpaca_api_key: Optional[str] = None,
        alpaca_secret_key: Optional[str] = None
    ):
        """
        Initialize DataFetcher with API credentials.
        
        Args:
            alpaca_api_key: Alpaca API key (defaults to env var)
            alpaca_secret_key: Alpaca secret key (defaults to env var)
        """
        self.alpaca_api_key = alpaca_api_key or os.getenv('ALPACA_API_KEY')
        self.alpaca_secret_key = alpaca_secret_key or os.getenv('ALPACA_SECRET_KEY')
        
        if not self.alpaca_api_key or not self.alpaca_secret_key:
            logger.warning("Alpaca API credentials not provided, will fall back to Yahoo Finance")
            self.alpaca_client = None
        else:
            self.alpaca_client = self._initialize_alpaca_client()
    
    @handle_data_error(fallback_value=None)
    def _initialize_alpaca_client(self) -> Optional[StockHistoricalDataClient]:
        """Initialize Alpaca client with error handling."""
        client = StockHistoricalDataClient(
            api_key=self.alpaca_api_key,
            secret_key=self.alpaca_secret_key
        )
        logger.info("Alpaca data client initialized successfully")
        return client
    
    def fetch_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        timeframe: str = 'day'
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'PLTR')
            start_date: Start date for historical data
            end_date: End date (defaults to now)
            timeframe: Bar timeframe ('day', 'hour', 'minute')
        
        Returns:
            DataFrame with columns: open, high, low, close, volume, timestamp
        """
        if end_date is None:
            end_date = datetime.now()
        
        logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
        
        # Try Alpaca first
        if self.alpaca_client:
            try:
                data = self._fetch_from_alpaca(symbol, start_date, end_date, timeframe)
                if data is not None and not data.empty:
                    logger.info(f"Successfully fetched {len(data)} bars from Alpaca for {symbol}")
                    return data
            except Exception as e:
                logger.warning(f"Alpaca fetch failed: {e}, falling back to Yahoo Finance")
        
        # Fall back to Yahoo Finance
        try:
            data = self._fetch_from_yahoo(symbol, start_date, end_date)
            if data is not None and not data.empty:
                logger.info(f"Successfully fetched {len(data)} bars from Yahoo Finance for {symbol}")
                return data
        except Exception as e:
            logger.error(f"Yahoo Finance fetch failed: {e}")
        
        # If both fail, return empty DataFrame
        logger.error(f"Failed to fetch data for {symbol} from all sources")
        return pd.DataFrame()
    
    @handle_data_error(fallback_value=None)
    def _fetch_from_alpaca(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data from Alpaca API.
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            timeframe: Bar timeframe
        
        Returns:
            DataFrame or None if fetch fails
        """
        # Map timeframe string to TimeFrame object
        if timeframe == 'day':
            tf = TimeFrame(amount=1, unit=TimeFrameUnit.Day)
        elif timeframe == 'hour':
            tf = TimeFrame(amount=1, unit=TimeFrameUnit.Hour)
        elif timeframe == 'minute':
            tf = TimeFrame(amount=1, unit=TimeFrameUnit.Minute)
        else:
            logger.warning(f"Unknown timeframe '{timeframe}', defaulting to day")
            tf = TimeFrame(amount=1, unit=TimeFrameUnit.Day)
        
        # Create request
        request = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=tf,
            start=start_date,
            end=end_date
        )
        
        # Fetch data
        response = self.alpaca_client.get_stock_bars(request)
        
        # Convert to DataFrame
        df = response.df
        
        if df.empty:
            logger.warning(f"Alpaca returned empty data for {symbol}")
            return None
        
        # Reset index to make symbol a column, then drop it
        df = df.reset_index()
        
        # Rename columns to standard format
        df = df.rename(columns={
            'timestamp': 'timestamp',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        })
        
        # Drop symbol column if it exists
        if 'symbol' in df.columns:
            df = df.drop(columns=['symbol'])
        
        # Set timestamp as index
        df = df.set_index('timestamp')
        
        return df
    
    @handle_data_error(fallback_value=None)
    def _fetch_from_yahoo(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame or None if fetch fails
        """
        # Fetch data using yfinance
        ticker = yf.Ticker(symbol)
        df = ticker.history(
            start=start_date,
            end=end_date,
            interval='1d'
        )
        
        if df.empty:
            logger.warning(f"Yahoo Finance returned empty data for {symbol}")
            return None
        
        # Rename columns to lowercase
        df.columns = df.columns.str.lower()
        
        # Keep only OHLCV columns
        df = df[['open', 'high', 'low', 'close', 'volume']]
        
        # Rename index to 'timestamp'
        df.index.name = 'timestamp'
        
        return df
    
    @handle_data_error(fallback_value=None)
    def _fetch_latest_price_alpaca(self, symbol: str) -> Optional[float]:
        """Fetch latest price from Alpaca."""
        request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
        response = self.alpaca_client.get_stock_latest_quote(request)
        
        if symbol in response:
            quote = response[symbol]
            price = (quote.bid_price + quote.ask_price) / 2  # Mid price
            logger.debug(f"Latest price for {symbol}: ${price:.2f} (Alpaca)")
            return float(price)
        return None
    
    @handle_data_error(fallback_value=None)
    def _fetch_latest_price_yahoo(self, symbol: str) -> Optional[float]:
        """Fetch latest price from Yahoo Finance."""
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d', interval='1m')
        if not data.empty:
            price = data['Close'].iloc[-1]
            logger.debug(f"Latest price for {symbol}: ${price:.2f} (Yahoo)")
            return float(price)
        return None
    
    def fetch_latest_price(self, symbol: str) -> Optional[float]:
        """
        Fetch the latest price for a symbol with automatic fallback.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Latest price or None if fetch fails
        """
        logger.debug(f"Fetching latest price for {symbol}")
        
        # Try Alpaca first
        if self.alpaca_client:
            price = self._fetch_latest_price_alpaca(symbol)
            if price is not None:
                return price
        
        # Fall back to Yahoo Finance
        price = self._fetch_latest_price_yahoo(symbol)
        if price is not None:
            return price
        
        logger.error(f"Failed to fetch latest price for {symbol}")
        return None
    
    @handle_data_error(fallback_value=None)
    def _fetch_realtime_data_alpaca(self, symbol: str) -> Optional[dict]:
        """Fetch real-time data from Alpaca."""
        request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
        response = self.alpaca_client.get_stock_latest_quote(request)
        
        if symbol in response:
            quote = response[symbol]
            data = {
                'symbol': symbol,
                'price': (quote.bid_price + quote.ask_price) / 2,
                'bid': quote.bid_price,
                'ask': quote.ask_price,
                'bid_size': quote.bid_size,
                'ask_size': quote.ask_size,
                'timestamp': quote.timestamp
            }
            logger.debug(f"Real-time data for {symbol}: ${data['price']:.2f} (Alpaca)")
            return data
        return None
    
    @handle_data_error(fallback_value=None)
    def _fetch_realtime_data_yahoo(self, symbol: str) -> Optional[dict]:
        """Fetch real-time data from Yahoo Finance."""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        data = {
            'symbol': symbol,
            'price': info.get('currentPrice', info.get('regularMarketPrice')),
            'bid': info.get('bid'),
            'ask': info.get('ask'),
            'volume': info.get('volume'),
            'timestamp': datetime.now()
        }
        logger.debug(f"Real-time data for {symbol}: ${data['price']:.2f} (Yahoo)")
        return data
    
    def fetch_realtime_data(self, symbol: str) -> Optional[dict]:
        """
        Fetch real-time market data for a symbol with automatic fallback.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dict with current price, volume, bid, ask, or None if fetch fails
        """
        logger.debug(f"Fetching real-time data for {symbol}")
        
        # Try Alpaca first
        if self.alpaca_client:
            data = self._fetch_realtime_data_alpaca(symbol)
            if data is not None:
                return data
        
        # Fall back to Yahoo Finance
        data = self._fetch_realtime_data_yahoo(symbol)
        if data is not None:
            return data
        
        logger.error(f"Failed to fetch real-time data for {symbol}")
        return None
    
    def is_market_open(self) -> bool:
        """
        Check if the US stock market is currently open.
        
        Returns:
            True if market is open, False otherwise
        """
        from pytz import timezone
        
        # Convert current time to Eastern Time
        et = timezone('US/Eastern')
        now = datetime.now(et)
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def get_market_calendar(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[datetime]:
        """
        Get list of trading days between start and end dates.
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            List of datetime objects for trading days
        """
        # Simple implementation - excludes weekends
        # TODO: Enhance to exclude market holidays
        trading_days = []
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:
                trading_days.append(current_date)
            current_date += timedelta(days=1)
        
        logger.info(f"Found {len(trading_days)} trading days between {start_date} and {end_date}")
        return trading_days


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Configure logging
    logger.add("logs/data_fetcher.log", rotation="1 day", level="DEBUG")
    
    # Initialize fetcher
    fetcher = DataFetcher()
    
    # Test historical data fetch
    start = datetime.now() - timedelta(days=90)
    data = fetcher.fetch_historical_data('PLTR', start)
    print(f"Fetched {len(data)} bars")
    print(data.head())
    
    # Test latest price
    price = fetcher.fetch_latest_price('PLTR')
    print(f"Latest price: ${price}")
    
    # Test market status
    is_open = fetcher.is_market_open()
    print(f"Market is {'open' if is_open else 'closed'}")
