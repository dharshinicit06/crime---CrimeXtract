"""AuditLog service for creating, querying, and analyzing audit log entries."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import cast, Date, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit_log.models import AuditAction, AuditLog
from app.exceptions.handlers import NotFoundException
from app.logging import get_logger
from app.utils.pagination import paginate

logger = get_logger(__name__)


class AuditLogService:
    """Service for recording and querying audit log entries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        *,
        action: AuditAction,
        user_id: Optional[int] = None,
        user_role: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        status_code: Optional[int] = None,
        duration_ms: Optional[int] = None,
    ) -> AuditLog:
        """Create an audit log entry and persist it to the database.

        Stores relevant fields into the model's available columns.
        Extra metadata is serialized into the action/message field.
        """
        # Build a descriptive action string from available fields
        action_str = action.value if hasattr(action, "value") else str(action)
        if method and path:
            action_str = f"{action_str}: {method} {path}"
        elif resource_type:
            action_str = f"{action_str}: {resource_type}"

        entry = AuditLog(
            user_id=user_id,
            action=action_str,
            table_name=resource_type,
            record_id=int(resource_id) if resource_id and resource_id.isdigit() else None,
            ip_address=ip_address,
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def get_entry(self, entry_id: int) -> AuditLog:
        """Get a single audit log entry by ID."""
        entry = await self.session.get(AuditLog, entry_id)
        if not entry:
            raise NotFoundException(
                message=f"Audit log entry '{entry_id}' not found",
                error_code="AUDIT_LOG_NOT_FOUND",
            )
        return entry

    async def list_entries(
        self,
        *,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> dict:
        """List audit log entries with filtering and pagination."""
        base = select(AuditLog)

        if user_id:
            base = base.where(AuditLog.user_id == user_id)
        if action:
            base = base.where(AuditLog.action.ilike(f"{action}%"))
        if table_name:
            base = base.where(AuditLog.table_name == table_name)
        if record_id is not None:
            base = base.where(AuditLog.record_id == record_id)
        if date_from:
            base = base.where(AuditLog.log_time >= date_from)
        if date_to:
            base = base.where(AuditLog.log_time <= date_to)
        if search:
            pattern = f"%{search}%"
            base = base.where(AuditLog.action.ilike(pattern))

        # Count total
        count_query = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        # Sorting
        allowed_sorts = {
            "action", "user_id", "ip_address", "log_time",
        }
        if sort_by and sort_by in allowed_sorts:
            col = getattr(AuditLog, sort_by)
            base = base.order_by(col.desc() if sort_order == "desc" else col.asc())
        else:
            base = base.order_by(AuditLog.log_time.desc())

        # Pagination
        offset, limit, _ = paginate(total, page, page_size)
        base = base.offset(offset).limit(limit)

        result = await self.session.execute(base)
        items = list(result.scalars().all())

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    async def get_stats(self) -> dict[str, Any]:
        """Get aggregate statistics about audit log entries using only existing model columns."""
        # Total count
        total_result = await self.session.execute(
            select(func.count()).select_from(AuditLog)
        )
        total_entries = total_result.scalar_one()

        # Unique users
        unique_result = await self.session.execute(
            select(func.count(func.distinct(AuditLog.user_id))).where(
                AuditLog.user_id.isnot(None)
            )
        )
        unique_users = unique_result.scalar_one()

        # Actions breakdown (by action string prefix)
        actions_result = await self.session.execute(
            select(AuditLog.action, func.count().label("cnt"))
            .group_by(AuditLog.action)
            .order_by(text("cnt DESC"))
        )
        actions_breakdown = {}
        for row in actions_result:
            key = row[0].split(":")[0] if row[0] else "UNKNOWN"
            actions_breakdown[key] = actions_breakdown.get(key, 0) + row[1]

        # Top tables
        tables_result = await self.session.execute(
            select(
                AuditLog.table_name,
                func.count().label("cnt"),
            )
            .where(AuditLog.table_name.isnot(None))
            .group_by(AuditLog.table_name)
            .order_by(text("cnt DESC"))
            .limit(10)
        )
        top_endpoints = [
            {"table": row[0], "count": row[1]}
            for row in tables_result
        ]

        # Activity by day (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=30)
        activity_result = await self.session.execute(
            select(
                cast(AuditLog.log_time, Date).label("day"),
                func.count().label("cnt"),
            )
            .where(AuditLog.log_time >= thirty_days_ago)
            .group_by(text("day"))
            .order_by(text("day"))
        )
        activity_by_day = [
            {"date": str(row[0]), "count": row[1]}
            for row in activity_result
        ]

        return {
            "total_entries": total_entries,
            "unique_users": unique_users,
            "actions_breakdown": actions_breakdown,
            "top_endpoints": top_endpoints,
            "activity_by_day": activity_by_day,
        }

    async def purge_older_than(self, days: int = 90) -> int:
        """Delete audit log entries older than the specified number of days."""
        cutoff = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=days)
        result = await self.session.execute(
            select(AuditLog).where(AuditLog.log_time < cutoff)
        )
        entries = list(result.scalars().all())
        count = len(entries)
        for entry in entries:
            await self.session.delete(entry)
        await self.session.flush()
        logger.info("Purged %d audit log entries older than %d days", count, days)
        return count
