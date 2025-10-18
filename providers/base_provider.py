"""
Base Provider Abstract Class
All model providers must inherit from this
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ProviderResponse:
    """Standardized response from any provider"""
    answer: str
    provider_name: str
    model_name: str
    tokens_used: Optional[int] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EmbeddingResponse:
    """Standardized embedding response"""
    embeddings: List[List[float]]
    provider_name: str
    model_name: str
    dimension: int
    metadata: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """Abstract base class for all AI model providers"""
    
    def __init__(self, api_key: str, model_name: str, config: Dict[str, Any] = None):
        self.api_key = api_key
        self.model_name = model_name
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30)
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'InLegalBERT', 'DeepSeek')"""
        pass
    
    @abstractmethod
    async def inference(
        self,
        query: str,
        context: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> ProviderResponse:
        """
        Run inference on the model
        
        Args:
            query: The user query
            context: Optional context for the query
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            ProviderResponse with standardized output
        """
        pass
    
    @abstractmethod
    async def generate_embeddings(
        self,
        texts: List[str]
    ) -> EmbeddingResponse:
        """
        Generate embeddings for given texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            EmbeddingResponse with embeddings
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is available
        
        Returns:
            True if provider is healthy, False otherwise
        """
        pass

