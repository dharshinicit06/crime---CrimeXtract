"""FastAPI application entry point with rate limiting, security headers, and health monitoring."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import __app_name__, __version__
from app.api.v1.router import router as v1_router
from app.audit_log.middleware import AuditMiddleware
from app.config import settings
from app.core.database import dispose_engine
from app.exceptions.handlers import register_exception_handlers
from app.logging import get_logger, setup_logging
from app.core.security_middleware import SecurityHeadersMiddleware
from app.rate_limit import limiter

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    # ─── Startup ────────────────────────────────────────────────
    setup_logging()
    logger.info(
        "Starting %s v%s [%s]",
        __app_name__,
        __version__,
        settings.ENVIRONMENT,
    )
    yield
    # ─── Shutdown ───────────────────────────────────────────────
    logger.info("Shutting down %s ...", __app_name__)
    await dispose_engine()
    logger.info("Shutdown complete")


app = FastAPI(
    title=__app_name__,
    version=__version__,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
)

# ─── Rate Limiter state ─────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# ─── Rate Limiting ───────────────────────────────────────────────
app.add_middleware(SlowAPIMiddleware)

# ─── Security Headers ────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ─── Trusted Hosts ───────────────────────────────────────────────
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# ─── Compression ─────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─── Audit Logging ───────────────────────────────────────────────
app.add_middleware(AuditMiddleware)

# ─── Exception Handlers ─────────────────────────────────────────
register_exception_handlers(app)

# ─── Routers ────────────────────────────────────────────────────
app.include_router(v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["root"], summary="Root Endpoint")
async def root() -> dict:
    """Welcome endpoint."""
    return {
        "app": __app_name__,
        "version": __version__,
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }


if __name__ == "__main__":
    import os
    import uvicorn

    # Use Catalyst-assigned port if available, otherwise fall back to config
    port = int(os.getenv("X_ZOHO_CATALYST_LISTEN_PORT", settings.PORT))

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=port,
        reload=settings.is_development,
        workers=settings.WORKERS if not settings.is_development else 1,
        log_level=settings.LOG_LEVEL.lower(),
    )
