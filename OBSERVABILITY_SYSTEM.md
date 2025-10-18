# Observability & Monitoring System - Complete Specification

## ✅ What's Been Implemented (699 lines)

### 1. Structured JSON Logging (`logger.py` - 180 lines)

**Complete Implementation** ✅

**Features:**
- Line-delimited JSON to stdout/stderr
- Consistent schema across all logs
- Context-aware logging with request/job/tenant IDs
- Machine-parsable format

**Log Schema:**
```json
{
  "timestamp": "2025-10-18T10:30:00.123Z",
  "request_id": "req_abc123",
  "job_id": "job_xyz789",
  "tenant_id": "tenant_123",
  "service": "ai-service",
  "endpoint": "/rag/query",
  "provider": "InLegalBERT",
  "model": "inlegalbert-v1",
  "level": "INFO",
  "message": "RAG query completed successfully",
  "latency_ms": 891.2,
  "token_usage_in": 847,
  "token_usage_out": 234,
  "cost_estimate": 0.0023,
  "status_code": 200,
  "error_code": null,
  "stack": null,
  "index_snapshot_id": "snap_20251018",
  "env": "production"
}
```

**Usage:**
```python
from observability import get_logger, set_request_context

logger = get_logger()

# Set context
set_request_context(
    request_id="req_abc123",
    tenant_id="tenant_123",
    endpoint="/rag/query"
)

# Log with context
logger.info(
    "RAG query completed",
    provider="InLegalBERT",
    latency_ms=891.2,
    token_usage_in=847,
    token_usage_out=234,
    cost_estimate=0.0023
)
```

### 2. Request Context & Propagation (`request_context.py` - 150 lines)

**Complete Implementation** ✅

**Features:**
- UUID request_id generation
- Middleware for automatic propagation
- X-Request-ID header support
- W3C trace context headers
- Context variables for async safety
- Timing tracking

**Headers Propagated:**
- `X-Request-ID`: Request identifier
- `traceparent`: W3C trace context
- `tracestate`: Service-specific state
- `X-Response-Time`: Response latency

**Middleware:**
```python
from fastapi import FastAPI
from observability import RequestContextMiddleware

app = FastAPI()
app.add_middleware(RequestContextMiddleware)
```

**Usage in Downstream Calls:**
```python
from observability import get_trace_headers

# Propagate to provider
headers = get_trace_headers()
response = await httpx.post(
    provider_url,
    headers=headers,
    json=payload
)
```

### 3. Prometheus Metrics (`metrics.py` - 360 lines)

**Complete Implementation** ✅

**Metrics Exposed:**

**Counters:**
- `requests_total{endpoint,tenant,provider,status}`
- `tokens_in_total{tenant,provider,model}`
- `tokens_out_total{tenant,provider,model}`
- `model_cost_estimate_total{tenant,provider,model}`
- `provider_calls_total{provider,model,status}`
- `rag_queries_total{tenant,template,status}`
- `cache_hits_total{cache_type,tenant}`
- `cache_misses_total{cache_type,tenant}`

**Histograms:**
- `request_duration_seconds{endpoint,provider}`
- `inference_tokens{provider,model}`
- `batch_size{job_type}`
- `provider_latency_seconds{provider,model}`
- `rag_citations_count{template}`
- `rag_confidence_score{template}`
- `vector_search_latency_seconds`

**Gauges:**
- `queue_depth{queue}`
- `workers_active{worker_type}`
- `circuit_breaker_state{provider}`
- `vector_index_size_bytes`

**Usage:**
```python
from observability import get_metrics

metrics = get_metrics()

# Record request
metrics.record_request(
    endpoint="/rag/query",
    tenant="tenant_123",
    provider="InLegalBERT",
    status="success",
    duration_seconds=0.891
)

# Record tokens
metrics.record_tokens(
    tenant="tenant_123",
    provider="InLegalBERT",
    model="inlegalbert-v1",
    tokens_in=847,
    tokens_out=234
)

# Record cost
metrics.record_cost(
    tenant="tenant_123",
    provider="InLegalBERT",
    model="inlegalbert-v1",
    cost=0.0023
)
```

**Metrics Endpoint:**
```python
from fastapi import FastAPI, Response
from observability import get_metrics

@app.get("/metrics")
async def metrics():
    metrics_collector = get_metrics()
    return Response(
        content=metrics_collector.get_metrics(),
        media_type=metrics_collector.get_content_type()
    )
```

---

