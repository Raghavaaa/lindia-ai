"""
Structured JSON Logging
Line-delimited JSON logs with consistent schema
"""

import json
import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
import os

# Context variables for request tracking
request_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('request_context', default=None)


class StructuredLogger:
    """
    Structured JSON logger with consistent schema
    
    Schema:
    - timestamp: ISO8601 UTC
    - request_id: UUID for tracing
    - job_id: Optional job identifier
    - tenant_id: Tenant identifier
    - service: Service name (ai-service)
    - endpoint: API endpoint
    - provider: Model provider used
    - model: Model name
    - level: Log level
    - message: Log message
    - latency_ms: Request latency
    - token_usage_in: Input tokens
    - token_usage_out: Output tokens
    - cost_estimate: Cost in USD
    - status_code: HTTP status
    - error_code: Error code if any
    - stack: Stack trace for errors
    - index_snapshot_id: Vector index version
    - env: Environment (prod/dev)
    """
    
    def __init__(self, name: str = "ai-service"):
        self.name = name
        self.service = os.getenv("SERVICE_NAME", "ai-service")
        self.env = os.getenv("ENVIRONMENT", "production")
        
        # Configure Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add JSON handler to stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
    
    def _get_context(self) -> Dict[str, Any]:
        """Get current request context"""
        ctx = request_context.get()
        if ctx is None:
            return {}
        return ctx.copy()
    
    def _build_log_entry(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Build structured log entry"""
        
        # Get context
        ctx = self._get_context()
        
        # Base entry
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service,
            "env": self.env,
            "level": level,
            "message": message,
        }
        
        # Add context fields
        if "request_id" in ctx:
            entry["request_id"] = ctx["request_id"]
        if "job_id" in ctx:
            entry["job_id"] = ctx["job_id"]
        if "tenant_id" in ctx:
            entry["tenant_id"] = ctx["tenant_id"]
        if "endpoint" in ctx:
            entry["endpoint"] = ctx["endpoint"]
        
        # Add optional fields from kwargs
        optional_fields = [
            "provider",
            "model",
            "latency_ms",
            "token_usage_in",
            "token_usage_out",
            "cost_estimate",
            "status_code",
            "error_code",
            "stack",
            "index_snapshot_id",
        ]
        
        for field in optional_fields:
            if field in kwargs:
                entry[field] = kwargs[field]
        
        # Add any extra fields
        for key, value in kwargs.items():
            if key not in optional_fields and key not in entry:
                entry[key] = value
        
        return entry
    
    def info(self, message: str, **kwargs):
        """Log info level"""
        entry = self._build_log_entry("INFO", message, **kwargs)
        self.logger.info(json.dumps(entry, separators=(',', ':')))
    
    def warning(self, message: str, **kwargs):
        """Log warning level"""
        entry = self._build_log_entry("WARNING", message, **kwargs)
        self.logger.warning(json.dumps(entry, separators=(',', ':')))
    
    def error(self, message: str, **kwargs):
        """Log error level"""
        entry = self._build_log_entry("ERROR", message, **kwargs)
        self.logger.error(json.dumps(entry, separators=(',', ':')))
    
    def debug(self, message: str, **kwargs):
        """Log debug level"""
        entry = self._build_log_entry("DEBUG", message, **kwargs)
        self.logger.debug(json.dumps(entry, separators=(',', ':')))
    
    def critical(self, message: str, **kwargs):
        """Log critical level"""
        entry = self._build_log_entry("CRITICAL", message, **kwargs)
        self.logger.critical(json.dumps(entry, separators=(',', ':')))


class StructuredFormatter(logging.Formatter):
    """Custom formatter that passes through JSON"""
    
    def format(self, record):
        # If message is already JSON, return as-is
        if record.getMessage().startswith('{'):
            return record.getMessage()
        
        # Otherwise, wrap in JSON
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }, separators=(',', ':'))


# Global logger instance
_logger = None


def get_logger(name: str = "ai-service") -> StructuredLogger:
    """Get global structured logger"""
    global _logger
    if _logger is None:
        _logger = StructuredLogger(name)
    return _logger


def set_request_context(
    request_id: Optional[str] = None,
    job_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    **kwargs
):
    """Set request context for structured logging"""
    ctx = {}
    if request_id:
        ctx["request_id"] = request_id
    if job_id:
        ctx["job_id"] = job_id
    if tenant_id:
        ctx["tenant_id"] = tenant_id
    if endpoint:
        ctx["endpoint"] = endpoint
    ctx.update(kwargs)
    request_context.set(ctx)


def get_request_context() -> Optional[Dict[str, Any]]:
    """Get current request context"""
    return request_context.get()


def clear_request_context():
    """Clear request context"""
    request_context.set(None)

