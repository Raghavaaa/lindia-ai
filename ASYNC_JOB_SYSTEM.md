# Async Job Queue System

## Overview

Enterprise-grade async job queue system for handling heavy AI workloads with:
- ✅ Non-blocking job intake with idempotency
- ✅ Durable FIFO queue with priorities (high/normal/low)
- ✅ Worker pool with configurable concurrency
- ✅ Micro-batching for compatible jobs
- ✅ Retry logic with exponential backoff
- ✅ Circuit breaker per provider
- ✅ Backpressure and flow control
- ✅ Dead letter queue for failed jobs
- ✅ Per-tenant quotas and rate limiting
- ✅ Full observability and metrics
- ✅ Graceful shutdown

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Request                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Job Intake API (Non-blocking)                  │
│  • Validate input                                           │
│  • Check idempotency                                        │
│  • Enforce quotas & rate limits                             │
│  • Assign job ID                                            │
│  • Return 202 Accepted immediately                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Priority Queue (FIFO)                      │
│  Backend: In-memory (dev) or Redis (prod)                   │
│  Max queue length enforced                                  │
│  Priorities: HIGH > NORMAL > LOW                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Micro-Batcher (Optional)                   │
│  • Groups compatible jobs (same provider/type)              │
│  • Flushes on: time window OR size limit                   │
│  • Preserves individual job IDs                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Worker Pool (N workers)                        │
│  • Async workers pull from queue                            │
│  • M concurrent provider calls per worker                   │
│  • Per-tenant & global concurrency caps                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Circuit Breaker Manager                        │
│  • Tracks success/failure per provider                      │
│  • States: CLOSED → OPEN → HALF_OPEN                        │
│  • Routes to fallback on breaker open                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Retry Handler                                  │
│  • Exponential backoff with jitter                          │
│  • Only retries: timeouts, 5xx, rate limits                 │
│  • Max attempts configurable                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Provider Manager                               │
│  • InLegalBERT, DeepSeek, Grok                             │
│  • Automatic fallback on failure                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Result Storage                                 │
│  • Job status & results                                     │
│  • Dead letter queue for failures                           │
│  • TTL-based cleanup                                        │
└─────────────────────────────────────────────────────────────┘
```

## Components Implemented

### 1. Job Models (`jobs/models.py`)
- `Job`: Core job data structure with full lifecycle tracking
- `JobStatus`: PENDING → QUEUED → RUNNING → COMPLETED/FAILED/CANCELLED/TIMEOUT/DEAD_LETTER
- `Priority`: HIGH (3) > NORMAL (2) > LOW (1)
- `JobType`: INFERENCE, EMBEDDING, SEARCH
- `BatchRequest`: Micro-batch container
- `CircuitBreakerState`: Circuit breaker state tracking

**Key Features**:
- Unique job IDs (UUID4)
- Tenant ID for multi-tenancy
- Idempotency keys to prevent duplicate submissions
- Target provider selection
- Webhook URL support
- Full timestamp tracking (created, queued, started, completed)
- Attempt counter for retries
- Configurable timeouts (job-level and provider-level)
- Request ID for tracing

### 2. Queue Backend (`jobs/queue_backend.py`)
**In-Memory Queue** (Development):
- Uses Python `heapq` for priority queue
- FIFO within same priority level
- Thread-safe with asyncio locks
- Configurable max size (default: 10,000)

**Redis Queue** (Production):
- Uses Redis sorted sets for durability
- Score-based priority + FIFO ordering
- Atomic operations
- Configurable max size (default: 100,000)
- Auto-TTL for cleanup

**Operations**:
- `enqueue(job)`: Add with priority
- `dequeue()`: Get highest priority job
- `size()`: Current queue depth
- `peek()`: Look without removing
- `remove(job_id)`: Cancel specific job

### 3. Job Storage (`jobs/storage.py`)
**Features**:
- Dual backend: In-memory (dev) or Redis (prod)
- Idempotency checking
- Job status persistence
- Result storage with TTL
- Dead letter queue (DLQ) management

**Operations**:
- `save_job(job)`: Persist job state
- `get_job(job_id)`: Retrieve job
- `check_idempotency(key)`: Prevent duplicates
- `save_result(result)`: Store job result
- `add_to_dlq(job)`: Move to dead letter queue
- `get_dlq_jobs()`: List failed jobs
- `requeue_from_dlq(job_id)`: Retry failed job
- `cleanup_old_jobs()`: TTL-based cleanup

### 4. Circuit Breaker (`jobs/circuit_breaker.py`)
**Per-Provider Circuit Breaking**:
- **CLOSED** (normal): All requests pass through
- **OPEN** (failing): Block requests, route to fallback
- **HALF_OPEN** (testing): Allow limited probe requests

**Configuration**:
- `failure_threshold`: Failures before opening (default: 5)
- `success_threshold`: Successes to close from half-open (default: 2)
- `timeout_seconds`: Time before trying half-open (default: 60)
- `half_open_max_calls`: Max probes in half-open (default: 3)

**CircuitBreakerManager**:
- Manages breakers for all providers
- `is_provider_available(provider)`: Check if usable
- `record_success(provider)`: Track success
- `record_failure(provider)`: Track failure
- `get_all_states()`: Monitor all breakers
- `reset(provider)`: Manual reset

### 5. Retry Logic (`jobs/retry.py`)
**Exponential Backoff**:
```
delay = initial_delay * (base ^ attempt)
delay = min(delay, max_delay)
delay *= random(0.75, 1.25)  # Jitter
```

**Configuration**:
- `max_attempts`: Default 3
- `initial_delay`: Default 1.0s
- `max_delay`: Default 60s
- `exponential_base`: Default 2.0
- `jitter`: Default true (±25%)

**Retryable Errors**:
- Timeouts
- 5xx server errors (502, 503, 504)
- Rate limits (429)
- Connection failures

**Non-Retryable Errors**:
- 4xx client errors (except 429)
- Invalid input
- Authorization failures

**Usage**:
```python
result = await retry_on_error(some_async_func, arg1, arg2, job_id="123")
```

### 6. Micro-Batching (`jobs/batcher.py`)
**Batching Strategy**:
- Groups compatible jobs (same provider + job type)
- Flushes when: **time window** expires OR **size limit** reached
- Preserves individual job IDs in results

**Configuration**:
- `max_batch_size`: Default 10 jobs
- `batch_window_ms`: Default 100ms
- `enabled`: Default true

**Operations**:
- `add_job(job, callback)`: Add to batch
- `force_flush_all()`: Flush on shutdown
- `get_stats()`: Monitor batching

**Benefits**:
- Reduces API calls by up to 10x
- Lower latency per job
- Better throughput under load

### 7. Quota & Rate Limiting (`jobs/quota.py`)
**Per-Tenant Quotas**:
- Daily quota limits
- Per-minute rate limits
- Automatic daily reset
- Sliding window rate limiting

**Tier System**:
| Tier | Daily Quota | Rate/Min | Env Vars |
|------|-------------|----------|----------|
| Free | 100 | 10 | `QUOTA_FREE_*` |
| Basic | 1,000 | 60 | `QUOTA_BASIC_*` |
| Pro | 10,000 | 300 | `QUOTA_PRO_*` |
| Enterprise | 100,000 | 1,000 | `QUOTA_ENTERPRISE_*` |

**Operations**:
- `check_and_consume(tenant_id, tier)`: Check and use quota
- `get_tenant_info(tenant_id)`: View quota status
- `update_tenant_tier(tenant_id, tier)`: Change tier
- `reset_tenant(tenant_id)`: Admin reset

**Response Info**:
```json
{
  "daily_usage": 150,
  "daily_quota": 1000,
  "remaining_quota": 850,
  "rate_limit_per_minute": 60,
  "current_rate": 12,
  "resets_at": "2025-10-19T00:00:00Z"
}
```

## Configuration

All parameters are environment-driven (`.env` file):

### Queue Configuration
```bash
QUEUE_BACKEND=memory  # or redis
QUEUE_MAX_SIZE=10000
REDIS_URL=redis://localhost:6379
```

### Worker Configuration
```bash
WORKER_COUNT=4  # Number of workers
WORKER_MAX_CONCURRENT_JOBS=10  # Jobs per worker
WORKER_MAX_CONCURRENT_PROVIDER_CALLS=5  # Provider calls per worker
TENANT_MAX_CONCURRENT_JOBS=3  # Per tenant
```

### Batching Configuration
```bash
BATCH_ENABLED=true
BATCH_MAX_SIZE=10
BATCH_WINDOW_MS=100
```

### Retry Configuration
```bash
RETRY_MAX_ATTEMPTS=3
RETRY_INITIAL_DELAY_SECONDS=1.0
RETRY_MAX_DELAY_SECONDS=60.0
RETRY_EXPONENTIAL_BASE=2.0
RETRY_JITTER=true
```

### Circuit Breaker Configuration
```bash
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=2
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60
CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS=3
```

### Quota Configuration
```bash
# Per tier
QUOTA_FREE_DAILY=100
QUOTA_FREE_RATE=10
QUOTA_BASIC_DAILY=1000
QUOTA_BASIC_RATE=60
QUOTA_PRO_DAILY=10000
QUOTA_PRO_RATE=300
QUOTA_ENTERPRISE_DAILY=100000
QUOTA_ENTERPRISE_RATE=1000
```

### Timeout Configuration
```bash
JOB_TIMEOUT_SECONDS=60  # Total job timeout
PROVIDER_TIMEOUT_SECONDS=30  # Per provider call
```

### Storage Configuration
```bash
STORAGE_BACKEND=memory  # or redis
STORAGE_TTL_HOURS=24
```

## API Endpoints (To Be Implemented)

### Job Submission
```
POST /jobs/submit
```
**Request**:
```json
{
  "tenant_id": "tenant-123",
  "job_type": "inference",
  "payload": {
    "query": "What is contract law?",
    "context": "Indian Contract Act"
  },
  "priority": "normal",
  "target_provider": "inlegalbert",
  "idempotency_key": "unique-key-123",
  "webhook_url": "https://api.example.com/webhook"
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "quota_info": {
    "daily_usage": 151,
    "remaining_quota": 849
  }
}
```

### Job Status
```
GET /jobs/{job_id}/status
```
**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-10-18T10:00:00Z",
  "completed_at": "2025-10-18T10:00:05Z",
  "provider_used": "InLegalBERT",
  "attempt_count": 1
}
```

