"""Pydantic schemas for Offender Profiling responses."""

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ScorerResult(BaseModel):
    """Output from a single modular scorer."""
    name: str
    weight: float
    raw_score: float
    normalized_score: float
    reasoning: str


class CrimeFrequencyInfo(BaseModel):
    total_firs: int = 0
    total_crime_history: int = 0
    unique_crime_categories: list[str] = Field(default_factory=list)
    first_offense_date: Optional[date] = None
    last_offense_date: Optional[date] = None
    months_active: Optional[int] = None


class GangLinkInfo(BaseModel):
    raw_gang_links: Optional[str] = None
    gangs_mentioned: list[str] = Field(default_factory=list)
    has_gang_affiliation: bool = False


class PreviousFirInfo(BaseModel):
    fir_id: str
    fir_number: str
    title: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None
    incident_date: Optional[date] = None
    crime_category: Optional[str] = None


class TimelineEvent(BaseModel):
    date: Optional[str] = None
    event_type: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    reference_id: Optional[str] = None


class OffenderStatistics(BaseModel):
    total_firs: int = 0
    active_firs: int = 0
    solved_firs: int = 0
    pending_firs: int = 0
    total_victims: int = 0
    total_evidence: int = 0
    repeat_offender_score: Optional[float] = None
    unique_locations: int = 0
    most_common_district: Optional[str] = None
    co_accused_count: int = 0


class OffenderLocation(BaseModel):
    district: str
    city: str = ""
    area: str = ""
    fir_count: int = 0


class OffenderProfile(BaseModel):
    """Complete offender profiling response."""
    accused_id: str
    name: str
    alias: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    is_active: bool = True

    # Risk score
    risk_score: float = 0.0
    risk_level: str = "low"
    recommendation: Optional[str] = None

    # Breakdown
    statistics: OffenderStatistics = Field(default_factory=OffenderStatistics)
    crime_frequency: CrimeFrequencyInfo = Field(default_factory=CrimeFrequencyInfo)
    crime_categories: list[str] = Field(default_factory=list)
    previous_firs: list[PreviousFirInfo] = Field(default_factory=list)
    locations: list[OffenderLocation] = Field(default_factory=list)

    # Modular scoring
    scorer_results: list[ScorerResult] = Field(default_factory=list)
    reasoning_summary: str = ""


class TimelineResponse(BaseModel):
    accused_id: str
    name: str
    events: list[TimelineEvent] = Field(default_factory=list)
    total_events: int = 0
