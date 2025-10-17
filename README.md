# Legal India AI Engine

Standalone FastAPI service providing AI/ML capabilities for the Legal India platform.

## Overview

This service provides:
- **Inference**: Legal query processing using InLegalBERT
- **Embeddings**: Vector embeddings generation for legal documents
- **Semantic Search**: Vector similarity search for relevant legal content
- **Health Monitoring**: Service status and uptime tracking

## Architecture

This is an **internal service** designed to run on Railway and communicate privately with the Legal India backend. Public access is restricted via CORS.

## Endpoints

### `GET /health`
Health check endpoint for Railway monitoring.

**Response:**
```json
{
  "status": "ok",
  "uptime_seconds": 12345.67,
  "model_provider": "InLegalBERT",
  "service": "ai-engine",
  "timestamp": "2025-10-17T10:30:00"
}
```

### `POST /inference`
Process lawyer queries through AI model.

**Request:**
```json
{
  "query": "What are the requirements for a valid contract?",
  "context": "Indian Contract Act, 1872",
  "max_tokens": 512,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "answer": "According to Section 10 of the Indian Contract Act...",
  "model": "InLegalBERT",
  "tokens_used": 150,
  "confidence": 0.95
}
```

### `POST /embed`
Generate vector embeddings for text.

**Request:**
```json
{
  "texts": ["Legal document 1", "Legal document 2"],
  "model": "InLegalBERT"
}
```

**Response:**
```json
{
  "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
  "model": "InLegalBERT",
  "dimension": 768
}
```

### `POST /search`
Semantic search within stored embeddings.

**Request:**
```json
{
  "query": "contract law precedents",
  "top_k": 5,
  "filter": {"court": "Supreme Court", "year": 2024}
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "doc_1",
      "content": "...",
      "score": 0.95,
      "metadata": {}
    }
  ],
  "query": "contract law precedents",
  "total_results": 5
}
```

## Setup & Deployment

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run the server:**
```bash
uvicorn main:app --reload --port 8080
```

4. **Test endpoints:**
```bash
curl http://localhost:8080/health
```

### Railway Deployment

1. **Push to GitHub:**
```bash
git add .
git commit -m "Initial AI Engine setup"
git push origin main
```

2. **Deploy on Railway:**
   - Create new project on Railway
   - Connect GitHub repository
   - Railway will auto-detect Procfile and deploy
   - Add environment variables in Railway dashboard

3. **Configure environment variables on Railway:**
   - `MODEL_PROVIDER=InLegalBERT`
   - `BACKEND_URL=https://api.legalindia.ai`
   - `ENVIRONMENT=production`

4. **Verify deployment:**
   - Visit: `https://your-service.railway.app/health`
   - Should return: `{"status": "ok", ...}`

## CORS Configuration

CORS is configured to allow requests **only from internal domains**:
- `https://legalindia.ai`
- `https://api.legalindia.ai`
- `https://backend.legalindia.ai`

Public access is restricted for security.

## Future Enhancements

Current implementation uses placeholder responses. Future updates will include:

1. **Model Integration:**
   - InLegalBERT for legal text understanding
   - Fine-tuned models for Indian legal system
   - Support for multiple model providers

2. **Vector Database:**
   - Pinecone/Weaviate for production-scale search
   - FAISS for local/development testing
   - Efficient similarity search algorithms

3. **Advanced Features:**
   - Document summarization
   - Case law citation extraction
   - Legal entity recognition (NER)
   - Multi-language support (English, Hindi)

## API Keys Management

When ready to integrate actual models:

1. Add API keys to `.env`:
```
API_KEYS=your-huggingface-token,your-openai-key
```

2. Update Railway environment variables accordingly

3. Never commit `.env` to git (already in `.gitignore`)

## Tech Stack

- **Framework:** FastAPI 0.109.0
- **Server:** Gunicorn + Uvicorn workers
- **ML Models:** InLegalBERT (placeholder)
- **Deployment:** Railway
- **Language:** Python 3.10+

## Monitoring

Check service status:
- Health endpoint: `/health`
- Railway logs for errors and performance
- Uptime tracking via health checks

## Security

- CORS restricted to internal domains only
- Environment variables for sensitive data
- No public API access
- Private communication with backend

## Contact

For issues or questions, contact the development team.

---

**Status:** ✅ Deployed and operational  
**Last Updated:** October 2025
