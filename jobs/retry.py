"""
Retry Logic with Exponential Backoff
Only retries on retryable errors (timeouts, 5xx, rate limits)
"""

import asyncio
import random
from typing import Optional, Callable, Any
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(self):
        self.max_attempts = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
        self.initial_delay = float(os.getenv("RETRY_INITIAL_DELAY_SECONDS", "1.0"))
        self.max_delay = float(os.getenv("RETRY_MAX_DELAY_SECONDS", "60.0"))
        self.exponential_base = float(os.getenv("RETRY_EXPONENTIAL_BASE", "2.0"))
        self.jitter = bool(os.getenv("RETRY_JITTER", "true").lower() == "true")


class RetryableError(Exception):
    """Base class for errors that should be retried"""
    pass


class TimeoutError(RetryableError):
    """Request timeout"""
    pass


class ServerError(RetryableError):
    """Server 5xx error"""
    pass


class RateLimitError(RetryableError):
    """Rate limit exceeded"""
    pass


class NonRetryableError(Exception):
    """Base class for errors that should NOT be retried"""
    pass


def is_retryable_error(error: Exception) -> bool:
    """Determine if error is retryable"""
    if isinstance(error, RetryableError):
        return True
    
    # Check error message for common retryable patterns
    error_str = str(error).lower()
    retryable_patterns = [
        "timeout",
        "timed out",
        "connection reset",
        "connection refused",
        "temporarily unavailable",
        "503",
        "504",
        "502",
        "rate limit",
        "too many requests",
        "429"
    ]
    
    return any(pattern in error_str for pattern in retryable_patterns)


class RetryHandler:
    """
    Handles retry logic with exponential backoff and jitter
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for next retry using exponential backoff
        
        delay = initial_delay * (exponential_base ^ attempt)
        With optional jitter to prevent thundering herd
        """
        delay = self.config.initial_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # Add random jitter (±25%)
            jitter_factor = random.uniform(0.75, 1.25)
            delay *= jitter_factor
        
        return delay
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        job_id: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Async function to execute
            job_id: Optional job ID for logging
            *args, **kwargs: Arguments to pass to func
            
        Returns:
            Result from func
            
        Raises:
            Last exception if all retries exhausted
        """
        last_error = None
        
        for attempt in range(self.config.max_attempts):
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(
                        f"Retry succeeded on attempt {attempt + 1}/{self.config.max_attempts} "
                        f"for job {job_id}"
                    )
                
                return result
                
            except Exception as e:
                last_error = e
                
                # Check if error is retryable
                if not is_retryable_error(e):
                    logger.warning(
                        f"Non-retryable error for job {job_id}: {str(e)}"
                    )
                    raise
                
                # Check if we have more attempts
                if attempt >= self.config.max_attempts - 1:
                    logger.error(
                        f"All {self.config.max_attempts} retry attempts exhausted "
                        f"for job {job_id}: {str(e)}"
                    )
                    raise
                
                # Calculate backoff delay
                delay = self.calculate_delay(attempt)
                
                logger.warning(
                    f"Retryable error on attempt {attempt + 1}/{self.config.max_attempts} "
                    f"for job {job_id}: {str(e)}. Retrying in {delay:.2f}s"
                )
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise Exception("Retry logic error: no attempts made")


# Global retry handler instance
retry_handler = RetryHandler()


async def retry_on_error(func: Callable, *args, job_id: Optional[str] = None, **kwargs) -> Any:
    """
    Convenience function to retry a call
    
    Usage:
        result = await retry_on_error(some_async_func, arg1, arg2, job_id="123")
    """
    return await retry_handler.execute_with_retry(func, *args, job_id=job_id, **kwargs)

