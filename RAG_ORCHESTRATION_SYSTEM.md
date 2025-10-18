# RAG Orchestration System - Complete Specification

## Overview

A **production-grade RAG orchestration API** that handles the complete flow from query to answer with:
- Input sanitization and security
- Vector search with ranking
- Configurable prompt templates
- Hallucination detection
- Comprehensive observability
- Admin controls

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│           RAG Orchestration API Endpoint                │
│     POST /rag/query (sync or async)                     │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Input Sanitizer           │
         │  • Strip control chars       │
         │  • Check token limits        │
         │  • Detect injection          │
         │  • Generate idempotency key  │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Cache Manager             │
         │  • Check cache by key        │
         │  • Return if hit             │
         └──────────────┬───────────────┘
                        │ (cache miss)
                        ▼
         ┌──────────────────────────────┐
         │    Vector Search             │
         │  • Tenant-scoped query       │
         │  • Apply filters             │
         │  • Safety scores             │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Metadata Retrieval        │
         │  • Fetch doc metadata        │
         │  • Get snippets (not full)   │
         │  • Check redactions          │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Ranking Engine            │
         │  • Score = similarity        │
         │    * weight                  │
         │    + recency boost           │
         │    + source trust            │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Context Builder           │
         │  • Token budget management   │
         │  • Metadata headers          │
         │  • Citation tokens           │
         │  • Redaction notices         │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Template Manager          │
         │  • Load template by ID       │
         │  • Apply citation style      │
         │  • Set strictness level      │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Prompt Builder            │
         │  • Fill placeholders         │
         │  • Inject instructions       │
         │  • Add citation requirements │
         │  • Set response format       │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Model Adapter             │
         │  • Call provider with prompt │
         │  • Timeout & token limits    │
         │  • Cost tracking             │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Post-Processor            │
         │  • Validate JSON structure   │
         │  • Map citations to docs     │
         │  • Normalize confidence      │
         │  • Extract follow-ups        │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Hallucination Detector    │
         │  • Verify citations exist    │
         │  • Check against provenance  │
         │  • Re-run if needed          │
         │  • Add disclaimer            │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Result Assembly           │
         │  • Build final response      │
         │  • Add provenance info       │
         │  • Set flags                 │
         │  • Cache result              │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │    Metrics & Logging         │
         │  • Emit structured logs      │
         │  • Prometheus metrics        │
         │  • Audit trail               │
         └──────────────────────────────┘
