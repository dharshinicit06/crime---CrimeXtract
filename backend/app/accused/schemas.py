"""Pydantic schemas for Accused CRUD operations — aligned with ORM model."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginationParams


class FIRAccusedLinkCreate(BaseModel):
    """Payload for linking an accused to an FIR."""
    fir_id: int = Field(..., description="FIR ID to link")


class FIRAccusedLinkResponse(BaseModel):
    """Response for an FIR-Accused link (composite key junction table)."""
    fir_id: int
    accused_id: int

    model_config = {"from_attributes": True}


class AccusedCreate(BaseModel):
    """Payload for creating a new accused record.
    Field names match the ORM model (full_name, not name).
    """
    full_name: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    occupation: Optional[str] = Field(None, max_length=100)
    aadhaar_number: Optional[str] = Field(None, max_length=20)
    risk_score: Optional[float] = Field(None, ge=0, le=100, description="Risk assessment score (1-100)")
    fir_ids: list[int] = Field(default_factory=list, description="FIR IDs to link this accused to")


class AccusedUpdate(BaseModel):
    """Payload for updating an accused record."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    occupation: Optional[str] = Field(None, max_length=100)
    aadhaar_number: Optional[str] = Field(None, max_length=20)
    risk_score: Optional[float] = Field(None, ge=0, le=100)


class AccusedFilterParams(PaginationParams):
    """Query parameters for filtering and searching accused records."""
    search: Optional[str] = Field(None, description="Search by name or alias")
    fir_id: Optional[str] = Field(None, description="Filter by linked FIR ID")
    min_risk_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum risk score")
    max_risk_score: Optional[float] = Field(None, ge=0, le=100, description="Maximum risk score")


class AccusedResponse(BaseModel):
    """Full accused record response — matches ORM model fields exactly."""
    accused_id: int
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    aadhaar_number: Optional[str] = None
    risk_score: Optional[float] = None
    is_repeat_offender: Optional[bool] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AccusedListResponse(BaseModel):
    """Paginated accused list response."""
    items: list[AccusedResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
