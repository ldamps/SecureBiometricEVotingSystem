"""Global exception handlers registered on the FastAPI app."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.core.exceptions import (
    BusinessLogicError,
    NotFoundError,
    ValidationError,
)


def register_error_handlers(app: FastAPI) -> None:
    """Attach exception handlers to the application."""

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
