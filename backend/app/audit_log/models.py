"""Audit log ORM model matching the existing MySQL audit_logs table."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditAction(str, enum.Enum):
    """Audit action types for categorizing API request types."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    API_CALL = "API_CALL"
    LOGIN = "LOGIN"
    REGISTER = "REGISTER"
    TOKEN_REFRESH = "TOKEN_REFRESH"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    __table_args__ = (
        Index("idx_audit_user", "user_id"),
    )

    log_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )

    action: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    table_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    record_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    log_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(log_id={self.log_id}, "
            f"user_id={self.user_id}, "
            f"action='{self.action}')>"
        )