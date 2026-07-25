"""Audit Log API endpoints for querying and managing audit logs."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit_log.schemas import (
    AuditLogFilterParams,
    AuditLogListResponse,
    AuditLogResponse,
    AuditLogStatsResponse,
)
from app.audit_log.services import AuditLogService
from app.dependencies import RoleChecker, get_current_user, get_db_session
from app.auth.models import User

router = APIRouter(prefix="/audit-logs", tags=["audit-logging"])


def get_audit_service(session: AsyncSession = Depends(get_db_session)) -> AuditLogService:
    return AuditLogService(session=session)


@router.get(
    "/",
    response_model=AuditLogListResponse,
    summary="List audit log entries with filtering and pagination",
    dependencies=[Depends(RoleChecker(1, 4))],  # Supervisor or Policy Maker
)
async def list_audit_logs(
    filters: AuditLogFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: AuditLogService = Depends(get_audit_service),
) -> AuditLogListResponse:
    """Retrieve paginated audit log entries with filtering.

    Restricted to supervisors and policy makers.
    """
    return await service.list_entries(
        user_id=filters.user_id,
        action=filters.action,
        table_name=filters.table_name,
        record_id=filters.record_id,
        date_from=filters.date_from,
        date_to=filters.date_to,
        search=filters.search,
        page=filters.page,
        page_size=filters.page_size,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )


@router.get(
    "/stats",
    response_model=AuditLogStatsResponse,
    summary="Get audit log statistics",
    dependencies=[Depends(RoleChecker(1, 4))],  # Supervisor or Policy Maker
)
async def get_audit_stats(
    current_user: User = Depends(get_current_user),
    service: AuditLogService = Depends(get_audit_service),
) -> AuditLogStatsResponse:
    """Get aggregate statistics about audit log entries.

    Includes total entries, unique users, actions breakdown,
    top endpoints, and activity by day (last 30 days).

    Restricted to supervisors and policy makers.
    """
    return await service.get_stats()


@router.get(
    "/{entry_id}",
    response_model=AuditLogResponse,
    summary="Get a single audit log entry",
    dependencies=[Depends(RoleChecker(1, 4))],  # Supervisor or Policy Maker
)
async def get_audit_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    service: AuditLogService = Depends(get_audit_service),
) -> AuditLogResponse:
    """Get a specific audit log entry by its ID.

    Restricted to supervisors and policy makers.
    """
    return await service.get_entry(entry_id)


@router.delete(
    "/purge",
    response_model=dict,
    summary="Purge audit logs older than specified days",
    dependencies=[Depends(RoleChecker(1))],  # Supervisor only
)
async def purge_audit_logs(
    days: int = Query(
        default=90,
        ge=1,
        le=365,
        description="Delete logs older than this many days (default: 90, max: 365)",
    ),
    current_user: User = Depends(get_current_user),
    service: AuditLogService = Depends(get_audit_service),
) -> dict:
    """Delete audit log entries older than the specified number of days.

    Restricted to supervisors. Use with caution as this operation
    permanently removes audit data.
    """
    deleted = await service.purge_older_than(days=days)
    return {
        "message": f"Purged {deleted} audit log entries older than {days} days",
        "deleted_count": deleted,
        "retention_days": days,
    }


@router.get(
    "/my-activity",
    response_model=AuditLogListResponse,
    summary="Get current user's audit activity",
)
async def get_my_activity(
    filters: AuditLogFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: AuditLogService = Depends(get_audit_service),
) -> AuditLogListResponse:
    """Retrieve audit log entries for the currently authenticated user.

    This endpoint is available to all authenticated users and
    automatically filters by their user ID.
    """
    return await service.list_entries(
        user_id=current_user.id,
        action=filters.action,
        table_name=filters.table_name,
        date_from=filters.date_from,
        date_to=filters.date_to,
        search=filters.search,
        page=filters.page,
        page_size=filters.page_size,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )
