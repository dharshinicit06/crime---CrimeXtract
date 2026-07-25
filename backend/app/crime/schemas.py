"""Pydantic schemas for Crime incident CRUD operations."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.crime.models import CrimeStatus
from app.fir.models import CrimeCategorySeverity
from app.schemas.common import PaginationParams


class CrimeCategoryBriefResponse(BaseModel):
    """Brief crime category info for nested display in crime responses."""

    id: str
    name: str
    section_law: Optional[str] = None
    severity: CrimeCategorySeverity

    model_config = {"from_attributes": True}


class UserBriefResponse(BaseModel):
    """Brief user info for nested display."""

    id: int
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class FIRBriefResponse(BaseModel):
    """Brief FIR info for nested display."""

    id: str
    fir_number: str
    title: str

    model_config = {"from_attributes": True}


class CrimeCreate(BaseModel):
    """Payload for creating a new crime incident record."""

    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    crime_status: CrimeStatus = CrimeStatus.REPORTED
    crime_date: date
    district: str = Field(..., min_length=1, max_length=100)
    crime_type_id: str = Field(..., description="Crime category ID (e.g., IPC section)")
    fir_id: Optional[str] = Field(None, description="Optional link to an FIR")
    assigned_to_id: Optional[int] = Field(None, description="Optional investigating officer ID")


class CrimeUpdate(BaseModel):
    """Payload for updating a crime incident record. All fields optional."""

    title: Optional[str] = Field(None, min_length=3, max_length=300)
    description: Optional[str] = None
    crime_status: Optional[CrimeStatus] = None
    crime_date: Optional[date] = None
    district: Optional[str] = Field(None, min_length=1, max_length=100)
    crime_type_id: Optional[str] = None
    fir_id: Optional[str] = None
    assigned_to_id: Optional[int] = None


class CrimeFilterParams(PaginationParams):
    """Query parameters for filtering and searching crime records."""

    crime_status: Optional[CrimeStatus] = Field(None, description="Filter by crime status")
    crime_type_id: Optional[str] = Field(None, description="Filter by crime category")
    district: Optional[str] = Field(None, description="Filter by district")
    fir_id: Optional[str] = Field(None, description="Filter by linked FIR")
    assigned_to_id: Optional[int] = Field(None, description="Filter by assigned officer")
    reported_by_id: Optional[int] = Field(None, description="Filter by reporting user")
    search: Optional[str] = Field(None, description="Search in title, description, crime number")
    date_from: Optional[date] = Field(None, description="Filter crimes on or after this date")
    date_to: Optional[date] = Field(None, description="Filter crimes on or before this date")


class CrimeResponse(BaseModel):
    """Full crime incident response."""

    id: str
    crime_number: str
    title: str
    description: Optional[str] = None
    crime_status: CrimeStatus
    crime_date: date
    district: str
    crime_type_id: str
    fir_id: Optional[str] = None
    reported_by_id: int
    assigned_to_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    crime_type: Optional[CrimeCategoryBriefResponse] = None
    fir: Optional[FIRBriefResponse] = None
    reported_by: Optional[UserBriefResponse] = None
    assigned_to: Optional[UserBriefResponse] = None

    model_config = {"from_attributes": True}


class CrimeListResponse(BaseModel):
    """Paginated crime incident list response."""

    items: list[CrimeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CrimeTypeResponse(BaseModel):
    """Crime type reference for dropdowns."""

    crime_type_id: int
    crime_name: str
    category: Optional[str] = None
    severity: Optional[str] = None

    model_config = {"from_attributes": True}
