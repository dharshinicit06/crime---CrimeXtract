"""Settings service: profile management, password changes, preferences, and system info.

All operations are scoped to the currently authenticated user.
Admin-only operations use the RoleChecker dependency rather than
service-level checks, following the Users module pattern.
"""

import platform
import time
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Track server start time for uptime calculation
_server_start_time = time.time()

from app.auth.hashing import hash_password, verify_password
from app.auth.models import User
from app import __version__
from app.config import settings as app_settings
from app.exceptions.handlers import (
    ConflictException,
    UnauthorizedException,
)
from app.logging import get_logger
from app.settings.models import UserPreference

logger = get_logger(__name__)

# Role name mapping (mirrors users/services.py)
ROLE_NAMES_MAP = {1: "Admin", 2: "Investigator", 3: "Analyst", 4: "Supervisor"}


class SettingsService:
    """Business logic for all settings-related operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ─── Profile ────────────────────────────────────────────────

    def _enrich_profile(self, user: User) -> dict[str, Any]:
        """Build a profile dict matching ProfileResponse."""
        return {
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "role_id": user.role_id or 3,
            "role_name": ROLE_NAMES_MAP.get(user.role_id or 3, "Officer"),
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

    async def get_profile(self, current_user: User) -> dict[str, Any]:
        """Return the current user's profile."""
        return self._enrich_profile(current_user)

    async def update_profile(
        self,
        current_user: User,
        *,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update the current user's profile fields."""
        # Re-fetch user in this service's session
        user = await self.session.get(User, current_user.id)
        if not user:
            raise UnauthorizedException(
                message="User not found",
                error_code="USER_NOT_FOUND",
            )

        # Email uniqueness check
        if email and email != user.email:
            existing = await self.session.execute(
                select(User).where(User.email == email)
            )
            if existing.scalar_one_or_none():
                raise ConflictException(
                    message=f"Email '{email}' is already taken",
                    error_code="EMAIL_TAKEN",
                )
            user.email = email

        if full_name is not None:
            user.full_name = full_name

        if phone is not None:
            user.phone = phone

        await self.session.flush()
        await self.session.refresh(user)

        logger.info(
            "User %s updated their profile", user.email,
        )
        return self._enrich_profile(user)

    # ─── Password ──────────────────────────────────────────────

    async def change_password(
        self,
        current_user: User,
        *,
        current_password: str,
        new_password: str,
    ) -> None:
        """Verify current password and update to the new one."""
        # Re-fetch user in this service's session to avoid cross-session issues
        user = await self.session.get(User, current_user.id)
        if not user:
            raise UnauthorizedException(
                message="User not found",
                error_code="USER_NOT_FOUND",
            )

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedException(
                message="Current password is incorrect",
                error_code="INVALID_PASSWORD",
            )

        # Hash and set new password
        user.password_hash = hash_password(new_password)
        await self.session.flush()
        await self.session.refresh(user)

        logger.info(
            "User %s changed their password", user.email,
        )

    # ─── Preferences ───────────────────────────────────────────

    async def _get_or_create_preferences(
        self, user_id: int,
    ) -> UserPreference:
        """Get existing preferences or create defaults for a user."""
        result = await self.session.execute(
            select(UserPreference).where(
                UserPreference.user_id == user_id
            )
        )
        pref = result.scalar_one_or_none()
        if pref:
            return pref

        # Create default preferences
        pref = UserPreference(user_id=user_id)
        self.session.add(pref)
        await self.session.flush()
        await self.session.refresh(pref)
        return pref

    async def get_preferences(
        self, current_user: User,
    ) -> UserPreference:
        """Get the current user's preferences (auto-create defaults)."""
        return await self._get_or_create_preferences(current_user.id)

    async def update_preferences(
        self,
        current_user: User,
        **kwargs: Any,
    ) -> UserPreference:
        """Update the current user's preferences."""
        pref = await self._get_or_create_preferences(current_user.id)

        # Allowed preference fields
        allowed = {
            "theme", "language", "timezone", "date_format",
            "email_notifications", "sms_notifications",
            "ai_notifications", "report_notifications", "security_alerts",
        }

        updated = False
        for key, value in kwargs.items():
            if key in allowed and value is not None:
                setattr(pref, key, value)
                updated = True

        if updated:
            await self.session.flush()
            await self.session.refresh(pref)

            logger.info(
                "User %s updated their preferences", current_user.email,
            )

        return pref

    # ─── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Format uptime seconds into a human-readable string."""
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, secs = divmod(remainder, 60)
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        return " ".join(parts)

    # ─── System Info (admin) ─────────────────────────────────

    async def get_system_info(self) -> dict[str, Any]:
        """Return system information (admin only)."""
        # Verify database connectivity
        db_status = "connected"
        try:
            await self.session.execute(select(1))
        except Exception:
            db_status = "disconnected"

        return {
            "app_name": app_settings.APP_NAME,
            "app_version": __version__,
            "environment": app_settings.ENVIRONMENT,
            "database_status": db_status,
            "python_version": platform.python_version(),
            "server_time": datetime.now(UTC).isoformat(),
            "server_uptime": self._format_uptime(time.time() - _server_start_time),
        }
