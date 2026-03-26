"""CORS configuration.

Centralises allowed origins so they can be used by both the FastAPI
CORSMiddleware and any validation logic.
"""

import os

# Comma-separated list in production; fallback to React dev server.
_raw = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw.split(",") if o.strip()]
