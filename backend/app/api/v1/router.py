"""Main API v1 router aggregating all endpoint modules."""

from fastapi import APIRouter

from app.accused.router import router as accused_router
from app.audit_log.router import router as audit_log_router
from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.crime.router import router as crime_router
from app.network.router import router as network_graph_router
from app.prediction.router import router as prediction_router
from app.crime_analytics.router import router as crime_analytics_router
from app.crime_history.router import router as crime_history_router
from app.crime_prediction.router import router as crime_prediction_router
from app.evidence.router import router as evidence_router
from app.financial_transaction.router import router as financial_transaction_router
from app.fir.router import router as fir_router
from app.health_router import router as health_router
from app.location.router import router as location_router
from app.ml.router import router as ml_router
from app.hotspots.router import router as hotspots_router
from app.network_analysis.router import router as network_analysis_router
from app.offender_profiling.router import router as offender_profiling_router
from app.settings.router import router as settings_router
from app.users.router import router as users_router
from app.victim.router import router as victim_router
from app.schemas.common import HealthResponse, MessageResponse
from app.demo.router import router as demo_router


router = APIRouter()

router.include_router(accused_router)
router.include_router(audit_log_router)
router.include_router(auth_router)
router.include_router(chat_router)
router.include_router(users_router)
router.include_router(network_graph_router)
router.include_router(prediction_router)
router.include_router(hotspots_router)
router.include_router(fir_router)
router.include_router(crime_router)
router.include_router(crime_analytics_router)
router.include_router(crime_history_router)
router.include_router(crime_prediction_router)
router.include_router(evidence_router)
router.include_router(financial_transaction_router)
router.include_router(health_router)
router.include_router(location_router)
router.include_router(ml_router)
router.include_router(network_analysis_router)
router.include_router(offender_profiling_router)
router.include_router(settings_router)
router.include_router(victim_router)
router.include_router(demo_router)



@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["legacy-health"],
    summary="Simple Health Check (legacy)",
)
async def simple_health_check() -> HealthResponse:
    """Quick health check — returns basic status."""
    return HealthResponse()


@router.get(
    "/version",
    response_model=MessageResponse,
    tags=["health"],
    summary="Version Info",
)
async def version() -> MessageResponse:
    """Return the current API version."""
    from app import __version__

    return MessageResponse(message=f"Crime Intelligence Platform v{__version__}")
