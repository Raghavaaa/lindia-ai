"""
RAG Pipeline - Main orchestrator
Ties together search, context building, prompt formatting, and generation
"""

import time
import json
import logging
from typing import Optional
from .models import (
    RAGQuery,
    RAGResponse,
    RAGMode,
    RetrievedDocument,
    Citation,
    FollowUpQuestion
)
from .prompt_manager import PromptManager
from .context_builder import ContextBuilder

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    End-to-end RAG pipeline:
    1. Semantic search for relevant documents
    2. Build context window
    3. Apply prompt templates
    4. Call LLM provider
    5. Extract citations and generate follow-ups
    """
    
    def __init__(
        self,
        provider_manager,  # From providers module
        search_service=None,  # From vector_store module (to be implemented)
    ):
        self.provider_manager = provider_manager
        self.search_service = search_service
        
        # Initialize components
        self.prompt_manager = PromptManager()
        self.context_builder = ContextBuilder()
        
        logger.info("RAG Pipeline initialized")
    
    async def process(self, query: RAGQuery) -> RAGResponse:
        """
        Process RAG query end-to-end
        
        Args:
            query: RAGQuery with user question and parameters
            
        Returns:
            RAGResponse with answer, citations, and follow-ups
        """
        start_time = time.time()
        
        try:
            # Step 1: Semantic search
            logger.info(f"Starting RAG pipeline for query: {query.query[:100]}...")
            retrieved_docs, retrieval_time = await self._retrieve_documents(query)
            
            # Step 2: Build context window
            context_window = self.context_builder.build_context(
                documents=retrieved_docs,
                max_tokens=query.max_context_tokens,
                include_metadata=query.include_metadata
            )
            
            # Step 3: Format prompts
            system_prompt, user_prompt = self._format_prompts(
                query=query,
                context=context_window.formatted_context
            )
            
            # Step 4: Generate answer
            answer, generation_time = await self._generate_answer(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                query=query
            )
            
            # Step 5: Extract citations
            citations = self._extract_citations(
                answer=answer,
                context_window=context_window,
                query=query
            )
            
            # Step 6: Generate follow-up questions
            follow_ups = await self._generate_follow_ups(
                query=query,
                answer=answer,
                context=context_window.formatted_context
            )
            
            # Build response
            total_time = (time.time() - start_time) * 1000
            
            response = RAGResponse(
                answer=answer,
                citations=citations,
                follow_up_questions=follow_ups,
                model_used=f"{self.provider_manager.providers[0].provider_name if self.provider_manager.providers else 'unknown'}",
                retrieval_count=len(retrieved_docs),
                context_tokens=context_window.token_count,
                generation_tokens=len(answer.split()),  # Rough estimate
                retrieval_time_ms=retrieval_time,
                generation_time_ms=generation_time,
                total_time_ms=total_time,
                mode=query.mode,
                request_id=query.request_id
            )
            
            logger.info(
                f"RAG pipeline completed in {total_time:.2f}ms: "
                f"retrieved {len(retrieved_docs)} docs, "
                f"{len(citations)} citations, "
                f"{len(follow_ups)} follow-ups"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}", exc_info=True)
            raise
    
    async def _retrieve_documents(
        self,
        query: RAGQuery
    ) -> tuple[list[RetrievedDocument], float]:
        """
        Step 1: Retrieve relevant documents via semantic search
        """
        start_time = time.time()
        
        if not self.search_service:
            # Placeholder: Return mock documents
            logger.warning("No search service configured, using placeholder documents")
            mock_docs = self._get_mock_documents(query)
            return mock_docs, (time.time() - start_time) * 1000
        
        try:
            # TODO: Call actual vector search service
            # results = await self.search_service.search(
            #     query_vector=await self._embed_query(query.query),
            #     top_k=query.top_k,
            #     tenant_id=query.tenant_id,
            #     filters=query.filters,
            #     score_threshold=query.score_threshold
            # )
            
            # For now, use mock data
            documents = self._get_mock_documents(query)
            
            retrieval_time = (time.time() - start_time) * 1000
            logger.info(f"Retrieved {len(documents)} documents in {retrieval_time:.2f}ms")
            
            return documents, retrieval_time
            
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            raise
    
    def _format_prompts(
        self,
        query: RAGQuery,
        context: str
    ) -> tuple[str, str]:
        """
        Step 3: Format prompts using templates
        """
        # Determine template name based on mode
        template_name = query.prompt_template or query.mode.value
        
        # Format conversation history if present
        conversation_history = None
        if query.conversation_history:
            conversation_history = self.context_builder.format_conversation_history(
                query.conversation_history
            )
        
        # Format prompts
        system_prompt, user_prompt = self.prompt_manager.format_prompt(
            template_name=template_name,
            query=query.query,
            context=context,
            conversation_history=conversation_history
        )
        
        # Override system prompt if provided
        if query.system_prompt:
            system_prompt = query.system_prompt
        
        logger.debug(f"Formatted prompts using template: {template_name}")
        
        return system_prompt, user_prompt
    
    async def _generate_answer(
        self,
        system_prompt: str,
        user_prompt: str,
        query: RAGQuery
    ) -> tuple[str, float]:
        """
        Step 4: Generate answer using LLM provider
        """
        start_time = time.time()
        
        try:
            # Combine system and user prompts
            full_context = f"{system_prompt}\n\n{user_prompt}"
            
            # Call provider manager
            response = await self.provider_manager.inference(
                query=user_prompt,
                context=system_prompt,
                max_tokens=query.max_tokens,
                temperature=query.temperature
            )
            
            answer = response.answer
            generation_time = (time.time() - start_time) * 1000
            
            logger.info(f"Generated answer in {generation_time:.2f}ms")
            
            return answer, generation_time
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise
    
    def _extract_citations(
        self,
        answer: str,
        context_window,
        query: RAGQuery
    ) -> list[Citation]:
        """
        Step 5: Extract and format citations
        """
        citations = []
        
        # Get documents from context
        for i, doc in enumerate(context_window.documents, 1):
            # Check if document is referenced in answer
            if self._is_document_cited(answer, i):
                # Extract relevant snippet
                snippet = self.context_builder.extract_snippet(
                    content=doc.content,
                    query=query.query,
                    snippet_length=200
                )
                
                citation = Citation(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    source=doc.source,
                    url=doc.url,
                    snippet=snippet,
                    relevance_score=doc.score,
                    page_number=doc.metadata.get("page_number"),
                    section=doc.metadata.get("section")
                )
                citations.append(citation)
        
        # If no explicit citations found, include top documents anyway
        if not citations and context_window.documents:
            for doc in context_window.documents[:3]:  # Top 3
                snippet = self.context_builder.extract_snippet(
                    content=doc.content,
                    query=query.query
                )
                citations.append(doc.to_citation(snippet=snippet))
        
        logger.info(f"Extracted {len(citations)} citations")
        
        return citations
    
    def _is_document_cited(self, answer: str, doc_number: int) -> bool:
        """Check if document number is cited in answer"""
        # Look for citation markers like [1], [2], etc.
        return f"[{doc_number}]" in answer or f"Document {doc_number}" in answer
    
    async def _generate_follow_ups(
        self,
        query: RAGQuery,
        answer: str,
        context: str
    ) -> list[FollowUpQuestion]:
        """
        Step 6: Generate follow-up questions
        """
        try:
            # Format prompt for follow-up generation
            system_prompt, user_prompt = self.prompt_manager.format_prompt(
                template_name="follow_up",
                query=query.query,
                answer=answer,
                context=context[:1000]  # Truncate context for efficiency
            )
            
            # Generate follow-ups
            response = await self.provider_manager.inference(
                query=user_prompt,
                context=system_prompt,
                max_tokens=200,
                temperature=0.8  # Higher temp for creativity
            )
            
            # Parse JSON response
            follow_ups = self._parse_follow_ups(response.answer)
            
            logger.info(f"Generated {len(follow_ups)} follow-up questions")
            
            return follow_ups
            
        except Exception as e:
            logger.warning(f"Follow-up generation failed: {e}")
            # Return default follow-ups
            return self._get_default_follow_ups(query.query)
    
    def _parse_follow_ups(self, response_text: str) -> list[FollowUpQuestion]:
        """Parse follow-up questions from LLM response"""
        try:
            # Try to parse as JSON
            if "[" in response_text and "]" in response_text:
                start = response_text.index("[")
                end = response_text.rindex("]") + 1
                json_str = response_text[start:end]
                follow_ups_data = json.loads(json_str)
                
                return [
                    FollowUpQuestion(
                        question=item["question"],
                        reasoning=item.get("reasoning", ""),
                        priority=item.get("priority", 1)
                    )
                    for item in follow_ups_data[:2]  # Max 2 questions
                ]
        except Exception as e:
            logger.warning(f"Failed to parse follow-ups as JSON: {e}")
        
        # Fallback: Extract questions from text
        return self._extract_questions_from_text(response_text)
    
    def _extract_questions_from_text(self, text: str) -> list[FollowUpQuestion]:
        """Extract questions from free text"""
        questions = []
        lines = text.split("\n")
        
        for line in lines:
            line = line.strip()
            if line.endswith("?") and len(line) > 10:
                # Remove numbering or bullets
                clean_question = line.lstrip("0123456789.-• ")
                questions.append(FollowUpQuestion(
                    question=clean_question,
                    reasoning="Extracted from response",
                    priority=len(questions) + 1
                ))
                
                if len(questions) >= 2:
                    break
        
        return questions
    
    def _get_default_follow_ups(self, query: str) -> list[FollowUpQuestion]:
        """Generate default follow-up questions"""
        return [
            FollowUpQuestion(
                question=f"Can you provide more details about {query}?",
                reasoning="Request for elaboration",
                priority=1
            ),
            FollowUpQuestion(
                question="What are the practical implications of this?",
                reasoning="Application-focused question",
                priority=2
            )
        ]
    
    def _get_mock_documents(self, query: RAGQuery) -> list[RetrievedDocument]:
        """Mock documents for testing (when search service not available)"""
        return [
            RetrievedDocument(
                doc_id="doc_1",
                content=f"This is a relevant document about {query.query}. It contains important information that answers the user's question with specific details and citations.",
                title="Legal Document 1",
                source="Indian Contract Act, 1872",
                url="https://example.com/doc1",
                score=0.95,
                rank=1,
                metadata={"section": "Section 10", "page_number": 5}
            ),
            RetrievedDocument(
                doc_id="doc_2",
                content=f"Additional context about {query.query} with supporting evidence and case law references.",
                title="Case Law Reference",
                source="Supreme Court Judgment",
                url="https://example.com/doc2",
                score=0.87,
                rank=2,
                metadata={"case_number": "123/2020", "date": "2020-05-15"}
            ),
        ]

