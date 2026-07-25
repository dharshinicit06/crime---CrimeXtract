"""Crime Type ORM model matching the existing MySQL crime_types table."""

import enum
from datetime import datetime

from sqlalchemy import Enum, Index, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CrimeSeverity(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class CrimeStatus(str, enum.Enum):
    """Crime incident status matching schema expectations."""
    REPORTED = "Reported"
    UNDER_INVESTIGATION = "Under Investigation"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class CrimeType(Base):
    __tablename__ = "crime_types"

    __table_args__ = (
        Index("idx_crime_name", "crime_name"),
    )

    crime_type_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    crime_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    severity: Mapped[CrimeSeverity | None] = mapped_column(
        Enum(CrimeSeverity, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
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
            f"<CrimeType(crime_type_id={self.crime_type_id}, "
            f"crime_name='{self.crime_name}')>"
        )