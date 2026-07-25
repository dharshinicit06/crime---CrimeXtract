"""Crime History business logic with CRUD, timeline, and repeat-offender queries."""

from datetime import date
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.models import Accused
from app.crime_history.models import CrimeHistory, ConvictionStatus, Disposition
from app.exceptions.handlers import NotFoundException
from app.logging import get_logger
from app.utils.pagination import paginate

logger = get_logger(__name__)


class CrimeHistoryService:
    """Handles crime history lifecycle: create, read, update, delete, timeline."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_or_404(self, history_id: int) -> CrimeHistory:
        obj = await self.session.get(CrimeHistory, history_id)
        if not obj:
            raise NotFoundException(
                message=f"Crime history '{history_id}' not found",
                error_code="CRIME_HISTORY_NOT_FOUND",
            )
        return obj

    async def create(self, data: dict) -> CrimeHistory:
        """Create a new crime history record."""
        model_data = {}
        field_map = {
            "accused_id": "accused_id",
            "fir_id": "fir_id",
            "crime_type": "crime_type",
            "offense_type": "crime_type",
            "arrest_date": "arrest_date",
            "crime_date": "arrest_date",
            "conviction_status": "conviction_status",
            "disposition": "conviction_status",
            "sentence": "sentence",
            "remarks": "remarks",
            "notes": "remarks",
        }
        for k, v in data.items():
            mapped = field_map.get(k)
            if mapped and v is not None:
                model_data[mapped] = v

        # Map Disposition enum values to ConvictionStatus
        if "conviction_status" in model_data:
            status = model_data["conviction_status"]
            if isinstance(status, Disposition):
                disposition_to_conviction = {
                    Disposition.CONVICTED: ConvictionStatus.CONVICTED,
                    Disposition.ACQUITTED: ConvictionStatus.ACQUITTED,
                    Disposition.PENDING: ConvictionStatus.PENDING,
                    Disposition.UNKNOWN: ConvictionStatus.PENDING,
                    Disposition.DISMISSED: ConvictionStatus.ACQUITTED,
                }
                model_data["conviction_status"] = disposition_to_conviction.get(
                    status, ConvictionStatus.PENDING
                )

        obj = CrimeHistory(**model_data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        logger.info(
            "Crime history created for accused %s: %s",
            obj.accused_id, obj.crime_type,
        )
        return obj

    async def get(self, history_id: int) -> CrimeHistory:
        obj = await self.session.get(CrimeHistory, history_id)
        if not obj:
            raise NotFoundException(
                message=f"Crime history '{history_id}' not found",
                error_code="CRIME_HISTORY_NOT_FOUND",
            )
        return obj

    async def list(
        self,
        *,
        accused_id: Optional[str] = None,
        fir_id: Optional[str] = None,
        disposition: Optional[Disposition] = None,
        offense_type: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> dict:
        """List crime history with filtering and keyword search."""
        base = select(CrimeHistory)

        if accused_id:
            base = base.where(CrimeHistory.accused_id == int(accused_id))
        if fir_id:
            base = base.where(CrimeHistory.fir_id == int(fir_id))
        if offense_type:
            base = base.where(CrimeHistory.crime_type.ilike(f"%{offense_type}%"))
        if search:
            pattern = f"%{search}%"
            base = base.where(
                CrimeHistory.crime_type.ilike(pattern)
            )
        if date_from:
            base = base.where(CrimeHistory.arrest_date >= date_from)
        if date_to:
            base = base.where(CrimeHistory.arrest_date <= date_to)

        # Filter by disposition: map Disposition to ConvictionStatus
        if disposition is not None:
            disposition_map = {
                Disposition.CONVICTED: ConvictionStatus.CONVICTED,
                Disposition.ACQUITTED: ConvictionStatus.ACQUITTED,
                Disposition.PENDING: ConvictionStatus.PENDING,
                Disposition.UNKNOWN: ConvictionStatus.PENDING,
                Disposition.DISMISSED: ConvictionStatus.ACQUITTED,
            }
            mapped = disposition_map.get(disposition)
            if mapped:
                base = base.where(CrimeHistory.conviction_status == mapped)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        sort_field_map = {
            "crime_date": CrimeHistory.arrest_date,
            "arrest_date": CrimeHistory.arrest_date,
            "offense_type": CrimeHistory.crime_type,
            "crime_type": CrimeHistory.crime_type,
            "conviction_status": CrimeHistory.conviction_status,
            "disposition": CrimeHistory.conviction_status,
            "created_at": CrimeHistory.created_at,
        }
        if sort_by and sort_by in sort_field_map:
            col = sort_field_map[sort_by]
            base = base.order_by(col.desc() if sort_order == "desc" else col.asc())
        else:
            base = base.order_by(CrimeHistory.arrest_date.desc())

        offset, _, _ = paginate(total, page, page_size)
        base = base.offset(offset).limit(page_size)

        r = await self.session.execute(base)
        items = list(r.unique().scalars().all())

        return {
            "items": items, "total": total, "page": page,
            "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    async def update(self, history_id: int, data: dict) -> CrimeHistory:
        """Update a crime history record."""
        obj = await self._get_or_404(history_id)
        field_map = {
            "crime_type": "crime_type", "offense_type": "crime_type",
            "arrest_date": "arrest_date", "crime_date": "arrest_date",
            "conviction_status": "conviction_status", "disposition": "conviction_status",
            "sentence": "sentence",
            "remarks": "remarks", "notes": "remarks",
        }
        for k, v in data.items():
            mapped = field_map.get(k)
            if mapped and v is not None:
                # Handle Disposition → ConvictionStatus mapping
                if mapped == "conviction_status" and isinstance(v, Disposition):
                    disposition_map = {
                        Disposition.CONVICTED: ConvictionStatus.CONVICTED,
                        Disposition.ACQUITTED: ConvictionStatus.ACQUITTED,
                        Disposition.PENDING: ConvictionStatus.PENDING,
                        Disposition.UNKNOWN: ConvictionStatus.PENDING,
                        Disposition.DISMISSED: ConvictionStatus.ACQUITTED,
                    }
                    v = disposition_map.get(v, ConvictionStatus.PENDING)
                setattr(obj, mapped, v)
        await self.session.flush()
        await self.session.refresh(obj)
        logger.info("Crime history %s updated", history_id)
        return obj

    async def delete(self, history_id: int) -> None:
        """Delete a crime history record."""
        obj = await self._get_or_404(history_id)
        await self.session.delete(obj)
        await self.session.flush()
        logger.info("Crime history %s deleted", history_id)

    # ─── Repeat-offender queries ────────────────────────────────

    async def get_repeat_offenders(
        self,
        min_offenses: int = 2,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Identify repeat offenders — accused with multiple crime history records.

        Returns paginated list of (accused_id, name, offense_count).
        """
        q = (
            select(
                CrimeHistory.accused_id,
                func.count(CrimeHistory.history_id).label("offense_count"),
            )
            .group_by(CrimeHistory.accused_id)
            .having(func.count(CrimeHistory.history_id) >= min_offenses)
            .order_by(func.count(CrimeHistory.history_id).desc())
        )

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        offset, _, _ = paginate(total, page, page_size)
        q = q.offset(offset).limit(page_size)
        r = await self.session.execute(q)
        rows = r.all()

        # Fetch accused names
        accused_ids = [row.accused_id for row in rows]
        name_map = {}
        if accused_ids:
            ar = await self.session.execute(
                select(Accused).where(Accused.accused_id.in_(accused_ids))
            )
            for a in ar.scalars().all():
                name_map[a.accused_id] = a.full_name

        items = [
            {
                "accused_id": row.accused_id,
                "name": name_map.get(row.accused_id, "Unknown"),
                "offense_count": row.offense_count,
            }
            for row in rows
        ]

        return {
            "items": items, "total": total, "page": page,
            "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size),
        }
