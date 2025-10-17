"""
Structured logging module with request ID injection.
"""
import sys
import uuid
import json
from typing import Any, Dict
from loguru import logger as _logger
from fastapi import Request

from core.config import settings


# Configure loguru logger
_logger.remove()  # Remove default handler

# Add structured JSON logging for production
if settings.ENVIRONMENT == "production":
    def serialize(record):
        """Serialize log record to JSON."""
        subset = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
        }
        
        # Add extra fields
        if record["extra"]:
            subset.update(record["extra"])
        
        return json.dumps(subset)
    
    _logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="{message}",
        serialize=True,
    )
else:
    # Human-readable format for development
    _logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    )


def inject_request_id(request: Request) -> str:
    """
    Generate or extract request ID for tracking.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request ID string
    """
    # Check if request ID already exists in headers
    request_id = request.headers.get("X-Request-ID")
    
    if not request_id:
        # Generate new UUID-based request ID
        request_id = str(uuid.uuid4())
    
    return request_id


class RequestLogger:
    """Context manager for request-scoped logging."""
    
    def __init__(self, request_id: str, **kwargs):
        self.context = {"request_id": request_id, **kwargs}
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def info(self, message: str, **extra):
        """Log info with context."""
        _logger.info(message, extra={**self.context, **extra})
    
    def warning(self, message: str, **extra):
        """Log warning with context."""
        _logger.warning(message, extra={**self.context, **extra})
    
    def error(self, message: str, **extra):
        """Log error with context."""
        _logger.error(message, extra={**self.context, **extra})
    
    def debug(self, message: str, **extra):
        """Log debug with context."""
        _logger.debug(message, extra={**self.context, **extra})


# Export the logger
logger = _logger

