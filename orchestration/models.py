"""
RAG Orchestration Models
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
import hashlib


class ProcessingMode(str, Enum):
    """RAG processing mode"""
    SYNC = "sync"  # Return full response immediately
    ASYNC = "async"  # Return job ID for later retrieval


class CitationStyle(str, Enum):
    """Citation formatting styles"""
    INLINE_NUMBERS = "inline_numbers"  # [1], [2], etc.
    BRACKETED_IDS = "bracketed_ids"  # [doc_123], [doc_456]
    END_LIST = "end_list"  # List at end of answer


class ResponseStyle(str, Enum):
    """Response detail levels"""
    TERSE = "terse"  # Minimal, direct answer
    BALANCED = "balanced"  # Standard detail
    DETAILED = "detailed"  # Comprehensive analysis


class StrictnessLevel(str, Enum):
    """Prompt strictness for hallucination control"""
    LENIENT = "lenient"  # Allow some interpretation
    NORMAL = "normal"  # Standard rules
    STRICT = "strict"  # Force exact source usage only


@dataclass
class DocumentFilter:
    """Filters for document retrieval"""
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    jurisdictions: Optional[List[str]] = None
    doc_types: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    min_date: Optional[date] = None
    max_date: Optional[date] = None
    exclude_doc_ids: Optional[List[str]] = None


@dataclass
class RAGRequest:
    """
    Input request for RAG orchestration
    """
    # Required
    tenant_id: str
    query: str
    
    # Processing
    mode: ProcessingMode = ProcessingMode.SYNC
    
    # Retrieval parameters
    top_k: int = 5
    min_similarity_threshold: float = 0.5
    filters: Optional[DocumentFilter] = None
    
    # Template selection
    template_id: Optional[str] = None
    citation_style: CitationStyle = CitationStyle.INLINE_NUMBERS
    response_style: ResponseStyle = ResponseStyle.BALANCED
    
    # Prompt control
    strictness: StrictnessLevel = StrictnessLevel.NORMAL
    follow_up_count: int = 2
    
    # Advanced
    token_budget: int = 3000
    snippet_size: int = 300
    include_provenance: bool = True
    dry_run: bool = False  # Return prompt only, don't call model
    
    # Idempotency
    idempotency_key: Optional[str] = None
    request_id: Optional[str] = None
    
    def generate_cache_key(self) -> str:
        """Generate cache key for this request"""
        # Normalize query
        normalized_query = self.query.lower().strip()
        
        # Create hash
        key_parts = [
            self.tenant_id,
            normalized_query,
            self.template_id or "default",
            str(self.top_k),
            self.citation_style.value,
            self.response_style.value,
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()


@dataclass
class CitationReference:
    """
    Citation with full metadata and snippet
    """
    citation_id: str
    doc_id: str
    title: str
    source: str
    source_url: Optional[str] = None
    
    # Content
    snippet: str = ""
    section: Optional[str] = None
    page_number: Optional[int] = None
    
    # Scores
    similarity_score: float = 0.0
    rank_score: float = 0.0
    safety_score: float = 1.0
    
    # Metadata
    date: Optional[date] = None
    author: Optional[str] = None
    jurisdiction: Optional[str] = None
    doc_type: Optional[str] = None
    
    # Provenance
    offset_start: Optional[int] = None
    offset_end: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "citation_id": self.citation_id,
            "doc_id": self.doc_id,
            "title": self.title,
            "source": self.source,
            "source_url": self.source_url,
            "snippet": self.snippet,
            "section": self.section,
            "page_number": self.page_number,
            "similarity_score": float(self.similarity_score),
            "rank_score": float(self.rank_score),
            "safety_score": float(self.safety_score),
            "date": self.date.isoformat() if self.date else None,
            "author": self.author,
            "jurisdiction": self.jurisdiction,
            "doc_type": self.doc_type,
        }


@dataclass
class ProvenanceInfo:
    """
    Provenance and audit information
    """
    index_version: str = ""
    snapshot_id: Optional[str] = None
    retrieval_latency_ms: float = 0.0
    
    # Vector search details
    total_candidates: int = 0
    filtered_candidates: int = 0
    final_results: int = 0
    
    # Context building
    context_tokens: int = 0
    snippets_used: int = 0
    snippets_truncated: int = 0
    
    # Model details
    model_provider: str = ""
    model_name: str = ""
    model_latency_ms: float = 0.0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    
    # Timing breakdown
    sanitization_ms: float = 0.0
    search_ms: float = 0.0
    ranking_ms: float = 0.0
    context_build_ms: float = 0.0
    prompt_build_ms: float = 0.0
    inference_ms: float = 0.0
    post_process_ms: float = 0.0
    total_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "index_version": self.index_version,
            "snapshot_id": self.snapshot_id,
            "retrieval_latency_ms": self.retrieval_latency_ms,
            "total_candidates": self.total_candidates,
            "final_results": self.final_results,
            "context_tokens": self.context_tokens,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "tokens_used": self.tokens_used,
            "cost_estimate": self.cost_estimate,
            "timing": {
                "search_ms": self.search_ms,
                "ranking_ms": self.ranking_ms,
                "inference_ms": self.inference_ms,
                "total_ms": self.total_ms,
            }
        }


@dataclass
class RAGResult:
    """
    Complete RAG response
    """
    # Core response
    answer: str
    citations: List[CitationReference] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    
    # Quality indicators
    confidence_score: float = 0.0
    
    # Flags
    hallucination_warning: bool = False
    redactions_applied: bool = False
    cache_hit: bool = False
    needs_verification: bool = False
    
    # Provenance
    provenance: Optional[ProvenanceInfo] = None
    
    # Metadata
    request_id: Optional[str] = None
    tenant_id: str = ""
    template_used: str = ""
    citation_style: CitationStyle = CitationStyle.INLINE_NUMBERS
    
    # Timestamps
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Dry run info (when dry_run=True)
    generated_prompt: Optional[str] = None
    selected_snippets: Optional[List[Dict]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "answer": self.answer,
            "citations": [c.to_dict() for c in self.citations],
            "follow_up_questions": self.follow_up_questions,
            "confidence_score": float(self.confidence_score),
            "flags": {
                "hallucination_warning": self.hallucination_warning,
                "redactions_applied": self.redactions_applied,
                "cache_hit": self.cache_hit,
                "needs_verification": self.needs_verification,
            },
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "template_used": self.template_used,
            "timestamp": self.timestamp.isoformat(),
        }
        
        if self.provenance:
            result["provenance"] = self.provenance.to_dict()
        
        if self.generated_prompt:
            result["dry_run"] = {
                "generated_prompt": self.generated_prompt,
                "selected_snippets": self.selected_snippets or [],
            }
        
        return result


@dataclass
class RAGMetrics:
    """
    Metrics for observability
    """
    query_id: str
    tenant_id: str
    template_id: str
    
    # Retrieval metrics
    docs_retrieved: int = 0
    similarity_distribution: Dict[str, float] = field(default_factory=dict)
    
    # Model metrics
    model_used: str = ""
    tokens_used: int = 0
    cost_estimate: float = 0.0
    
    # Latency breakdown
    search_latency_ms: float = 0.0
    prompt_build_latency_ms: float = 0.0
    inference_latency_ms: float = 0.0
    post_process_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    
    # Quality metrics
    citations_count: int = 0
    follow_ups_count: int = 0
    confidence_score: float = 0.0
    
    # Flags
    fallback_triggered: bool = False
    mitigation_applied: bool = False
    cache_hit: bool = False
    hallucination_detected: bool = False
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "query_id": self.query_id,
            "tenant_id": self.tenant_id,
            "template_id": self.template_id,
            "metrics": {
                "docs_retrieved": self.docs_retrieved,
                "model_used": self.model_used,
                "tokens_used": self.tokens_used,
                "cost_estimate": self.cost_estimate,
                "citations_count": self.citations_count,
                "confidence_score": self.confidence_score,
            },
            "latency": {
                "search_ms": self.search_latency_ms,
                "inference_ms": self.inference_latency_ms,
                "total_ms": self.total_latency_ms,
            },
            "flags": {
                "fallback": self.fallback_triggered,
                "mitigation": self.mitigation_applied,
                "cache_hit": self.cache_hit,
                "hallucination": self.hallucination_detected,
            },
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class SanitizedInput:
    """
    Sanitized and validated input
    """
    original_query: str
    sanitized_query: str
    tenant_id: str
    
    # Validation results
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    # Detection results
    detected_language: str = "en"
    prompt_injection_detected: bool = False
    injection_patterns: List[str] = field(default_factory=list)
    
    # Normalization
    token_count: int = 0
    char_count: int = 0
    idempotency_key: str = ""
    
    # Flags
    control_chars_removed: bool = False
    excessive_length: bool = False

