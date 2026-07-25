"""Pydantic schemas for Predictive Crime Analytics API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PredictionPoint(BaseModel):
    """A single prediction point in a time series."""
    month: str = Field(..., description="Month label (e.g. '2026-08')")
    predicted_count: float = Field(..., description="Predicted number of crimes")
    lower_bound: float = Field(..., description="Lower confidence interval")
    upper_bound: float = Field(..., description="Upper confidence interval")
    historical_count: Optional[float] = Field(None, description="Actual historical count if available")


class HotspotTrend(BaseModel):
    """Predicted trend for a hotspot district."""
    district: str = Field(..., description="District name")
    current_count: int = Field(..., description="Current crime count")
    predicted_next_month: float = Field(..., description="Predicted crimes next month")
    trend: str = Field(..., description="Trend direction: rising, stable, declining")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Risk score 0-100")


class SeasonalPattern(BaseModel):
    """Seasonal crime pattern insight."""
    season: str = Field(..., description="Season name (e.g. 'Winter', 'Summer', 'Monsoon')")
    average_crimes: float = Field(..., description="Average historical crimes in this season")
    peak_crime_type: Optional[str] = Field(None, description="Most common crime type in this season")
    change_percent: Optional[float] = Field(None, description="Percent change from previous season")


class CrimeForecast(BaseModel):
    """Complete crime forecast response."""
    predictions: list[PredictionPoint] = Field(..., description="Monthly prediction time series")
    hotspot_trends: list[HotspotTrend] = Field(default_factory=list, description="District-level trend forecasts")
    seasonal_patterns: list[SeasonalPattern] = Field(default_factory=list, description="Seasonal crime patterns")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score 0.0-1.0")
    total_predicted: float = Field(..., description="Total predicted crimes for next month")
    total_historical: int = Field(0, description="Total historical crimes analyzed")
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Generation timestamp")
