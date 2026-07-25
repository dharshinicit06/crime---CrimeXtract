"""Pydantic schemas for FIR CRUD operations - matching actual MySQL fir table."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.fir.models import InvestigationStatus, Priority
from app.schemas.common import PaginationParams


# ─── FIR ────────────────────────────────────────────────────────


class FIRCreate(BaseModel):
    """Payload for creating a new FIR."""

    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    priority: Priority = Priority.MEDIUM
    incident_date: date
    crime_type_id: Optional[int] = Field(None, description="Crime type ID (from crime_types table)")
    location_id: Optional[int] = Field(None, description="Location ID (from locations table)")
    officer_id: Optional[int] = Field(None, description="Investigating officer ID")
    crime_type: Optional[str] = Field(None, description="Crime type name (text input)")
    location: Optional[str] = Field(None, description="Location text (e.g. 'Bengaluru Urban')")
    officer: Optional[str] = Field(None, description="Officer name or badge number (text input)")


class FIRUpdate(BaseModel):
    """Payload for updating an FIR. All fields optional."""

    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    priority: Optional[Priority] = None
    investigation_status: Optional[InvestigationStatus] = None
    incident_date: Optional[date] = None
    crime_type_id: Optional[int] = None
    location_id: Optional[int] = None
    officer_id: Optional[int] = None


class FIRFilterParams(PaginationParams):
    """Query parameters for filtering FIRs."""

    status: Optional[InvestigationStatus] = None
    priority: Optional[Priority] = None
    search: Optional[str] = Field(
        None, description="Search in title, description, FIR number"
    )
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class FIRSummaryResponse(BaseModel):
    """Condensed FIR response for list views."""

    fir_id: int
    fir_number: str
    title: Optional[str] = None
    investigation_status: Optional[InvestigationStatus] = None
    priority: Optional[Priority] = None
    incident_date: Optional[date] = None
    crime_type_id: Optional[int] = None
    location_id: Optional[int] = None
    officer_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FIRDetailResponse(BaseModel):
    """Full FIR response with details."""

    fir_id: int
    fir_number: str
    title: Optional[str] = None
    description: Optional[str] = None
    investigation_status: Optional[InvestigationStatus] = None
    priority: Optional[Priority] = None
    incident_date: Optional[date] = None
    crime_type_id: Optional[int] = None
    location_id: Optional[int] = None
    officer_id: Optional[int] = None
    complaint_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FIRListResponse(BaseModel):
    """Paginated FIR list response."""

    items: list[FIRSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── FIR Statistics ──────────────────────────────────────────────


class FIRStatistics(BaseModel):
    """FIR statistics for dashboard/KPI cards."""

    total_firs: int = 0
    pending_count: int = 0
    under_investigation_count: int = 0
    solved_count: int = 0
    closed_count: int = 0
    high_priority_count: int = 0
    critical_priority_count: int = 0


class FIRSummary(BaseModel):
    """Summary for a single FIR with extra context."""

    fir_id: int
    fir_number: str
    title: Optional[str] = None
    investigation_status: Optional[InvestigationStatus] = None
    priority: Optional[Priority] = None
    incident_date: Optional[date] = None
    created_at: Optional[datetime] = None
    crime_type_name: Optional[str] = None
    district: Optional[str] = None
    officer_name: Optional[str] = None