```

---

## Components

### 1. Input Sanitizer (`input_sanitizer.py`)

**Responsibilities:**
- Strip control characters (\\x00-\\x1F)
- Trim excessive whitespace
- Check token length limits
- Detect language (simple heuristics)
- Detect prompt injection patterns
- Generate idempotency key

**Injection Patterns Detected:**
- `ignore previous instructions`
- `forget your instructions`
- `system:`
- `<script>`, `<iframe>`
- SQL injection attempts
- Excessive special characters

**Output:**
```python
SanitizedInput(
    original_query="...",
    sanitized_query="...",
    is_valid=True,
    detected_language="en",
    prompt_injection_detected=False,
    token_count=45,
    idempotency_key="sha256_hash"
)
```

### 2. Ranking Engine (`ranking_engine.py`)

**Configurable Ranking Function:**
```python
rank_score = (
    similarity_score * similarity_weight +
    recency_boost * recency_weight +
    source_trust_score * trust_weight
)
```

**Default Weights:**
- `similarity_weight`: 0.7
- `recency_weight`: 0.2
- `trust_weight`: 0.1

**Recency Boost:**
- Documents from last 30 days: +0.3
- 30-90 days: +0.2
- 90-365 days: +0.1
- Older: +0.0

**Source Trust Scores:**
- Supreme Court: 1.0
- High Court: 0.9
- Acts/Statutes: 1.0
- Secondary sources: 0.7
- User-uploaded: 0.5

### 3. Template Manager (`template_manager.py`)

**Template Structure:**
```json
{
  "template_id": "legal_analysis_balanced",
  "name": "Legal Analysis - Balanced",
  "response_style": "balanced",
  "system_prompt": "You are an expert legal AI...",
  "user_prompt": "Context: {context}\n\nQuestion: {question}\n\n{instructions}",
  "instructions_block": "Provide: (a) citations [1][2], (b) source list, (c) 2 follow-ups, (d) confidence",
  "citation_style": "inline_numbers",
  "follow_up_count": 2,
  "placeholders": ["context", "question", "instructions", "citation_style"]
}
```

**Built-in Templates:**
1. **Terse** - Minimal answer, direct citations
2. **Balanced** - Standard detail, structured
3. **Detailed** - Comprehensive analysis

**Citation Styles:**
- **inline_numbers**: `[1], [2], [3]`
- **bracketed_ids**: `[doc_abc123], [doc_def456]`
- **end_list**: List of sources at end

### 4. Prompt Builder (`prompt_builder.py`)

**Fills Template with:**
- `{context}`: Ranked snippets with metadata
- `{question}`: Sanitized user query
- `{instructions}`: Citation & format requirements
- `{citation_style}`: Formatting rules
- `{follow_up_count}`: Number of follow-ups

**Instruction Block (Auto-injected):**
```
REQUIREMENTS:
1. Cite every factual claim using {citation_style}
2. List all sources used at the end
3. Generate {follow_up_count} concise follow-up questions
4. Provide confidence estimate (0-1 scale)
5. Add disclaimer for uncertain information
6. ONLY use information from provided context
```

**Strictness Levels:**
- **Lenient**: Allow some interpretation
- **Normal**: Standard rules
- **Strict**: "You MUST ONLY use provided sources. Cite EVERY claim."

### 5. Post-Processor (`post_processor.py`)

**Validation Steps:**
1. Parse JSON response
2. Validate required fields (answer, citations, follow_ups)
3. Map citation tokens ([1], [2]) to doc IDs
4. Fetch snippet text for each citation
5. Normalize confidence to 0-1
6. Verify all cited docs exist in provenance

**Expected Model Output Format:**
```json
{
  "answer": "According to Section 10 [1], a valid contract requires...",
  "citations": [
    {"id": "1", "doc_id": "doc_123", "snippet": "..."}
  ],
  "follow_ups": [
    "What happens if consideration is missing?",
    "Are there any exceptions to this rule?"
  ],
  "confidence": 0.85,
  "disclaimer": "This is general information, not legal advice."
}
```

### 6. Hallucination Detector (`hallucination_detector.py`)

**Detection Methods:**
1. **Citation Verification**: Check if all cited doc IDs exist in provenance
2. **Content Verification**: Verify snippets match retrieved documents
3. **Fact Checking**: Compare claims against context

**Mitigation Strategies:**
1. **Re-run with stricter prompt**: Add "ONLY use provided sources"
2. **Add disclaimer**: Flag as "needs verification"
3. **Remove hallucinated citations**: Strip invalid references
4. **Log for review**: Track hallucination patterns

**Output Flags:**
- `hallucination_detected`: Boolean
- `invalid_citations`: List of citation IDs
- `mitigation_applied`: "re-run" | "disclaimer" | "removed"

### 7. Cache Manager (`cache_manager.py`)

**Cache Key:**
```python
cache_key = sha256(
    tenant_id +
    normalized_query +
    template_id +
    top_k +
    citation_style
)
```

**Cache Entry:**
```json
{
  "key": "abc123...",
  "result": {...},
  "created_at": "2025-10-18T...",
  "ttl": 3600,
  "invalidation_triggers": ["index_update", "template_change"]
}
```

**Invalidation:**
- On corpus update (op-log watch)
- On admin reindex
- On template modification
- TTL expiry (default: 1 hour)

**Backend:**
- **Development**: In-memory LRU cache
- **Production**: Redis with TTL

### 8. RAG Orchestrator (`rag_orchestrator.py`)

**Main Entry Point:**
```python
async def process_rag_query(request: RAGRequest) -> RAGResult:
    """
    End-to-end RAG orchestration
    """
    # 1. Sanitize input
    sanitized = await sanitizer.sanitize(request.query)
    
    # 2. Check cache
    cache_key = request.generate_cache_key()
    if cached := await cache.get(cache_key):
        return cached
    
    # 3. Vector search
    documents = await vector_search(
        query=sanitized.sanitized_query,
        tenant_id=request.tenant_id,
        top_k=request.top_k,
        filters=request.filters
    )
    
    # 4. Rank results
    ranked = await ranking_engine.rank(documents)
    
    # 5. Build context
    context = await context_builder.build(
        ranked_docs=ranked,
        token_budget=request.token_budget
    )
    
    # 6. Select template
    template = template_manager.get_template(
        request.template_id,
        request.citation_style,
        request.response_style
    )
    
    # 7. Build prompt
    prompt = prompt_builder.build(
        template=template,
        context=context,
        query=sanitized.sanitized_query,
        strictness=request.strictness
    )
    
    # 8. Call model
    if request.dry_run:
        return dry_run_result(prompt, context)
    
    model_output = await model_adapter.generate(prompt)
    
    # 9. Post-process
    processed = post_processor.process(model_output)
    
    # 10. Detect hallucinations
    verified = hallucination_detector.verify(
        processed,
        provenance=context.provenance
    )
    
    # 11. Assemble result
    result = assemble_result(verified, provenance)
    
    # 12. Cache
    await cache.set(cache_key, result)
    
    # 13. Emit metrics
    emit_metrics(result)
    
    return result
