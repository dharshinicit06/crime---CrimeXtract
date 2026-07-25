"""Pydantic schemas for Victim CRUD operations — aligned with ORM model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginationParams


class VictimCreate(BaseModel):
    """Payload for creating a new victim.
    Field names match the ORM model (full_name, phone, email).
    """
    full_name: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    occupation: Optional[str] = Field(None, max_length=100)


class VictimUpdate(BaseModel):
    """Payload for updating a victim — all fields optional."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    occupation: Optional[str] = Field(None, max_length=100)


class VictimFilterParams(PaginationParams):
    """Query parameters for filtering and searching victims."""
    fir_id: Optional[str] = Field(None, description="Filter by FIR ID")
    search: Optional[str] = Field(None, description="Search by name, phone, email, or address")


class VictimResponse(BaseModel):
    """Victim response matching the ORM model fields exactly."""
    victim_id: int
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class VictimListResponse(BaseModel):
    """Paginated victim list response."""
    items: list[VictimResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
