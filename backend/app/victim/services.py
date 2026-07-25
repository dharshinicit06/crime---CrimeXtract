"""Victim business logic with CRUD, filtering, search, and pagination."""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.handlers import NotFoundException
from app.logging import get_logger
from app.utils.pagination import paginate
from app.victim.models import FIRVictimLink, Victim

logger = get_logger(__name__)


class VictimService:
    """Handles victim lifecycle: create, read, update, delete, list."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_victim_or_404(self, victim_id: int) -> Victim:
        victim = await self.session.get(Victim, victim_id)
        if not victim:
            raise NotFoundException(
                message=f"Victim '{victim_id}' not found",
                error_code="VICTIM_NOT_FOUND",
            )
        return victim

    async def create_victim(self, fir_id: str | None, data: dict) -> Victim:
        """Create a new victim record.

        If fir_id is provided, also link to the FIR via FIRVictimLink.
        """
        model_data = {}
        field_map = {
            "full_name": "full_name",
            "age": "age", "gender": "gender",
            "phone": "phone", "email": "email", "address": "address",
            "occupation": "occupation",
        }
        for k, v in data.items():
            mapped = field_map.get(k)
            if mapped and v is not None:
                model_data[mapped] = v

        victim = Victim(**model_data)
        self.session.add(victim)
        await self.session.flush()

        # Link to FIR via junction table (only if fir_id provided)
        if fir_id:
            link = FIRVictimLink(fir_id=int(fir_id), victim_id=victim.victim_id)
            self.session.add(link)
            await self.session.flush()

        await self.session.refresh(victim)

        if fir_id:
            logger.info("Victim created for FIR %s: %s", fir_id, victim.full_name)
        else:
            logger.info("Victim created (standalone): %s", victim.full_name)
        return victim

    async def get_victim(self, victim_id: int) -> Victim:
        """Get a victim record."""
        return await self._get_victim_or_404(victim_id)

    async def list_victims(
        self, *, fir_id=None, search=None,
        page=1, page_size=20, sort_by=None, sort_order="desc",
    ):
        """List victims with filtering by FIR and keyword search."""
        base = select(Victim)

        if fir_id:
            # Find victims linked to this FIR via the junction table
            base = base.where(
                Victim.victim_id.in_(
                    select(FIRVictimLink.victim_id).where(FIRVictimLink.fir_id == int(fir_id))
                )
            )
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    Victim.full_name.ilike(pattern),
                    Victim.phone.ilike(pattern),
                    Victim.email.ilike(pattern),
                    Victim.address.ilike(pattern),
                )
            )

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        sort_field_map = {
            "name": Victim.full_name, "full_name": Victim.full_name,
            "age": Victim.age, "gender": Victim.gender,
            "created_at": Victim.created_at,
        }
        if sort_by and sort_by in sort_field_map:
            col = sort_field_map[sort_by]
            base = base.order_by(col.desc() if sort_order == "desc" else col.asc())
        else:
            base = base.order_by(Victim.created_at.desc())

        offset, _, _ = paginate(total, page, page_size)
        base = base.offset(offset).limit(page_size)

        result = await self.session.execute(base)
        victims = list(result.scalars().all())

        return {
            "items": victims, "total": total, "page": page,
            "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    async def update_victim(self, victim_id: int, data: dict) -> Victim:
        """Update a victim record's fields."""
        victim = await self._get_victim_or_404(victim_id)
        field_map = {
            "full_name": "full_name", "name": "full_name",
            "age": "age", "gender": "gender",
            "phone": "phone", "email": "email", "address": "address",
            "occupation": "occupation",
        }
        for key, value in data.items():
            mapped = field_map.get(key)
            if mapped and value is not None:
                setattr(victim, mapped, value)
        await self.session.flush()
        await self.session.refresh(victim)
        logger.info("Victim %s updated", victim_id)
        return victim

    async def delete_victim(self, victim_id: int) -> None:
        """Delete a victim record."""
        victim = await self._get_victim_or_404(victim_id)
        await self.session.delete(victim)
        await self.session.flush()
        logger.info("Victim %s deleted", victim_id)
