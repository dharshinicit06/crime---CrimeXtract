"""Predictive Crime Analytics API."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db_session
from app.auth.models import User
from app.prediction.predictor import CrimePredictor

router = APIRouter(prefix="/prediction", tags=["crime-prediction-lr"])

@router.get("", summary="Linear Regression crime forecast")
@router.get("/", summary="Linear Regression crime forecast", include_in_schema=False)
async def get_crime_forecast(
    months_ahead: int = Query(3, ge=1, le=12, description="Months to forecast"),
    district: Optional[str] = Query(None, description="Scope to a district"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Generate crime forecasts using Linear Regression on historical FIR data."""
    predictor = CrimePredictor(session)
    return await predictor.forecast(months_ahead=months_ahead, district=district)