## 📋 Remaining Components (To Implement)

### 4. OpenTelemetry Tracing (`tracer.py` - ~300 lines)

**Specification:**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from contextlib import contextmanager

class TracingManager:
    """OpenTelemetry distributed tracing"""
    
    def __init__(self):
        # Configure tracer provider
        provider = TracerProvider()
        
        # Configure exporter (OTLP/Jaeger/Zipkin)
        exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
        )
        
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer("ai-service")
    
    @contextmanager
    def create_span(self, name: str, **attributes):
        """Create a traced span"""
        with self.tracer.start_as_current_span(name) as span:
            # Add attributes
            span.set_attribute("request_id", RequestContext.get_request_id())
            for key, value in attributes.items():
                span.set_attribute(key, value)
            yield span

# Usage:
@trace_span("rag_query")
async def process_rag_query(query):
    with tracer.create_span("vector_search", query=query):
        docs = await search_vectors()
    
    with tracer.create_span("llm_inference", provider="InLegalBERT"):
        answer = await generate_answer()
    
    return answer
```

**Spans to Create:**
- `http_request` - Ingress
- `input_validation` - Sanitization
- `queue_enqueue` - Job submission
- `queue_dequeue` - Job pickup
- `vector_search` - FAISS search
- `metadata_fetch` - Metadata lookup
- `context_build` - Context assembly
- `prompt_build` - Prompt formatting
- `llm_inference` - Provider call
- `post_process` - Response processing
- `cache_write` - Cache update

### 5. Health Checks (`health.py` - ~200 lines)

**Specification:**

```python
from typing import Dict, Any, List
from enum import Enum

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"

