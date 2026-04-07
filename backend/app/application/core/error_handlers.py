"""Global exception handlers registered on the FastAPI app."""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    NotFoundError,
    ValidationError,
)

logger = structlog.get_logger()


def register_error_handlers(app: FastAPI) -> None:
    """Attach exception handlers to the application."""

    @app.exception_handler(AuthenticationError)
    async def authentication_handler(
        _request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc), "code": "AUTHENTICATION_ERROR"},
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_handler(
        _request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"detail": str(exc), "code": "AUTHORIZATION_ERROR"},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "code": "NOT_FOUND"},
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(
        _request: Request, exc: ValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "code": "VALIDATION_ERROR"},
        )

    @app.exception_handler(BusinessLogicError)
    async def business_error_handler(
        _request: Request, exc: BusinessLogicError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "code": "BUSINESS_ERROR"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception,
    ) -> JSONResponse:
        """Catch-all for unhandled exceptions.

        Logs the full traceback with the request ID so officials can
        trace the failure in structured logs and open an investigation.
        Returns a safe, generic message — never leaks internal details.
        """
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception(
            "unhandled_server_error",
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            exc_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": (
                    "An unexpected error occurred. Please quote the request ID "
                    "when reporting this issue to an election official."
                ),
                "code": "INTERNAL_SERVER_ERROR",
                "request_id": request_id,
            },
        )
