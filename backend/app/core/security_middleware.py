"""Security headers middleware for production hardening.

Adds security-related HTTP response headers to mitigate common web vulnerabilities.
"""

from typing import Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that attaches security headers to every response.

    Headers applied:
      - X-Content-Type-Options: nosniff
      - X-Frame-Options: DENY
      - X-XSS-Protection: 1; mode=block
      - Strict-Transport-Security: (only in production)
      - Cache-Control: no-store (for sensitive API paths)
    """

    SENSITIVE_PREFIXES = {"/api/v1/auth/", "/api/v1/users/"}

    STABLE_HEADERS: Dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # ── Always-on security headers ────────────────────────
        for header, value in self.STABLE_HEADERS.items():
            response.headers[header] = value

        # ── HSTS only in production ───────────────────────────
        from app.config import settings

        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # ── Cache-Control for sensitive endpoints ─────────────
        path = request.url.path
        if any(path.startswith(prefix) for prefix in self.SENSITIVE_PREFIXES):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response
