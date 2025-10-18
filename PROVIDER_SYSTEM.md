# Multi-Provider AI System

## Overview

The AI Engine now supports **multiple LLM providers** with **automatic fallback**. If the primary provider fails or times out, the system automatically switches to the next provider in the configured order.

## Supported Providers

1. **InLegalBERT** - Legal-specific BERT model (primary)
2. **DeepSeek** - DeepSeek AI model  
3. **Grok** - xAI's Grok model

## Architecture

```
┌─────────────────────────────────────────┐
│         Incoming Request                │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│        Provider Manager                 │
│  • Handles routing                      │
│  • Manages fallback                     │
│  • Tracks statistics                    │
└────────────────┬────────────────────────┘
                 │
          ┌──────┴──────┬──────────┐
          ▼             ▼          ▼
     ┌─────────┐  ┌─────────┐  ┌─────────┐
     │InLegal  │  │DeepSeek │  │  Grok   │
     │  BERT   │  │         │  │         │
     └─────────┘  └─────────┘  └─────────┘
     Primary       Fallback 1   Fallback 2
```

## Configuration

### Environment Variables (.env)

```bash
# Provider Order (comma-separated, priority order)
PROVIDER_ORDER=inlegalbert,deepseek,grok

# InLegalBERT Configuration
INLEGALBERT_API_KEY=your-api-key-here
INLEGALBERT_MODEL=inlegalbert-v1
INLEGALBERT_API_URL=https://api.inlegalbert.ai/v1
INLEGALBERT_TIMEOUT=30

# DeepSeek Configuration
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_URL=https://api.deepseek.com/v1
DEEPSEEK_TIMEOUT=30

# Grok Configuration
GROK_API_KEY=your-api-key-here
GROK_MODEL=grok-beta
GROK_API_URL=https://api.x.ai/v1
GROK_TIMEOUT=30
```

### Changing Provider Order

Simply modify `PROVIDER_ORDER` in `.env`:

```bash
# Use DeepSeek as primary, InLegalBERT as fallback
PROVIDER_ORDER=deepseek,inlegalbert

# Use only Grok
PROVIDER_ORDER=grok
```

## How Fallback Works

1. **Request arrives** at `/inference` or `/embed`
2. **Provider Manager** tries **primary provider** (first in PROVIDER_ORDER)
3. If primary **fails or times out**:
   - Automatically tries **next provider** in order
   - Logs the fallback event
   - Returns response from successful provider
4. If **all providers fail**: Returns error

## Code Structure

```
providers/
├── __init__.py                  # Module exports
├── base_provider.py             # Abstract base class
├── provider_manager.py          # Main orchestration logic
├── inlegal_bert_provider.py     # InLegalBERT implementation
├── deepseek_provider.py         # DeepSeek implementation
└── grok_provider.py             # Grok implementation
```

### Key Components

#### 1. BaseProvider (Abstract Class)

All providers inherit from this:

```python
class BaseProvider(ABC):
    @abstractmethod
    async def inference(query, context, max_tokens, temperature) -> ProviderResponse
    
    @abstractmethod
    async def generate_embeddings(texts) -> EmbeddingResponse
    
    @abstractmethod
    async def health_check() -> bool
```

#### 2. ProviderManager

Orchestrates all providers:

```python
class ProviderManager:
    def __init__(self)  # Loads from env vars
    
    async def inference(...)  # With automatic fallback
    async def generate_embeddings(...)  # With fallback
    async def health_check_all()  # Check all providers
    def get_stats()  # Usage statistics
```

#### 3. Individual Providers

Each provider implements the base interface:
- `InLegalBERTProvider` - Legal AI
- `DeepSeekProvider` - General AI
- `GrokProvider` - xAI's model

## API Endpoints

### GET /health

Returns service status and active providers:

```json
{
  "status": "ok",
  "uptime_seconds": 123.45,
  "model_provider": "InLegalBERT, DeepSeek, Grok",
  "service": "ai-engine",
  "timestamp": "2025-10-18T..."
}
```

### GET /providers/status

Returns detailed provider health and statistics:

