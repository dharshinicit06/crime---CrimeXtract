"""Pydantic v2 schemas for the Settings module.

Aligns with the User ORM model (auth/models.py) and
the UserPreference ORM model (settings/models.py).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ═══════════════════════════════════════════════════════════════
# Profile
# ═══════════════════════════════════════════════════════════════


class ProfileResponse(BaseModel):
    """Current user's profile — uses User ORM fields directly."""

    user_id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    """Payload for updating profile fields. All fields optional."""

    full_name: Optional[str] = Field(
        None, min_length=1, max_length=100,
    )
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(
        None, max_length=20,
    )


# ═══════════════════════════════════════════════════════════════
# Password
# ═══════════════════════════════════════════════════════════════


class ChangePasswordRequest(BaseModel):
    """Payload for changing password — requires current password."""

    current_password: str = Field(
        ..., min_length=1, description="Current password for verification",
    )
    new_password: str = Field(
        ..., min_length=8, max_length=128,
        description="New password (min 8 characters)",
    )


class ChangePasswordResponse(BaseModel):
    """Response after successful password change."""

    message: str = "Password changed successfully"


# ═══════════════════════════════════════════════════════════════
# Preferences
# ═══════════════════════════════════════════════════════════════


class PreferenceResponse(BaseModel):
    """User preferences — matches UserPreference ORM fields."""

    preference_id: int
    user_id: int
    theme: str = "dark"
    language: str = "en"
    timezone: str = "Asia/Kolkata"
    date_format: str = "DD/MM/YYYY"
    email_notifications: bool = True
    sms_notifications: bool = False
    ai_notifications: bool = True
    report_notifications: bool = True
    security_alerts: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PreferenceUpdateRequest(BaseModel):
    """Payload for updating user preferences. All fields optional."""

    theme: Optional[str] = Field(
        None, pattern="^(dark|light|system)$",
        description="UI theme: dark, light, or system",
    )
    language: Optional[str] = Field(
        None, max_length=10,
    )
    timezone: Optional[str] = Field(
        None, max_length=50,
    )
    date_format: Optional[str] = Field(
        None, max_length=20,
    )
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    ai_notifications: Optional[bool] = None
    report_notifications: Optional[bool] = None
    security_alerts: Optional[bool] = None


# ═══════════════════════════════════════════════════════════════
# System Info (admin only)
# ═══════════════════════════════════════════════════════════════


class SystemInfoResponse(BaseModel):
    """System information visible only to administrators."""

    app_name: str
    app_version: str
    environment: str
    database_status: str = "connected"
    python_version: str = ""
    server_time: str = ""
    server_uptime: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# Message response
# ═══════════════════════════════════════════════════════════════


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class LogoutAllResponse(BaseModel):
    """Response after logging out all sessions."""

    message: str = "All sessions have been logged out"
