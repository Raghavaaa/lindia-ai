"""
RAG Data Models
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RAGMode(str, Enum):
    """RAG operation modes"""
    STANDARD = "standard"  # Normal RAG with citations
    CONVERSATIONAL = "conversational"  # Multi-turn with history
    SUMMARIZATION = "summarization"  # Summarize retrieved docs
    COMPARISON = "comparison"  # Compare multiple sources
    LEGAL_ANALYSIS = "legal_analysis"  # Specific to legal domain


@dataclass
class Citation:
    """
    Source citation for answer
    """
    doc_id: str
    title: str
    source: str
    url: Optional[str] = None
    snippet: str = ""  # Relevant text excerpt
    relevance_score: float = 0.0
    page_number: Optional[int] = None
    section: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "snippet": self.snippet,
            "relevance_score": float(self.relevance_score),
            "page_number": self.page_number,
            "section": self.section,
        }


@dataclass
class FollowUpQuestion:
    """
    Suggested follow-up question
    """
    question: str
    reasoning: str = ""  # Why this question is relevant
    priority: int = 1  # 1 = highest priority
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "question": self.question,
            "reasoning": self.reasoning,
            "priority": self.priority,
        }


@dataclass
class RetrievedDocument:
    """
    Document retrieved from vector search
    """
    doc_id: str
    content: str
    title: str
    source: str
    url: Optional[str] = None
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    rank: int = 0
    
    def to_citation(self, snippet: Optional[str] = None) -> Citation:
        """Convert to citation"""
        return Citation(
            doc_id=self.doc_id,
            title=self.title,
            source=self.source,
            url=self.url,
            snippet=snippet or self.content[:200] + "...",
            relevance_score=self.score,
            page_number=self.metadata.get("page_number"),
            section=self.metadata.get("section"),
        )


@dataclass
class RAGQuery:
    """
    Input query for RAG pipeline
    """
    query: str
    tenant_id: str
    
    # Search parameters
    top_k: int = 5
    score_threshold: float = 0.0
    
    # Context parameters
    max_context_tokens: int = 3000
    include_metadata: bool = True
    
    # Generation parameters
    mode: RAGMode = RAGMode.STANDARD
    temperature: float = 0.7
    max_tokens: int = 512
    
    # Prompt customization
    prompt_template: Optional[str] = None  # Override default template
    system_prompt: Optional[str] = None
    
    # Conversational context
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    
    # Filters
    filters: Optional[Dict[str, Any]] = None
    
    # Request metadata
    request_id: Optional[str] = None


@dataclass
class RAGResponse:
    """
    Output response from RAG pipeline
    """
    # Answer
    answer: str
    
    # Citations
    citations: List[Citation] = field(default_factory=list)
    
    # Follow-up questions
    follow_up_questions: List[FollowUpQuestion] = field(default_factory=list)
    
    # Metadata
    model_used: str = ""
    retrieval_count: int = 0
    context_tokens: int = 0
    generation_tokens: int = 0
    
    # Timing
    retrieval_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    total_time_ms: float = 0.0
    
    # RAG metadata
    mode: RAGMode = RAGMode.STANDARD
    confidence_score: Optional[float] = None
    
    # Request tracking
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "answer": self.answer,
            "citations": [c.to_dict() for c in self.citations],
            "follow_up_questions": [q.to_dict() for q in self.follow_up_questions],
            "metadata": {
                "model_used": self.model_used,
                "retrieval_count": self.retrieval_count,
                "context_tokens": self.context_tokens,
                "generation_tokens": self.generation_tokens,
                "retrieval_time_ms": self.retrieval_time_ms,
                "generation_time_ms": self.generation_time_ms,
                "total_time_ms": self.total_time_ms,
                "mode": self.mode.value,
                "confidence_score": self.confidence_score,
            },
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ContextWindow:
    """
    Constructed context window for LLM
    """
    documents: List[RetrievedDocument] = field(default_factory=list)
    formatted_context: str = ""
    token_count: int = 0
    truncated: bool = False
    
    def add_document(self, doc: RetrievedDocument):
        """Add document to context"""
        self.documents.append(doc)
    
    def get_citations(self) -> List[Citation]:
        """Extract citations from documents"""
        return [doc.to_citation() for doc in self.documents]

