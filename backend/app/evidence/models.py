"""Evidence ORM model matching the existing MySQL evidence table."""

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EvidenceType(str, enum.Enum):
    PHOTO = "Photo"
    VIDEO = "Video"
    DOCUMENT = "Document"
    FINGERPRINT = "Fingerprint"
    DNA = "DNA"
    WEAPON = "Weapon"
    DIGITAL = "Digital"
    OTHER = "Other"


class EvidenceStatus(str, enum.Enum):
    """Evidence lifecycle status values (schema compatibility)."""
    COLLECTED = "Collected"
    ANALYZING = "Analyzing"
    STORED = "Stored"
    PRESENTED = "Presented"
    DISPOSED = "Disposed"


class Evidence(Base):
    __tablename__ = "evidence"

    __table_args__ = (
        Index("idx_evidence_type", "evidence_type"),
    )

    evidence_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    fir_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("firs.fir_id", ondelete="CASCADE"),
        nullable=False,
    )

    evidence_type: Mapped[EvidenceType | None] = mapped_column(
        Enum(EvidenceType),
        nullable=True,
    )

    evidence_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    file_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    collected_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("officers.officer_id", ondelete="SET NULL"),
        nullable=True,
    )

    collected_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Evidence("
            f"evidence_id={self.evidence_id}, "
            f"evidence_name='{self.evidence_name}')>"
        )