"""Pydantic schemas for Evidence CRUD operations — aligned with ORM model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.evidence.models import EvidenceType
from app.schemas.common import PaginationParams


class EvidenceCreate(BaseModel):
    """Payload for creating a new evidence record.
    Field names match the ORM model (evidence_name, evidence_type, etc.).
    """
    evidence_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    evidence_type: Optional[EvidenceType] = None
    file_path: Optional[str] = None
    collected_date: Optional[datetime] = None


class EvidenceUpdate(BaseModel):
    """Payload for updating an evidence record. All fields optional."""
    evidence_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    evidence_type: Optional[EvidenceType] = None
    file_path: Optional[str] = None
    collected_date: Optional[datetime] = None


class EvidenceFilterParams(PaginationParams):
    """Query parameters for filtering and searching evidence records."""
    fir_id: Optional[str] = Field(None, description="Filter by linked FIR ID")
    evidence_type: Optional[EvidenceType] = Field(None, description="Filter by evidence type")
    search: Optional[str] = Field(None, description="Search by name or description")


class EvidenceResponse(BaseModel):
    """Full evidence record response — matches ORM model fields exactly."""
    evidence_id: int
    fir_id: int
    evidence_type: Optional[EvidenceType] = None
    evidence_name: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    collected_by: Optional[int] = None
    collected_date: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    """Paginated evidence list response."""
    items: list[EvidenceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
