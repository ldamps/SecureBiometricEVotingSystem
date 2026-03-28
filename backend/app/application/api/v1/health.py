# app/application/api/v1/health.py - Health check API

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
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

class ReadinessResponse(BaseModel):
    status: str = Field(..., example="ok")
    database: str = Field(..., example="connected")
    version: str = Field(..., example="1.0.0")

### ROUTES ###
@router.get(
    "",
    summary="Health check - liveness check",
    response_model=HealthResponse,
    status_code=200,
)
async def health_check(request: Request) -> HealthResponse:
    """
    Liveness check — confirms the process is running.
    """
    return HealthResponse(
        status="ok",
        version=getattr(request.app, "version", "0.1.0"),
        stage=getattr(request.app, "stage", "dev"),
    )


@router.get(
    "/ready",
    summary="Readiness check - verifies DB connectivity",
    response_model=ReadinessResponse,
    status_code=200,
)
async def readiness_check(request: Request) -> ReadinessResponse:
    """
    Readiness check — verifies the service can handle requests
    by confirming database connectivity.
    """
    db_status = "disconnected"
    try:
        session_factory = request.app.state.session_factory
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        logger.error("readiness_check_failed", component="database")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "version": getattr(request.app, "version", "0.1.0"),
            },
        )

    return ReadinessResponse(
        status="ok",
        database=db_status,
        version=getattr(request.app, "version", "0.1.0"),
    )
