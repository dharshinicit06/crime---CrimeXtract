"""Accused business logic with CRUD, FIR linking, filtering, and pagination."""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.models import Accused, FIRAccusedLink
from app.exceptions.handlers import NotFoundException
from app.logging import get_logger
from app.utils.pagination import paginate

logger = get_logger(__name__)


class AccusedService:
    """Handles accused lifecycle: create, read, update, delete, link FIRs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_accused_or_404(self, accused_id: int) -> Accused:
        accused = await self.session.get(Accused, accused_id)
        if not accused:
            raise NotFoundException(message=f"Accused '{accused_id}' not found", error_code="ACCUSED_NOT_FOUND")
        return accused

    async def create_accused(self, data: dict) -> Accused:
        """Create a new accused record with optional FIR links."""
        fir_ids = data.pop("fir_ids", [])
        # Map schema field names to model field names
        model_data = {}
        field_map = {
            "full_name": "full_name", "name": "full_name",
            "age": "age", "gender": "gender", "dob": "dob",
            "phone": "phone", "email": "email", "address": "address",
            "occupation": "occupation", "aadhaar_number": "aadhaar_number",
            "risk_score": "risk_score", "is_repeat_offender": "is_repeat_offender",
        }
        for k, v in data.items():
            mapped = field_map.get(k)
            if mapped and v is not None:
                model_data[mapped] = v

        accused = Accused(**model_data)
        self.session.add(accused)
        await self.session.flush()
        for fid in fir_ids:
            link = FIRAccusedLink(fir_id=int(fid), accused_id=accused.accused_id)
            self.session.add(link)
        await self.session.flush()
        await self.session.refresh(accused)
        logger.info("Accused created: %s (linked to %d FIRs)", accused.full_name, len(fir_ids))
        return accused

    async def get_accused(self, accused_id: int) -> Accused:
        return await self._get_accused_or_404(accused_id)

    async def list_accused(
        self, *, search=None, is_active=None, fir_id=None,
        min_risk_score=None, max_risk_score=None,
        page=1, page_size=20, sort_by=None, sort_order="desc",
    ):
        """List accused with filtering and keyword search."""
        base = select(Accused)
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    Accused.full_name.ilike(pattern),
                    Accused.phone.ilike(pattern),
                    Accused.email.ilike(pattern),
                )
            )
        if fir_id:
            base = base.where(
                Accused.accused_id.in_(
                    select(FIRAccusedLink.accused_id).where(FIRAccusedLink.fir_id == int(fir_id))
                )
            )
        if min_risk_score is not None:
            base = base.where(Accused.risk_score >= min_risk_score)
        if max_risk_score is not None:
            base = base.where(Accused.risk_score <= max_risk_score)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        sort_field_map = {
            "name": Accused.full_name, "full_name": Accused.full_name,
            "risk_score": Accused.risk_score,
            "created_at": Accused.created_at,
        }
        if sort_by and sort_by in sort_field_map:
            col = sort_field_map[sort_by]
            base = base.order_by(col.desc() if sort_order == "desc" else col.asc())
        else:
            base = base.order_by(Accused.created_at.desc())

        offset, _, _ = paginate(total, page, page_size)
        base = base.offset(offset).limit(page_size)

        r = await self.session.execute(base)
        items = list(r.unique().scalars().all())

        return {
            "items": items, "total": total, "page": page,
            "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    async def update_accused(self, accused_id: int, data: dict) -> Accused:
        accused = await self._get_accused_or_404(accused_id)
        field_map = {
            "full_name": "full_name", "name": "full_name",
            "age": "age", "gender": "gender",
            "phone": "phone", "email": "email", "address": "address",
            "occupation": "occupation",
            "risk_score": "risk_score", "is_repeat_offender": "is_repeat_offender",
        }
        for k, v in data.items():
            mapped = field_map.get(k)
            if mapped and v is not None:
                setattr(accused, mapped, v)
        await self.session.flush()
        await self.session.refresh(accused)
        logger.info("Accused %s updated", accused_id)
        return accused

    async def delete_accused(self, accused_id: int) -> None:
        accused = await self._get_accused_or_404(accused_id)
        await self.session.delete(accused)
        await self.session.flush()
        logger.info("Accused %s deleted", accused_id)

    # FIR Link management
    async def link_to_fir(self, accused_id: int, fir_id: str) -> FIRAccusedLink:
        await self._get_accused_or_404(accused_id)
        link = FIRAccusedLink(fir_id=int(fir_id), accused_id=accused_id)
        self.session.add(link)
        await self.session.flush()
        await self.session.refresh(link)
        logger.info("Accused %s linked to FIR %s", accused_id, fir_id)
        return link

    async def unlink_from_fir(self, fir_id: str, accused_id: str) -> None:
        """Remove the link between an FIR and an accused using composite key."""
        link = await self.session.get(FIRAccusedLink, (int(fir_id), int(accused_id)))
        if not link:
            raise NotFoundException(message="FIR-Accused link not found", error_code="LINK_NOT_FOUND")
        await self.session.delete(link)
        await self.session.flush()
        logger.info("FIR-Accused link removed: FIR %s, Accused %s", fir_id, accused_id)

    async def list_fir_links(self, accused_id: int) -> list[FIRAccusedLink]:
        await self._get_accused_or_404(accused_id)
        r = await self.session.execute(
            select(FIRAccusedLink).where(FIRAccusedLink.accused_id == accused_id)
        )
        return list(r.scalars().all())
