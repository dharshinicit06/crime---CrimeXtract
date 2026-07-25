"""Pydantic schemas for Financial Transaction CRUD operations — aligned with ORM model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.financial_transaction.models import TransactionType
from app.schemas.common import PaginationParams


class FinancialTransactionCreate(BaseModel):
    """Payload for creating a new financial transaction record.
    Field names match the ORM model (bank_name, not bank).
    """
    bank_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    transaction_reference: Optional[str] = Field(None, max_length=100)
    amount: Optional[float] = None
    transaction_type: Optional[TransactionType] = None
    transaction_date: Optional[datetime] = None
    remarks: Optional[str] = None
    accused_id: Optional[int] = None


class FinancialTransactionUpdate(BaseModel):
    """Payload for updating a financial transaction record. All fields optional."""
    bank_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    transaction_reference: Optional[str] = Field(None, max_length=100)
    amount: Optional[float] = None
    transaction_type: Optional[TransactionType] = None
    transaction_date: Optional[datetime] = None
    remarks: Optional[str] = None
    accused_id: Optional[int] = None


class FinancialTransactionFilterParams(PaginationParams):
    """Query parameters for filtering and searching financial transactions."""
    fir_id: Optional[str] = Field(None, description="Filter by linked FIR ID")
    accused_id: Optional[int] = Field(None, description="Filter by accused ID")
    bank_name: Optional[str] = Field(None, description="Filter by bank name")
    transaction_type: Optional[TransactionType] = Field(None, description="Filter by transaction type")
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum transaction amount")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum transaction amount")
    date_from: Optional[datetime] = Field(None, description="Filter transactions from this date")
    date_to: Optional[datetime] = Field(None, description="Filter transactions up to this date")
    search: Optional[str] = Field(None, description="Search by bank name, account number, or reference")


class FinancialTransactionResponse(BaseModel):
    """Full financial transaction record response — matches ORM model fields exactly."""
    transaction_id: int
    accused_id: Optional[int] = None
    fir_id: Optional[int] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    transaction_reference: Optional[str] = None
    amount: Optional[float] = None
    transaction_type: Optional[TransactionType] = None
    transaction_date: Optional[datetime] = None
    remarks: Optional[str] = None

    model_config = {"from_attributes": True}


class FinancialTransactionListResponse(BaseModel):
    """Paginated financial transaction list response."""
    items: list[FinancialTransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BankBreakdownItem(BaseModel):
    """Bank-wise transaction breakdown."""
    bank: Optional[str] = None
    count: int = 0
    total: float = 0.0


class TypeBreakdownItem(BaseModel):
    """Transaction type breakdown."""
    type: str = "Unknown"
    count: int = 0
    total: float = 0.0


class HighValueTransaction(BaseModel):
    """High-value or suspicious transaction summary."""
    transaction_id: int
    bank_name: Optional[str] = None
    amount: float = 0.0
    transaction_type: Optional[str] = None
    transaction_date: Optional[str] = None
    transaction_reference: Optional[str] = None


class FinancialTransactionAnalyticsResponse(BaseModel):
    """Aggregated financial summary with suspicious detection."""
    total_count: int = 0
    total_amount: float = 0.0
    average_amount: float = 0.0
    bank_breakdown: list[BankBreakdownItem] = Field(default_factory=list)
    type_breakdown: list[TypeBreakdownItem] = Field(default_factory=list)
    high_value_transactions: list[HighValueTransaction] = Field(default_factory=list)
    high_value_threshold: float = 10_00_000.0
    suspicious_transactions: list[HighValueTransaction] = Field(default_factory=list)
    suspicious_count: int = 0
    high_value_count: int = 0