```

---

## API Endpoints

### POST /api/v1/rag/query

**Request:**
```json
{
  "tenant_id": "tenant_123",
  "query": "What are the requirements for a valid contract?",
  "mode": "sync",
  "top_k": 5,
  "template_id": "legal_analysis_balanced",
  "citation_style": "inline_numbers",
  "response_style": "balanced",
  "filters": {
    "date_range_start": "2020-01-01",
    "jurisdictions": ["India"],
    "doc_types": ["act", "judgment"]
  },
  "strictness": "normal",
  "follow_up_count": 2,
  "dry_run": false
}
```

**Response (Sync):**
```json
{
  "answer": "According to Section 10 of the Indian Contract Act, 1872 [1], a valid contract requires...",
  "citations": [
    {
      "citation_id": "1",
      "doc_id": "doc_contract_act_sec10",
      "title": "Indian Contract Act, 1872 - Section 10",
      "source": "Bare Act",
      "snippet": "All agreements are contracts if they are made by...",
      "similarity_score": 0.95,
      "rank_score": 0.92,
      "date": "1872-09-01"
    }
  ],
  "follow_up_questions": [
    "What happens if one of these elements is missing?",
    "Are there any exceptions to these requirements?"
  ],
  "confidence_score": 0.88,
  "flags": {
    "hallucination_warning": false,
    "redactions_applied": false,
    "needs_verification": false,
    "cache_hit": false
  },
  "provenance": {
    "index_version": "v1.2.3",
    "snapshot_id": "snap_20251018",
    "retrieval_latency_ms": 42.3,
    "model_provider": "InLegalBERT",
    "tokens_used": 1247,
    "cost_estimate": 0.0023,
    "timing": {
      "search_ms": 42.3,
      "inference_ms": 823.5,
      "total_ms": 891.2
    }
  },
  "request_id": "req_abc123",
  "timestamp": "2025-10-18T10:30:00Z"
}
```

**Response (Async):**
```json
{
  "job_id": "job_xyz789",
  "status": "queued",
  "request_id": "req_abc123",
  "poll_url": "/api/v1/rag/jobs/job_xyz789"
}
```

### GET /api/v1/rag/jobs/{job_id}

Poll for async job result.

### POST /api/v1/rag/admin/templates

Create or update prompt template.

### GET /api/v1/rag/admin/templates

List all templates.

### POST /api/v1/rag/admin/simulate

Dry-run simulation showing prompt and context.

### GET /api/v1/rag/admin/metrics

Prometheus metrics endpoint.

---

## Configuration

All limits and weights configurable via environment:

```bash
# Input limits
RAG_MAX_QUERY_LENGTH=500
RAG_MAX_TOKEN_LENGTH=2000

# Retrieval
RAG_DEFAULT_TOP_K=5
RAG_MIN_SIMILARITY_THRESHOLD=0.5
RAG_SNIPPET_SIZE=300

# Ranking weights
RAG_SIMILARITY_WEIGHT=0.7
RAG_RECENCY_WEIGHT=0.2
RAG_TRUST_WEIGHT=0.1

# Context building
RAG_TOKEN_BUDGET=3000
RAG_MAX_SNIPPETS=10

# Response
RAG_DEFAULT_TEMPLATE=legal_analysis_balanced
RAG_DEFAULT_FOLLOW_UP_COUNT=2

# Cache
RAG_CACHE_TTL_SECONDS=3600
RAG_CACHE_BACKEND=redis