### Job Result
```
GET /jobs/{job_id}/result
```
**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "answer": "...",
    "confidence": 0.95
  },
  "provider_used": "InLegalBERT"
}
```

### Cancel Job
```
POST /jobs/{job_id}/cancel
```
**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "cancelled_at": "2025-10-18T10:00:03Z"
}
```

### System Status
```
GET /jobs/system/status
```
**Response**:
```json
{
  "queue_depth": 45,
  "active_workers": 4,
  "processing_jobs": 12,
  "circuit_breakers": {
    "InLegalBERT": "closed",
    "DeepSeek": "open",
    "Grok": "closed"
  },
  "batch_stats": {
    "active_batches": 3,
    "avg_batch_size": 7
  }
}
```

### Dead Letter Queue
```
GET /jobs/dlq
POST /jobs/dlq/{job_id}/requeue
```

### Admin Operations
```
POST /admin/quotas/{tenant_id}/reset
POST /admin/circuit-breakers/{provider}/reset
GET /admin/metrics
```

## Observability & Metrics

### Key Metrics
- **Queue metrics**: depth, wait time, throughput
- **Worker metrics**: active workers, job processing time
- **Provider metrics**: success rate, latency, circuit breaker states
- **Batch metrics**: batch size, batch formation time
- **Retry metrics**: retry count, backoff delays
- **Quota metrics**: usage per tenant, rate limit hits
- **Error metrics**: failure reasons, DLQ size

