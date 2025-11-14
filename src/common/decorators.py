"""
Reusable decorators for error handling, logging, and validation.

This module provides decorators that eliminate duplicate try-catch blocks
throughout the codebase, implementing DRY principles and consistent error handling.
"""

import functools
import time
from typing import Any, Callable, Optional, TypeVar, cast
from loguru import logger

from src.common.error_types import (
    ErrorContext,
    RetryStrategy,
    RetryableError,
    CircuitBreakerError,
)


T = TypeVar('T')


def handle_broker_error(
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for Alpaca broker API calls with retry logic.
    
    Handles common broker errors like rate limits, temporary network issues,
    and API timeouts. Implements configurable retry strategies.
    
    Args:
        retry_strategy: Strategy for retrying failed operations
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds between retries
        
    Returns:
        Decorated function with error handling and retry logic
        
    Example:
        @handle_broker_error(retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF)
        def place_order(symbol: str, qty: int):
            # ... implementation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            context = ErrorContext(
                operation=func.__name__,
                module="broker",
                max_retries=max_retries,
            )
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"{context.module}.{context.operation} succeeded after {attempt} retries"
                        )
                    return result
                    
                except Exception as e:
                    context.retry_count = attempt
                    
                    # Don't retry on last attempt
                    if attempt >= max_retries:
                        logger.error(
                            f"{context.module}.{context.operation} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    # Calculate delay based on strategy
                    if retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                        delay = base_delay * (2 ** attempt)
                    elif retry_strategy == RetryStrategy.FIXED_DELAY:
                        delay = base_delay
                    elif retry_strategy == RetryStrategy.IMMEDIATE:
                        delay = 0
                    else:  # NO_RETRY
                        raise
                    
                    logger.warning(
                        f"{context.module}.{context.operation} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    
                    if delay > 0:
                        time.sleep(delay)
            
            # Should never reach here, but for type safety
            raise RuntimeError(f"Unexpected error in {func.__name__}")
        
        return cast(Callable[..., T], wrapper)
    return decorator


def handle_data_error(
    fallback_value: Optional[Any] = None,
    log_level: str = "ERROR",
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    Decorator for data fetching operations.
    
    Handles data fetch failures gracefully by returning a fallback value
    instead of crashing the application.
    
    Args:
        fallback_value: Value to return if operation fails (default: None)
        log_level: Logging level for errors ("ERROR", "WARNING", "INFO")
        
    Returns:
        Decorated function with error handling
        
    Example:
        @handle_data_error(fallback_value=pd.DataFrame())
        def fetch_historical_data(symbol: str):
            # ... implementation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_message = f"data.{func.__name__} failed: {e}"
                
                if log_level == "ERROR":
                    logger.error(log_message)
                elif log_level == "WARNING":
                    logger.warning(log_message)
                else:
                    logger.info(log_message)
                
                return fallback_value
        
        return wrapper
    return decorator


def handle_ml_error(
    fallback_to_baseline: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    Decorator for ML operations (training, prediction).
    
    Handles ML errors gracefully, optionally falling back to baseline predictions.
    
    Args:
        fallback_to_baseline: Whether to use baseline prediction on failure
        
    Returns:
        Decorated function with error handling
        
    Example:
        @handle_ml_error(fallback_to_baseline=True)
        def predict(features):
            # ... implementation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"ml.{func.__name__} failed: {e}")
                
                if fallback_to_baseline:
                    logger.warning(
                        f"ml.{func.__name__} falling back to baseline prediction"
                    )
                    # Return None to signal caller to use baseline
                    return None
                else:
                    raise
        
        return wrapper
    return decorator


def handle_trading_error(
    circuit_breaker: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for trading operations.
    
    Handles trading errors and can activate circuit breaker on critical failures.
    
    Args:
        circuit_breaker: Whether to activate circuit breaker on failure
        
    Returns:
        Decorated function with error handling
        
    Example:
        @handle_trading_error(circuit_breaker=True)
        def execute_trade(signal):
            # ... implementation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"trading.{func.__name__} failed: {e}")
                
                # Check if this is a critical error that should trigger circuit breaker
                if circuit_breaker and _is_critical_error(e):
                    logger.critical(
                        f"Critical trading error in {func.__name__}, "
                        "circuit breaker should be activated"
                    )
                    raise CircuitBreakerError(
                        f"Circuit breaker activated due to critical error in {func.__name__}",
                        trigger_reason=str(e)
                    )
                raise
        
        return wrapper
    return decorator


def log_execution_time(
    threshold_seconds: float = 1.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to log execution time of slow operations.
    
    Logs a warning if the operation takes longer than the threshold.
    
    Args:
        threshold_seconds: Time threshold in seconds for logging
        
    Returns:
        Decorated function with timing logging
        
    Example:
        @log_execution_time(threshold_seconds=2.0)
        def expensive_calculation():
            # ... implementation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            if elapsed > threshold_seconds:
                logger.warning(
                    f"{func.__name__} took {elapsed:.2f}s (threshold: {threshold_seconds}s)"
                )
            else:
                logger.debug(f"{func.__name__} took {elapsed:.2f}s")
            
            return result
        
        return wrapper
    return decorator


def validate_inputs(**validation_rules: Callable[[Any], bool]) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to validate function inputs.
    
    Args:
        **validation_rules: Keyword arguments mapping parameter names to validation functions
        
    Returns:
        Decorated function with input validation
        
    Example:
        @validate_inputs(
            symbol=lambda s: len(s) > 0,
            quantity=lambda q: q > 0
        )
        def place_order(symbol: str, quantity: int):
            # ... implementation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each specified parameter
            for param_name, validator in validation_rules.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(
                            f"Validation failed for parameter '{param_name}' "
                            f"in {func.__name__}: value={value}"
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def _is_critical_error(error: Exception) -> bool:
    """
    Determine if an error is critical enough to trigger circuit breaker.
    
    Args:
        error: Exception to check
        
    Returns:
        True if error is critical, False otherwise
    """
    critical_patterns = [
        "insufficient funds",
        "account suspended",
        "trading not allowed",
        "loss limit exceeded",
    ]
    
    error_str = str(error).lower()
    return any(pattern in error_str for pattern in critical_patterns)
