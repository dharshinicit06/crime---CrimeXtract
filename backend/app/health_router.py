"""Health monitoring endpoints for production readiness."""

import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import get_db_session
from app.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class HealthComponent(BaseModel):
    status: str = "healthy"
    message: str = ""
    latency_ms: float = 0.0


class HealthReport(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    environment: str = "development"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    uptime: float = 0.0
    components: dict[str, HealthComponent] = {}


_start_time = time.monotonic()


@router.get(
    "",
    response_model=HealthReport,
    summary="Comprehensive health check",
    description="Returns the overall health status and individual component health.",
)
async def health_check(session: AsyncSession = Depends(get_db_session)) -> HealthReport:
    """Check overall system health including database connectivity."""
    components: dict[str, HealthComponent] = {}
    overall = "healthy"

    # Database health
    db_start = time.monotonic()
    try:
        await session.execute(text("SELECT 1"))
        db_latency = (time.monotonic() - db_start) * 1000
        components["database"] = HealthComponent(
            status="healthy", message="PostgreSQL connected", latency_ms=round(db_latency, 2)
        )
    except Exception as exc:
        db_latency = (time.monotonic() - db_start) * 1000
        components["database"] = HealthComponent(
            status="unhealthy", message=str(exc), latency_ms=round(db_latency, 2)
        )
        overall = "unhealthy"

    from app import __version__
    return HealthReport(
        status=overall,
        version=__version__,
        environment=settings.ENVIRONMENT,
        uptime=round(time.monotonic() - _start_time, 2),
        components=components,
    )


@router.get(
    "/database",
    response_model=HealthComponent,
    summary="Database health check",
)
async def database_health(session: AsyncSession = Depends(get_db_session)) -> HealthComponent:
    """Check database connectivity."""
    start = time.monotonic()
    try:
        await session.execute(text("SELECT 1"))
        latency = (time.monotonic() - start) * 1000
        return HealthComponent(status="healthy", message="PostgreSQL connected", latency_ms=round(latency, 2))
    except Exception as exc:
        latency = (time.monotonic() - start) * 1000
        return HealthComponent(status="unhealthy", message=str(exc), latency_ms=round(latency, 2))


@router.get(
    "/ml",
    response_model=HealthComponent,
    summary="ML model health check",
)
async def ml_health() -> HealthComponent:
    """Check whether the ML prediction model is loaded."""
    from app.ml.services import model as ml_model
    if ml_model is not None:
        return HealthComponent(status="healthy", message="ML model is loaded and ready")
    return HealthComponent(status="unhealthy", message="ML model is not loaded")


@router.get(
    "/gemini",
    response_model=HealthComponent,
    summary="Gemini AI health check",
)
async def gemini_health() -> HealthComponent:
    """Check whether the Gemini AI service is configured."""
    from app.chat.gemini_service import _model as gemini_model
    if gemini_model is not None:
        return HealthComponent(status="healthy", message="Gemini AI is configured and ready")
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ("", "your-gemini-api-key-here"):
        return HealthComponent(status="degraded", message="GEMINI_API_KEY is set but model failed to load")
    return HealthComponent(status="degraded", message="GEMINI_API_KEY not configured")


@router.get(
    "/system",
    response_model=HealthComponent,
    summary="System resource health check",
)
async def system_health() -> HealthComponent:
    """Check system resources (CPU, memory, disk)."""
    import os
    import psutil
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        message = (
            f"CPU: {cpu_percent}% | Memory: {memory.percent}% used "
            f"({memory.used // (1024**2)}MB/{memory.total // (1024**2)}MB) | "
            f"Disk: {disk.percent}% used"
        )
        status = "healthy" if cpu_percent < 90 and memory.percent < 90 and disk.percent < 90 else "degraded"
        return HealthComponent(status=status, message=message)
    except ImportError:
        return HealthComponent(status="healthy", message="psutil not installed - system metrics unavailable")
    except Exception as exc:
        return HealthComponent(status="degraded", message=str(exc))
