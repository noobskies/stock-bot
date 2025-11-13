"""
Feature Engineer Module

Responsible for calculating technical indicators and preparing features for ML models.
Uses TA-Lib for technical analysis and pandas for data manipulation.
"""

from typing import Optional
import pandas as pd
import numpy as np
from loguru import logger

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    logger.warning("TA-Lib not available, using pandas-based indicators")
    TALIB_AVAILABLE = False


class FeatureEngineer:
    """Calculates technical indicators and prepares ML features from OHLCV data."""
    
    def __init__(self):
        """Initialize FeatureEngineer."""
        self.talib_available = TALIB_AVAILABLE
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators from OHLCV data.
        
        Args:
            df: DataFrame with columns: open, high, low, close, volume
        
        Returns:
            DataFrame with original data plus technical indicators
        """
        if df.empty:
            logger.warning("Empty DataFrame provided, returning as is")
            return df
        
        logger.info(f"Calculating technical indicators for {len(df)} rows")
        
        # Create a copy to avoid modifying original
        result = df.copy()
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in result.columns for col in required_cols):
            logger.error(f"Missing required columns. Need: {required_cols}")
            return df
        
        try:
            # RSI (Relative Strength Index)
            result['rsi'] = self._calculate_rsi(result['close'])
            
            # MACD (Moving Average Convergence Divergence)
            macd_result = self._calculate_macd(result['close'])
            result['macd'] = macd_result['macd']
            result['macd_signal'] = macd_result['signal']
            result['macd_hist'] = macd_result['histogram']
            
            # Bollinger Bands
            bb_result = self._calculate_bollinger_bands(result['close'])
            result['bb_upper'] = bb_result['upper']
            result['bb_middle'] = bb_result['middle']
            result['bb_lower'] = bb_result['lower']
            result['bb_width'] = bb_result['width']
            
            # Moving Averages
            result['sma_20'] = self._calculate_sma(result['close'], period=20)
            result['sma_50'] = self._calculate_sma(result['close'], period=50)
            result['ema_12'] = self._calculate_ema(result['close'], period=12)
            result['ema_26'] = self._calculate_ema(result['close'], period=26)
            
            # Volume indicators
            result['volume_sma'] = self._calculate_sma(result['volume'], period=20)
            result['volume_ratio'] = result['volume'] / result['volume_sma']
            
            # Price changes
            result['price_change'] = result['close'].pct_change()
            result['price_change_5d'] = result['close'].pct_change(periods=5)
            result['price_change_20d'] = result['close'].pct_change(periods=20)
            
            # Volatility (20-day standard deviation of returns)
            result['volatility'] = result['price_change'].rolling(window=20).std()
            
            # Average True Range (ATR)
            result['atr'] = self._calculate_atr(result)
            
            # Momentum
            result['momentum'] = result['close'] - result['close'].shift(10)
            
            logger.info(f"Successfully calculated {len(result.columns) - len(df.columns)} technical indicators")
            
            return result
        
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.
        
        Args:
            prices: Series of closing prices
            period: RSI period (default 14)
        
        Returns:
            Series of RSI values
        """
        if self.talib_available:
            try:
                return pd.Series(talib.RSI(prices.values, timeperiod=period), index=prices.index)
            except Exception as e:
                logger.warning(f"TA-Lib RSI failed: {e}, using pandas implementation")
        
        # Pandas-based RSI calculation
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> dict:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Series of closing prices
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period
        
        Returns:
            Dict with 'macd', 'signal', and 'histogram' Series
        """
        if self.talib_available:
            try:
                macd, signal_line, hist = talib.MACD(
                    prices.values,
                    fastperiod=fast,
                    slowperiod=slow,
                    signalperiod=signal
                )
                return {
                    'macd': pd.Series(macd, index=prices.index),
                    'signal': pd.Series(signal_line, index=prices.index),
                    'histogram': pd.Series(hist, index=prices.index)
                }
            except Exception as e:
                logger.warning(f"TA-Lib MACD failed: {e}, using pandas implementation")
        
        # Pandas-based MACD calculation
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> dict:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Series of closing prices
            period: Moving average period
            std_dev: Number of standard deviations
        
        Returns:
            Dict with 'upper', 'middle', 'lower', 'width' Series
        """
        if self.talib_available:
            try:
                upper, middle, lower = talib.BBANDS(
                    prices.values,
                    timeperiod=period,
                    nbdevup=std_dev,
                    nbdevdn=std_dev
                )
                upper = pd.Series(upper, index=prices.index)
                middle = pd.Series(middle, index=prices.index)
                lower = pd.Series(lower, index=prices.index)
                width = ((upper - lower) / middle) * 100
                
                return {
                    'upper': upper,
                    'middle': middle,
                    'lower': lower,
                    'width': width
                }
            except Exception as e:
                logger.warning(f"TA-Lib Bollinger Bands failed: {e}, using pandas implementation")
        
        # Pandas-based Bollinger Bands calculation
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        width = ((upper - lower) / middle) * 100
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'width': width
        }
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average.
        
        Args:
            prices: Series of prices
            period: Moving average period
        
        Returns:
            Series of SMA values
        """
        if self.talib_available:
            try:
                return pd.Series(talib.SMA(prices.values, timeperiod=period), index=prices.index)
            except Exception as e:
                logger.warning(f"TA-Lib SMA failed: {e}, using pandas implementation")
        
        return prices.rolling(window=period).mean()
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: Series of prices
            period: Moving average period
        
        Returns:
            Series of EMA values
        """
        if self.talib_available:
            try:
                return pd.Series(talib.EMA(prices.values, timeperiod=period), index=prices.index)
            except Exception as e:
                logger.warning(f"TA-Lib EMA failed: {e}, using pandas implementation")
        
        return prices.ewm(span=period, adjust=False).mean()
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range.
        
        Args:
            df: DataFrame with high, low, close columns
            period: ATR period
        
        Returns:
            Series of ATR values
        """
        if self.talib_available:
            try:
                atr = talib.ATR(
                    df['high'].values,
                    df['low'].values,
                    df['close'].values,
                    timeperiod=period
                )
                return pd.Series(atr, index=df.index)
            except Exception as e:
                logger.warning(f"TA-Lib ATR failed: {e}, using pandas implementation")
        
        # Pandas-based ATR calculation
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def create_ml_features(
        self,
        df: pd.DataFrame,
        sequence_length: int = 60
    ) -> tuple:
        """
        Create feature matrix for ML models.
        
        Args:
            df: DataFrame with technical indicators
            sequence_length: Number of time steps for sequences (for LSTM)
        
        Returns:
            Tuple of (X, y) where X is features and y is target
            X shape: (samples, features) for non-sequence models
            y: 1 for price up next day, 0 for price down
        """
        logger.info(f"Creating ML features with sequence length {sequence_length}")
        
        # Calculate target (next day price direction)
        df = df.copy()
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        # Drop rows with NaN values
        df_clean = df.dropna()
        
        if len(df_clean) < sequence_length:
            logger.error(f"Not enough data points ({len(df_clean)}) for sequence length {sequence_length}")
            return None, None
        
        # Select feature columns (exclude OHLCV and target)
        feature_cols = [col for col in df_clean.columns if col not in 
                       ['open', 'high', 'low', 'close', 'volume', 'target']]
        
        X = df_clean[feature_cols].values
        y = df_clean['target'].values
        
        logger.info(f"Created feature matrix: {X.shape}, target: {y.shape}")
        logger.info(f"Features: {feature_cols}")
        
        return X, y
    
    def create_sequences(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sequence_length: int = 60
    ) -> tuple:
        """
        Create sequences for LSTM models.
        
        Args:
            X: Feature matrix (samples, features)
            y: Target array (samples,)
            sequence_length: Number of time steps per sequence
        
        Returns:
            Tuple of (X_seq, y_seq) where X_seq has shape (samples, timesteps, features)
        """
        if len(X) < sequence_length:
            logger.error(f"Not enough data points ({len(X)}) for sequence length {sequence_length}")
            return None, None
        
        X_seq = []
        y_seq = []
        
        for i in range(sequence_length, len(X)):
            X_seq.append(X[i - sequence_length:i])
            y_seq.append(y[i])
        
        X_seq = np.array(X_seq)
        y_seq = np.array(y_seq)
        
        logger.info(f"Created sequences: {X_seq.shape}, targets: {y_seq.shape}")
        
        return X_seq, y_seq
    
    def normalize_features(self, X: np.ndarray, scaler=None) -> tuple:
        """
        Normalize features using StandardScaler.
        
        Args:
            X: Feature matrix
            scaler: Pre-fitted scaler (optional, will create new if None)
        
        Returns:
            Tuple of (X_normalized, scaler)
        """
        from sklearn.preprocessing import StandardScaler
        
        if scaler is None:
            scaler = StandardScaler()
            X_normalized = scaler.fit_transform(X)
            logger.info("Created and fitted new StandardScaler")
        else:
            X_normalized = scaler.transform(X)
            logger.info("Used existing StandardScaler")
        
        return X_normalized, scaler


# Example usage
if __name__ == "__main__":
    from data_fetcher import DataFetcher
    from datetime import datetime, timedelta
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Configure logging
    logger.add("logs/feature_engineer.log", rotation="1 day", level="DEBUG")
    
    # Fetch some data
    fetcher = DataFetcher()
    start = datetime.now() - timedelta(days=365)  # 1 year of data
    data = fetcher.fetch_historical_data('PLTR', start)
    
    print(f"Fetched {len(data)} bars")
    print(data.head())
    
    # Calculate technical indicators
    engineer = FeatureEngineer()
    data_with_indicators = engineer.calculate_technical_indicators(data)
    
    print(f"\nData with indicators: {data_with_indicators.shape}")
    print(data_with_indicators.columns.tolist())
    print(data_with_indicators.tail())
    
    # Create ML features
    X, y = engineer.create_ml_features(data_with_indicators)
    
    if X is not None:
        print(f"\nFeature matrix: {X.shape}")
        print(f"Target: {y.shape}")
        print(f"Target distribution: {np.bincount(y.astype(int))}")
        
        # Normalize features
        X_normalized, scaler = engineer.normalize_features(X)
        print(f"\nNormalized features: {X_normalized.shape}")
        
        # Create sequences for LSTM
        X_seq, y_seq = engineer.create_sequences(X_normalized, y, sequence_length=60)
        if X_seq is not None:
            print(f"\nSequence shape: {X_seq.shape}")
            print(f"Sequence targets: {y_seq.shape}")
