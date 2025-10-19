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
import logging
from dotenv import load_dotenv

# Import provider manager
from providers import ProviderManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Legal India AI Engine",
    description="AI/ML service for legal document processing and intelligent querying",
    version="1.0.0"
)

# Initialize provider manager with error handling
try:
    provider_manager = ProviderManager()
    logger.info("Provider manager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize provider manager: {e}")
    # Create a minimal fallback
    provider_manager = None

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
    
    # Get active providers
    if provider_manager and provider_manager.providers:
        active_providers = [p.provider_name for p in provider_manager.providers]
        provider_str = ", ".join(active_providers)
    else:
        provider_str = "None (initialization failed)"
    
    return HealthResponse(
        status="ok",
        uptime_seconds=uptime,
        model_provider=provider_str,
        service="ai-engine-with-real-inlegalbert",
        timestamp=datetime.now().isoformat()
    )


@app.post("/inference", response_model=InferenceResponse)
async def inference(request: InferenceRequest):
    """
    Receives lawyer queries, processes through AI model, returns answer
    
    Uses provider manager with automatic fallback between providers
    """
    try:
        logger.info(f"Inference request received: query='{request.query[:50]}...'")
        
        # Check if provider manager is available
        if not provider_manager:
            raise HTTPException(status_code=503, detail="AI providers not available - service initialization failed")
        
        # Use provider manager with automatic fallback
        response = await provider_manager.inference(
            query=request.query,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        logger.info(f"Inference successful with provider: {response.provider_name}")
        
        return InferenceResponse(
            answer=response.answer,
            model=f"{response.provider_name}/{response.model_name}",
            tokens_used=response.tokens_used,
            confidence=response.confidence
        )
    
    except Exception as e:
        logger.error(f"Inference failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.post("/embed", response_model=EmbedResponse)
async def generate_embeddings(request: EmbedRequest):
    """
    Generates vector embeddings for documents or text
    
    Uses provider manager with automatic fallback
    """
    try:
        logger.info(f"Embedding request received for {len(request.texts)} texts")
        
        # Use provider manager with automatic fallback
        response = await provider_manager.generate_embeddings(request.texts)
        
        logger.info(f"Embeddings generated with provider: {response.provider_name}")
        
        return EmbedResponse(
            embeddings=response.embeddings,
            model=f"{response.provider_name}/{response.model_name}",
            dimension=response.dimension
        )
    
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    Runs semantic search within stored embeddings
    
    This endpoint performs vector similarity search for relevant legal documents
    Currently returns placeholder results
    """
    try:
        logger.info(f"Search request: query='{request.query}', top_k={request.top_k}")
        
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
        
        logger.info(f"Search completed, returning {len(dummy_results)} results")
        
        return SearchResponse(
            results=dummy_results,
            query=request.query,
            total_results=len(dummy_results)
        )
    
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/providers/status")
async def provider_status():
    """Get status of all configured providers"""
    try:
        health_status = await provider_manager.health_check_all()
        stats = provider_manager.get_stats()
        
        return {
            "provider_health": health_status,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Provider status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with service information"""
    if provider_manager:
        stats = provider_manager.get_stats()
        return {
            "service": "Legal India AI Engine",
            "version": "1.0.0",
            "status": "running",
            "active_providers": stats["active_providers"],
            "provider_order": stats["provider_order"],
            "endpoints": {
                "health": "/health",
                "inference": "/inference",
                "embed": "/embed",
                "search": "/search",
                "provider_status": "/providers/status"
            }
        }
    else:
        return {
            "service": "Legal India AI Engine",
            "version": "1.0.0",
            "status": "initialization_failed",
            "error": "Provider manager failed to initialize",
            "endpoints": {
                "health": "/health"
            }
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting AI Engine on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
