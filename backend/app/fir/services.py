"""FIR business logic with CRUD, relationships, and status management."""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.crime.models import CrimeType
from app.exceptions.handlers import (
    BadRequestException,
    NotFoundException,
)
from app.fir.models import FIR, InvestigationStatus, Priority
from app.location.models import Location
from app.logging import get_logger
from app.officer.models import Officer
from app.utils.pagination import paginate

logger = get_logger(__name__)


class FIRService:
    """Handles FIR lifecycle: create, read, update, delete."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ─── Helpers ────────────────────────────────────────────────

    async def _generate_fir_number(self) -> str:
        """Generate a unique FIR number like FIR-2026-00001."""
        year = datetime.now().year
        result = await self.session.execute(
            select(func.count()).select_from(
                select(FIR).where(
                    func.extract("year", FIR.created_at) == year
                ).subquery()
            )
        )
        count = result.scalar_one() + 1
        return f"FIR-{year}-{count:05d}"

    async def _get_fir_or_404(self, fir_id: int) -> FIR:
        fir = await self.session.get(FIR, fir_id)
        if not fir:
            raise NotFoundException(
                message=f"FIR #{fir_id} not found",
                error_code="FIR_NOT_FOUND",
            )
        return fir

    # ─── Create FIR ─────────────────────────────────────────────

    async def _resolve_crime_type(self, data: dict) -> int | None:
        """Resolve crime_type_id from either ID or text name."""
        if data.get("crime_type_id"):
            return int(data["crime_type_id"])
        crime_type_text = data.get("crime_type")
        if crime_type_text:
            # Look up existing crime type by name
            result = await self.session.execute(
                select(CrimeType).where(CrimeType.crime_name.ilike(crime_type_text))
            )
            ct = result.scalar_one_or_none()
            if ct:
                return ct.crime_type_id
            # Create new crime type
            new_ct = CrimeType(crime_name=crime_type_text)
            self.session.add(new_ct)
            await self.session.flush()
            return new_ct.crime_type_id
        return None

    async def _resolve_location(self, data: dict) -> int | None:
        """Resolve location_id from either ID or text."""
        if data.get("location_id"):
            return int(data["location_id"])
        location_text = data.get("location")
        if location_text:
            # Try to find existing location by district or city
            result = await self.session.execute(
                select(Location).where(
                    or_(Location.district.ilike(location_text), Location.city.ilike(location_text))
                )
            )
            loc = result.scalar_one_or_none()
            if loc:
                return loc.location_id
            # Create a new location - treat text as district, use text as city placeholder
            new_loc = Location(
                district=location_text,
                city=location_text,
                area=location_text,
            )
            self.session.add(new_loc)
            await self.session.flush()
            return new_loc.location_id
        return None

    async def _resolve_officer(self, data: dict) -> int | None:
        """Resolve officer_id from either ID or text."""
        if data.get("officer_id"):
            return int(data["officer_id"])
        officer_text = data.get("officer")
        if officer_text:
            # Try to find existing officer by badge number or name
            result = await self.session.execute(
                select(Officer).where(
                    or_(Officer.badge_number.ilike(officer_text), Officer.designation.ilike(officer_text))
                )
            )
            off = result.scalar_one_or_none()
            if off:
                return off.officer_id
            # Create a new placeholder officer
            badge = officer_text[:30].upper().replace(" ", "_")
            new_off = Officer(
                badge_number=badge,
                designation=officer_text[:100],
            )
            self.session.add(new_off)
            await self.session.flush()
            return new_off.officer_id
        return data.get("assigned_to_id")

    async def create_fir(
        self, user: User, data: dict
    ) -> FIR:
        """Create a new FIR."""
        # Resolve IDs from text inputs
        crime_type_id = await self._resolve_crime_type(data)
        location_id = await self._resolve_location(data)
        officer_id = await self._resolve_officer(data)

        if not crime_type_id:
            from app.exceptions.handlers import BadRequestException
            raise BadRequestException(
                message="Crime type is required (provide crime_type_id or crime_type text)",
                error_code="MISSING_CRIME_TYPE",
            )
        if not location_id:
            from app.exceptions.handlers import BadRequestException
            raise BadRequestException(
                message="Location is required (provide location_id or location text)",
                error_code="MISSING_LOCATION",
            )

        # Generate FIR number
        fir_number = await self._generate_fir_number()

        # Parse priority enum
        priority_val = None
        if data.get("priority"):
            try:
                priority_val = Priority(data["priority"])
            except ValueError:
                priority_val = Priority.MEDIUM

        # Parse investigation status
        inv_status = InvestigationStatus.PENDING
        if data.get("investigation_status"):
            try:
                inv_status = InvestigationStatus(data["investigation_status"])
            except ValueError:
                pass

        # Create the FIR
        fir = FIR(
            fir_number=fir_number,
            title=data.get("title"),
            description=data.get("description"),
            priority=priority_val,
            incident_date=data.get("incident_date"),
            complaint_date=data.get("complaint_date"),
            crime_type_id=crime_type_id,
            location_id=location_id,
            officer_id=officer_id,
            investigation_status=inv_status,
        )
        self.session.add(fir)
        await self.session.flush()
        await self.session.refresh(fir)

        logger.info(
            "FIR %s created by %s", fir.fir_number, user.email
        )
        return fir

    # ─── Get FIR ────────────────────────────────────────────────

    async def get_fir(self, fir_id: int) -> FIR:
        """Get FIR by ID."""
        query = select(FIR).where(FIR.fir_id == fir_id)
        result = await self.session.execute(query)
        fir = result.unique().scalar_one_or_none()
        if not fir:
            raise NotFoundException(
                message=f"FIR #{fir_id} not found",
                error_code="FIR_NOT_FOUND",
            )
        return fir

    # ─── List FIRs ──────────────────────────────────────────────

    async def list_firs(
        self,
        user: User,
        *,
        page: int = 1,
        page_size: int = 20,
        status: Optional[InvestigationStatus] = None,
        priority: Optional[str] = None,
        assigned_to_id: Optional[int] = None,
        filed_by_id: Optional[int] = None,
        crime_category_id: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> dict:
        """List FIRs with filtering, search, and pagination."""
        base = select(FIR)

        # Filters
        if status:
            base = base.where(FIR.investigation_status == status)
        if priority:
            try:
                pri = Priority(priority)
                base = base.where(FIR.priority == pri)
            except ValueError:
                pass
        if crime_category_id:
            base = base.where(FIR.crime_type_id == crime_category_id)
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    FIR.fir_number.ilike(pattern),
                    FIR.title.ilike(pattern),
                    FIR.description.ilike(pattern),
                )
            )
        if date_from:
            base = base.where(FIR.incident_date >= date_from)
        if date_to:
            base = base.where(FIR.incident_date <= date_to)

        # Total count
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        # Sorting
        allowed_sorts = {
            "fir_number", "title", "incident_date", "created_at",
            "priority", "investigation_status",
        }
        if sort_by and sort_by in allowed_sorts:
            col = getattr(FIR, sort_by)
            base = base.order_by(
                col.desc() if sort_order == "desc" else col.asc()
            )
        else:
            base = base.order_by(FIR.created_at.desc())

        # Pagination
        offset, _, _ = paginate(total, page, page_size)
        base = base.offset(offset).limit(page_size)

        result = await self.session.execute(base)
        firs = list(result.unique().scalars().all())

        logger.info(
            "User %s listed FIRs (page=%d, total=%d)",
            user.email, page, total,
        )
        return {
            "items": firs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    # ─── Update FIR ─────────────────────────────────────────────

    async def update_fir(self, user: User, fir_id: int, data: dict) -> FIR:
        """Update an FIR's fields."""
        fir = await self._get_fir_or_404(fir_id)

        # Status transition validation
        if "investigation_status" in data and data["investigation_status"] is not None:
            new_status = InvestigationStatus(data["investigation_status"])
            valid_transitions = {
                InvestigationStatus.PENDING: [InvestigationStatus.UNDER_INVESTIGATION],
                InvestigationStatus.UNDER_INVESTIGATION: [InvestigationStatus.SOLVED, InvestigationStatus.CLOSED],
                InvestigationStatus.SOLVED: [InvestigationStatus.CLOSED],
                InvestigationStatus.CLOSED: [],
            }
            allowed = valid_transitions.get(fir.investigation_status, [])
            if new_status not in allowed:
                raise BadRequestException(
                    message=f"Cannot transition from {fir.investigation_status.value} to {new_status.value}",
                    error_code="INVALID_STATUS_TRANSITION",
                )
            data["investigation_status"] = new_status

        # Map old attribute names to current ones
        field_map = {
            "title": "title",
            "description": "description",
            "priority": "priority",
            "incident_date": "incident_date",
            "crime_category_id": "crime_type_id",
            "assigned_to_id": "officer_id",
            "investigation_status": "investigation_status",
            "status": "investigation_status",
        }

        updatable_fields = {"title", "description", "priority", "incident_date",
                            "crime_type_id", "officer_id", "investigation_status"}

        for key, value in data.items():
            mapped_key = field_map.get(key, key)
            if mapped_key in updatable_fields and value is not None:
                setattr(fir, mapped_key, value)

        await self.session.flush()
        await self.session.refresh(fir)
        logger.info("FIR %s updated by %s", fir.fir_number, user.email)
        return fir

    # ─── Delete FIR ─────────────────────────────────────────────

    async def delete_fir(self, user: User, fir_id: int) -> None:
        """Delete an FIR."""
        fir = await self._get_fir_or_404(fir_id)
        await self.session.delete(fir)
        await self.session.flush()
        logger.info("FIR %s deleted by %s", fir.fir_number, user.email)

    # ─── Assign Officer ─────────────────────────────────────────

    async def assign_officer(
        self, user: User, fir_id: int, officer_id: int
    ) -> FIR:
        """Assign or reassign an investigating officer to an FIR."""
        fir = await self._get_fir_or_404(fir_id)
        fir.officer_id = officer_id
        if fir.investigation_status == InvestigationStatus.PENDING:
            fir.investigation_status = InvestigationStatus.UNDER_INVESTIGATION
        await self.session.flush()
        await self.session.refresh(fir)
        logger.info(
            "Officer %s assigned to FIR %s by %s",
            officer_id, fir.fir_number, user.email,
        )
        return fir

    # ─── Statistics ──────────────────────────────────────────────

    async def get_statistics(self) -> dict:
        """Return FIR statistics for KPI cards - optimized with 3 grouped queries."""
        # Total count
        total_q = select(func.count(FIR.fir_id))
        total = (await self.session.execute(total_q)).scalar_one()

        # All status counts in one grouped query
        status_q = select(
            FIR.investigation_status, func.count(FIR.fir_id).label("cnt")
        ).group_by(FIR.investigation_status)
        status_rows = (await self.session.execute(status_q)).all()
        counts = {row.investigation_status.value if row.investigation_status else None: row.cnt for row in status_rows}

        # All priority counts in one grouped query
        priority_q = select(
            FIR.priority, func.count(FIR.fir_id).label("cnt")
        ).group_by(FIR.priority)
        pri_rows = (await self.session.execute(priority_q)).all()
        pri_counts = {row.priority.value if row.priority else None: row.cnt for row in pri_rows}

        return {
            "total_firs": total,
            "pending_count": counts.get("Pending", 0),
            "under_investigation_count": counts.get("Under Investigation", 0),
            "solved_count": counts.get("Solved", 0),
            "closed_count": counts.get("Closed", 0),
            "high_priority_count": pri_counts.get("High", 0),
            "critical_priority_count": pri_counts.get("Critical", 0),
        }

    # ─── FIR Summary ─────────────────────────────────────────────

    async def get_fir_summary(self, fir_id: int) -> dict:
        """Return FIR summary with joined names."""
        stmt = select(
            FIR.fir_id, FIR.fir_number, FIR.title,
            FIR.investigation_status, FIR.priority,
            FIR.incident_date, FIR.created_at,
            CrimeType.crime_name,
            Location.district,
            Officer.badge_number,
            Officer.designation,
        ).join(CrimeType, FIR.crime_type_id == CrimeType.crime_type_id, isouter=True
        ).join(Location, FIR.location_id == Location.location_id, isouter=True
        ).join(Officer, FIR.officer_id == Officer.officer_id, isouter=True
        ).where(FIR.fir_id == fir_id)

        result = await self.session.execute(stmt)
        row = result.one_or_none()
        if not row:
            raise NotFoundException(
                message=f"FIR #{fir_id} not found",
                error_code="FIR_NOT_FOUND",
            )
        from app.officer.models import Officer
        return {
            "fir_id": row.fir_id,
            "fir_number": row.fir_number,
            "title": row.title,
            "investigation_status": row.investigation_status.value if row.investigation_status else None,
            "priority": row.priority.value if row.priority else None,
            "incident_date": str(row.incident_date) if row.incident_date else None,
            "created_at": str(row.created_at) if row.created_at else None,
            "crime_type_name": row.crime_name,
            "district": row.district,
            "officer_name": f"{row.designation or ''} {row.badge_number or ''}".strip() or None,
        }

    # ─── FIR Timeline ────────────────────────────────────────────

    async def get_fir_timeline(self, fir_id: int) -> list[dict]:
        """Return timeline events for an FIR based on its lifecycle."""
        fir = await self._get_fir_or_404(fir_id)
        events = []
        events.append({
            "date": str(fir.created_at) if fir.created_at else None,
            "event": "FIR Registered",
            "description": f"FIR {fir.fir_number} was registered",
        })
        if fir.investigation_status in (InvestigationStatus.UNDER_INVESTIGATION,
                                         InvestigationStatus.SOLVED,
                                         InvestigationStatus.CLOSED):
            events.append({
                "date": str(fir.created_at) if fir.created_at else None,
                "event": "Investigation Started",
                "description": f"Investigation began for {fir.fir_number}",
            })
        if fir.investigation_status in (InvestigationStatus.SOLVED, InvestigationStatus.CLOSED):
            events.append({
                "date": str(fir.created_at) if fir.created_at else None,
                "event": "Case Solved",
                "description": f"{fir.fir_number} marked as solved",
            })
        if fir.investigation_status == InvestigationStatus.CLOSED:
            events.append({
                "date": str(fir.created_at) if fir.created_at else None,
                "event": "Case Closed",
                "description": f"{fir.fir_number} closed",
            })
        if fir.officer_id:
            from app.officer.models import Officer
            off = await self.session.get(Officer, fir.officer_id)
            if off:
                events.append({
                    "date": str(fir.created_at) if fir.created_at else None,
                    "event": "Officer Assigned",
                    "description": f"{off.designation or 'Officer'} {off.badge_number} assigned",
                })
        events.sort(key=lambda e: e["date"] or "", reverse=True)
        return events

    # ─── Reference Data for Dropdowns ────────────────────────────

    async def list_crime_types(self) -> list[CrimeType]:
        """List all crime types."""
        result = await self.session.execute(
            select(CrimeType).order_by(CrimeType.crime_name)
        )
        return list(result.scalars().all())

    async def list_locations(self) -> list[dict]:
        """List all locations (simplified for dropdowns)."""
        result = await self.session.execute(
            select(Location.location_id, Location.district, Location.city)
            .order_by(Location.district, Location.city)
        )
        rows = result.all()
        return [
            {"location_id": r.location_id, "district": r.district, "city": r.city}
            for r in rows
        ]

    async def list_officers(self) -> list[dict]:
        """List all officers (simplified for dropdowns)."""
        from app.officer.models import Officer
        result = await self.session.execute(
            select(Officer.officer_id, Officer.badge_number, Officer.designation, Officer.police_station)
            .order_by(Officer.badge_number)
        )
        rows = result.all()
        return [
            {
                "officer_id": r.officer_id,
                "badge_number": r.badge_number,
                "designation": r.designation,
                "police_station": r.police_station,
            }
            for r in rows
        ]
