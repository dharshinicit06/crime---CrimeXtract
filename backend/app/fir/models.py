"""FIR ORM model matching the existing MySQL firs table."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, TIMESTAMP, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InvestigationStatus(str, enum.Enum):
    PENDING = "Pending"
    UNDER_INVESTIGATION = "Under Investigation"
    SOLVED = "Solved"
    CLOSED = "Closed"


class CrimeCategorySeverity(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
    SERIOUS = "Serious"


class FirPriority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class FirStatus(str, enum.Enum):
    DRAFT = "Draft"
    REGISTERED = "Registered"
    UNDER_INVESTIGATION = "Under Investigation"
    CHARGE_SHEET_FILED = "Charge Sheet Filed"
    CLOSED = "Closed"


class Priority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class FIR(Base):
    __tablename__ = "firs"

    __table_args__ = (
        Index("idx_fir_number", "fir_number"),
        Index("idx_incident_date", "incident_date"),
        Index("idx_fir_crime_type", "crime_type_id"),
        Index("idx_fir_location", "location_id"),
        Index("idx_fir_officer", "officer_id"),
        Index("idx_fir_priority", "priority"),
        Index("idx_fir_status", "investigation_status"),
    )

    fir_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    fir_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    crime_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("crime_types.crime_type_id"),
        nullable=False,
    )

    location_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("locations.location_id"),
        nullable=False,
    )

    officer_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("officers.officer_id"),
        nullable=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    incident_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    complaint_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=True,
    )

    investigation_status: Mapped[InvestigationStatus | None] = mapped_column(
        Enum(
            InvestigationStatus,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
        ),
        server_default="Pending",
        nullable=True,
    )

    priority: Mapped[Priority | None] = mapped_column(
        Enum(
            Priority,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
        ),
        server_default="Medium",
        nullable=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<FIR(fir_id={self.fir_id}, "
            f"fir_number='{self.fir_number}')>"
        )