class HealthChecker:
    """Health and readiness checks"""
    
    async def check_redis(self) -> bool:
        """Check Redis connectivity"""
        try:
            await redis.ping()
            return True
        except:
            return False
    
    async def check_faiss_index(self) -> bool:
        """Check FAISS index loaded"""
        return index_manager.is_loaded()
    
    async def check_object_storage(self) -> bool:
        """Check S3/GCS connectivity"""
        try:
            await storage.head_bucket()
            return True
        except:
            return False
    
    async def check_providers(self) -> Dict[str, bool]:
        """Check provider reachability"""
        results = {}
        for provider in provider_manager.providers:
            results[provider.name] = await provider.health_check()
        return results
    
    async def check_queue(self) -> bool:
        """Check queue connectivity"""
        try:
            size = await queue.size()
            return True
        except:
            return False
    
    async def get_error_rate(self) -> float:
        """Get recent error rate"""
        # Calculate from metrics
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Liveness probe - basic health"""
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ai-service"
        }
    
    async def readiness_check(self) -> Dict[str, Any]:
        """Readiness probe - dependency checks"""
        redis_ok = await self.check_redis()
        index_ok = await self.check_faiss_index()
        storage_ok = await self.check_object_storage()
        providers = await self.check_providers()
        queue_ok = await self.check_queue()
        error_rate = await self.get_error_rate()
        
        all_healthy = all([
            redis_ok,
            index_ok,
            storage_ok,
            all(providers.values()),
            queue_ok,
            error_rate < 0.1  # 10% threshold
        ])
        
        return {
            "status": "ready" if all_healthy else "not_ready",
            "dependencies": {
                "redis": "healthy" if redis_ok else "unhealthy",
                "faiss_index": "healthy" if index_ok else "unhealthy",
                "object_storage": "healthy" if storage_ok else "unhealthy",
                "providers": providers,
                "queue": "healthy" if queue_ok else "unhealthy",
            },
            "metrics": {
                "error_rate": error_rate
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# Endpoints:
@app.get("/health")
async def health():
    """Liveness probe"""
    result = await health_checker.health_check()
    return result

@app.get("/ready")
async def ready():
    """Readiness probe"""
    result = await health_checker.readiness_check()
    status_code = 200 if result["status"] == "ready" else 503
    return Response(
        content=json.dumps(result),
        status_code=status_code,
        media_type="application/json"
    )
```

### 6. Alert Rules & SLOs (`alerts.py` - ~200 lines)

**Prometheus Alert Rules:**

```yaml
groups:
  - name: ai_service_alerts
    interval: 30s
    rules:
      # Latency SLOs
      - alert: HighLatencyP95
        expr: histogram_quantile(0.95, request_duration_seconds_bucket) > 2.0
        for: 5m
        labels:
          severity: warning
          runbook: https://docs.company.com/runbooks/high-latency
        annotations:
          summary: "P95 latency above 2s"
          description: "{{ $labels.endpoint }} p95 latency is {{ $value }}s"
      
      - alert: HighLatencyP99
        expr: histogram_quantile(0.99, request_duration_seconds_bucket) > 5.0
        for: 5m
        labels:
          severity: critical
          runbook: https://docs.company.com/runbooks/high-latency
        annotations:
          summary: "P99 latency above 5s"
      
      # Error rate SLOs
      - alert: HighErrorRate
        expr: |
          rate(requests_total{status="error"}[5m]) /
          rate(requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Error rate above 5%"
      
      # Queue depth
      - alert: QueueBacklog
        expr: queue_depth > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Queue depth above 1000"
      
      # Provider failures
      - alert: ProviderHighFailureRate
        expr: |
          rate(provider_calls_total{status="error"}[10m]) /
          rate(provider_calls_total[10m]) > 0.20
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Provider {{ $labels.provider }} failure rate > 20%"
      
      # Cost spike
      - alert: HighCostSpike
        expr: |
          rate(model_cost_estimate_total[1h]) > 10.0
        labels:
          severity: warning
        annotations:
          summary: "Cost spike detected: ${{ $value }}/hour"
      
      # Circuit breaker
      - alert: CircuitBreakerOpen
        expr: circuit_breaker_state{provider} == 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker open for {{ $labels.provider }}"
```

**Notification Channels:**
```yaml
receivers:
  - name: 'slack-alerts'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#ai-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
  
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_KEY}'
        description: '{{ .GroupLabels.alertname }}'

route:
  receiver: 'slack-alerts'
  group_by: ['alertname', 'severity']
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
```

### 7. Grafana Dashboards

**Dashboard Panels:**

```json
{
  "dashboard": {
    "title": "AI Service - Operations",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(requests_total[5m])"
        }]
      },
      {
        "title": "Latency Percentiles",
        "targets": [
          {"expr": "histogram_quantile(0.50, request_duration_seconds_bucket)", "legend": "p50"},
          {"expr": "histogram_quantile(0.90, request_duration_seconds_bucket)", "legend": "p90"},
          {"expr": "histogram_quantile(0.99, request_duration_seconds_bucket)", "legend": "p99"}
        ]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(requests_total{status=\"error\"}[5m]) / rate(requests_total[5m])"
        }]
      },
      {
        "title": "Provider Success/Failure",
        "targets": [{
          "expr": "rate(provider_calls_total[5m]) by (provider, status)"
        }]
      },
      {
        "title": "Queue Depth",
        "targets": [{
          "expr": "queue_depth"
        }]
      },
      {
        "title": "Active Workers",
        "targets": [{
          "expr": "workers_active"
        }]
      },
      {
        "title": "Token Consumption per Hour",
        "targets": [{
          "expr": "rate(tokens_in_total[1h]) + rate(tokens_out_total[1h])"
        }]
      },
      {
        "title": "Cost per Hour",
        "targets": [{
          "expr": "rate(model_cost_estimate_total[1h]) by (tenant)"
        }]
      },
      {
        "title": "FAISS Index Size & RAM",
        "targets": [
          {"expr": "vector_index_size_bytes"},
          {"expr": "process_resident_memory_bytes"}
        ]
      }
    ]
  }
}
```

### 8. Cost Tracking (`cost_tracker.py` - ~150 lines)

**Specification:**

```python
class CostTracker:
    """Per-request cost tracking and billing export"""
    
    # Provider pricing (per 1M tokens)
    PRICING = {
        "InLegalBERT": {"input": 0.50, "output": 1.50},
        "DeepSeek": {"input": 0.14, "output": 0.28},
        "Grok": {"input": 5.00, "output": 15.00},
    }
    
    def calculate_cost(
        self,
        provider: str,
        model: str,
        tokens_in: int,
        tokens_out: int
    ) -> float:
        """Calculate cost estimate in USD"""
        pricing = self.PRICING.get(provider, {"input": 1.0, "output": 2.0})
        
        cost = (
            (tokens_in / 1_000_000) * pricing["input"] +
            (tokens_out / 1_000_000) * pricing["output"]
        )
        
        return round(cost, 6)
    
    async def export_hourly_aggregates(self):
        """Export hourly cost aggregates for billing"""
        # Query Prometheus for last hour
        query = f"""
            sum(increase(model_cost_estimate_total[1h])) 
            by (tenant, provider, model)
        """
        
        results = await prometheus.query(query)
        
        # Export to billing system
        for result in results:
            await billing_system.record({
                "tenant_id": result["tenant"],
                "provider": result["provider"],
                "model": result["model"],
                "cost": result["value"],
                "period_start": hour_start,
                "period_end": hour_end,
            })
```

### 9. Debugging & Admin Tools

**Request Debug Endpoint:**
```python
@app.get("/admin/debug/{request_id}")
async def debug_request(request_id: str):
    """Get all data for a request"""
    
    # Query logs
    logs = await log_store.query(request_id=request_id)
    
    # Get trace
    trace = await tracing.get_trace(request_id)
    
    # Get cached context (if available)
    context = await cache.get_debug_context(request_id)
    
    return {
        "request_id": request_id,
        "logs": logs,
        "trace": trace,
        "context": context,  # Sanitized
        "retrieved_at": datetime.utcnow().isoformat()
    }
```

---

## Configuration

```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
SERVICE_NAME=ai-service
ENVIRONMENT=production

# Tracing
OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317
OTEL_SERVICE_NAME=ai-service
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1  # 10% sampling

# Metrics
METRICS_PORT=9090
METRICS_PATH=/metrics

# Health checks
HEALTH_CHECK_INTERVAL=30
READINESS_ERROR_RATE_THRESHOLD=0.1

# Retention
LOG_RETENTION_DAYS=30
TRACE_RETENTION_DAYS=7
METRICS_RETENTION_DAYS=90
DEBUG_CONTEXT_RETENTION_HOURS=72
```

---

## Integration Example

```python
from fastapi import FastAPI
from observability import (
    RequestContextMiddleware,
    get_logger,
    get_metrics,
    HealthChecker
)

app = FastAPI()

# Add middleware
app.add_middleware(RequestContextMiddleware)

# Initialize
logger = get_logger()
metrics = get_metrics()
health = HealthChecker()

@app.post("/rag/query")
async def rag_query(request: RAGRequest):
    start_time = time.time()
    
    try:
        # Log request
        logger.info("RAG query received", query=request.query[:50])
        
        # Process
        result = await rag_orchestrator.process(request)
        
        # Record metrics
        duration = time.time() - start_time
        metrics.record_request(
            endpoint="/rag/query",
            tenant=request.tenant_id,
            provider=result.provenance.model_provider,
            status="success",
            duration_seconds=duration
        )
        
        metrics.record_tokens(
            tenant=request.tenant_id,
            provider=result.provenance.model_provider,
            model=result.provenance.model_name,
            tokens_in=result.provenance.tokens_used // 2,
            tokens_out=result.provenance.tokens_used // 2
        )
        
        # Log completion
        logger.info(
            "RAG query completed",
            latency_ms=duration * 1000,
            citations_count=len(result.citations),
            cost_estimate=result.provenance.cost_estimate
        )
        
        return result
    
    except Exception as e:
        # Log error
        logger.error(
            "RAG query failed",
            error_code=type(e).__name__,
            stack=str(e)
        )
        
        # Record error metric
        metrics.record_request(
            endpoint="/rag/query",
            tenant=request.tenant_id,
            provider="none",
            status="error",
            duration_seconds=time.time() - start_time
        )
        
        raise

@app.get("/metrics")
async def prometheus_metrics():
    return Response(
        content=metrics.get_metrics(),
        media_type=metrics.get_content_type()
    )

@app.get("/health")
async def health_check():
    return await health.health_check()

@app.get("/ready")
async def readiness_check():
    result = await health.readiness_check()
    status = 200 if result["status"] == "ready" else 503
    return Response(
        content=json.dumps(result),
        status_code=status
    )
```

---

## Summary

**✅ Implemented (699 lines):**
1. Structured JSON logging with full schema
2. Request ID generation and propagation
3. Comprehensive Prometheus metrics
4. Request context management

**📋 Specified (Need Implementation):**
1. OpenTelemetry distributed tracing (~300 lines)
2. Health and readiness checks (~200 lines)
3. Alert rules and SLO definitions
4. Grafana dashboard configs
5. Cost tracking and export (~150 lines)
6. Debug and admin tools (~150 lines)

**Total Estimated:** ~1,500 lines for complete observability system

**Current: 699 lines implemented + comprehensive specifications**

This observability system provides production-grade monitoring, tracing, and debugging capabilities! 🚀

