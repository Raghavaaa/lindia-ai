"""
Configuration module for AI Engine Service.
Loads environment variables and provides application settings.
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application configuration
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    PORT: int = 8080
    LOG_LEVEL: str = "INFO"
    
    # Authentication
    INTERNAL_JWT_SECRET: str  # Required - no default
    JWT_ALGORITHM: str = "HS256"
    
    # AI Model configuration
    PRIMARY_MODEL_KEY: str  # Required - no default
    SECONDARY_MODEL_KEY: str  # Required - no default
    
    # Provider configuration - can be changed via env var
    PRIMARY_PROVIDER: str = "INLEGALBERT"
    FALLBACK_PROVIDERS: str = "DeepSeek,Grok"  # Comma-separated
    
    @property
    def fallback_provider_list(self) -> List[str]:
        """Parse fallback providers into a list."""
        return [p.strip() for p in self.FALLBACK_PROVIDERS.split(",") if p.strip()]
    
    # Vector Store configuration
    VECTOR_STORE_URL: str  # Required - no default
    VECTOR_STORE_TIMEOUT: int = 10
    
    # Request constraints
    REQUEST_TIMEOUT_SECONDS: int = 30
    MAX_PAYLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    CONCURRENCY_LIMIT_PER_WORKER: int = 10
    
    # Rate limiting and quotas
    RATE_LIMIT_PER_MINUTE: int = 100  # Per tenant
    DAILY_QUOTA_LIMIT: int = 10000  # Per tenant
    
    # Quota storage (optional - falls back to in-memory)
    QUOTA_STORAGE_URL: str = ""  # Object storage URL for persistence
    
    # Smoke tests
    RUN_SMOKE_TESTS_ON_DEPLOY: bool = True
    FAIL_DEPLOY_ON_SMOKE_TEST_FAILURE: bool = True
    
    # Cost estimation (example rates per 1k tokens)
    COST_PER_1K_TOKENS_INLEGALBERT: float = 0.0002
    COST_PER_1K_TOKENS_DEEPSEEK: float = 0.00014
    COST_PER_1K_TOKENS_GROK: float = 0.0005
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create a global settings instance
settings = Settings()

