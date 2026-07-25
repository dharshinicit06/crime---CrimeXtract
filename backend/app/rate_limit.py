"""Rate limiting configuration: limiter instance and per-endpoint limiters.

This module initializes the Limiter from slowapi using settings.
Import it in main.py to attach to the app, and in individual routers
for per-endpoint decorators.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    enabled=settings.RATE_LIMIT_ENABLED,
)

# ── Per-endpoint rate limiters (decorators) ────────────────────
login_limiter = limiter.limit(settings.LOGIN_RATE_LIMIT)
chat_limiter = limiter.limit("30/minute")
upload_limiter = limiter.limit("10/minute")
ml_limiter = limiter.limit("20/minute")
password_limiter = limiter.limit("5/minute")
