"""FinancialTransaction ORM model matching the existing MySQL table."""

import enum
from datetime import datetime

from sqlalchemy import (
    DECIMAL,
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


class TransactionType(str, enum.Enum):
    CREDIT = "Credit"
    DEBIT = "Debit"


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    __table_args__ = (
        Index("idx_transaction_accused", "accused_id"),
    )

    transaction_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    accused_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("accused.accused_id", ondelete="SET NULL"),
        nullable=True,
    )

    fir_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("firs.fir_id", ondelete="SET NULL"),
        nullable=True,
    )

    bank_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    account_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    transaction_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    amount: Mapped[float | None] = mapped_column(
        DECIMAL(15, 2),
        nullable=True,
    )

    transaction_type: Mapped[TransactionType | None] = mapped_column(
        Enum(
            TransactionType,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
        ),
        nullable=True,
    )

    transaction_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<FinancialTransaction("
            f"transaction_id={self.transaction_id}, "
            f"reference='{self.transaction_reference}')>"
        )