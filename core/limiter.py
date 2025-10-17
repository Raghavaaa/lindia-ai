"""
Rate limiting and quota enforcement module.
Uses in-memory storage with optional persistence to object storage.
"""
import time
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status

from core.config import settings
from core.logger import logger


class RateLimitStore:
    """
    In-memory rate limit and quota store.
    Tracks per-tenant per-minute rate limits and daily quotas.
    """
    
    def __init__(self):
        # Per-minute rate limiting: {tenant_id: [(timestamp, count), ...]}
        self.rate_limits: Dict[str, list] = defaultdict(list)
        
        # Daily quotas: {tenant_id: {'date': date, 'count': int}}
        self.daily_quotas: Dict[str, dict] = {}
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(self, tenant_id: str) -> Tuple[bool, int]:
        """
        Check if tenant is within rate limit.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tuple of (allowed: bool, remaining: int)
        """
        async with self.lock:
            now = time.time()
            one_minute_ago = now - 60
            
            # Clean up old entries
            self.rate_limits[tenant_id] = [
                (ts, count) for ts, count in self.rate_limits[tenant_id]
                if ts > one_minute_ago
            ]
            
            # Count requests in the last minute
            current_count = sum(count for _, count in self.rate_limits[tenant_id])
            
            if current_count >= settings.RATE_LIMIT_PER_MINUTE:
                return False, 0
            
            # Add current request
            self.rate_limits[tenant_id].append((now, 1))
            
            remaining = settings.RATE_LIMIT_PER_MINUTE - current_count - 1
            return True, remaining
    
    async def check_daily_quota(self, tenant_id: str) -> Tuple[bool, int]:
        """
        Check if tenant is within daily quota.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tuple of (allowed: bool, remaining: int)
        """
        async with self.lock:
            today = datetime.now().date()
            
            # Initialize or reset quota for new day
            if tenant_id not in self.daily_quotas or self.daily_quotas[tenant_id]['date'] != today:
                self.daily_quotas[tenant_id] = {'date': today, 'count': 0}
            
            quota_data = self.daily_quotas[tenant_id]
            current_count = quota_data['count']
            
            if current_count >= settings.DAILY_QUOTA_LIMIT:
                return False, 0
            
            # Increment quota
            quota_data['count'] += 1
            
            remaining = settings.DAILY_QUOTA_LIMIT - current_count - 1
            return True, remaining
    
    async def get_stats(self, tenant_id: str) -> dict:
        """Get current usage stats for a tenant."""
        async with self.lock:
            # Rate limit stats
            now = time.time()
            one_minute_ago = now - 60
            recent_requests = [
                count for ts, count in self.rate_limits[tenant_id]
                if ts > one_minute_ago
            ]
            rate_limit_used = sum(recent_requests)
            
            # Daily quota stats
            today = datetime.now().date()
            quota_used = 0
            if tenant_id in self.daily_quotas and self.daily_quotas[tenant_id]['date'] == today:
                quota_used = self.daily_quotas[tenant_id]['count']
            
            return {
                "rate_limit": {
                    "used": rate_limit_used,
                    "limit": settings.RATE_LIMIT_PER_MINUTE,
                    "remaining": settings.RATE_LIMIT_PER_MINUTE - rate_limit_used,
                },
                "daily_quota": {
                    "used": quota_used,
                    "limit": settings.DAILY_QUOTA_LIMIT,
                    "remaining": settings.DAILY_QUOTA_LIMIT - quota_used,
                }
            }


# Global rate limit store instance
rate_limit_store = RateLimitStore()


async def check_rate_limit(request: Request):
    """
    Dependency to check rate limits.
    
    Raises:
        HTTPException: If rate limit exceeded
    """
    tenant_id = getattr(request.state, "tenant_id", "default")
    request_id = getattr(request.state, "request_id", "unknown")
    
    allowed, remaining = await rate_limit_store.check_rate_limit(tenant_id)
    
    if not allowed:
        logger.warning(
            f"Rate limit exceeded for tenant {tenant_id}",
            extra={"request_id": request_id, "tenant_id": tenant_id}
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit of {settings.RATE_LIMIT_PER_MINUTE} requests per minute exceeded",
                "retry_after_seconds": 60,
            }
        )
    
    # Add rate limit headers to response
    request.state.rate_limit_remaining = remaining


async def check_quota(request: Request):
    """
    Dependency to check daily quotas.
    
    Raises:
        HTTPException: If quota exceeded
    """
    tenant_id = getattr(request.state, "tenant_id", "default")
    request_id = getattr(request.state, "request_id", "unknown")
    
    allowed, remaining = await rate_limit_store.check_daily_quota(tenant_id)
    
    if not allowed:
        logger.warning(
            f"Daily quota exceeded for tenant {tenant_id}",
            extra={"request_id": request_id, "tenant_id": tenant_id}
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "quota_exceeded",
                "message": f"Daily quota of {settings.DAILY_QUOTA_LIMIT} requests exceeded",
                "reset_time": (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat(),
            }
        )
    
    # Add quota info to response
    request.state.quota_remaining = remaining

