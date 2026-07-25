"""CrimeHistory ORM model matching the existing MySQL crime_history table."""

import enum
from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ConvictionStatus(str, enum.Enum):
    PENDING = "Pending"
    CONVICTED = "Convicted"
    ACQUITTED = "Acquitted"


class Disposition(str, enum.Enum):
    """Legal disposition/outcome values (schema compatibility)."""
    UNKNOWN = "Unknown"
    PENDING = "Pending"
    CONVICTED = "Convicted"
    ACQUITTED = "Acquitted"
    DISMISSED = "Dismissed"


class CrimeHistory(Base):
    __tablename__ = "crime_history"

    __table_args__ = (
        Index("idx_history_accused", "accused_id"),
    )

    history_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    accused_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accused.accused_id", ondelete="CASCADE"),
        nullable=False,
    )

    fir_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("firs.fir_id", ondelete="SET NULL"),
        nullable=True,
    )

    crime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    arrest_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    conviction_status: Mapped[ConvictionStatus | None] = mapped_column(
        Enum(ConvictionStatus),
        server_default="Pending",
        nullable=True,
    )

    sentence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
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
            f"<CrimeHistory(history_id={self.history_id}, "
            f"accused_id={self.accused_id})>"
        )
