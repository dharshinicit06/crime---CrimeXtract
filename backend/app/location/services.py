"""Location business logic with CRUD, filtering, search, pagination, and FK validation."""

from typing import Optional

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.location.models import Location
from app.fir.models import FIR
from app.evidence.models import Evidence
from app.exceptions.handlers import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.logging import get_logger
from app.utils.pagination import paginate

logger = get_logger(__name__)


class LocationService:
    """Handles location lifecycle: create, read, update, delete, list."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_location_or_404(self, location_id: int) -> Location:
        loc = await self.session.get(Location, location_id)
        if not loc:
            raise NotFoundException(
                message=f"Location #{location_id} not found",
                error_code="LOCATION_NOT_FOUND",
            )
        return loc

    async def create_location(self, data: dict) -> Location:
        """Create a new location record. Checks for duplicates."""
        district = data.get("district", "")
        city = data.get("city", "")
        area = data.get("area", "")

        # Duplicate check
        dup_q = select(func.count()).where(
            Location.district == district,
            Location.city == city,
            Location.area == area,
        )
        dup_count = (await self.session.execute(dup_q)).scalar_one()
        if dup_count > 0:
            raise ConflictException(
                message=f"Location '{area}, {city}, {district}' already exists",
                error_code="LOCATION_DUPLICATE",
            )

        loc = Location(
            district=district,
            city=city,
            area=area,
            pincode=data.get("pincode"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
        )
        self.session.add(loc)
        await self.session.flush()
        await self.session.refresh(loc)
        logger.info("Location created: %s, %s, %s", loc.area, loc.city, loc.district)
        return loc

    async def get_location(self, location_id: int) -> Location:
        return await self._get_location_or_404(location_id)

    async def list_locations(
        self,
        *,
        city: Optional[str] = None,
        district: Optional[str] = None,
        area: Optional[str] = None,
        search: Optional[str] = None,
        pincode: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> dict:
        """List locations with filtering and keyword search."""
        base = select(Location)

        if district:
            base = base.where(Location.district.ilike(f"%{district}%"))
        if city:
            base = base.where(Location.city.ilike(f"%{city}%"))
        if area:
            base = base.where(Location.area.ilike(f"%{area}%"))
        if pincode:
            base = base.where(Location.pincode.ilike(f"%{pincode}%"))
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    Location.district.ilike(pattern),
                    Location.city.ilike(pattern),
                    Location.area.ilike(pattern),
                )
            )

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        sort_field_map = {
            "city": Location.city, "district": Location.district,
            "area": Location.area, "created_at": Location.created_at,
        }
        if sort_by and sort_by in sort_field_map:
            col = sort_field_map[sort_by]
            base = base.order_by(col.desc() if sort_order == "desc" else col.asc())
        else:
            base = base.order_by(Location.city.asc())

        offset, _, _ = paginate(total, page, page_size)
        base = base.offset(offset).limit(page_size)

        r = await self.session.execute(base)
        items = list(r.scalars().all())

        return {
            "items": items, "total": total, "page": page,
            "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    async def update_location(self, location_id: int, data: dict) -> Location:
        """Update a location record."""
        loc = await self._get_location_or_404(location_id)
        updatable = {"district", "city", "area", "pincode", "latitude", "longitude"}
        for key, value in data.items():
            if key in updatable and value is not None:
                setattr(loc, key, value)
        await self.session.flush()
        await self.session.refresh(loc)
        logger.info("Location %s updated", location_id)
        return loc

    async def get_location_usage(self, location_id: int) -> dict:
        """Return usage counts for a location across modules."""
        await self._get_location_or_404(location_id)

        # FIRs at this location
        fir_count_q = select(func.count()).where(FIR.location_id == location_id)
        fir_count = (await self.session.execute(fir_count_q)).scalar_one()

        # Get FIR IDs for this location to count linked records
        fir_ids_q = select(FIR.fir_id).where(FIR.location_id == location_id)
        fir_ids = list((await self.session.execute(fir_ids_q)).scalars().all())

        # Evidence linked via those FIRs
        ev_count = 0
        if fir_ids:
            ev_count_q = select(func.count()).where(Evidence.fir_id.in_(fir_ids))
            ev_count = (await self.session.execute(ev_count_q)).scalar_one()

        # Accused and victims linked via join tables
        acc_count = 0
        vic_count = 0
        if fir_ids:
            acc_q = select(func.count(func.distinct(text("accused_id")))).select_from(
                text("fir_accused")
            ).where(text("fir_id").in_(fir_ids))
            acc_count = (await self.session.execute(acc_q)).scalar_one() or 0

            vic_q = select(func.count(func.distinct(text("victim_id")))).select_from(
                text("fir_victims")
            ).where(text("fir_id").in_(fir_ids))
            vic_count = (await self.session.execute(vic_q)).scalar_one() or 0

        return {
            "location_id": location_id,
            "fir_count": fir_count,
            "evidence_count": ev_count,
            "accused_count": acc_count,
            "victim_count": vic_count,
        }

    async def get_statistics(self) -> dict:
        """Return aggregate location statistics."""
        total_q = select(func.count(Location.location_id))
        total = (await self.session.execute(total_q)).scalar_one()

        # Locations by district
        district_q = select(
            Location.district, func.count(Location.location_id).label("cnt")
        ).group_by(Location.district).order_by(text("cnt DESC"))
        district_rows = (await self.session.execute(district_q)).all()
        by_district = [{"district": r.district, "count": r.cnt} for r in district_rows]

        # Locations by city
        city_q = select(
            Location.city, func.count(Location.location_id).label("cnt")
        ).group_by(Location.city).order_by(text("cnt DESC"))
        city_rows = (await self.session.execute(city_q)).all()
        by_city = [{"city": r.city, "count": r.cnt} for r in city_rows]

        # Newest locations
        newest_q = select(Location).order_by(Location.created_at.desc()).limit(5)
        newest_rows = (await self.session.execute(newest_q)).scalars().all()
        newest = [
            {
                "location_id": l.location_id,
                "district": l.district,
                "city": l.city,
                "area": l.area,
                "created_at": str(l.created_at) if l.created_at else None,
            }
            for l in newest_rows
        ]

        return {
            "total_locations": total,
            "unique_districts": len(by_district),
            "unique_cities": len(by_city),
            "by_district": by_district,
            "by_city": by_city,
            "newest": newest,
        }

    async def delete_location(self, location_id: int) -> None:
        """Delete a location record. Checks for FIR references first."""
        loc = await self._get_location_or_404(location_id)

        # Check if any FIR references this location
        fir_check = select(func.count()).where(FIR.location_id == location_id)
        fir_count = (await self.session.execute(fir_check)).scalar_one()
        if fir_count > 0:
            raise BadRequestException(
                message=f"Location is linked with {fir_count} existing FIR record(s). Remove FIR references first.",
                error_code="LOCATION_IN_USE",
            )

        await self.session.delete(loc)
        await self.session.flush()
        logger.info("Location %s deleted", location_id)
