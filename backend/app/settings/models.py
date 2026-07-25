"""User preferences ORM model for storing per-user settings.

Stores theme, language, timezone, notification preferences, etc.
Linked 1:1 with the users table via user_id.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserPreference(Base):
    """Per-user application preferences stored as discrete columns."""

    __tablename__ = "user_preferences"

    preference_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # ── Theme & Display ────────────────────────────────────────
    theme: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="dark",
    )

    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        server_default="en",
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="Asia/Kolkata",
    )

    date_format: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="DD/MM/YYYY",
    )

    # ── Notification Preferences ────────────────────────────────
    email_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="1",
    )

    sms_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="0",
    )

    ai_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="1",
    )

    report_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="1",
    )

    security_alerts: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="1",
    )

    # ── Timestamps ─────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<UserPreference(preference_id={self.preference_id}, "
            f"user_id={self.user_id}, theme='{self.theme}')>"
        )
