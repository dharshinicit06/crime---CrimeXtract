"""Victim ORM model matching the existing MySQL victims table."""

import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Gender(str, enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class FIRVictimLink(Base):
    """Junction table linking FIRs and victims (many-to-many)."""

    __tablename__ = "fir_victims"

    fir_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("firs.fir_id", ondelete="CASCADE"),
        primary_key=True,
    )

    victim_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("victims.victim_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    fir = relationship("FIR")
    victim = relationship("Victim")

    def __repr__(self) -> str:
        return (
            f"<FIRVictimLink("
            f"fir_id={self.fir_id}, "
            f"victim_id={self.victim_id})>"
        )


class Victim(Base):
    """Victim model matching the MySQL victims table."""

    __tablename__ = "victims"

    __table_args__ = (
        Index("idx_victim_name", "full_name"),
    )

    victim_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    gender: Mapped[Gender | None] = mapped_column(
        Enum(
            Gender,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
        ),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    occupation: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Victim("
            f"victim_id={self.victim_id}, "
            f"full_name='{self.full_name}')>"
        )