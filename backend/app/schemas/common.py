"""Common Pydantic schemas: pagination, health check, error responses."""

from datetime import UTC, datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ─── Pagination ─────────────────────────────────────────────────


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort direction")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = {"arbitrary_types_allowed": True}


# ─── Standard Responses ─────────────────────────────────────────


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


class HealthResponse(BaseModel):
    """Health check endpoint response."""

    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ErrorDetail(BaseModel):
    """Individual error detail."""

    loc: List[str] = Field(default_factory=list, description="Location of the error")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: Any
    error_code: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""

    sub: str
    exp: int
    type: str
    extra: Optional[Dict[str, Any]] = None
