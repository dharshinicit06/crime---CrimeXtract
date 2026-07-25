"""Base SQLAlchemy model with common columns."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    """Abstract base model with id, created_at, and updated_at."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )
