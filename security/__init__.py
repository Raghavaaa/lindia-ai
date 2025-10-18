"""
Security & Access Control System
JWT authentication, RBAC, rate limiting, and quota management
"""

from .models import TokenClaims, Scope, SecurityError
from .jwt_handler import JWTHandler, generate_service_token
from .auth_middleware import AuthenticationMiddleware, require_scope
from .rate_limiter import RateLimiter, RateLimitExceeded
from .quota_manager import QuotaManager, QuotaExceeded
from .revocation import RevocationManager
from .secret_manager import SecretManager

__all__ = [
    "TokenClaims",
    "Scope",
    "SecurityError",
    "JWTHandler",
    "generate_service_token",
    "AuthenticationMiddleware",
    "require_scope",
    "RateLimiter",
    "RateLimitExceeded",
    "QuotaManager",
    "QuotaExceeded",
    "RevocationManager",
    "SecretManager",
]

