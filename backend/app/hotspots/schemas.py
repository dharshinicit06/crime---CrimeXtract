"""Crime Hotspots schemas - dedicated hotspot analysis response models."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HotspotSummary(BaseModel):
    """A single hotspot district summary."""
    district: str = Field(..., description="District name")
    city: str = Field("", description="City name")
    area: str = Field("", description="Area name")
    crime_count: int = Field(0, description="Total FIRs in this hotspot")
    risk_score: float = Field(0.0, description="Computed risk score (0-1000)")
    risk_level: str = Field("Low", description="Risk level: High/Medium/Low")
    priority_count: int = Field(0, description="High/Critical priority FIRs")
    pending_count: int = Field(0, description="Pending/Under Investigation FIRs")
    recent_count: int = Field(0, description="FIRs in last 30 days")
    last_incident: Optional[str] = Field(None, description="Date of most recent FIR")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")


class HotspotListResponse(BaseModel):
    """Response for GET /hotspots."""
    hotspots: list[HotspotSummary] = Field(default_factory=list)
    total_hotspots: int = Field(0)
    high_risk_count: int = Field(0)
    medium_risk_count: int = Field(0)
    low_risk_count: int = Field(0)
    total_crimes: int = Field(0)
    unique_districts: int = Field(0)
    unique_cities: int = Field(0)


class CrimeTypeBreakdown(BaseModel):
    """Crime type breakdown for a district."""
    crime_type: str
    count: int


class StatusBreakdown(BaseModel):
    """Investigation status breakdown."""
    status: str
    count: int


class RecentFIRItem(BaseModel):
    """Recent FIR in a hotspot district."""
    fir_number: str
    title: Optional[str] = None
    incident_date: Optional[str] = None
    investigation_status: Optional[str] = None
    priority: Optional[str] = None


class HotspotDetail(BaseModel):
    """Detailed information for a single hotspot district."""
    district: str
    city: str
    area: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    crime_count: int = 0
    risk_score: float = 0.0
    risk_level: str = "Low"
    crime_types: list[CrimeTypeBreakdown] = Field(default_factory=list)
    status_breakdown: list[StatusBreakdown] = Field(default_factory=list)
    monthly_trend: list[dict] = Field(default_factory=list)
    recent_firs: list[RecentFIRItem] = Field(default_factory=list)
    ai_insight: str = ""


class MapPoint(BaseModel):
    """GIS-ready hotspot map point."""
    district: str
    city: str = ""
    area: str = ""
    latitude: float
    longitude: float
    crime_count: int
    risk_score: float
    risk_level: str


class HotspotMapResponse(BaseModel):
    """Response for GET /hotspots/map - GIS-ready data."""
    points: list[MapPoint] = Field(default_factory=list)
    total_points: int = Field(0)


class AIInsight(BaseModel):
    """AI-generated hotspot insight."""
    district: str
    insight: str
    impact: str = "info"


class HotspotAIInsightsResponse(BaseModel):
    """Response for GET /hotspots/insights."""
    insights: list[AIInsight] = Field(default_factory=list)
