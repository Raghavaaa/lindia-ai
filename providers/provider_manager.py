"""
Provider Manager
Handles multiple model providers with automatic fallback
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base_provider import BaseProvider, ProviderResponse, EmbeddingResponse
from .inlegal_bert_provider import InLegalBERTProvider
from .deepseek_provider import DeepSeekProvider
from .grok_provider import GrokProvider


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Manages multiple AI model providers with automatic fallback
    Configurable from environment variables
    """
    
    # Registry of available providers
    PROVIDER_REGISTRY = {
        "inlegalbert": InLegalBERTProvider,
        "deepseek": DeepSeekProvider,
        "grok": GrokProvider,
    }
    
    def __init__(self):
        """Initialize provider manager from environment variables"""
        
        # Get provider order from env (comma-separated)
        provider_order = os.getenv("PROVIDER_ORDER", "inlegalbert,deepseek,grok")
        self.provider_names = [p.strip().lower() for p in provider_order.split(",")]
        
        # Initialize providers list and stats first
        self.providers: List[BaseProvider] = []
        
        # Track usage statistics
        self.stats = {
            "total_requests": 0,
            "provider_usage": {},
            "fallback_count": 0
        }
        
        # Now initialize providers
        self._initialize_providers()
        
        logger.info(f"ProviderManager initialized with order: {self.provider_names}")
    
    def _initialize_providers(self):
        """Initialize all configured providers"""
        
        for provider_name in self.provider_names:
            if provider_name not in self.PROVIDER_REGISTRY:
                logger.warning(f"Unknown provider: {provider_name}, skipping")
                continue
            
            # Get provider-specific configuration
            api_key = os.getenv(f"{provider_name.upper()}_API_KEY", "")
            model_name = os.getenv(f"{provider_name.upper()}_MODEL", f"{provider_name}-default")
            timeout = int(os.getenv(f"{provider_name.upper()}_TIMEOUT", "30"))
            
            # Provider-specific config
            config = {
                "timeout": timeout,
                "api_url": os.getenv(f"{provider_name.upper()}_API_URL", ""),
                "health_url": os.getenv(f"{provider_name.upper()}_HEALTH_URL", ""),
            }
            
            # Initialize provider
            provider_class = self.PROVIDER_REGISTRY[provider_name]
            provider = provider_class(
                api_key=api_key,
                model_name=model_name,
                config=config
            )
            
            self.providers.append(provider)
            self.stats["provider_usage"][provider_name] = 0
            
            logger.info(f"Initialized provider: {provider_name} with model: {model_name}")
    
    async def inference(
        self,
        query: str,
        context: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> ProviderResponse:
        """
        Run inference with automatic fallback
        
        Tries primary provider first, falls back to next if it fails
        """
        
        self.stats["total_requests"] += 1
        
        last_error = None
        for i, provider in enumerate(self.providers):
            try:
                logger.info(f"Attempting inference with provider: {provider.provider_name}")
                
                # Run inference
                response = await provider.inference(
                    query=query,
                    context=context,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Track success
                self.stats["provider_usage"][provider.provider_name.lower()] += 1
                
                if i > 0:
                    # Fallback occurred
                    self.stats["fallback_count"] += 1
                    logger.warning(f"Fallback to {provider.provider_name} (attempt {i + 1})")
                else:
                    logger.info(f"Primary provider {provider.provider_name} succeeded")
                
                # Add fallback metadata
                if response.metadata is None:
                    response.metadata = {}
                response.metadata["fallback_occurred"] = i > 0
                response.metadata["attempt_number"] = i + 1
                response.metadata["timestamp"] = datetime.now().isoformat()
                
                return response
                
            except Exception as e:
                last_error = e
                logger.error(f"Provider {provider.provider_name} failed: {str(e)}")
                
                # Try next provider
                if i < len(self.providers) - 1:
                    logger.info(f"Trying next provider in fallback chain...")
                    continue
                else:
                    # All providers failed
                    logger.error("All providers failed")
                    raise Exception(f"All providers failed. Last error: {str(last_error)}")
        
        # Should not reach here, but for safety
        raise Exception("No providers available")
    
    async def generate_embeddings(
        self,
        texts: List[str]
    ) -> EmbeddingResponse:
        """
        Generate embeddings with automatic fallback
        """
        
        last_error = None
        for i, provider in enumerate(self.providers):
            try:
                logger.info(f"Attempting embeddings with provider: {provider.provider_name}")
                
                # Generate embeddings
                response = await provider.generate_embeddings(texts)
                
                if i > 0:
                    logger.warning(f"Fallback to {provider.provider_name} for embeddings")
                else:
                    logger.info(f"Primary provider {provider.provider_name} succeeded for embeddings")
                
                # Add metadata
                if response.metadata is None:
                    response.metadata = {}
                response.metadata["fallback_occurred"] = i > 0
                response.metadata["attempt_number"] = i + 1
                response.metadata["timestamp"] = datetime.now().isoformat()
                
                return response
                
            except Exception as e:
                last_error = e
                logger.error(f"Provider {provider.provider_name} embedding failed: {str(e)}")
                
                if i < len(self.providers) - 1:
                    continue
                else:
                    raise Exception(f"All providers failed for embeddings. Last error: {str(last_error)}")
        
        raise Exception("No providers available for embeddings")
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Check health of all providers"""
        
        health_status = {}
        
        for provider in self.providers:
            try:
                is_healthy = await provider.health_check()
                health_status[provider.provider_name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "model": provider.model_name
                }
            except Exception as e:
                health_status[provider.provider_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            **self.stats,
            "active_providers": [p.provider_name for p in self.providers],
            "provider_order": self.provider_names
        }

