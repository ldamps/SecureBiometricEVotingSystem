"""Request-level security checks.

• Validates that requests coming through the gateway carry the expected
  X-Forwarded-For / X-Real-IP headers (optional, configurable via env).
• Rejects requests with excessively large Content-Length early.
"""

import os

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Max body size the backend will accept (bytes). Default 5 MB.
MAX_BODY_BYTES = int(os.getenv("MAX_REQUEST_BODY_BYTES", str(5 * 1024 * 1024)))

# When True, reject requests that do not have X-Forwarded-For
# (i.e. they did not come through the gateway). Disabled in dev.
REQUIRE_GATEWAY = os.getenv("REQUIRE_GATEWAY", "false").lower() == "true"


class RequestSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 1. Gateway-origin check (production only)
        if REQUIRE_GATEWAY and not request.headers.get("X-Forwarded-For"):
            return JSONResponse(
                {"detail": "Direct access not allowed"}, status_code=403
            )

        # 2. Content-Length guard
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_BODY_BYTES:
            return JSONResponse(
                {"detail": "Request body too large"}, status_code=413
            )

        return await call_next(request)
