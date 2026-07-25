"""Pydantic schemas for Crime Prediction responses."""

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CrimeProbability(BaseModel):
    """Predicted crime probability for a specific district/category."""
    district: str = Field(..., description="District or area")
    crime_category: Optional[str] = Field(None, description="Specific crime type (None = overall)")
    probability: float = Field(..., ge=0.0, le=1.0, description="Crime probability score 0.0-1.0")
    predicted_count: float = Field(..., description="Expected number of incidents")
    confidence: str = Field(..., description="Confidence level: low, medium, high")
    reasoning: str = Field(..., description="Rule-based reasoning for this prediction")


class HotspotInfo(BaseModel):
    """Identified crime hotspot."""
    district: str = Field(..., description="District name")
    hotspot_score: float = Field(..., ge=0.0, le=100.0, description="Hotspot intensity score")
    crime_count: int = Field(0, description="Historical crime count")
    trend: str = Field(..., description="Trend direction: rising, stable, declining")
    top_crime_types: list[str] = Field(default_factory=list, description="Most frequent crime types")
    reasoning: str = Field(..., description="Why this is identified as a hotspot")


class PatrolSuggestion(BaseModel):
    """Actionable patrol recommendation."""
    district: str = Field(..., description="District for patrol")
    priority: str = Field(..., description="Priority: low, medium, high, critical")
    suggestion: str = Field(..., description="Concrete patrol action")
    reason: str = Field(..., description="Data-driven justification")
    time_window: Optional[str] = Field(None, description="Recommended patrol time window (e.g. '18:00-22:00')")


class CrimePredictionMetadata(BaseModel):
    """Metadata about the prediction computation."""
    data_period: str = Field(..., description="Date range of analyzed historical data")
    total_crimes_analyzed: int = Field(0, description="Number of crime records used")
    total_districts: int = Field(0, description="Number of districts analyzed")
    prediction_horizon: str = Field("next_7_days", description="Forecast timeframe")
    model_version: str = Field("rule-based-v1", description="Prediction model identifier")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


class CrimePredictionResponse(BaseModel):
    """Complete crime prediction response."""
    predictions: list[CrimeProbability] = Field(..., description="Per-district crime probability forecasts")
    hotspots: list[HotspotInfo] = Field(..., description="Identified crime hotspots")
    patrol_suggestions: list[PatrolSuggestion] = Field(..., description="Actionable patrol recommendations")
    metadata: CrimePredictionMetadata = Field(..., description="Prediction metadata")
