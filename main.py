"""
AI Engine Service - FastAPI Application
Provides AI/ML inference, embeddings, and semantic search for Legal India platform
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Legal India AI Engine",
    description="AI/ML service for legal document processing and intelligent querying",
    version="1.0.0"
)

# CORS Configuration - Allow internal domains only
ALLOWED_ORIGINS = [
    "https://legalindia.ai",
    "https://api.legalindia.ai",
    "https://backend.legalindia.ai",
    os.getenv("BACKEND_URL", "http://localhost:8000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Track service start time for uptime calculation
SERVICE_START_TIME = datetime.now()

# Pydantic Models for Request/Response
class InferenceRequest(BaseModel):
    query: str
    context: Optional[str] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7

class InferenceResponse(BaseModel):
    answer: str
    model: str
    tokens_used: Optional[int] = None
    confidence: Optional[float] = None

class EmbedRequest(BaseModel):
    texts: List[str]
    model: Optional[str] = "InLegalBERT"

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimension: int

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    filter: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    total_results: int

class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    status: str
    uptime_seconds: float
    model_provider: str
    service: str
    timestamp: str


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for Railway monitoring
    Returns service status and uptime information
    """
    uptime = (datetime.now() - SERVICE_START_TIME).total_seconds()
    
    return HealthResponse(
        status="ok",
        uptime_seconds=uptime,
        model_provider=os.getenv("MODEL_PROVIDER", "InLegalBERT"),
        service="ai-engine",
        timestamp=datetime.now().isoformat()
    )


@app.post("/inference", response_model=InferenceResponse)
async def inference(request: InferenceRequest):
    """
    Receives lawyer queries, processes through AI model, returns answer
    
    This endpoint will integrate with InLegalBERT or other legal AI models
    Currently returns placeholder response
    """
    try:
        # Placeholder logic - will be replaced with actual model inference
        model_provider = os.getenv("MODEL_PROVIDER", "InLegalBERT")
        
        # TODO: Integrate actual model inference
        # answer = await run_model_inference(request.query, request.context)
        
        answer = f"Inference working. Query received: '{request.query}'. Model: {model_provider}. This is a placeholder response that will be replaced with actual legal AI inference."
        
        return InferenceResponse(
            answer=answer,
            model=model_provider,
            tokens_used=50,  # Placeholder
            confidence=0.95  # Placeholder
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.post("/embed", response_model=EmbedResponse)
async def generate_embeddings(request: EmbedRequest):
    """
    Generates vector embeddings for documents or text
    
    This endpoint will use InLegalBERT or similar model for embeddings
    Currently returns placeholder embeddings
    """
    try:
        model = request.model or os.getenv("MODEL_PROVIDER", "InLegalBERT")
        
        # Placeholder logic - will be replaced with actual embedding generation
        # TODO: Integrate actual embedding model
        # embeddings = await generate_text_embeddings(request.texts, model)
        
        # Generate dummy embeddings (768 dimensions typical for BERT models)
        dummy_embeddings = [[0.1] * 768 for _ in request.texts]
        
        return EmbedResponse(
            embeddings=dummy_embeddings,
            model=model,
            dimension=768
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    Runs semantic search within stored embeddings
    
    This endpoint performs vector similarity search for relevant legal documents
    Currently returns placeholder results
    """
    try:
        # Placeholder logic - will be replaced with actual vector search
        # TODO: Integrate vector database (Pinecone, Weaviate, or FAISS)
        # results = await vector_search(request.query, request.top_k, request.filter)
        
        # Generate dummy search results
        dummy_results = [
            {
                "id": f"doc_{i}",
                "content": f"Legal document {i} matching query: {request.query}",
                "score": 0.95 - (i * 0.1),
                "metadata": {
                    "case_id": f"CASE_{i}",
                    "year": 2024,
                    "court": "Supreme Court"
                }
            }
            for i in range(1, min(request.top_k + 1, 6))
        ]
        
        return SearchResponse(
            results=dummy_results,
            query=request.query,
            total_results=len(dummy_results)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Legal India AI Engine",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "inference": "/inference",
            "embed": "/embed",
            "search": "/search"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
