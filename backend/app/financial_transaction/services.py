"""Financial Transaction business logic with CRUD, filtering, search, and pagination."""

from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.handlers import NotFoundException
from app.financial_transaction.models import FinancialTransaction, TransactionType
from app.logging import get_logger
from app.utils.pagination import paginate

logger = get_logger(__name__)


class FinancialTransactionService:
    """Handles financial transaction lifecycle: create, read, update, delete, list."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_transaction_or_404(self, transaction_id: int) -> FinancialTransaction:
        tx = await self.session.get(FinancialTransaction, transaction_id)
        if not tx:
            raise NotFoundException(
                message=f"Financial transaction '{transaction_id}' not found",
                error_code="FINANCIAL_TRANSACTION_NOT_FOUND",
            )
        return tx

    async def create_transaction(self, fir_id: str | None, data: dict) -> FinancialTransaction:
        """Create a new financial transaction record. If fir_id is provided, links to that FIR."""
        model_data = {}
        field_map = {
            "bank_name": "bank_name",
            "account_number": "account_number",
            "transaction_reference": "transaction_reference",
            "amount": "amount",
            "transaction_type": "transaction_type",
            "transaction_date": "transaction_date",
            "remarks": "remarks",
            "accused_id": "accused_id",
        }
        for k, v in data.items():
            mapped = field_map.get(k)
            if mapped and v is not None:
                model_data[mapped] = v

        if fir_id:
            model_data["fir_id"] = int(fir_id)

        tx = FinancialTransaction(**model_data)
        self.session.add(tx)
        await self.session.flush()
        await self.session.refresh(tx)
        logger.info(
            "Financial transaction created: amount=%.2f",
            tx.amount or 0,
        )
        return tx

    async def get_transaction(self, transaction_id: int) -> FinancialTransaction:
        """Get a financial transaction by ID."""
        return await self._get_transaction_or_404(transaction_id)

    async def list_transactions(
        self,
        *,
        fir_id: Optional[str] = None,
        bank_name: Optional[str] = None,
        transaction_type: Optional[TransactionType] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> dict:
        """List financial transactions with filtering and pagination."""
        base = select(FinancialTransaction)

        if fir_id:
            base = base.where(FinancialTransaction.fir_id == int(fir_id))
        if bank_name:
            base = base.where(FinancialTransaction.bank_name.ilike(f"%{bank_name}%"))
        if transaction_type:
            base = base.where(FinancialTransaction.transaction_type == transaction_type)
        if min_amount is not None:
            base = base.where(FinancialTransaction.amount >= min_amount)
        if max_amount is not None:
            base = base.where(FinancialTransaction.amount <= max_amount)
        if date_from:
            base = base.where(FinancialTransaction.transaction_date >= date_from)
        if date_to:
            base = base.where(FinancialTransaction.transaction_date <= date_to)
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    FinancialTransaction.bank_name.ilike(pattern),
                    FinancialTransaction.account_number.ilike(pattern),
                    FinancialTransaction.transaction_reference.ilike(pattern),
                )
            )

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        sort_field_map = {
            "amount": FinancialTransaction.amount,
            "transaction_date": FinancialTransaction.transaction_date,
            "bank_name": FinancialTransaction.bank_name,
        }
        if sort_by and sort_by in sort_field_map:
            col = sort_field_map[sort_by]
            base = base.order_by(col.desc() if sort_order == "desc" else col.asc())
        else:
            base = base.order_by(
                FinancialTransaction.transaction_date.desc(),
            )

        offset, _, _ = paginate(total, page, page_size)
        base = base.offset(offset).limit(page_size)

        r = await self.session.execute(base)
        items = list(r.scalars().all())

        return {
            "items": items, "total": total, "page": page,
            "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    async def get_summary(self) -> dict:
        """Return aggregated financial summary: totals, bank breakdown, high-value, suspicious."""
        base = select(FinancialTransaction)

        # Total stats
        count_q = select(func.count()).select_from(base.subquery())
        total_count = (await self.session.execute(count_q)).scalar_one()

        sum_q = select(func.sum(FinancialTransaction.amount))
        total_amount = (await self.session.execute(sum_q)).scalar() or 0.0

        avg_q = select(func.avg(FinancialTransaction.amount))
        avg_amount = (await self.session.execute(avg_q)).scalar() or 0.0

        # Bank-wise breakdown
        bank_q = select(
            FinancialTransaction.bank_name,
            func.count(FinancialTransaction.transaction_id).label("cnt"),
            func.sum(FinancialTransaction.amount).label("total"),
        ).where(
            FinancialTransaction.bank_name.isnot(None),
        ).group_by(FinancialTransaction.bank_name).order_by(func.count(FinancialTransaction.transaction_id).desc())
        r = await self.session.execute(bank_q)
        bank_breakdown = [
            {"bank": row.bank_name, "count": row.cnt, "total": float(row.total or 0)}
            for row in r.all()
        ]

        # Transaction type breakdown
        type_q = select(
            FinancialTransaction.transaction_type,
            func.count(FinancialTransaction.transaction_id).label("cnt"),
            func.sum(FinancialTransaction.amount).label("total"),
        ).where(
            FinancialTransaction.transaction_type.isnot(None),
        ).group_by(FinancialTransaction.transaction_type)
        r = await self.session.execute(type_q)
        type_breakdown = [
            {"type": row.transaction_type.value if row.transaction_type else "Unknown",
             "count": row.cnt, "total": float(row.total or 0)}
            for row in r.all()
        ]

        # High-value transactions (>= ₹10,00,000)
        HIGH_VALUE_THRESHOLD = 10_00_000.0
        high_value_q = select(FinancialTransaction).where(
            FinancialTransaction.amount >= HIGH_VALUE_THRESHOLD
        ).order_by(FinancialTransaction.amount.desc()).limit(20)
        r = await self.session.execute(high_value_q)
        high_value_items = list(r.scalars().all())

        # Suspicious detection: flag transactions with unusual patterns
        # Criteria: high-value + remarks mentioning suspicious terms + large debits
        suspicious_keywords = ["suspicious", "unusual", "flagged", "alert", "fraud", "irregular"]
        suspicious_q = select(FinancialTransaction).where(
            or_(
                FinancialTransaction.amount >= HIGH_VALUE_THRESHOLD * 2,
                FinancialTransaction.remarks.ilike("%suspicious%"),
                FinancialTransaction.remarks.ilike("%fraud%"),
                FinancialTransaction.remarks.ilike("%irregular%"),
            )
        ).order_by(FinancialTransaction.amount.desc()).limit(20)
        r = await self.session.execute(suspicious_q)
        suspicious_items = list(r.scalars().all())

        return {
            "total_count": total_count,
            "total_amount": float(total_amount),
            "average_amount": round(float(avg_amount), 2),
            "bank_breakdown": bank_breakdown,
            "type_breakdown": type_breakdown,
            "high_value_transactions": [
                {
                    "transaction_id": t.transaction_id,
                    "bank_name": t.bank_name,
                    "amount": float(t.amount),
                    "transaction_type": t.transaction_type.value if t.transaction_type else None,
                    "transaction_date": str(t.transaction_date) if t.transaction_date else None,
                    "transaction_reference": t.transaction_reference,
                }
                for t in high_value_items
            ],
            "high_value_threshold": HIGH_VALUE_THRESHOLD,
            "suspicious_transactions": [
                {
                    "transaction_id": t.transaction_id,
                    "bank_name": t.bank_name,
                    "amount": float(t.amount),
                    "transaction_type": t.transaction_type.value if t.transaction_type else None,
                    "transaction_date": str(t.transaction_date) if t.transaction_date else None,
                    "transaction_reference": t.transaction_reference,
                }
                for t in suspicious_items
            ],
            "suspicious_count": len(suspicious_items),
            "high_value_count": len(high_value_items),
        }

    async def update_transaction(self, transaction_id: int, data: dict) -> FinancialTransaction:
        """Update a financial transaction record."""
        tx = await self._get_transaction_or_404(transaction_id)
        field_map = {
            "bank_name": "bank_name",
            "account_number": "account_number",
            "transaction_reference": "transaction_reference",
            "amount": "amount",
            "transaction_type": "transaction_type",
            "transaction_date": "transaction_date",
            "remarks": "remarks",
            "accused_id": "accused_id",
        }
        for k, v in data.items():
            mapped = field_map.get(k)
            if mapped and v is not None:
                setattr(tx, mapped, v)
        await self.session.flush()
        await self.session.refresh(tx)
        logger.info("Financial transaction %s updated", transaction_id)
        return tx

    async def delete_transaction(self, transaction_id: int) -> None:
        """Delete a financial transaction record."""
        tx = await self._get_transaction_or_404(transaction_id)
        await self.session.delete(tx)
        await self.session.flush()
        logger.info("Financial transaction %s deleted", transaction_id)
