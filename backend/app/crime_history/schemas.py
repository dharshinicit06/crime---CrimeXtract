"""Pydantic schemas for Crime History CRUD operations."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.crime_history.models import Disposition
from app.schemas.common import PaginationParams


class AccusedBriefResponse(BaseModel):
    """Brief accused info for nested display."""
    id: str
    name: str
    model_config = {"from_attributes": True}


class CrimeBriefResponse(BaseModel):
    """Brief crime info for nested display."""
    id: str
    crime_number: str
    title: str
    model_config = {"from_attributes": True}


class FIRBriefResponse(BaseModel):
    """Brief FIR info for nested display."""
    id: str
    fir_number: str
    title: str
    model_config = {"from_attributes": True}


class CrimeHistoryCreate(BaseModel):
    """Payload for creating a new crime history record."""
    accused_id: str = Field(..., description="Accused person ID")
    crime_id: Optional[str] = Field(None, description="Linked crime incident ID")
    fir_id: Optional[str] = Field(None, description="Linked FIR ID")
    crime_date: date
    offense_type: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    disposition: Disposition = Disposition.UNKNOWN
    sentence: Optional[str] = Field(None, max_length=500)
    is_repeat_offense: bool = False
    modus_operandi: Optional[str] = None
    location: Optional[str] = Field(None, max_length=300)
    notes: Optional[str] = None


class CrimeHistoryUpdate(BaseModel):
    """Payload for updating a crime history record."""
    crime_date: Optional[date] = None
    offense_type: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    disposition: Optional[Disposition] = None
    sentence: Optional[str] = Field(None, max_length=500)
    is_repeat_offense: Optional[bool] = None
    modus_operandi: Optional[str] = None
    location: Optional[str] = Field(None, max_length=300)
    notes: Optional[str] = None


class CrimeHistoryFilterParams(PaginationParams):
    """Query parameters for filtering crime history records."""
    accused_id: Optional[str] = Field(None, description="Filter by accused")
    crime_id: Optional[str] = Field(None, description="Filter by crime incident")
    fir_id: Optional[str] = Field(None, description="Filter by FIR")
    disposition: Optional[Disposition] = Field(None, description="Filter by legal outcome")
    is_repeat_offense: Optional[bool] = Field(None, description="Filter repeat offenders")
    offense_type: Optional[str] = Field(None, description="Filter by offense type")
    search: Optional[str] = Field(None, description="Search in description, notes, offense type")
    date_from: Optional[date] = Field(None, description="On or after this date")
    date_to: Optional[date] = Field(None, description="On or before this date")


class CrimeHistoryResponse(BaseModel):
    """Full crime history record response."""
    id: str
    accused_id: str
    crime_id: Optional[str] = None
    fir_id: Optional[str] = None
    crime_date: date
    offense_type: str
    description: Optional[str] = None
    disposition: Disposition
    sentence: Optional[str] = None
    is_repeat_offense: bool
    modus_operandi: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Nested relations
    accused: Optional[AccusedBriefResponse] = None
    crime: Optional[CrimeBriefResponse] = None
    fir: Optional[FIRBriefResponse] = None

    model_config = {"from_attributes": True}


class CrimeHistoryListResponse(BaseModel):
    """Paginated crime history list response."""
    items: list[CrimeHistoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
