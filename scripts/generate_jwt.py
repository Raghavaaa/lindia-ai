#!/usr/bin/env python3
"""
Script to generate JWT tokens for testing AI Engine endpoints.
Usage: python scripts/generate_jwt.py --tenant-id test_tenant --secret your-secret
"""

import argparse
import jwt
from datetime import datetime, timedelta


def generate_jwt_token(tenant_id: str, secret: str, expiry_minutes: int = 60) -> str:
    """
    Generate a JWT token for AI Engine authentication.
    
    Args:
        tenant_id: Tenant identifier
        secret: JWT secret (INTERNAL_JWT_SECRET)
        expiry_minutes: Token expiry time in minutes
        
    Returns:
        JWT token string
    """
    payload = {
        "tenant_id": tenant_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=expiry_minutes),
    }
    
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


def main():
    parser = argparse.ArgumentParser(
        description="Generate JWT token for AI Engine testing"
    )
    parser.add_argument(
        "--tenant-id",
        required=True,
        help="Tenant ID for the token"
    )
    parser.add_argument(
        "--secret",
        required=True,
        help="JWT secret (INTERNAL_JWT_SECRET value)"
    )
    parser.add_argument(
        "--expiry",
        type=int,
        default=60,
        help="Token expiry time in minutes (default: 60)"
    )
    
    args = parser.parse_args()
    
    token = generate_jwt_token(args.tenant_id, args.secret, args.expiry)
    
    print("\n" + "="*80)
    print("JWT Token Generated Successfully")
    print("="*80)
    print(f"\nTenant ID: {args.tenant_id}")
    print(f"Expiry: {args.expiry} minutes")
    print(f"\nToken:\n{token}")
    print("\n" + "="*80)
    print("\nUsage Example:")
    print(f'\ncurl -X POST http://ai-engine.railway.internal/inference \\')
    print(f'  -H "Authorization: Bearer {token}" \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -d \'{{"query":"test","context":"test","tenant_id":"{args.tenant_id}"}}\'')
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()

