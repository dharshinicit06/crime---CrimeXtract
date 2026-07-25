"""Chart.js-compatible schemas for Crime Analytics responses."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChartDataset(BaseModel):
    """A single dataset within a Chart.js chart configuration."""
    label: str = Field(..., description="Dataset label")
    data: list[Any] = Field(..., description="Data values")
    backgroundColor: Optional[list[str]] = Field(None, description="Background colors")
    borderColor: Optional[list[str]] = Field(None, description="Border colors")
    borderWidth: Optional[int] = Field(None, description="Border width")


class ChartResponse(BaseModel):
    """Standard Chart.js-compatible response format."""
    labels: list[str] = Field(..., description="X-axis / category labels")
    datasets: list[ChartDataset] = Field(..., description="One or more datasets")


class AnalyticsSummary(BaseModel):
    """Aggregated summary statistics."""
    total_crimes: int = Field(0, description="Total number of crime incidents")
    total_firs: int = Field(0, description="Total number of FIRs registered")
    solved_count: int = Field(0, description="Number of solved/closed cases")
    pending_count: int = Field(0, description="Number of pending/open cases")
    conviction_rate: float = Field(0.0, description="Percentage of solved cases")
    unique_districts: int = Field(0, description="Number of distinct districts with crime")
    time_period: Optional[str] = Field(None, description="Analysed time period (e.g. '2025-01 to 2026-07')")


class RecentFIRItem(BaseModel):
    """Condensed FIR item for dashboard list views."""
    fir_id: int
    fir_number: str
    title: Optional[str] = None
    investigation_status: Optional[str] = None
    priority: Optional[str] = None
    incident_date: Optional[str] = None
    created_at: Optional[str] = None


class DashboardResponse(BaseModel):
    """Consolidated dashboard data returned in a single API call."""
    summary: AnalyticsSummary
    crime_by_type: ChartResponse
    crime_by_month: ChartResponse
    top_hotspots: ChartResponse
    recent_firs: list[RecentFIRItem]
    total_users: int = Field(0, description="Total registered users")


class PredictionForecast(BaseModel):
    """Single month forecast entry."""
    month: str = Field(..., description="Month label")
    value: int = Field(..., description="Predicted crime count")


class AnalyticsPrediction(BaseModel):
    """Analytics prediction / forecast response."""
    expected_firs: int = Field(0, description="Expected FIRs next month")
    forecast_confidence: int = Field(0, description="Forecast confidence percentage")
    high_risk_districts: int = Field(0, description="Number of high-risk districts")
    model_confidence: int = Field(0, description="Model confidence percentage")
    next_month_forecast: list[PredictionForecast] = Field(default_factory=list, description="Monthly forecast breakdown")


class OfficerPerformance(BaseModel):
    """Officer investigation performance entry."""
    name: str = Field(..., description="Officer name")
    assigned: int = Field(0, description="Cases assigned")
    solved: int = Field(0, description="Cases solved")
    pending: int = Field(0, description="Cases pending")
    efficiency: float = Field(0.0, description="Efficiency percentage")


class AnalyticsPerformance(BaseModel):
    """Officer performance leaderboard response."""
    officers: list[OfficerPerformance] = Field(default_factory=list, description="Officer performance list")


class RealtimeEvent(BaseModel):
    """Single real-time event entry."""
    icon: str = Field(..., description="Event icon emoji")
    text: str = Field(..., description="Event description")
    time: str = Field(..., description="Relative time string")


class AnalyticsRealtime(BaseModel):
    """Real-time activity feed response."""
    events: list[RealtimeEvent] = Field(default_factory=list, description="Recent activity events")
