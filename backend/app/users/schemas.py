"""Pydantic v2 schemas for user management CRUD operations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr

from app.schemas.common import PaginationParams


# ─── Create ──────────────────────────────────────────────────────


class UserCreateRequest(BaseModel):
    """Payload for creating a new user by an administrator."""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=20)
    role_id: int = Field(default=3, ge=1, description="User role ID: 1=Admin, 2=Investigator, 3=Analyst")
    is_active: bool = Field(default=True, description="Whether the account is active")


# ─── Update ──────────────────────────────────────────────────────


class UserUpdateRequest(BaseModel):
    """Payload for updating an existing user. All fields optional."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    role_id: Optional[int] = Field(None, ge=1, description="User role ID for RBAC")
    is_active: Optional[bool] = Field(None, description="Whether the account is active")


# ─── Status Toggle ───────────────────────────────────────────────


class UserStatusUpdateRequest(BaseModel):
    """Payload for activating/deactivating a user."""

    is_active: bool = Field(..., description="Set true to activate, false to deactivate")


# ─── Password Reset ─────────────────────────────────────────────


class UserPasswordResetRequest(BaseModel):
    """Payload for resetting a user's password."""

    new_password: str = Field(..., min_length=8, max_length=128, description="New password")


# ─── Filter / Search ────────────────────────────────────────────


class UserFilterParams(PaginationParams):
    """Query parameters for filtering and searching users."""

    search: Optional[str] = Field(
        None, description="Search term matching email or full name",
    )
    role_id: Optional[int] = Field(None, ge=1, description="Filter by role ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")


# ─── Response ────────────────────────────────────────────────────


class UserResponse(BaseModel):
    """User response visible to administrators."""

    user_id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    role_id: int
    role_name: Optional[str] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Paginated list of users."""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
