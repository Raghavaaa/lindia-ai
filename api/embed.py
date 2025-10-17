"""
Embedding endpoint for document vectorization.
"""
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field

from core.logger import logger
from core.providers import provider_router

router = APIRouter()


class EmbedRequest(BaseModel):
    """Request model for embedding endpoint."""
    doc_id: str = Field(..., min_length=1, max_length=200, description="Document identifier")
    text: str = Field(..., min_length=1, max_length=20000, description="Text to embed")


class EmbedResponse(BaseModel):
    """Response model for embedding endpoint."""
    vector_id: str
    vector_meta: dict


@router.post("/embed", response_model=EmbedResponse)
async def embed(request: Request, body: EmbedRequest):
    """
    Generate embeddings for the provided text.
    
    Args:
        request: FastAPI request
        body: Embedding request body
        
    Returns:
        EmbedResponse with vector_id and metadata
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.info(
        "Embedding request received",
        extra={
            "request_id": request_id,
            "doc_id": body.doc_id,
            "text_length": len(body.text),
        }
    )
    
    try:
        result = await provider_router.embed(
            doc_id=body.doc_id,
            text=body.text,
            request_id=request_id
        )
        
        return EmbedResponse(**result)
        
    except Exception as e:
        logger.error(
            f"Embedding generation failed: {str(e)}",
            extra={"request_id": request_id, "doc_id": body.doc_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "embedding_failed",
                "message": "Failed to generate embeddings",
            }
        )

