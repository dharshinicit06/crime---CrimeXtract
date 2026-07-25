"""Officer ORM model matching the existing MySQL officers table."""

from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Index, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Officer(Base):
    __tablename__ = "officers"

    __table_args__ = (
        Index("idx_officer_badge", "badge_number"),
    )

    officer_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
    )

    badge_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )

    designation: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    police_station: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    joining_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Officer(officer_id={self.officer_id}, "
            f"badge_number='{self.badge_number}')>"
        )