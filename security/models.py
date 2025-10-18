"""
Security Data Models
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Scope(str, Enum):
    """Permission scopes for RBAC"""
    # Read operations
    READ_SEARCH = "search:read"
    READ_HEALTH = "health:read"
    READ_STATUS = "status:read"
    
    # Write operations
    WRITE_INDEX = "index:write"
    WRITE_EMBED = "embed:write"
    WRITE_INFERENCE = "inference:write"
    
    # Admin operations
    ADMIN_MANAGE = "admin:manage"
    ADMIN_REVOKE = "admin:revoke"
    ADMIN_CONFIG = "admin:config"
    
    # Service-to-service
    SERVICE_INTERNAL = "service:internal"


class TokenType(str, Enum):
    """Token types"""
    SERVICE = "service"  # Service-to-service
    USER = "user"  # User access
    ADMIN = "admin"  # Admin access


class SecurityErrorCode(str, Enum):
    """Machine-readable security error codes"""
    TOKEN_MISSING = "TOKEN_MISSING"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    CLAIM_MISSING = "CLAIM_MISSING"
    CLAIM_INVALID = "CLAIM_INVALID"
    SCOPE_INSUFFICIENT = "SCOPE_INSUFFICIENT"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    COST_CAP_EXCEEDED = "COST_CAP_EXCEEDED"


@dataclass
class TokenClaims:
    """
    JWT token claims
    
    Standard claims:
    - sub: Subject (service/user identifier)
    - iss: Issuer
    - aud: Audience
    - exp: Expiration time
    - iat: Issued at time
    - jti: JWT ID (unique identifier)
    
    Custom claims:
    - tenant_id: Tenant identifier
    - scopes: List of permission scopes
    - token_type: Type of token (service/user/admin)
    """
    sub: str  # Subject (service or user)
    tenant_id: str
    scopes: List[str] = field(default_factory=list)
    
    # Standard claims
    iss: str = "ai-service"
    aud: str = "ai-service"
    exp: Optional[int] = None
    iat: Optional[int] = None
    jti: Optional[str] = None
    
    # Custom claims
    token_type: TokenType = TokenType.SERVICE
    key_version: str = "v1"
    
    def has_scope(self, required_scope: str) -> bool:
        """Check if token has required scope"""
        return required_scope in self.scopes
    
    def has_any_scope(self, required_scopes: List[str]) -> bool:
        """Check if token has any of the required scopes"""
        return any(scope in self.scopes for scope in required_scopes)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JWT payload"""
        return {
            "sub": self.sub,
            "tenant_id": self.tenant_id,
            "scopes": self.scopes,
            "iss": self.iss,
            "aud": self.aud,
            "exp": self.exp,
            "iat": self.iat,
            "jti": self.jti,
            "token_type": self.token_type.value,
            "key_version": self.key_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenClaims":
        """Create from dictionary"""
        return cls(
            sub=data["sub"],
            tenant_id=data["tenant_id"],
            scopes=data.get("scopes", []),
            iss=data.get("iss", "ai-service"),
            aud=data.get("aud", "ai-service"),
            exp=data.get("exp"),
            iat=data.get("iat"),
            jti=data.get("jti"),
            token_type=TokenType(data.get("token_type", "service")),
            key_version=data.get("key_version", "v1"),
        )


@dataclass
class RateLimitInfo:
    """Rate limit status information"""
    limit: int
    remaining: int
    reset: int  # Unix timestamp
    window: str  # "second", "minute", "day"


@dataclass
class QuotaInfo:
    """Quota status information"""
    tenant_id: str
    daily_limit: int
    daily_usage: int
    remaining: int
    resets_at: datetime
    cost_cap: float
    cost_used: float


class SecurityError(Exception):
    """Base class for security errors"""
    def __init__(
        self,
        message: str,
        code: SecurityErrorCode,
        status_code: int = 403
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "error": self.code.value,
            "message": self.message,
            "status_code": self.status_code,
        }


class TokenError(SecurityError):
    """Token-related errors"""
    pass


class ScopeError(SecurityError):
    """Scope/permission errors"""
    def __init__(self, required_scope: str):
        super().__init__(
            f"Insufficient permissions. Required scope: {required_scope}",
            SecurityErrorCode.SCOPE_INSUFFICIENT,
            403
        )


class RateLimitError(SecurityError):
    """Rate limit exceeded"""
    def __init__(self, window: str, reset: int):
        super().__init__(
            f"Rate limit exceeded for {window} window. Resets at {reset}",
            SecurityErrorCode.RATE_LIMIT_EXCEEDED,
            429
        )
        self.window = window
        self.reset = reset


class QuotaError(SecurityError):
    """Quota exceeded"""
    def __init__(self, quota_type: str, resets_at: datetime):
        super().__init__(
            f"{quota_type} quota exceeded. Resets at {resets_at.isoformat()}",
            SecurityErrorCode.QUOTA_EXCEEDED,
            429
        )


@dataclass
class EndpointLimit:
    """Per-endpoint rate limit configuration"""
    endpoint: str
    per_second: int
    per_minute: int
    per_day: int
    burst_capacity: int
    cost_weight: float = 1.0  # Relative cost for quota


# Default endpoint limits
DEFAULT_LIMITS = {
    "/rag/query": EndpointLimit(
        endpoint="/rag/query",
        per_second=10,
        per_minute=100,
        per_day=10000,
        burst_capacity=20,
        cost_weight=10.0
    ),
    "/inference": EndpointLimit(
        endpoint="/inference",
        per_second=20,
        per_minute=500,
        per_day=50000,
        burst_capacity=50,
        cost_weight=5.0
    ),
    "/embed": EndpointLimit(
        endpoint="/embed",
        per_second=50,
        per_minute=1000,
        per_day=100000,
        burst_capacity=100,
        cost_weight=2.0
    ),
    "/search": EndpointLimit(
        endpoint="/search",
        per_second=100,
        per_minute=2000,
        per_day=200000,
        burst_capacity=200,
        cost_weight=1.0
    ),
    "/health": EndpointLimit(
        endpoint="/health",
        per_second=1000,
        per_minute=10000,
        per_day=1000000,
        burst_capacity=2000,
        cost_weight=0.0  # Free
    ),
}


@dataclass
class TenantTier:
    """Tenant tier configuration"""
    name: str
    daily_requests: int
    cost_cap_daily: float
    per_minute_limit: int
    burst_capacity: int
    
    # Provider limits
    provider_calls_per_minute: int
    provider_cost_cap_daily: float


# Tier definitions
TENANT_TIERS = {
    "free": TenantTier(
        name="free",
        daily_requests=100,
        cost_cap_daily=1.0,
        per_minute_limit=10,
        burst_capacity=20,
        provider_calls_per_minute=5,
        provider_cost_cap_daily=0.5
    ),
    "basic": TenantTier(
        name="basic",
        daily_requests=10000,
        cost_cap_daily=100.0,
        per_minute_limit=100,
        burst_capacity=200,
        provider_calls_per_minute=50,
        provider_cost_cap_daily=50.0
    ),
    "pro": TenantTier(
        name="pro",
        daily_requests=100000,
        cost_cap_daily=1000.0,
        per_minute_limit=500,
        burst_capacity=1000,
        provider_calls_per_minute=200,
        provider_cost_cap_daily=500.0
    ),
    "enterprise": TenantTier(
        name="enterprise",
        daily_requests=1000000,
        cost_cap_daily=10000.0,
        per_minute_limit=2000,
        burst_capacity=5000,
        provider_calls_per_minute=1000,
        provider_cost_cap_daily=5000.0
    ),
}

