"""
Authentication module for internal JWT validation.
"""
import jwt
from fastapi import Request, HTTPException, status
from datetime import datetime

from core.config import settings
from core.logger import logger


async def verify_internal_jwt(request: Request) -> dict:
    """
    Verify internal JWT token from request headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        logger.warning("Missing Authorization header", extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "path": request.url.path,
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized_missing_token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check Bearer scheme
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized_invalid_token_format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    try:
        # Decode and verify JWT
        payload = jwt.decode(
            token,
            settings.INTERNAL_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Store tenant_id in request state for rate limiting
        request.state.tenant_id = payload.get("tenant_id", "default")
        
        logger.debug(
            "JWT verified successfully",
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "tenant_id": request.state.tenant_id,
            }
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token", extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized_token_expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}", extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized_invalid_token",
            headers={"WWW-Authenticate": "Bearer"},
        )

