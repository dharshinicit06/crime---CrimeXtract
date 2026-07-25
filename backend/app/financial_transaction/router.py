"""Financial Transaction API endpoints with RBAC, filtering, and pagination."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import RoleChecker, get_current_user, get_db_session
from app.auth.models import User
from app.financial_transaction.schemas import (
    FinancialTransactionAnalyticsResponse, FinancialTransactionCreate,
    FinancialTransactionFilterParams, FinancialTransactionListResponse,
    FinancialTransactionResponse, FinancialTransactionUpdate,
)
from app.financial_transaction.services import FinancialTransactionService

router = APIRouter(prefix="/financial-transactions", tags=["financial-transaction-management"])


def get_financial_transaction_service(
    session: AsyncSession = Depends(get_db_session),
) -> FinancialTransactionService:
    return FinancialTransactionService(session=session)


@router.post(
    "/",
    response_model=FinancialTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new financial transaction record",
)
async def create_financial_transaction(
    request: FinancialTransactionCreate,
    fir_id: Optional[int] = Query(None, description="FIR ID to link this transaction to (optional)"),
    current_user: User = Depends(get_current_user),
    service: FinancialTransactionService = Depends(get_financial_transaction_service),
) -> FinancialTransactionResponse:
    """Create a new financial transaction. If fir_id is provided, links to that FIR."""
    return await service.create_transaction(fir_id=str(fir_id) if fir_id else None, data=request.model_dump())


@router.get(
    "/",
    response_model=FinancialTransactionListResponse,
    summary="List financial transactions with filtering and pagination",
)
async def list_financial_transactions(
    filters: FinancialTransactionFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: FinancialTransactionService = Depends(get_financial_transaction_service),
) -> FinancialTransactionListResponse:
    """List financial transactions with optional filtering."""
    return await service.list_transactions(
        fir_id=filters.fir_id,
        bank_name=filters.bank_name,
        transaction_type=filters.transaction_type,
        min_amount=filters.min_amount,
        max_amount=filters.max_amount,
        date_from=filters.date_from,
        date_to=filters.date_to,
        search=filters.search,
        page=filters.page,
        page_size=filters.page_size,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )


@router.get(
    "/{transaction_id}",
    response_model=FinancialTransactionResponse,
    summary="Get financial transaction details",
)
async def get_financial_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    service: FinancialTransactionService = Depends(get_financial_transaction_service),
) -> FinancialTransactionResponse:
    """Get a financial transaction record by ID."""
    return await service.get_transaction(transaction_id)


@router.patch(
    "/{transaction_id}",
    response_model=FinancialTransactionResponse,
    summary="Update financial transaction details",
)
async def update_financial_transaction(
    transaction_id: int,
    request: FinancialTransactionUpdate,
    current_user: User = Depends(get_current_user),
    service: FinancialTransactionService = Depends(get_financial_transaction_service),
) -> FinancialTransactionResponse:
    """Update a financial transaction record's fields."""
    return await service.update_transaction(
        transaction_id=transaction_id,
        data=request.model_dump(exclude_unset=True),
    )


@router.get(
    "/analytics/summary",
    response_model=FinancialTransactionAnalyticsResponse,
    summary="Financial transaction summary and suspicious activity detection",
)
async def financial_transaction_summary(
    current_user: User = Depends(get_current_user),
    service: FinancialTransactionService = Depends(get_financial_transaction_service),
) -> FinancialTransactionAnalyticsResponse:
    """Return aggregated financial summary including:
    - Total counts and amounts
    - Bank-wise breakdown
    - Transaction type breakdown
    - High-value transactions (>= ₹10L)
    - Suspicious transaction detection
    """
    return await service.get_summary()


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a financial transaction record",
    dependencies=[Depends(RoleChecker(1))],  # Supervisor only
)
async def delete_financial_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    service: FinancialTransactionService = Depends(get_financial_transaction_service),
) -> None:
    """Delete a financial transaction record. Restricted to supervisors."""
    await service.delete_transaction(transaction_id=transaction_id)