```json
{
  "provider_health": {
    "InLegalBERT": {
      "status": "healthy",
      "model": "inlegalbert-v1"
    },
    "DeepSeek": {
      "status": "healthy",
      "model": "deepseek-chat"
    }
  },
  "statistics": {
    "total_requests": 150,
    "provider_usage": {
      "inlegalbert": 120,
      "deepseek": 25,
      "grok": 5
    },
    "fallback_count": 30,
    "active_providers": ["InLegalBERT", "DeepSeek", "Grok"]
  }
}
```

### POST /inference

Uses provider system with automatic fallback:

```bash
curl -X POST http://localhost:8080/inference \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are contract requirements?",
    "context": "Indian Contract Act",
    "max_tokens": 512,
    "temperature": 0.7
  }'
```

Response includes which provider handled it:

```json
{
  "answer": "...",
  "model": "InLegalBERT/inlegalbert-v1",
  "tokens_used": 45,
  "confidence": 0.92
}
```

### POST /embed

Generates embeddings with fallback:

```bash
curl -X POST http://localhost:8080/embed \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Legal document 1", "Legal document 2"]
  }'
```

## Logging

The system logs all provider interactions:

```
INFO:providers.provider_manager:Attempting inference with provider: InLegalBERT
INFO:providers.provider_manager:Primary provider InLegalBERT succeeded

# Or if fallback occurs:
ERROR:providers.provider_manager:Provider InLegalBERT failed: Connection timeout
INFO:providers.provider_manager:Trying next provider in fallback chain...
WARNING:providers.provider_manager:Fallback to DeepSeek (attempt 2)
```

## Adding a New Provider

1. **Create provider file**: `providers/new_provider.py`

```python
from .base_provider import BaseProvider, ProviderResponse, EmbeddingResponse

class NewProvider(BaseProvider):
    @property
    def provider_name(self) -> str:
        return "NewProvider"
    
    async def inference(self, query, context, max_tokens, temperature):
        # Your implementation
        pass
    
    async def generate_embeddings(self, texts):
        # Your implementation
        pass
    
    async def health_check(self):
        # Your implementation
        pass
```

2. **Register in ProviderManager**:

```python
# In provider_manager.py
from .new_provider import NewProvider

PROVIDER_REGISTRY = {
    "inlegalbert": InLegalBERTProvider,
    "deepseek": DeepSeekProvider,
    "grok": GrokProvider,
    "newprovider": NewProvider,  # Add here
}
```

3. **Add to .env**:

```bash
PROVIDER_ORDER=newprovider,inlegalbert,deepseek

NEWPROVIDER_API_KEY=your-key
NEWPROVIDER_MODEL=model-name
NEWPROVIDER_API_URL=https://api.newprovider.com/v1
NEWPROVIDER_TIMEOUT=30
```

4. **Done!** The system will automatically use your new provider.

## Testing

### Test All Providers

```bash
cd /Users/raghavankarthik/ai-law-junior/ai-engine

# Start server
uvicorn main:app --reload --port 8080

# Test health
curl http://localhost:8080/health

# Test provider status
curl http://localhost:8080/providers/status

# Test inference
curl -X POST http://localhost:8080/inference \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'

# Test embeddings
curl -X POST http://localhost:8080/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["test text"]}'
```

### Verify Fallback

1. Set invalid API key for primary provider
2. Make request
3. Check logs - should show fallback to next provider

## Production Deployment

### Railway Environment Variables

In Railway dashboard, add:

```
PROVIDER_ORDER=inlegalbert,deepseek,grok
INLEGALBERT_API_KEY=<your-key>
DEEPSEEK_API_KEY=<your-key>
GROK_API_KEY=<your-key>
LOG_LEVEL=INFO
```

### Monitoring

- Check `/providers/status` for provider health
- Monitor logs for fallback events
- Track `statistics.fallback_count` for reliability metrics

## Benefits

1. ✅ **High Availability** - If one provider fails, others take over
2. ✅ **Flexibility** - Easy to add/remove providers
3. ✅ **No Code Changes** - Configure via environment variables
4. ✅ **Logging** - Full visibility into which provider handled each request
5. ✅ **Statistics** - Track usage and fallback patterns
6. ✅ **Modular** - Each provider is independent

## Future Enhancements

- [ ] Load balancing across multiple providers
- [ ] Cost optimization (route to cheapest provider first)
- [ ] Response quality scoring
- [ ] Provider-specific rate limiting
- [ ] Caching layer
- [ ] A/B testing between providers

---

**Version**: 1.0.0  
**Last Updated**: October 2025

