"""Prediction ORM model matching the existing MySQL predictions table."""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DECIMAL,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    TIMESTAMP,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RiskLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Prediction(Base):
    __tablename__ = "predictions"

    __table_args__ = (
        Index("idx_prediction_date", "prediction_date"),
        Index("idx_prediction_location", "location_id"),
    )

    prediction_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    location_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("locations.location_id", ondelete="SET NULL"),
        nullable=True,
    )

    crime_type_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("crime_types.crime_type_id", ondelete="SET NULL"),
        nullable=True,
    )

    prediction_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    predicted_cases: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    confidence_score: Mapped[float | None] = mapped_column(
        DECIMAL(5, 2),
        nullable=True,
    )

    risk_level: Mapped[RiskLevel | None] = mapped_column(
        Enum(
            RiskLevel,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
        ),
        nullable=True,
    )

    generated_by: Mapped[str | None] = mapped_column(
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
            f"<Prediction("
            f"prediction_id={self.prediction_id}, "
            f"prediction_date={self.prediction_date})>"
        )