"""Crime History API endpoints with RBAC, filtering, and repeat-offender queries."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    RoleChecker,
    get_current_user,
    get_db_session,
)
from app.auth.models import User
from app.crime_history.schemas import (
    CrimeHistoryCreate,
    CrimeHistoryFilterParams,
    CrimeHistoryListResponse,
    CrimeHistoryResponse,
    CrimeHistoryUpdate,
)
from app.crime_history.services import CrimeHistoryService

router = APIRouter(
    prefix="/crime-history",
    tags=["crime-history"],
)


def get_service(
    session: AsyncSession = Depends(get_db_session),
) -> CrimeHistoryService:
    """Return CrimeHistoryService instance."""
    return CrimeHistoryService(session=session)


@router.post(
    "/",
    response_model=CrimeHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a crime history record",
)
async def create(
    request: CrimeHistoryCreate,
    current_user: User = Depends(get_current_user),
    service: CrimeHistoryService = Depends(get_service),
) -> CrimeHistoryResponse:
    """Create a crime history record."""
    return await service.create(data=request.model_dump())


@router.get(
    "/",
    response_model=CrimeHistoryListResponse,
    summary="List crime history records",
)
async def list_history(
    filters: CrimeHistoryFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: CrimeHistoryService = Depends(get_service),
) -> CrimeHistoryListResponse:
    """List crime history records with filtering."""
    return await service.list(
        accused_id=filters.accused_id,
        fir_id=filters.fir_id,
        disposition=filters.disposition,
        offense_type=filters.offense_type,
        search=filters.search,
        date_from=filters.date_from,
        date_to=filters.date_to,
        page=filters.page,
        page_size=filters.page_size,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )


@router.get(
    "/repeat-offenders",
    response_model=dict,
    summary="Identify repeat offenders",
)
async def get_repeat_offenders(
    min_offenses: int = Query(
        default=2,
        ge=2,
        description="Minimum number of offenses",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: CrimeHistoryService = Depends(get_service),
) -> dict:
    """Return repeat offenders."""
    return await service.get_repeat_offenders(
        min_offenses=min_offenses,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{history_id}",
    response_model=CrimeHistoryResponse,
    summary="Get crime history details",
)
async def get_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    service: CrimeHistoryService = Depends(get_service),
) -> CrimeHistoryResponse:
    """Get a crime history record."""
    return await service.get(history_id)


@router.patch(
    "/{history_id}",
    response_model=CrimeHistoryResponse,
    summary="Update crime history record",
)
async def update_history(
    history_id: int,
    request: CrimeHistoryUpdate,
    current_user: User = Depends(get_current_user),
    service: CrimeHistoryService = Depends(get_service),
) -> CrimeHistoryResponse:
    """Update a crime history record."""
    return await service.update(
        history_id=history_id,
        data=request.model_dump(exclude_unset=True),
    )


@router.delete(
    "/{history_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete crime history record",
    dependencies=[Depends(RoleChecker(1))],
)
async def delete_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    service: CrimeHistoryService = Depends(get_service),
) -> None:
    """Delete a crime history record."""
    await service.delete(history_id=history_id)