"""
Request Context Management
Request ID generation and propagation
"""

import uuid
from typing import Optional, Dict
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

# Context variable for request tracking
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
_start_time: ContextVar[Optional[float]] = ContextVar('start_time', default=None)


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return f"req_{uuid.uuid4().hex[:16]}"


class RequestContext:
    """
    Request context manager
    Handles request ID generation and propagation
    """
    
    @staticmethod
    def get_request_id() -> Optional[str]:
        """Get current request ID"""
        return _request_id.get()
    
    @staticmethod
    def set_request_id(request_id: str):
        """Set request ID in context"""
        _request_id.set(request_id)
    
    @staticmethod
    def get_start_time() -> Optional[float]:
        """Get request start time"""
        return _start_time.get()
    
    @staticmethod
    def set_start_time(start_time: float):
        """Set request start time"""
        _start_time.set(start_time)
    
    @staticmethod
    def get_latency_ms() -> float:
        """Calculate request latency in milliseconds"""
        start = _start_time.get()
        if start is None:
            return 0.0
        return (time.time() - start) * 1000


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for request context management
    
    - Generates or extracts request ID
    - Propagates via X-Request-ID header
    - Adds W3C trace headers support
    - Tracks request timing
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extract or generate request ID
        request_id = (
            request.headers.get("X-Request-ID") or
            request.headers.get("X-Request-Id") or
            request.headers.get("Request-ID") or
            generate_request_id()
        )
        
        # Set in context
        RequestContext.set_request_id(request_id)
        
        # Track timing
        start_time = time.time()
        RequestContext.set_start_time(start_time)
        
        # Add to request state for easy access
        request.state.request_id = request_id
        request.state.start_time = start_time
        
        # Call next middleware/endpoint
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Add W3C trace context headers
        response.headers["traceparent"] = f"00-{uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-01"
        
        # Calculate and add latency header
        latency_ms = RequestContext.get_latency_ms()
        response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
        
        return response


def get_trace_headers(request_id: Optional[str] = None) -> Dict[str, str]:
    """
    Get headers for downstream service calls
    Includes X-Request-ID and W3C trace context
    """
    req_id = request_id or RequestContext.get_request_id() or generate_request_id()
    
    return {
        "X-Request-ID": req_id,
        "traceparent": f"00-{uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-01",
        "tracestate": f"ai-service={req_id}",
    }


def propagate_context_to_job(job_id: str) -> Dict[str, str]:
    """
    Propagate request context to async job
    Returns metadata to attach to job
    """
    return {
        "request_id": RequestContext.get_request_id() or "unknown",
        "parent_trace_id": uuid.uuid4().hex,
        "created_at": str(time.time()),
    }

