"""
FastAPI backend for Secure Biometric E-Voting System.
Run with: uvicorn main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db import get_db, init_async_db, dispose_async_db
from app.application.api import register_all_versions
from app.application.middleware import (
    RequestContextMiddleware,
    RequestSecurityMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggerMiddleware,
)
from app.application.middleware.cors.config import ALLOWED_ORIGINS
from app.application.core.error_handlers import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize async DB for versioned API (voter, etc.) and dispose on shutdown."""
    session_factory = init_async_db()
    app.state.session_factory = session_factory
    yield
    await dispose_async_db()


app = FastAPI(
    title="Secure Biometric E-Voting System API",
    description="Backend API for the Secure Biometric Electronic Voting System",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Middleware stack (outermost → innermost) ──────────────────────────────
# 1. CORS – must be outermost so preflight responses get correct headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-XSRF-TOKEN", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

# 2. Request context – assigns a unique request ID
app.add_middleware(RequestContextMiddleware)

# 3. Security checks – gateway-origin validation, body size guard
app.add_middleware(RequestSecurityMiddleware)

# 4. Security headers – defence-in-depth response headers
app.add_middleware(SecurityHeadersMiddleware)

# 5. Request logger – structured logging of every request
app.add_middleware(RequestLoggerMiddleware)

# Global error handlers
register_error_handlers(app)

# Mount versioned API (e.g. /api/v1/health, /api/v1/voter/...)
register_all_versions(app)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Secure Biometric E-Voting System API", "docs": "/docs"}


@app.get("/health")
def health():
    """Health check for deployment and monitoring."""
    return {"status": "ok"}


@app.get("/constituencies")
def list_constituencies(db: Session = Depends(get_db)):
    """List all constituencies (example DB-backed route)."""
    from app.models.sqlalchemy import Constituency
    return db.query(Constituency).all()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