# Security
RAG_ENABLE_INJECTION_DETECTION=true
RAG_MAX_RETRIES_ON_HALLUCINATION=2
```

---

## Observability

### Structured Logs

Every request emits:
```json
{
  "query_id": "req_abc123",
  "tenant_id": "tenant_123",
  "template_id": "legal_analysis_balanced",
  "docs_retrieved": 5,
  "docs_used": 3,
  "similarity_distribution": {
    "min": 0.62,
    "max": 0.95,
    "avg": 0.81
  },
  "model_used": "InLegalBERT/inlegalbert-v1",
  "latency": {
    "search_ms": 42.3,
    "rank_ms": 5.2,
    "build_ms": 12.1,
    "inference_ms": 823.5,
    "post_ms": 34.8,
    "total_ms": 917.9
  },
  "flags": {
    "cache_hit": false,
    "fallback": false,
    "hallucination": false
  }
}
```

### Prometheus Metrics

```
# Query metrics
rag_queries_total{tenant, template, status}
rag_query_duration_seconds{tenant, template}

# Retrieval metrics
rag_documents_retrieved{tenant}
rag_search_latency_seconds{tenant}

# Model metrics
rag_model_calls_total{provider, model}
rag_model_tokens_used{provider}
rag_model_cost_estimate{provider}

# Quality metrics
rag_citations_per_response{template}
rag_confidence_score{template}
rag_hallucinations_detected_total{tenant}

# Cache metrics
rag_cache_hits_total{tenant}
rag_cache_misses_total{tenant}
```

---

## Security

### Tenant Isolation

- All vector searches scoped to `tenant_id`
- Metadata queries filtered by tenant
- Cross-tenant results blocked
- Audit log per tenant

### Redaction Rules

```python
if doc.sensitivity == "confidential" and not user.has_permission(doc):
    doc.content = "[REDACTED]"
    result.flags.redactions_applied = True
```

### Injection Prevention

Detected patterns trigger:
1. Warning log
2. Query rejection (optional)
3. Sanitization attempt
4. Rate limiting

---

## Admin Controls

### Template CRUD

```python
# Create template
POST /admin/templates
{
  "template_id": "custom_terse",
  "name": "Custom Terse",
  "system_prompt": "...",
  "user_prompt": "...",
  "citation_style": "inline_numbers"
}

# Update template
PUT /admin/templates/custom_terse
{
  "system_prompt": "Updated prompt..."
}

# Delete template
DELETE /admin/templates/custom_terse

# List templates
GET /admin/templates
```

### Simulation / Dry Run

```python
POST /admin/simulate
{
  "query": "Test query",
  "template_id": "legal_analysis_balanced",
  "top_k": 3,
  "show_prompt": true,
  "show_context": true
}

Response:
{
  "generated_prompt": "Full prompt text...",
  "selected_snippets": [...],
  "estimated_tokens": 2847,
  "would_use_model": "InLegalBERT"
}
```

### Ranking Weights

```python
POST /admin/ranking/weights
{
  "similarity_weight": 0.6,
  "recency_weight": 0.3,
  "trust_weight": 0.1
}
```

---

## Implementation Status

### ✅ Designed (Models & Architecture)
- `models.py` - Complete data models (450 lines)
- Architecture diagrams
- API specifications
- Configuration system

### ⏳ To Implement (Estimated 2,000+ lines)
1. `input_sanitizer.py` (~150 lines)
2. `ranking_engine.py` (~200 lines)
3. `template_manager.py` (~300 lines)
4. `prompt_builder.py` (~200 lines)
5. `post_processor.py` (~250 lines)
6. `hallucination_detector.py` (~200 lines)
7. `cache_manager.py` (~150 lines)
8. `rag_orchestrator.py` (~400 lines)
9. FastAPI endpoints (~200 lines)
10. Admin UI/API (~300 lines)

---

## Testing Strategy

### Smoke Tests

```python
def test_rag_end_to_end():
    # Mock vector store
    mock_search = MockVectorSearch()
    
    # Create request
    request = RAGRequest(
        tenant_id="test_tenant",
        query="What is Section 10?",
        top_k=3
    )
    
    # Process
    result = await orchestrator.process(request)
    
    # Assertions
    assert result.answer != ""
    assert len(result.citations) > 0
    assert len(result.follow_up_questions) == 2
    
    # Verify citations map to real docs
    for citation in result.citations:
        assert citation.doc_id in provenance_map
```

---

**Total Estimated Code**: ~2,500 lines for complete orchestration system  
**Current Status**: Architecture & models complete (450 lines)  
**Remaining**: Core logic implementation

This is a **comprehensive, production-grade specification** ready for implementation! 🚀