### Logging
Every log line includes:
- `request_id`: Trace across services
- `job_id`: Track individual job
- `tenant_id`: Per-tenant analysis
- `provider`: Which provider handled request
- `timestamp`: UTC timestamp

Example:
```
2025-10-18T10:00:01.123Z INFO [job=550e8400] [tenant=123] [provider=InLegalBERT] Job completed successfully
```

## Backpressure & Flow Control

### Soft Threshold
When queue depth crosses 70% of max:
- Throttle low-priority jobs
- Return backpressure signal to clients
- Increase batch formation time

### Hard Threshold
When queue depth crosses 90% of max:
- Reject new low-priority jobs
- Delay medium-priority jobs
- Only accept high-priority jobs
- Return 429 with retry-after header

### Per-Tenant Limits
- Max concurrent jobs per tenant (default: 3)
- Prevents single tenant monopolizing workers
- Fair scheduling across tenants

## Graceful Shutdown

1. **Stop accepting new jobs**
2. **Finish in-flight jobs** (up to shutdown timeout)
3. **Flush pending batches**
4. **Persist unstarted jobs** back to queue
5. **Close connections** cleanly

Shutdown timeout configurable via `SHUTDOWN_TIMEOUT_SECONDS` (default: 30)

## Security

- **Internal Auth**: API key required for all job endpoints
- **Tenant Isolation**: Jobs segregated by tenant ID
- **Idempotency**: Prevents duplicate job submission
- **Quota Enforcement**: Prevents abuse
- **Webhook Signing**: HMAC signatures for callbacks
- **Input Validation**: Pydantic models for all requests

## Files Implemented (1,416+ lines)

```
jobs/
├── __init__.py (module exports)
├── models.py (200 lines) - Job, Status, Priority, Batch models
├── queue_backend.py (200 lines) - In-memory & Redis queues
├── storage.py (250 lines) - Job storage & DLQ
├── circuit_breaker.py (200 lines) - Circuit breaker per provider
├── retry.py (200 lines) - Exponential backoff retry
├── batcher.py (180 lines) - Micro-batching logic
└── quota.py (180 lines) - Quota & rate limiting
```

## Still To Implement

1. **Worker Pool** - Async workers with concurrency control
2. **Queue Manager** - Orchestrates queue + storage + workers
3. **Job Lifecycle** - High-level job management API
4. **Metrics System** - Prometheus-style metrics
5. **API Endpoints** - FastAPI routes
6. **Webhook Delivery** - Async callback system
7. **Integration** - Wire into main.py

## Next Steps

1. Complete worker pool implementation
2. Build queue manager orchestration
3. Create job lifecycle API
4. Add observability/metrics
5. Implement FastAPI endpoints
6. Test all components
7. Document usage examples
8. Deploy to Railway

---

**Status**: Core components complete (60% done)  
**Lines of Code**: 1,416+  
**Estimated Completion**: 2,500+ lines total

