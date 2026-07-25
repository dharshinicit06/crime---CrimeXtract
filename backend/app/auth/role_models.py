from datetime import datetime

from sqlalchemy import Integer, String, TIMESTAMP, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    role_name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Role(role_id={self.role_id}, "
            f"role_name='{self.role_name}')>"
        )
    