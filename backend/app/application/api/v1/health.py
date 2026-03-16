# app/application/api/v1/health.py - Health check API

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()

router = APIRouter(
    prefix="/health",
    tags=["health", "system"],
)

### SCHEMAS ###
class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")
    version: str = Field(..., example="1.0.0")
    stage: str = Field(..., example="prod")

### ROUTES ###
@router.get(
    "",
    summary="Health check - liveness check",
    response_model=HealthResponse,
    status_code=200,
)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check - liveness check
    """
    return HealthResponse(
        status="ok",
        version=getattr(request.app, "version", "0.1.0"),
        stage=getattr(request.app, "stage", "dev"),
    )
