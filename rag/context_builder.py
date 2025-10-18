"""
Context Window Builder
Constructs optimal context from retrieved documents
"""

from typing import List, Optional
from .models import RetrievedDocument, ContextWindow
import logging
import os

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds context windows from retrieved documents
    Handles token limits, formatting, and optimization
    """
    
    def __init__(self):
        # Configuration from environment
        self.max_context_tokens = int(os.getenv("RAG_MAX_CONTEXT_TOKENS", "3000"))
        self.chars_per_token = float(os.getenv("RAG_CHARS_PER_TOKEN", "4.0"))
        self.include_metadata = bool(os.getenv("RAG_INCLUDE_METADATA", "true").lower() == "true")
        
        # Context formatting
        self.doc_separator = "\n\n" + "=" * 50 + "\n\n"
        self.truncation_marker = "\n[... content truncated ...]\n"
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length"""
        return int(len(text) / self.chars_per_token)
    
    def build_context(
        self,
        documents: List[RetrievedDocument],
        max_tokens: Optional[int] = None,
        include_metadata: Optional[bool] = None
    ) -> ContextWindow:
        """
        Build context window from documents
        
        Args:
            documents: Retrieved documents to include
            max_tokens: Override max context tokens
            include_metadata: Override metadata inclusion
            
        Returns:
            ContextWindow with formatted context
        """
        max_tokens = max_tokens or self.max_context_tokens
        include_metadata = include_metadata if include_metadata is not None else self.include_metadata
        
        context_window = ContextWindow()
        formatted_parts = []
        current_tokens = 0
        
        for i, doc in enumerate(documents, 1):
            # Format document
            doc_text = self._format_document(doc, i, include_metadata)
            doc_tokens = self.estimate_tokens(doc_text)
            
            # Check if adding this doc would exceed limit
            if current_tokens + doc_tokens > max_tokens:
                if not formatted_parts:
                    # First document is too large, truncate it
                    doc_text = self._truncate_document(doc_text, max_tokens)
                    formatted_parts.append(doc_text)
                    current_tokens = max_tokens
                    context_window.truncated = True
                break
            
            # Add document to context
            formatted_parts.append(doc_text)
            context_window.add_document(doc)
            current_tokens += doc_tokens
        
        # Combine all parts
        context_window.formatted_context = self.doc_separator.join(formatted_parts)
        context_window.token_count = current_tokens
        
        logger.info(
            f"Built context with {len(context_window.documents)} documents, "
            f"~{current_tokens} tokens (max: {max_tokens})"
        )
        
        return context_window
    
    def _format_document(
        self,
        doc: RetrievedDocument,
        doc_number: int,
        include_metadata: bool
    ) -> str:
        """Format a single document for context"""
        parts = [f"[Document {doc_number}]"]
        
        if include_metadata:
            # Add metadata header
            metadata_parts = [
                f"Title: {doc.title}",
                f"Source: {doc.source}",
            ]
            
            if doc.url:
                metadata_parts.append(f"URL: {doc.url}")
            
            if doc.metadata.get("date"):
                metadata_parts.append(f"Date: {doc.metadata['date']}")
            
            if doc.metadata.get("section"):
                metadata_parts.append(f"Section: {doc.metadata['section']}")
            
            metadata_parts.append(f"Relevance Score: {doc.score:.3f}")
            
            parts.append("\n".join(metadata_parts))
            parts.append("")  # Empty line
        
        # Add content
        parts.append(doc.content)
        
        return "\n".join(parts)
    
    def _truncate_document(self, doc_text: str, max_tokens: int) -> str:
        """Truncate document to fit token limit"""
        max_chars = int(max_tokens * self.chars_per_token)
        
        if len(doc_text) <= max_chars:
            return doc_text
        
        # Truncate and add marker
        truncated = doc_text[:max_chars - len(self.truncation_marker)]
        return truncated + self.truncation_marker
    
    def format_conversation_history(
        self,
        history: List[dict]
    ) -> str:
        """Format conversation history for context"""
        if not history:
            return ""
        
        formatted = []
        for turn in history[-5:]:  # Last 5 turns
            role = turn.get("role", "user")
            content = turn.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        
        return "\n\n".join(formatted)
    
    def extract_snippet(
        self,
        content: str,
        query: str,
        snippet_length: int = 200
    ) -> str:
        """
        Extract relevant snippet from content based on query
        Simple implementation - can be enhanced with more sophisticated matching
        """
        # Convert to lowercase for matching
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Try to find query terms in content
        query_words = query_lower.split()
        best_position = 0
        max_matches = 0
        
        # Sliding window to find best matching segment
        window_size = snippet_length
        for i in range(0, len(content) - window_size, 50):
            segment = content_lower[i:i + window_size]
            matches = sum(1 for word in query_words if word in segment)
            
            if matches > max_matches:
                max_matches = matches
                best_position = i
        
        # Extract snippet
        start = max(0, best_position)
        end = min(len(content), start + snippet_length)
        
        snippet = content[start:end]
        
        # Add ellipsis
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet.strip()

