"""
Data Validator Module

Responsible for validating data quality, detecting outliers, and handling missing data.
Ensures clean data is fed to ML models and trading systems.
"""

from typing import Optional, Tuple
import pandas as pd
import numpy as np
from loguru import logger


class DataValidator:
    """Validates market data quality and handles data issues."""
    
    def __init__(
        self,
        max_missing_pct: float = 0.05,
        price_change_threshold: float = 0.20,
        volume_change_threshold: float = 5.0
    ):
        """
        Initialize DataValidator with quality thresholds.
        
        Args:
            max_missing_pct: Maximum allowed percentage of missing data (0-1)
            price_change_threshold: Maximum single-day price change (0-1, e.g., 0.20 = 20%)
            volume_change_threshold: Maximum volume ratio compared to average
        """
        self.max_missing_pct = max_missing_pct
        self.price_change_threshold = price_change_threshold
        self.volume_change_threshold = volume_change_threshold
    
    def validate_price_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate OHLCV price data for quality issues.
        
        Args:
            df: DataFrame with OHLCV columns
        
        Returns:
            Tuple of (is_valid, message)
        """
        if df.empty:
            return False, "DataFrame is empty"
        
        logger.info(f"Validating price data with {len(df)} rows")
        
        # Check required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return False, f"Missing required columns: {missing_cols}"
        
        # Check for missing data
        missing_pct = df[required_cols].isna().sum().sum() / (len(df) * len(required_cols))
        if missing_pct > self.max_missing_pct:
            return False, f"Too much missing data: {missing_pct:.2%} (max: {self.max_missing_pct:.2%})"
        
        # Check for zero or negative prices
        for col in ['open', 'high', 'low', 'close']:
            if (df[col] <= 0).any():
                invalid_count = (df[col] <= 0).sum()
                return False, f"Found {invalid_count} zero/negative values in {col}"
        
        # Check OHLC relationships
        if (df['high'] < df['low']).any():
            invalid_count = (df['high'] < df['low']).sum()
            return False, f"Found {invalid_count} rows where high < low"
        
        if (df['high'] < df['close']).any():
            invalid_count = (df['high'] < df['close']).sum()
            return False, f"Found {invalid_count} rows where high < close"
        
        if (df['low'] > df['close']).any():
            invalid_count = (df['low'] > df['close']).sum()
            return False, f"Found {invalid_count} rows where low > close"
        
        if (df['high'] < df['open']).any():
            invalid_count = (df['high'] < df['open']).sum()
            return False, f"Found {invalid_count} rows where high < open"
        
        if (df['low'] > df['open']).any():
            invalid_count = (df['low'] > df['open']).sum()
            return False, f"Found {invalid_count} rows where low > open"
        
        # Check for negative volume
        if (df['volume'] < 0).any():
            invalid_count = (df['volume'] < 0).sum()
            return False, f"Found {invalid_count} negative volume values"
        
        # Check for extreme price changes (possible data errors)
        price_changes = df['close'].pct_change().abs()
        extreme_changes = price_changes > self.price_change_threshold
        if extreme_changes.any():
            extreme_count = extreme_changes.sum()
            max_change = price_changes.max()
            logger.warning(
                f"Found {extreme_count} extreme price changes "
                f"(max: {max_change:.2%}, threshold: {self.price_change_threshold:.2%})"
            )
            # Don't fail validation, just warn
        
        logger.info("Price data validation passed")
        return True, "Data is valid"
    
    def detect_outliers(
        self,
        df: pd.DataFrame,
        columns: Optional[list] = None,
        method: str = 'iqr'
    ) -> pd.DataFrame:
        """
        Detect outliers in specified columns.
        
        Args:
            df: DataFrame to check
            columns: Columns to check (defaults to all numeric columns)
            method: Detection method ('iqr' or 'zscore')
        
        Returns:
            DataFrame with boolean columns indicating outliers (True = outlier)
        """
        if df.empty:
            logger.warning("Empty DataFrame provided")
            return pd.DataFrame()
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        logger.info(f"Detecting outliers in {len(columns)} columns using {method} method")
        
        outliers = pd.DataFrame(index=df.index)
        
        for col in columns:
            if col not in df.columns:
                logger.warning(f"Column {col} not found, skipping")
                continue
            
            if method == 'iqr':
                outliers[f'{col}_outlier'] = self._detect_outliers_iqr(df[col])
            elif method == 'zscore':
                outliers[f'{col}_outlier'] = self._detect_outliers_zscore(df[col])
            else:
                logger.error(f"Unknown outlier detection method: {method}")
                return pd.DataFrame()
        
        total_outliers = outliers.sum().sum()
        logger.info(f"Found {total_outliers} total outliers across all columns")
        
        return outliers
    
    def _detect_outliers_iqr(self, series: pd.Series, k: float = 1.5) -> pd.Series:
        """
        Detect outliers using Interquartile Range (IQR) method.
        
        Args:
            series: Data series
            k: IQR multiplier (typically 1.5)
        
        Returns:
            Boolean series indicating outliers
        """
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        
        outliers = (series < lower_bound) | (series > upper_bound)
        
        return outliers
    
    def _detect_outliers_zscore(self, series: pd.Series, threshold: float = 3.0) -> pd.Series:
        """
        Detect outliers using Z-score method.
        
        Args:
            series: Data series
            threshold: Z-score threshold (typically 3.0)
        
        Returns:
            Boolean series indicating outliers
        """
        mean = series.mean()
        std = series.std()
        
        if std == 0:
            return pd.Series(False, index=series.index)
        
        z_scores = ((series - mean) / std).abs()
        outliers = z_scores > threshold
        
        return outliers
    
    def handle_missing_data(
        self,
        df: pd.DataFrame,
        method: str = 'forward_fill',
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Handle missing data using specified method.
        
        Args:
            df: DataFrame with missing data
            method: Method to use ('forward_fill', 'backward_fill', 'interpolate', 'drop')
            limit: Maximum number of consecutive NaNs to fill
        
        Returns:
            DataFrame with missing data handled
        """
        if df.empty:
            return df
        
        missing_before = df.isna().sum().sum()
        logger.info(f"Handling {missing_before} missing values using {method}")
        
        result = df.copy()
        
        if method == 'forward_fill':
            result = result.fillna(method='ffill', limit=limit)
        elif method == 'backward_fill':
            result = result.fillna(method='bfill', limit=limit)
        elif method == 'interpolate':
            result = result.interpolate(method='linear', limit=limit)
        elif method == 'drop':
            result = result.dropna()
        else:
            logger.error(f"Unknown missing data handling method: {method}")
            return df
        
        missing_after = result.isna().sum().sum()
        filled = missing_before - missing_after
        
        logger.info(f"Filled {filled} missing values, {missing_after} remaining")
        
        return result
    
    def remove_outliers(
        self,
        df: pd.DataFrame,
        outlier_df: pd.DataFrame,
        action: str = 'remove'
    ) -> pd.DataFrame:
        """
        Remove or handle outliers based on outlier detection results.
        
        Args:
            df: Original DataFrame
            outlier_df: DataFrame with outlier indicators (from detect_outliers)
            action: Action to take ('remove', 'cap', 'interpolate')
        
        Returns:
            DataFrame with outliers handled
        """
        if df.empty or outlier_df.empty:
            return df
        
        logger.info(f"Handling outliers using action: {action}")
        
        result = df.copy()
        
        if action == 'remove':
            # Remove rows with any outliers
            mask = ~outlier_df.any(axis=1)
            result = result[mask]
            removed = len(df) - len(result)
            logger.info(f"Removed {removed} rows with outliers")
        
        elif action == 'cap':
            # Cap outliers at reasonable bounds (e.g., 99th percentile)
            for col in outlier_df.columns:
                original_col = col.replace('_outlier', '')
                if original_col in result.columns:
                    lower_bound = result[original_col].quantile(0.01)
                    upper_bound = result[original_col].quantile(0.99)
                    
                    result.loc[outlier_df[col], original_col] = result.loc[
                        outlier_df[col], original_col
                    ].clip(lower=lower_bound, upper=upper_bound)
            
            logger.info("Capped outliers to 1st-99th percentile range")
        
        elif action == 'interpolate':
            # Replace outliers with interpolated values
            for col in outlier_df.columns:
                original_col = col.replace('_outlier', '')
                if original_col in result.columns:
                    # Mark outliers as NaN
                    result.loc[outlier_df[col], original_col] = np.nan
                    # Interpolate
                    result[original_col] = result[original_col].interpolate(method='linear')
            
            logger.info("Interpolated outliers")
        
        else:
            logger.error(f"Unknown outlier action: {action}")
            return df
        
        return result
    
    def check_data_continuity(self, df: pd.DataFrame, max_gap_days: int = 7) -> Tuple[bool, str]:
        """
        Check if data has significant time gaps.
        
        Args:
            df: DataFrame with DatetimeIndex
            max_gap_days: Maximum allowed gap in days
        
        Returns:
            Tuple of (is_continuous, message)
        """
        if df.empty:
            return False, "DataFrame is empty"
        
        if not isinstance(df.index, pd.DatetimeIndex):
            return False, "Index must be DatetimeIndex"
        
        # Calculate time differences between consecutive rows
        time_diffs = df.index.to_series().diff()
        
        # Convert to days
        time_diffs_days = time_diffs.dt.total_seconds() / (24 * 3600)
        
        # Find gaps exceeding threshold
        large_gaps = time_diffs_days > max_gap_days
        
        if large_gaps.any():
            gap_count = large_gaps.sum()
            max_gap = time_diffs_days.max()
            return False, f"Found {gap_count} gaps > {max_gap_days} days (max gap: {max_gap:.1f} days)"
        
        logger.info("Data continuity check passed")
        return True, "Data is continuous"
    
    def validate_and_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Complete data validation and cleaning pipeline.
        
        Args:
            df: Raw DataFrame
        
        Returns:
            Cleaned and validated DataFrame
        """
        logger.info("Starting complete data validation and cleaning pipeline")
        
        # Step 1: Validate basic structure
        is_valid, message = self.validate_price_data(df)
        if not is_valid:
            logger.error(f"Data validation failed: {message}")
            return pd.DataFrame()
        
        # Step 2: Handle missing data
        df_clean = self.handle_missing_data(df, method='forward_fill', limit=3)
        
        # Step 3: Check continuity
        is_continuous, message = self.check_data_continuity(df_clean, max_gap_days=7)
        if not is_continuous:
            logger.warning(f"Data continuity issue: {message}")
        
        # Step 4: Detect outliers
        outliers = self.detect_outliers(df_clean, columns=['close', 'volume'], method='iqr')
        
        if not outliers.empty and outliers.any().any():
            # Handle outliers by capping (less aggressive than removal)
            df_clean = self.remove_outliers(df_clean, outliers, action='cap')
        
        # Step 5: Final validation
        is_valid, message = self.validate_price_data(df_clean)
        if not is_valid:
            logger.error(f"Final validation failed: {message}")
            return pd.DataFrame()
        
        logger.info(f"Data validation and cleaning complete: {len(df_clean)} rows")
        return df_clean


# Example usage
if __name__ == "__main__":
    from data_fetcher import DataFetcher
    from datetime import datetime, timedelta
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Configure logging
    logger.add("logs/data_validator.log", rotation="1 day", level="DEBUG")
    
    # Fetch some data
    fetcher = DataFetcher()
    start = datetime.now() - timedelta(days=365)
    data = fetcher.fetch_historical_data('PLTR', start)
    
    print(f"Fetched {len(data)} bars")
    print(data.head())
    
    # Initialize validator
    validator = DataValidator()
    
    # Validate data
    is_valid, message = validator.validate_price_data(data)
    print(f"\nValidation result: {is_valid}")
    print(f"Message: {message}")
    
    # Check continuity
    is_continuous, message = validator.check_data_continuity(data)
    print(f"\nContinuity check: {is_continuous}")
    print(f"Message: {message}")
    
    # Detect outliers
    outliers = validator.detect_outliers(data, columns=['close', 'volume'])
    print(f"\nOutliers detected: {outliers.sum().sum()}")
    
    # Complete cleaning pipeline
    clean_data = validator.validate_and_clean(data)
    print(f"\nCleaned data: {len(clean_data)} rows")
    print(clean_data.tail())
