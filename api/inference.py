"""
Inference endpoint for AI model predictions.
"""
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field

from core.logger import logger
from core.providers import provider_router

router = APIRouter()


class InferenceRequest(BaseModel):
    """Request model for inference endpoint."""
    query: str = Field(..., min_length=1, max_length=5000, description="User query")
    context: str = Field(..., max_length=10000, description="Context for the query")
    tenant_id: str = Field(..., min_length=1, max_length=100, description="Tenant identifier")


class InferenceResponse(BaseModel):
    """Response model for inference endpoint."""
    answer: str
    sources: list
    model: str
    latency_ms: float


@router.post("/inference", response_model=InferenceResponse)
async def inference(request: Request, body: InferenceRequest):
    """
    Run AI inference on the provided query and context.
    
    Args:
        request: FastAPI request
        body: Inference request body
        
    Returns:
        InferenceResponse with answer, sources, model, and latency
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.info(
        "Inference request received",
        extra={
            "request_id": request_id,
            "tenant_id": body.tenant_id,
            "query_length": len(body.query),
            "context_length": len(body.context),
        }
    )
    
    try:
        result = await provider_router.inference(
            query=body.query,
            context=body.context,
            tenant_id=body.tenant_id,
            request_id=request_id
        )
        
        return InferenceResponse(**result)
        
    except Exception as e:
        logger.error(
            f"Inference failed: {str(e)}",
            extra={"request_id": request_id, "tenant_id": body.tenant_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "inference_failed",
                "message": "Failed to generate inference response",
            }
        )

