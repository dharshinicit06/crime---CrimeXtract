"""Offender Profiling API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.auth.models import User
from app.offender_profiling.schemas import OffenderProfile, TimelineResponse
from app.offender_profiling.services import OffenderProfilingService

router = APIRouter(prefix="/offender", tags=["offender-profiling"])


def get_profiling_service(
    session: AsyncSession = Depends(get_db_session),
) -> OffenderProfilingService:
    return OffenderProfilingService(session=session)


@router.get(
    "/{accused_id}",
    response_model=OffenderProfile,
    summary="Get offender risk profile with full intelligence",
)
async def get_offender_profile(
    accused_id: int,
    current_user: User = Depends(get_current_user),
    service: OffenderProfilingService = Depends(get_profiling_service),
) -> OffenderProfile:
    """Build and return a comprehensive offender risk profile.
    Combines modular scorers with FIR history, evidence, victim, location, and network data.
    """
    return await service.get_profile(accused_id=accused_id)


@router.get(
    "/{accused_id}/timeline",
    response_model=TimelineResponse,
    summary="Get chronological timeline for an offender",
)
async def get_offender_timeline(
    accused_id: int,
    current_user: User = Depends(get_current_user),
    service: OffenderProfilingService = Depends(get_profiling_service),
) -> TimelineResponse:
    """Return chronological timeline of all events linked to this accused.
    Includes FIR registrations, crime history records, and evidence collections.
    """
    return await service.get_timeline(accused_id=accused_id)
