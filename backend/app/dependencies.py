"""FastAPI dependency injection container: authentication, RBAC, and database session.

This is the SINGLE source of truth for:
  - get_db_session()     — async database session
  - get_current_user()   — authenticated User ORM object
  - get_optional_user()  — optional authenticated User (or None)
  - RoleChecker          — RBAC via integer role_id

DO NOT duplicate these functions elsewhere.
"""

from collections.abc import AsyncGenerator
from typing import Optional

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import verify_token
from app.auth.models import User
from app.core.database import get_session
from app.exceptions.handlers import (
    ForbiddenException,
    UnauthorizedException,
)

bearer_scheme = HTTPBearer(auto_error=False)


# ------------------------------------------------------------------
# Database Session
# ------------------------------------------------------------------

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session.

    Usage:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    async for session in get_session():
        yield session


# ------------------------------------------------------------------
# Current User
# ------------------------------------------------------------------

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Extract and validate the current user from a JWT bearer token.

    Returns:
        The authenticated User ORM object.

    Raises:
        UnauthorizedException: If the token is missing, invalid, or expired.
    """

    if credentials is None:
        raise UnauthorizedException(message="Authentication required")

    try:
        payload = verify_token(credentials.credentials)
    except JWTError:
        raise UnauthorizedException(message="Invalid or expired token")

    if payload.get("type") != "access":
        raise UnauthorizedException(message="Invalid access token")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException(message="Invalid token payload")

    result = await session.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException(message="User not found")

    if not user.is_active:
        raise UnauthorizedException(message="Inactive account")

    return user


# ------------------------------------------------------------------
# Optional User
# ------------------------------------------------------------------

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """Extract user from JWT if present, otherwise return None.

    Usage:
        @router.get("/public-items")
        async def get_items(user: Optional[User] = Depends(get_optional_user)):
            ...
    """

    if credentials is None:
        return None

    try:
        payload = verify_token(credentials.credentials)
    except JWTError:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    result = await session.execute(
        select(User).where(User.id == int(user_id))
    )
    return result.scalar_one_or_none()


# ------------------------------------------------------------------
# Role Checker (RBAC via integer role_id)
# ------------------------------------------------------------------

class RoleChecker:
    """Role-based access control using integer role_id.

    Usage:
        Depends(RoleChecker(1))           # only role_id=1
        Depends(RoleChecker(1, 2))        # role_id=1 or 2
    """

    def __init__(self, *allowed_roles: int) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role_id not in self.allowed_roles:
            raise ForbiddenException(
                message="You do not have permission to access this resource.",
            )
        return current_user
