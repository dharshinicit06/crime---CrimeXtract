"""User ORM model matching the existing MySQL users table."""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        Index("idx_users_email", "email"),
    )

    # Maps Python attribute "id" to MySQL column "user_id"
    id: Mapped[int] = mapped_column(
        "user_id",
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    role_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("roles.role_id", ondelete="SET NULL"),
        nullable=True,      # Matches DESCRIBE users (YES)
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default="1",  # Matches DEFAULT 1
        nullable=True,       # Matches DESCRIBE users (YES)
    )

    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=True,       # Matches DESCRIBE users (YES)
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=True,       # Matches DESCRIBE users (YES)
    )

    @property
    def user_id(self) -> int:
        """Alias for id, matching the database column name user_id."""
        return self.id

    def __repr__(self) -> str:
        return (
            f"<User(user_id={self.id}, "
            f"email='{self.email}', "
            f"full_name='{self.full_name}')>"
        )