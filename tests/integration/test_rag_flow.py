"""
Integration tests for end-to-end RAG flow
Uses mocked external services
"""

import pytest
from rag import RAGPipeline, RAGQuery, RAGMode
from providers import ProviderManager
import os


os.environ["ENVIRONMENT"] = "test"
os.environ["USE_MOCK_PROVIDERS"] = "true"


@pytest.fixture
def provider_manager():
    """Create provider manager for tests"""
    return ProviderManager()


@pytest.fixture
def rag_pipeline(provider_manager):
    """Create RAG pipeline for tests"""
    return RAGPipeline(provider_manager=provider_manager)


class TestRAGEndToEnd:
    """End-to-end RAG integration tests"""
    
    @pytest.mark.asyncio
    async def test_standard_rag_flow(self, rag_pipeline):
        """Test complete RAG flow with mocked services"""
        
        # Create query
        query = RAGQuery(
            query="What are the requirements for a valid contract?",
            tenant_id="test_tenant",
            top_k=5,
            mode=RAGMode.STANDARD
        )
        
        # Process through pipeline
        response = await rag_pipeline.process(query)
        
        # Validate response structure
        assert response.answer is not None
        assert len(response.answer) > 0
        
        # Validate citations
        assert isinstance(response.citations, list)
        assert len(response.citations) > 0
        
        # Validate follow-ups
        assert isinstance(response.follow_up_questions, list)
        assert len(response.follow_up_questions) == 2
        
        # Validate metadata
        assert response.model_used is not None
        assert response.retrieval_count > 0
        assert response.total_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_legal_analysis_mode(self, rag_pipeline):
        """Test legal analysis RAG mode"""
        
        query = RAGQuery(
            query="Analyze contract enforceability",
            tenant_id="test_tenant",
            mode=RAGMode.LEGAL_ANALYSIS
        )
        
        response = await rag_pipeline.process(query)
        
        assert response.answer is not None
        assert response.mode == RAGMode.LEGAL_ANALYSIS
    
    @pytest.mark.asyncio
    async def test_conversational_mode(self, rag_pipeline):
        """Test conversational RAG with history"""
        
        query = RAGQuery(
            query="Tell me more about that",
            tenant_id="test_tenant",
            mode=RAGMode.CONVERSATIONAL,
            conversation_history=[
                {"role": "user", "content": "What is consideration?"},
                {"role": "assistant", "content": "Consideration is..."}
            ]
        )
        
        response = await rag_pipeline.process(query)
        
        assert response.answer is not None
        assert response.mode == RAGMode.CONVERSATIONAL
    
    @pytest.mark.asyncio
    async def test_citations_present(self, rag_pipeline):
        """Test that citations are always included"""
        
        query = RAGQuery(
            query="Test query for citations",
            tenant_id="test_tenant"
        )
        
        response = await rag_pipeline.process(query)
        
        # Must have citations
        assert len(response.citations) > 0
        
        # Each citation must have required fields
        for citation in response.citations:
            assert citation.doc_id is not None
            assert citation.title is not None
            assert citation.source is not None
            assert citation.snippet is not None
            assert citation.relevance_score >= 0.0
    
    @pytest.mark.asyncio
    async def test_follow_ups_present(self, rag_pipeline):
        """Test that follow-up questions are always generated"""
        
        query = RAGQuery(
            query="Test query for follow-ups",
            tenant_id="test_tenant"
        )
        
        response = await rag_pipeline.process(query)
        
        # Must have exactly 2 follow-ups
        assert len(response.follow_up_questions) == 2
        
        # Each follow-up must have question text
        for fq in response.follow_up_questions:
            assert fq.question is not None
            assert len(fq.question) > 0
            assert fq.question.endswith("?")
    
    @pytest.mark.asyncio
    async def test_provider_fallback_in_rag(self, rag_pipeline):
        """Test that RAG uses provider manager fallback"""
        
        query = RAGQuery(
            query="Test fallback in RAG",
            tenant_id="test_tenant"
        )
        
        response = await rag_pipeline.process(query)
        
        # Should successfully complete even if one provider fails
        assert response.answer is not None
        assert response.model_used is not None
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, rag_pipeline):
        """Test that metrics are tracked"""
        
        query = RAGQuery(
            query="Test metrics",
            tenant_id="test_tenant"
        )
        
        response = await rag_pipeline.process(query)
        
        # Timing metrics must be present
        assert response.retrieval_time_ms >= 0
        assert response.generation_time_ms >= 0
        assert response.total_time_ms >= 0
        
        # Total should be sum of parts (approximately)
        assert response.total_time_ms >= response.retrieval_time_ms
        assert response.total_time_ms >= response.generation_time_ms


class TestPromptTemplates:
    """Test prompt template system"""
    
    def test_all_templates_loadable(self):
        """Test all built-in templates load correctly"""
        from rag.prompt_manager import PromptManager
        
        pm = PromptManager()
        
        # Should have all 6 default templates
        templates = pm.list_templates()
        assert len(templates) >= 6
        
        expected_templates = [
            "standard",
            "legal_analysis",
            "conversational",
            "summarization",
            "comparison",
            "follow_up"
        ]
        
        for template_name in expected_templates:
            template = pm.get_template(template_name)
            assert template is not None
            assert template.system_prompt is not None
            assert template.user_prompt_template is not None
    
    def test_template_formatting(self):
        """Test template variable substitution"""
        from rag.prompt_manager import PromptManager
        
        pm = PromptManager()
        
        system, user = pm.format_prompt(
            template_name="standard",
            query="Test query",
            context="Test context"
        )
        
        assert "Test query" in user
        assert "Test context" in user
        assert system is not None


class TestContextBuilder:
    """Test context window building"""
    
    def test_context_building(self):
        """Test context assembly with token limits"""
        from rag.context_builder import ContextBuilder
        from rag.models import RetrievedDocument
        
        builder = ContextBuilder()
        
        docs = [
            RetrievedDocument(
                doc_id=f"doc_{i}",
                content=f"Document {i} content " * 100,
                title=f"Doc {i}",
                source="Test",
                score=0.9 - (i * 0.1),
                rank=i
            )
            for i in range(5)
        ]
        
        context = builder.build_context(docs, max_tokens=1000)
        
        assert context.formatted_context is not None
        assert context.token_count <= 1000
        assert len(context.documents) > 0
    
    def test_snippet_extraction(self):
        """Test relevant snippet extraction"""
        from rag.context_builder import ContextBuilder
        
        builder = ContextBuilder()
        
        content = "This is a long document about contract law. " * 50
        snippet = builder.extract_snippet(
            content=content,
            query="contract law",
            snippet_length=100
        )
        
        assert len(snippet) <= 150  # With ellipsis
        assert "contract law" in snippet.lower()

