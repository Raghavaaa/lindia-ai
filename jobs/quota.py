"""
Quota and Rate Limiting System
Per-tenant quotas and rate limits
"""

import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import deque
import logging
import os

logger = logging.getLogger(__name__)


class TenantQuota:
    """
    Quota tracker for a single tenant
    Tracks daily usage and rate limits
    """
    
    def __init__(
        self,
        tenant_id: str,
        daily_quota: int,
        rate_limit_per_minute: int
    ):
        self.tenant_id = tenant_id
        self.daily_quota = daily_quota
        self.rate_limit_per_minute = rate_limit_per_minute
        
        # Usage tracking
        self.daily_usage = 0
        self.last_reset = datetime.utcnow()
        
        # Rate limiting (sliding window)
        self.request_timestamps: deque = deque()
        self._lock = asyncio.Lock()
    
    async def check_and_consume(self) -> tuple[bool, Dict]:
        """
        Check if request can proceed and consume quota
        
        Returns:
            (allowed, info_dict)
        """
        async with self._lock:
            now = datetime.utcnow()
            
            # Reset daily quota if needed
            if (now - self.last_reset) >= timedelta(days=1):
                self.daily_usage = 0
                self.last_reset = now
                logger.info(f"Reset daily quota for tenant {self.tenant_id}")
            
            # Check daily quota
            if self.daily_usage >= self.daily_quota:
                return False, {
                    "reason": "daily_quota_exceeded",
                    "daily_usage": self.daily_usage,
                    "daily_quota": self.daily_quota,
                    "resets_at": (self.last_reset + timedelta(days=1)).isoformat()
                }
            
            # Clean old timestamps (older than 1 minute)
            cutoff = now - timedelta(minutes=1)
            while self.request_timestamps and self.request_timestamps[0] < cutoff:
                self.request_timestamps.popleft()
            
            # Check rate limit
            if len(self.request_timestamps) >= self.rate_limit_per_minute:
                return False, {
                    "reason": "rate_limit_exceeded",
                    "rate_limit": self.rate_limit_per_minute,
                    "current_rate": len(self.request_timestamps),
                    "retry_after_seconds": 60
                }
            
            # Consume quota
            self.daily_usage += 1
            self.request_timestamps.append(now)
            
            return True, {
                "daily_usage": self.daily_usage,
                "daily_quota": self.daily_quota,
                "remaining_quota": self.daily_quota - self.daily_usage,
                "rate_limit": self.rate_limit_per_minute,
                "current_rate": len(self.request_timestamps)
            }
    
    async def get_info(self) -> Dict:
        """Get quota information without consuming"""
        async with self._lock:
            now = datetime.utcnow()
            
            # Clean old timestamps
            cutoff = now - timedelta(minutes=1)
            while self.request_timestamps and self.request_timestamps[0] < cutoff:
                self.request_timestamps.popleft()
            
            return {
                "tenant_id": self.tenant_id,
                "daily_usage": self.daily_usage,
                "daily_quota": self.daily_quota,
                "remaining_quota": self.daily_quota - self.daily_usage,
                "rate_limit_per_minute": self.rate_limit_per_minute,
                "current_rate": len(self.request_timestamps),
                "resets_at": (self.last_reset + timedelta(days=1)).isoformat()
            }


class QuotaManager:
    """
    Manages quotas and rate limits for all tenants
    """
    
    def __init__(self):
        self.tenants: Dict[str, TenantQuota] = {}
        self._lock = asyncio.Lock()
        
        # Default limits from environment
        self.default_daily_quota = int(os.getenv("QUOTA_DEFAULT_DAILY", "1000"))
        self.default_rate_limit = int(os.getenv("QUOTA_DEFAULT_RATE_PER_MINUTE", "60"))
        
        # Tier-based quotas (can be expanded)
        self.tier_quotas = {
            "free": {
                "daily": int(os.getenv("QUOTA_FREE_DAILY", "100")),
                "rate": int(os.getenv("QUOTA_FREE_RATE", "10"))
            },
            "basic": {
                "daily": int(os.getenv("QUOTA_BASIC_DAILY", "1000")),
                "rate": int(os.getenv("QUOTA_BASIC_RATE", "60"))
            },
            "pro": {
                "daily": int(os.getenv("QUOTA_PRO_DAILY", "10000")),
                "rate": int(os.getenv("QUOTA_PRO_RATE", "300"))
            },
            "enterprise": {
                "daily": int(os.getenv("QUOTA_ENTERPRISE_DAILY", "100000")),
                "rate": int(os.getenv("QUOTA_ENTERPRISE_RATE", "1000"))
            }
        }
        
        logger.info(f"QuotaManager initialized with default daily quota: {self.default_daily_quota}")
    
    async def get_or_create_tenant(
        self,
        tenant_id: str,
        tier: str = "basic"
    ) -> TenantQuota:
        """Get or create tenant quota"""
        async with self._lock:
            if tenant_id not in self.tenants:
                # Get quota based on tier
                tier_config = self.tier_quotas.get(tier, {
                    "daily": self.default_daily_quota,
                    "rate": self.default_rate_limit
                })
                
                self.tenants[tenant_id] = TenantQuota(
                    tenant_id=tenant_id,
                    daily_quota=tier_config["daily"],
                    rate_limit_per_minute=tier_config["rate"]
                )
                logger.info(f"Created quota for tenant {tenant_id} with tier {tier}")
            
            return self.tenants[tenant_id]
    
    async def check_and_consume(
        self,
        tenant_id: str,
        tier: str = "basic"
    ) -> tuple[bool, Dict]:
        """
        Check if tenant can make request and consume quota
        
        Returns:
            (allowed, info_dict)
        """
        tenant = await self.get_or_create_tenant(tenant_id, tier)
        return await tenant.check_and_consume()
    
    async def get_tenant_info(
        self,
        tenant_id: str,
        tier: str = "basic"
    ) -> Dict:
        """Get tenant quota information"""
        tenant = await self.get_or_create_tenant(tenant_id, tier)
        return await tenant.get_info()
    
    async def update_tenant_tier(
        self,
        tenant_id: str,
        new_tier: str
    ) -> bool:
        """Update tenant's quota tier"""
        if new_tier not in self.tier_quotas:
            logger.warning(f"Unknown tier: {new_tier}")
            return False
        
        async with self._lock:
            if tenant_id in self.tenants:
                # Remove old quota
                del self.tenants[tenant_id]
            
            # Create with new tier
            await self.get_or_create_tenant(tenant_id, new_tier)
            logger.info(f"Updated tenant {tenant_id} to tier {new_tier}")
            return True
    
    async def reset_tenant(self, tenant_id: str):
        """Reset tenant quota (admin operation)"""
        async with self._lock:
            if tenant_id in self.tenants:
                tenant = self.tenants[tenant_id]
                tenant.daily_usage = 0
                tenant.last_reset = datetime.utcnow()
                tenant.request_timestamps.clear()
                logger.info(f"Reset quota for tenant {tenant_id}")
    
    async def get_all_tenants_info(self) -> Dict:
        """Get information for all tenants"""
        async with self._lock:
            return {
                tenant_id: await tenant.get_info()
                for tenant_id, tenant in self.tenants.items()
            }

