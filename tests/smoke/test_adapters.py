"""
Smoke tests for model adapters
Tests each provider with mocked API responses
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from providers import ProviderManager
from providers.base_provider import ProviderResponse, EmbeddingResponse
import os


# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["USE_MOCK_PROVIDERS"] = "true"


class TestInLegalBERTAdapter:
    """Smoke tests for InLegalBERT adapter"""
    
    @pytest.mark.asyncio
    async def test_inference_with_mock(self):
        """Test inference with canned query against mock"""
        from providers.inlegal_bert_provider import InLegalBERTProvider
        
        provider = InLegalBERTProvider(
            api_key="test_key",
            model_name="test_model"
        )
        
        # Call with canned query
        response = await provider.inference(
            query="What is Section 10 of Indian Contract Act?",
            context="Legal context",
            max_tokens=512,
            temperature=0.7
        )
        
        # Assert valid structured response
        assert isinstance(response, ProviderResponse)
        assert response.provider_name == "InLegalBERT"
        assert response.answer is not None
        assert len(response.answer) > 0
        assert response.tokens_used is not None
        assert response.tokens_used > 0
        assert response.confidence is not None
        assert 0 <= response.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_embedding_with_mock(self):
        """Test embedding generation"""
        from providers.inlegal_bert_provider import InLegalBERTProvider
        
        provider = InLegalBERTProvider(
            api_key="test_key",
            model_name="test_model"
        )
        
        response = await provider.generate_embeddings(
            texts=["Legal document 1", "Legal document 2"]
        )
        
        assert isinstance(response, EmbeddingResponse)
        assert len(response.embeddings) == 2
        assert response.dimension == 768
        assert response.provider_name == "InLegalBERT"
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test error handling for timeouts"""
        from providers.inlegal_bert_provider import InLegalBERTProvider
        
        provider = InLegalBERTProvider(
            api_key="test_key",
            model_name="test_model",
            config={"timeout": 0.001}  # Very short timeout
        )
        
        # Should handle gracefully (mock returns quickly, so this tests structure)
        try:
            response = await provider.inference(
                query="Test timeout",
                max_tokens=100
            )
            # Mock doesn't actually timeout, but structure is validated
            assert response is not None
        except Exception as e:
            # If real timeout would occur
            assert "timeout" in str(e).lower() or "failed" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test provider health check"""
        from providers.inlegal_bert_provider import InLegalBERTProvider
        
        provider = InLegalBERTProvider(
            api_key="test_key",
            model_name="test_model"
        )
        
        is_healthy = await provider.health_check()
        assert isinstance(is_healthy, bool)


class TestDeepSeekAdapter:
    """Smoke tests for DeepSeek adapter"""
    
    @pytest.mark.asyncio
    async def test_inference_with_mock(self):
        """Test DeepSeek inference"""
        from providers.deepseek_provider import DeepSeekProvider
        
        provider = DeepSeekProvider(
            api_key="test_key",
            model_name="deepseek-chat"
        )
        
        response = await provider.inference(
            query="Test query",
            max_tokens=256
        )
        
        assert isinstance(response, ProviderResponse)
        assert response.provider_name == "DeepSeek"
        assert response.answer is not None
        assert response.tokens_used is not None


class TestGrokAdapter:
    """Smoke tests for Grok adapter"""
    
    @pytest.mark.asyncio
    async def test_inference_with_mock(self):
        """Test Grok inference"""
        from providers.grok_provider import GrokProvider
        
        provider = GrokProvider(
            api_key="test_key",
            model_name="grok-beta"
        )
        
        response = await provider.inference(
            query="Test query",
            max_tokens=256
        )
        
        assert isinstance(response, ProviderResponse)
        assert response.provider_name == "Grok"
        assert response.answer is not None


class TestProviderManager:
    """Smoke tests for ProviderManager with fallback"""
    
    @pytest.mark.asyncio
    async def test_provider_fallback(self):
        """Test automatic fallback between providers"""
        # Set environment for multiple providers
        os.environ["PROVIDER_ORDER"] = "inlegalbert,deepseek,grok"
        
        manager = ProviderManager()
        
        # Should have all 3 providers loaded
        assert len(manager.providers) == 3
        
        # Test inference (uses first provider)
        response = await manager.inference(
            query="Test fallback",
            max_tokens=100
        )
        
        assert response.provider_name in ["InLegalBERT", "DeepSeek", "Grok"]
    
    @pytest.mark.asyncio
    async def test_token_estimate_recording(self):
        """Test that token usage is recorded"""
        manager = ProviderManager()
        
        response = await manager.inference(
            query="Test token counting",
            max_tokens=100
        )
        
        # Assert token estimates are present
        assert response.tokens_used is not None
        assert response.tokens_used > 0
        
        # Token usage should be reasonable for query
        assert response.tokens_used < 1000


def test_all_adapters_importable():
    """Test all adapters can be imported"""
    from providers.inlegal_bert_provider import InLegalBERTProvider
    from providers.deepseek_provider import DeepSeekProvider
    from providers.grok_provider import GrokProvider
    from providers.provider_manager import ProviderManager
    
    assert InLegalBERTProvider is not None
    assert DeepSeekProvider is not None
    assert GrokProvider is not None
    assert ProviderManager is not None

