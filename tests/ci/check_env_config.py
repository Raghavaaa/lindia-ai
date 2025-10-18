"""
CI: Validate environment configuration
Checks required env vars exist without exposing values
"""

import sys
from typing import List, Dict


# Required environment variables for deployment
REQUIRED_ENV_VARS = {
    # Service basics
    "PORT": "Service port number",
    "ENVIRONMENT": "Deployment environment (production/staging)",
    "SERVICE_NAME": "Service identifier",
    
    # Provider configuration
    "PROVIDER_ORDER": "Comma-separated provider priority",
    
    # Optional but recommended for production
    "LOG_LEVEL": "Logging level",
    "METRICS_PORT": "Metrics endpoint port",
}

# Secrets that should exist in Railway (checked without exposing)
REQUIRED_SECRETS = [
    "INLEGALBERT_API_KEY",
    "DEEPSEEK_API_KEY",
    "GROK_API_KEY",
]

# Optional env vars
OPTIONAL_ENV_VARS = {
    "QUEUE_BACKEND": "Queue backend (memory/redis)",
    "REDIS_URL": "Redis connection string",
    "VECTOR_INDEX_TYPE": "FAISS index type",
    "RAG_MAX_CONTEXT_TOKENS": "Max context tokens for RAG",
}


def check_required_env_vars() -> Dict[str, bool]:
    """Check that required env var keys are defined"""
    import os
    
    results = {}
    missing = []
    
    print("Checking required environment variables...")
    print("=" * 60)
    
    for var_name, description in REQUIRED_ENV_VARS.items():
        value = os.getenv(var_name)
        is_present = value is not None and value != ""
        results[var_name] = is_present
        
        status = "✓" if is_present else "✗"
        # Mask actual value for security
        display_value = "***SET***" if is_present else "MISSING"
        
        print(f"{status} {var_name:30} {display_value:15} ({description})")
        
        if not is_present:
            missing.append(var_name)
    
    print("=" * 60)
    
    if missing:
        print(f"\n❌ Missing {len(missing)} required environment variables:")
        for var in missing:
            print(f"   - {var}: {REQUIRED_ENV_VARS[var]}")
        print("\nPlease set these in Railway environment variables.")
        return False
    
    print(f"\n✅ All {len(REQUIRED_ENV_VARS)} required environment variables are set")
    return True


def check_secrets_exist() -> bool:
    """Check that secrets are present (without exposing values)"""
    import os
    
    print("\nChecking required secrets...")
    print("=" * 60)
    
    missing = []
    
    for secret_name in REQUIRED_SECRETS:
        value = os.getenv(secret_name)
        is_present = value is not None and value != ""
        
        status = "✓" if is_present else "⚠"
        display = "***SET***" if is_present else "NOT SET (OK for CI)"
        
        print(f"{status} {secret_name:30} {display}")
        
        # Secrets can be missing in CI (added in Railway)
        if not is_present:
            missing.append(secret_name)
    
    print("=" * 60)
    
    if missing:
        print(f"\n⚠️  {len(missing)} secrets not set (expected in CI):")
        for secret in missing:
            print(f"   - {secret}")
        print("\n💡 These must be set in Railway environment variables before deployment")
    else:
        print(f"\n✅ All {len(REQUIRED_SECRETS)} secrets are configured")
    
    # Don't fail CI if secrets missing (they're added in Railway)
    return True


def validate_config_format():
    """Validate configuration format"""
    import os
    
    print("\nValidating configuration format...")
    print("=" * 60)
    
    # Check PROVIDER_ORDER format
    provider_order = os.getenv("PROVIDER_ORDER", "inlegalbert,deepseek,grok")
    providers = [p.strip() for p in provider_order.split(",")]
    
    print(f"✓ Provider order: {', '.join(providers)}")
    
    # Check PORT is numeric
    port = os.getenv("PORT", "8080")
    try:
        int(port)
        print(f"✓ PORT is valid: {port}")
    except ValueError:
        print(f"✗ PORT is invalid: {port}")
        return False
    
    print("=" * 60)
    print("✅ Configuration format is valid")
    return True


def main():
    """Main validation function"""
    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║     Environment Configuration Validation              ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()
    
    # Run all checks
    env_ok = check_required_env_vars()
    secrets_ok = check_secrets_exist()
    format_ok = validate_config_format()
    
    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║                 Validation Summary                     ║")
    print("╠════════════════════════════════════════════════════════╣")
    
    if env_ok and secrets_ok and format_ok:
        print("║  ✅ All checks PASSED                                 ║")
        print("║  ✅ Configuration is valid                            ║")
        print("║  ✅ Ready for deployment                              ║")
        print("╚════════════════════════════════════════════════════════╝")
        return 0
    else:
        print("║  ❌ Some checks FAILED                                ║")
        print("║  ❌ Fix configuration before deploying                ║")
        print("╚════════════════════════════════════════════════════════╝")
        return 1


if __name__ == "__main__":
    sys.exit(main())

