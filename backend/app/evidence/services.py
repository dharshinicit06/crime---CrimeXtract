"""Evidence business logic with CRUD, filtering, search, and pagination."""

from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.evidence.models import Evidence, EvidenceType
from app.exceptions.handlers import NotFoundException
from app.logging import get_logger
from app.utils.pagination import paginate

logger = get_logger(__name__)


class EvidenceService:
    """Handles evidence lifecycle: create, read, update, delete, list."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_evidence_or_404(self, evidence_id: int) -> Evidence:
        ev = await self.session.get(Evidence, evidence_id)
        if not ev:
            raise NotFoundException(
                message=f"Evidence '{evidence_id}' not found",
                error_code="EVIDENCE_NOT_FOUND",
            )
        return ev

    async def create_evidence(self, fir_id: str, collected_by_id: int, data: dict) -> Evidence:
        """Create a new evidence record linked to an FIR."""
        model_data = {}
        field_map = {
            "evidence_name": "evidence_name", "name": "evidence_name",
            "description": "description",
            "evidence_type": "evidence_type",
            "file_path": "file_path",
            "collected_date": "collected_date",
            "collected_at": "collected_date",
        }
        for k, v in data.items():
            mapped = field_map.get(k)
            if mapped and v is not None:
                model_data[mapped] = v

        if "collected_date" not in model_data:
            model_data["collected_date"] = datetime.utcnow()

        ev = Evidence(
            fir_id=int(fir_id),
            collected_by=collected_by_id,
            **model_data,
        )
        self.session.add(ev)
        await self.session.flush()
        await self.session.refresh(ev)
        logger.info("Evidence created for FIR %s: %s", fir_id, ev.evidence_name)
        return ev

    async def get_evidence(self, evidence_id: int) -> Evidence:
        return await self._get_evidence_or_404(evidence_id)

    async def list_evidence(
        self,
        *,
        fir_id: Optional[str] = None,
        evidence_type: Optional[EvidenceType] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> dict:
        """List evidence with filtering by FIR, type, and keyword search."""
        base = select(Evidence)

        if fir_id:
            base = base.where(Evidence.fir_id == int(fir_id))
        if evidence_type:
            base = base.where(Evidence.evidence_type == evidence_type)
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    Evidence.evidence_name.ilike(pattern),
                    Evidence.description.ilike(pattern),
                )
            )

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        sort_field_map = {
            "name": Evidence.evidence_name,
            "evidence_name": Evidence.evidence_name,
            "evidence_type": Evidence.evidence_type,
            "collected_date": Evidence.collected_date,
            "collected_at": Evidence.collected_date,
        }
        if sort_by and sort_by in sort_field_map:
            col = sort_field_map[sort_by]
            base = base.order_by(col.desc() if sort_order == "desc" else col.asc())
        else:
            base = base.order_by(Evidence.collected_date.desc())

        offset, _, _ = paginate(total, page, page_size)
        base = base.offset(offset).limit(page_size)

        r = await self.session.execute(base)
        items = list(r.scalars().all())

        return {
            "items": items, "total": total, "page": page,
            "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    async def update_evidence(self, evidence_id: int, data: dict) -> Evidence:
        """Update an evidence record."""
        ev = await self._get_evidence_or_404(evidence_id)
        field_map = {
            "evidence_name": "evidence_name", "name": "evidence_name",
            "description": "description",
            "evidence_type": "evidence_type",
            "file_path": "file_path",
            "collected_date": "collected_date",
            "collected_at": "collected_date",
        }
        for k, v in data.items():
            mapped = field_map.get(k)
            if mapped and v is not None:
                setattr(ev, mapped, v)
        await self.session.flush()
        await self.session.refresh(ev)
        logger.info("Evidence %s updated", evidence_id)
        return ev

    async def delete_evidence(self, evidence_id: int) -> None:
        """Delete an evidence record."""
        ev = await self._get_evidence_or_404(evidence_id)
        await self.session.delete(ev)
        await self.session.flush()
        logger.info("Evidence %s deleted", evidence_id)
