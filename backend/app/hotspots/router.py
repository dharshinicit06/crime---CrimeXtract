"""Crime Hotspots API router - dedicated endpoint for hotspot analysis."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.auth.models import User
from app.hotspots.schemas import (
    HotspotDetail,
    HotspotListResponse,
    HotspotMapResponse,
    HotspotAIInsightsResponse,
)
from app.hotspots.services import CrimeHotspotService

router = APIRouter(prefix="/hotspots", tags=["crime-hotspots"])


def get_hotspot_service(
    session: AsyncSession = Depends(get_db_session),
) -> CrimeHotspotService:
    return CrimeHotspotService(session=session)


@router.get(
    "",
    response_model=HotspotListResponse,
    summary="List crime hotspot districts with risk scores",
)
@router.get(
    "/",
    response_model=HotspotListResponse,
    summary="List crime hotspot districts with risk scores",
    include_in_schema=False,
)
async def list_hotspots(
    time_range: str = Query("all", description="Time range: 7d, 30d, 90d, all"),
    crime_type_id: Optional[int] = Query(None, description="Filter by crime type ID"),
    priority: Optional[str] = Query(None, description="Filter by priority: Low, Medium, High, Critical"),
    search: Optional[str] = Query(None, description="Search by district, city, or area"),
    current_user: User = Depends(get_current_user),
    service: CrimeHotspotService = Depends(get_hotspot_service),
) -> HotspotListResponse:
    """Return all hotspot districts with computed risk scores and counts.
    Supports time range filtering, crime type filter, priority filter, and text search.
    """
    return await service.get_hotspots(
        time_range=time_range,
        crime_type_id=crime_type_id,
        priority=priority,
        search=search,
    )


@router.get(
    "/map",
    response_model=HotspotMapResponse,
    summary="GIS-ready map data for crime hotspots",
)
async def hotspot_map(
    current_user: User = Depends(get_current_user),
    service: CrimeHotspotService = Depends(get_hotspot_service),
) -> HotspotMapResponse:
    """Return all locations with crime data as GIS-ready points.
    Each point includes latitude, longitude, crime_count, and risk_level.
    Ready for Leaflet / Google Maps integration.
    """
    return await service.get_hotspot_map()


@router.get(
    "/insights",
    response_model=HotspotAIInsightsResponse,
    summary="AI-generated insights for hotspot districts",
)
async def hotspot_insights(
    current_user: User = Depends(get_current_user),
    service: CrimeHotspotService = Depends(get_hotspot_service),
) -> HotspotAIInsightsResponse:
    """Return AI-generated insights for top hotspot districts."""
    return await service.get_hotspot_insights()


@router.get(
    "/{district}",
    response_model=HotspotDetail,
    summary="Detailed hotspot information for a specific district",
)
async def hotspot_detail(
    district: str,
    current_user: User = Depends(get_current_user),
    service: CrimeHotspotService = Depends(get_hotspot_service),
) -> HotspotDetail:
    """Return detailed information for a specific hotspot district.
    Includes crime type breakdown, status breakdown, monthly trend,
    recent FIRs, and AI-generated insight.
    """
    result = await service.get_hotspot_detail(district=district)
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"No hotspot data found for district '{district}'",
        )
    return result
