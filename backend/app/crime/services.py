"""Crime type business logic with CRUD, filtering, search, and pagination."""

from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.crime.models import CrimeType, CrimeSeverity
from app.exceptions.handlers import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.logging import get_logger
from app.utils.pagination import paginate

logger = get_logger(__name__)


class CrimeService:
    """Handles crime type lifecycle: create, read, update, delete, search."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_crime_type_or_404(self, crime_type_id: str) -> CrimeType:
        crime_type = await self.session.get(CrimeType, crime_type_id)
        if not crime_type:
            raise NotFoundException(
                message=f"Crime type '{crime_type_id}' not found",
                error_code="CRIME_TYPE_NOT_FOUND",
            )
        return crime_type

    async def create_crime(self, user: User, data: dict) -> CrimeType:
        """Create a new crime type."""
        crime_type = CrimeType(
            crime_name=data["crime_name"],
            category=data.get("category"),
            severity=data.get("severity"),
            description=data.get("description"),
        )
        self.session.add(crime_type)
        await self.session.flush()
        await self.session.refresh(crime_type)
        logger.info("Crime type %s created by %s", crime_type.crime_name, user.email)
        return crime_type

    async def get_crime(self, crime_type_id: str) -> CrimeType:
        """Get a crime type by ID."""
        query = select(CrimeType).where(CrimeType.crime_type_id == crime_type_id)
        result = await self.session.execute(query)
        crime_type = result.unique().scalar_one_or_none()
        if not crime_type:
            raise NotFoundException(
                message=f"Crime type '{crime_type_id}' not found",
                error_code="CRIME_TYPE_NOT_FOUND",
            )
        return crime_type

    async def list_crimes(
        self,
        user: User,
        *,
        page: int = 1,
        page_size: int = 20,
        crime_status: Optional[CrimeSeverity] = None,
        crime_type_id: Optional[str] = None,
        district: Optional[str] = None,
        fir_id: Optional[str] = None,
        assigned_to_id: Optional[int] = None,
        reported_by_id: Optional[int] = None,
        search: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> dict:
        """List crime types with filtering by severity, category, name, and keyword search."""
        base = select(CrimeType)

        if crime_status:
            base = base.where(CrimeType.severity == crime_status)
        if crime_type_id:
            base = base.where(CrimeType.crime_type_id == crime_type_id)
        if district:
            base = base.where(CrimeType.category.ilike(f"%{district}%"))
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    CrimeType.crime_name.ilike(pattern),
                    CrimeType.description.ilike(pattern),
                )
            )
        if date_from:
            base = base.where(CrimeType.created_at >= date_from)
        if date_to:
            base = base.where(CrimeType.created_at <= date_to)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        allowed_sorts = {
            "crime_name", "category", "severity", "created_at",
        }
        if sort_by and sort_by in allowed_sorts:
            col = getattr(CrimeType, sort_by)
            base = base.order_by(
                col.desc() if sort_order == "desc" else col.asc()
            )
        else:
            base = base.order_by(CrimeType.crime_name.asc())

        offset, _, _ = paginate(total, page, page_size)
        base = base.offset(offset).limit(page_size)

        result = await self.session.execute(base)
        crime_types = list(result.unique().scalars().all())

        logger.info(
            "User %s listed crime types (page=%d, total=%d)",
            user.email, page, total,
        )
        return {
            "items": crime_types,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    async def update_crime(self, user: User, crime_type_id: str, data: dict) -> CrimeType:
        """Update a crime type's fields."""
        crime_type = await self._get_crime_type_or_404(crime_type_id)
        updatable = {
            "crime_name", "category", "severity", "description",
        }
        for key, value in data.items():
            if key in updatable and value is not None:
                setattr(crime_type, key, value)
        await self.session.flush()
        await self.session.refresh(crime_type)
        logger.info("Crime type %s updated by %s", crime_type.crime_name, user.email)
        return crime_type

    async def delete_crime(self, user: User, crime_type_id: str) -> None:
        """Delete a crime type."""
        crime_type = await self._get_crime_type_or_404(crime_type_id)
        await self.session.delete(crime_type)
        await self.session.flush()
        logger.info("Crime type %s deleted by %s", crime_type.crime_name, user.email)

    async def get_crime_stats(self) -> dict:
        """Get statistics about crime types grouped by severity and category."""
        total_q = select(func.count()).select_from(select(CrimeType).subquery())
        total = (await self.session.execute(total_q)).scalar_one()

        severity_q = select(
            CrimeType.severity, func.count()
        ).group_by(CrimeType.severity)
        result = await self.session.execute(severity_q)
        by_severity = {}
        for row in result.all():
            key = row[0].value if row[0] else "Unknown"
            by_severity[key] = row[1]

        category_q = select(
            CrimeType.category, func.count()
        ).group_by(CrimeType.category).order_by(func.count().desc()).limit(10)
        result = await self.session.execute(category_q)
        by_category = {row[0] or "Uncategorized": row[1] for row in result.all()}

        return {
            "total_crimes": total,
            "by_status": by_severity,
            "top_districts": by_category,
        }
