"""Crime Analytics API endpoints - returns Chart.js-compatible JSON."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.auth.models import User
from app.crime_analytics.schemas import (
    AnalyticsPerformance,
    AnalyticsPrediction,
    AnalyticsRealtime,
    AnalyticsSummary,
    ChartResponse,
    DashboardResponse,
)
from app.crime_analytics.services import CrimeAnalyticsService

router = APIRouter(prefix="/analytics", tags=["crime-analytics"])


def get_analytics_service(
    session: AsyncSession = Depends(get_db_session),
) -> CrimeAnalyticsService:
    return CrimeAnalyticsService(session=session)


@router.get("/crime-by-month", response_model=ChartResponse, summary="Crime incidents grouped by month")
async def crime_by_month(
    year: Optional[int] = Query(None, description="Filter by year (e.g. 2025, 2026)"),
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> ChartResponse:
    return await service.crime_by_month(year=year)


@router.get("/crime-by-district", response_model=ChartResponse, summary="Crime incidents grouped by district")
async def crime_by_district(
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> ChartResponse:
    return await service.crime_by_district()


@router.get("/crime-by-type", response_model=ChartResponse, summary="Crime incidents grouped by crime category")
async def crime_by_type(
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> ChartResponse:
    return await service.crime_by_type()


@router.get("/solved-vs-pending", response_model=ChartResponse, summary="Solved vs pending FIR comparison")
async def solved_vs_pending(
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> ChartResponse:
    return await service.solved_vs_pending()


@router.get("/gender-wise", response_model=ChartResponse, summary="Victim gender distribution")
async def gender_wise(
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> ChartResponse:
    return await service.gender_wise()


@router.get("/age-wise", response_model=ChartResponse, summary="Victim age distribution (brackets)")
async def age_wise(
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> ChartResponse:
    return await service.age_wise()


@router.get("/top-hotspots", response_model=ChartResponse, summary="Top crime hotspot districts")
async def top_hotspots(
    limit: int = Query(10, ge=1, le=50, description="Number of hotspots to return"),
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> ChartResponse:
    return await service.top_hotspots(limit=limit)


@router.get("/dashboard", response_model=DashboardResponse, summary="Consolidated dashboard data")
async def dashboard(
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> DashboardResponse:
    """Return all dashboard widgets in one call: summary, crime_by_type, crime_by_month, top_hotspots, recent_firs, total_users."""
    return await service.dashboard_data()


@router.get("/predictions", response_model=AnalyticsPrediction, summary="Crime prediction / forecast data")
async def analytics_predictions(
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> AnalyticsPrediction:
    """Return crime forecast data: expected FIRs, confidence, high-risk districts, monthly forecast."""
    return await service.predictions()


@router.get("/performance", response_model=AnalyticsPerformance, summary="Officer investigation performance leaderboard")
async def analytics_performance(
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> AnalyticsPerformance:
    """Return officer performance stats (cases assigned, solved, pending, efficiency)."""
    return await service.performance()


@router.get("/realtime", response_model=AnalyticsRealtime, summary="Real-time activity feed")
async def analytics_realtime(
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> AnalyticsRealtime:
    """Return recent activity events (FIRs, evidence, case updates)."""
    return await service.realtime()


@router.get("/summary", response_model=AnalyticsSummary, summary="Aggregate analytics summary")
async def analytics_summary(
    current_user: User = Depends(get_current_user),
    service: CrimeAnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummary:
    return await service.summary()
