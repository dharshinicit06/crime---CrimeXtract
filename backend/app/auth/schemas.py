"""Pydantic v2 schemas for authentication."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------
# Register
# ---------------------------------------------------------

class RegisterRequest(BaseModel):
    """Register a new user."""

    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    role_id: int = Field(default=2, ge=1)


# ---------------------------------------------------------
# Login
# ---------------------------------------------------------

class LoginRequest(BaseModel):
    """Login with email + password."""

    email: EmailStr
    password: str


# ---------------------------------------------------------
# Refresh Token
# ---------------------------------------------------------

class RefreshTokenRequest(BaseModel):
    """Refresh token request payload."""

    refresh_token: str


# ---------------------------------------------------------
# Token Response
# ---------------------------------------------------------

class TokenResponse(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------
# User Response
# ---------------------------------------------------------

class UserResponse(BaseModel):
    """Public user profile response."""

    user_id: int
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------
# Login Response (wraps user + tokens)
# ---------------------------------------------------------

class LoginResponse(BaseModel):
    """Login response with user info + JWT token pair."""

    user: UserResponse
    tokens: TokenResponse


# ---------------------------------------------------------
# Refresh Response (wraps token pair)
# ---------------------------------------------------------

class RefreshResponse(BaseModel):
    """Refresh token response with wrapped token pair."""

    tokens: TokenResponse


# ---------------------------------------------------------
# Current User (alias for consistency)
# ---------------------------------------------------------

class UserMeResponse(UserResponse):
    """Alias of UserResponse returned from /auth/me."""
    pass
