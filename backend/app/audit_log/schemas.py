"""Pydantic schemas for AuditLog CRUD and filtering — aligned with ORM model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.audit_log.models import AuditAction
from app.schemas.common import PaginationParams


class AuditLogCreate(BaseModel):
    """Payload for creating an audit log entry programmatically.
    Only fields that can be stored in the ORM are included.
    """
    user_id: Optional[int] = None
    action: str = Field(..., max_length=255)
    table_name: Optional[str] = Field(None, max_length=100)
    record_id: Optional[int] = None
    ip_address: Optional[str] = Field(None, max_length=50)


class AuditLogResponse(BaseModel):
    """Full audit log entry response — matches ORM model fields exactly."""
    log_id: int
    user_id: Optional[int] = None
    action: Optional[str] = None
    table_name: Optional[str] = None
    record_id: Optional[int] = None
    ip_address: Optional[str] = None
    log_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated audit log list response."""
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditLogFilterParams(PaginationParams):
    """Query parameters for filtering audit logs."""
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    action: Optional[str] = Field(None, description="Filter by action string")
    table_name: Optional[str] = Field(None, description="Filter by table name")
    record_id: Optional[int] = Field(None, description="Filter by record ID")
    date_from: Optional[datetime] = Field(None, description="Start date for filtering")
    date_to: Optional[datetime] = Field(None, description="End date for filtering")
    search: Optional[str] = Field(None, description="Search in action field")


class AuditLogStatsResponse(BaseModel):
    """Audit log statistics response."""
    total_entries: int
    unique_users: int
    actions_breakdown: dict[str, int]
    top_endpoints: list[dict]
    activity_by_day: list[dict]
