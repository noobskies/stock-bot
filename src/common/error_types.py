"""
Error handling type definitions for the trading bot.

This module defines custom exceptions and error context types used
throughout the application for consistent error handling.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RetryStrategy(Enum):
    """Retry strategies for failed operations."""
    
    EXPONENTIAL_BACKOFF = "exponential"  # 1s, 2s, 4s, 8s, etc.
    FIXED_DELAY = "fixed"                # Same delay between retries
    IMMEDIATE = "immediate"               # No delay between retries
    NO_RETRY = "none"                     # Don't retry, fail immediately


@dataclass
class ErrorContext:
    """
    Context information for error handling decorator.
    
    Attributes:
        operation: Name of the operation being performed (e.g., "place_order")
        module: Module where operation is called (e.g., "executor")
        retry_count: Current retry attempt number (default: 0)
        max_retries: Maximum number of retry attempts (default: 3)
        suppress_errors: Whether to suppress errors and return None (default: False)
    """
    
    operation: str
    module: str
    retry_count: int = 0
    max_retries: int = 3
    suppress_errors: bool = False


class RetryableError(Exception):
    """
    Custom exception for operations that should be retried.
    
    Raised when an operation fails but can potentially succeed
    if retried (e.g., temporary network issues, API rate limits).
    """
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class CircuitBreakerError(Exception):
    """
    Custom exception when circuit breaker is activated.
    
    Raised when the risk management circuit breaker is triggered
    (e.g., daily loss limit exceeded) and no new trades are allowed.
    """
    
    def __init__(self, message: str, trigger_reason: str):
        super().__init__(message)
        self.trigger_reason = trigger_reason
