"""Location ORM model matching the existing MySQL locations table."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Index, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Location(Base):
    __tablename__ = "locations"

    __table_args__ = (
        Index("idx_city", "city"),
        Index("idx_district", "district"),
        Index("idx_area", "area"),
        Index("idx_district_city", "district", "city"),
    )

    location_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    district: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    area: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    pincode: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        DECIMAL(10, 8),
        nullable=True,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        DECIMAL(11, 8),
        nullable=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Location(location_id={self.location_id}, "
            f"city='{self.city}', "
            f"district='{self.district}')>"
        )
