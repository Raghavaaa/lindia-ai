"""
Search endpoint for vector similarity search.
"""
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field

from core.logger import logger
from core.providers import provider_router

router = APIRouter()


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query: str = Field(..., min_length=1, max_length=5000, description="Search query")
    top_k: int = Field(5, ge=1, le=100, description="Number of results to return")
    tenant_id: str = Field(..., min_length=1, max_length=100, description="Tenant identifier")


class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    results: list
    total_count: int
    latency_ms: float


@router.post("/search", response_model=SearchResponse)
async def search(request: Request, body: SearchRequest):
    """
    Search for similar documents using vector similarity.
    
    Args:
        request: FastAPI request
        body: Search request body
        
    Returns:
        SearchResponse with results, count, and latency
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.info(
        "Search request received",
        extra={
            "request_id": request_id,
            "tenant_id": body.tenant_id,
            "query_length": len(body.query),
            "top_k": body.top_k,
        }
    )
    
    try:
        result = await provider_router.search(
            query=body.query,
            top_k=body.top_k,
            tenant_id=body.tenant_id,
            request_id=request_id
        )
        
        return SearchResponse(**result)
        
    except Exception as e:
        logger.error(
            f"Search failed: {str(e)}",
            extra={"request_id": request_id, "tenant_id": body.tenant_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "search_failed",
                "message": "Failed to perform vector search",
            }
        )

