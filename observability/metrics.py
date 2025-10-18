"""
Prometheus Metrics Collection
Exposes /metrics endpoint with comprehensive metrics
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST
)
from typing import Optional, Dict, List
import os


class MetricsCollector:
    """
    Centralized metrics collector for Prometheus
    
    Metrics:
    - Counters: requests_total, tokens_total, cost_total
    - Histograms: request_duration, inference_tokens, batch_size
    - Gauges: queue_depth, workers_active, index_size
    
    Labels: tenant, endpoint, provider, model, status
    """
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Request metrics
        self.requests_total = Counter(
            'requests_total',
            'Total number of requests',
            ['endpoint', 'tenant', 'provider', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'request_duration_seconds',
            'Request duration in seconds',
            ['endpoint', 'provider'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        # Token usage metrics
        self.tokens_in_total = Counter(
            'tokens_in_total',
            'Total input tokens consumed',
            ['tenant', 'provider', 'model'],
            registry=self.registry
        )
        
        self.tokens_out_total = Counter(
            'tokens_out_total',
            'Total output tokens generated',
            ['tenant', 'provider', 'model'],
            registry=self.registry
        )
        
        self.inference_tokens = Histogram(
            'inference_tokens',
            'Token usage per inference',
            ['provider', 'model'],
            buckets=[10, 50, 100, 250, 500, 1000, 2000, 5000],
            registry=self.registry
        )
        
        # Cost metrics
        self.cost_estimate_total = Counter(
            'model_cost_estimate_total',
            'Total estimated cost in USD',
            ['tenant', 'provider', 'model'],
            registry=self.registry
        )
        
        # Queue metrics
        self.queue_depth = Gauge(
            'queue_depth',
            'Current queue depth',
            ['queue'],
            registry=self.registry
        )
        
        self.workers_active = Gauge(
            'workers_active',
            'Number of active workers',
            ['worker_type'],
            registry=self.registry
        )
        
        # Batch metrics
        self.batch_size = Histogram(
            'batch_size',
            'Batch size distribution',
            ['job_type'],
            buckets=[1, 2, 5, 10, 20, 50, 100],
            registry=self.registry
        )
        
        # Provider metrics
        self.provider_calls_total = Counter(
            'provider_calls_total',
            'Total provider API calls',
            ['provider', 'model', 'status'],
            registry=self.registry
        )
        
        self.provider_latency = Histogram(
            'provider_latency_seconds',
            'Provider API call latency',
            ['provider', 'model'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        # Circuit breaker metrics
        self.circuit_breaker_state = Gauge(
            'circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=open, 2=half-open)',
            ['provider'],
            registry=self.registry
        )
        
        # RAG metrics
        self.rag_queries_total = Counter(
            'rag_queries_total',
            'Total RAG queries',
            ['tenant', 'template', 'status'],
            registry=self.registry
        )
        
        self.rag_citations_count = Histogram(
            'rag_citations_count',
            'Number of citations per RAG response',
            ['template'],
            buckets=[0, 1, 2, 3, 5, 10, 20],
            registry=self.registry
        )
        
        self.rag_confidence_score = Histogram(
            'rag_confidence_score',
            'RAG confidence score',
            ['template'],
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        # Vector store metrics
        self.vector_index_size = Gauge(
            'vector_index_size_bytes',
            'FAISS index size in bytes',
            registry=self.registry
        )
        
        self.vector_search_latency = Histogram(
            'vector_search_latency_seconds',
            'Vector search latency',
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['cache_type', 'tenant'],
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['cache_type', 'tenant'],
            registry=self.registry
        )
    
    def record_request(
        self,
        endpoint: str,
        tenant: str,
        provider: Optional[str],
        status: str,
        duration_seconds: float
    ):
        """Record a request"""
        self.requests_total.labels(
            endpoint=endpoint,
            tenant=tenant,
            provider=provider or "none",
            status=status
        ).inc()
        
        self.request_duration.labels(
            endpoint=endpoint,
            provider=provider or "none"
        ).observe(duration_seconds)
    
    def record_tokens(
        self,
        tenant: str,
        provider: str,
        model: str,
        tokens_in: int,
        tokens_out: int
    ):
        """Record token usage"""
        self.tokens_in_total.labels(
            tenant=tenant,
            provider=provider,
            model=model
        ).inc(tokens_in)
        
        self.tokens_out_total.labels(
            tenant=tenant,
            provider=provider,
            model=model
        ).inc(tokens_out)
        
        total_tokens = tokens_in + tokens_out
        self.inference_tokens.labels(
            provider=provider,
            model=model
        ).observe(total_tokens)
    
    def record_cost(
        self,
        tenant: str,
        provider: str,
        model: str,
        cost: float
    ):
        """Record cost estimate"""
        self.cost_estimate_total.labels(
            tenant=tenant,
            provider=provider,
            model=model
        ).inc(cost)
    
    def set_queue_depth(self, queue: str, depth: int):
        """Set current queue depth"""
        self.queue_depth.labels(queue=queue).set(depth)
    
    def set_workers_active(self, worker_type: str, count: int):
        """Set number of active workers"""
        self.workers_active.labels(worker_type=worker_type).set(count)
    
    def record_batch_size(self, job_type: str, size: int):
        """Record batch size"""
        self.batch_size.labels(job_type=job_type).observe(size)
    
    def record_provider_call(
        self,
        provider: str,
        model: str,
        status: str,
        latency_seconds: float
    ):
        """Record provider API call"""
        self.provider_calls_total.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        self.provider_latency.labels(
            provider=provider,
            model=model
        ).observe(latency_seconds)
    
    def set_circuit_breaker_state(self, provider: str, state: str):
        """Set circuit breaker state (closed=0, open=1, half_open=2)"""
        state_map = {"closed": 0, "open": 1, "half_open": 2}
        self.circuit_breaker_state.labels(provider=provider).set(
            state_map.get(state, 0)
        )
    
    def record_rag_query(
        self,
        tenant: str,
        template: str,
        status: str,
        citations_count: int,
        confidence: float
    ):
        """Record RAG query"""
        self.rag_queries_total.labels(
            tenant=tenant,
            template=template,
            status=status
        ).inc()
        
        self.rag_citations_count.labels(template=template).observe(citations_count)
        self.rag_confidence_score.labels(template=template).observe(confidence)
    
    def set_vector_index_size(self, size_bytes: int):
        """Set vector index size"""
        self.vector_index_size.set(size_bytes)
    
    def record_vector_search(self, latency_seconds: float):
        """Record vector search"""
        self.vector_search_latency.observe(latency_seconds)
    
    def record_cache_hit(self, cache_type: str, tenant: str):
        """Record cache hit"""
        self.cache_hits_total.labels(
            cache_type=cache_type,
            tenant=tenant
        ).inc()
    
    def record_cache_miss(self, cache_type: str, tenant: str):
        """Record cache miss"""
        self.cache_misses_total.labels(
            cache_type=cache_type,
            tenant=tenant
        ).inc()
    
    def get_metrics(self) -> bytes:
        """Get Prometheus metrics in text format"""
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get Prometheus content type"""
        return CONTENT_TYPE_LATEST


# Global metrics instance
_metrics = None


def get_metrics() -> MetricsCollector:
    """Get global metrics collector"""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics

