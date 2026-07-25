"""Crime incident API endpoints with RBAC, filtering, and pagination."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    RoleChecker,
    get_current_user,
    get_db_session,
)
from app.auth.models import User
from app.crime.schemas import (
    CrimeCreate,
    CrimeFilterParams,
    CrimeListResponse,
    CrimeResponse,
    CrimeUpdate,
)
from app.crime.services import CrimeService

router = APIRouter(prefix="/crimes", tags=["crime-management"])


def get_crime_service(
    session: AsyncSession = Depends(get_db_session),
) -> CrimeService:
    return CrimeService(session=session)


@router.post(
    "/",
    response_model=CrimeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new crime incident record",
)
async def create_crime(
    request: CrimeCreate,
    current_user: User = Depends(get_current_user),
    service: CrimeService = Depends(get_crime_service),
) -> CrimeResponse:
    """Create a new crime incident record with type, status, date, district, and optional FIR link."""
    crime = await service.create_crime(
        user=current_user,
        data=request.model_dump(),
    )
    return await service.get_crime(crime.id)


@router.get(
    "/",
    response_model=CrimeListResponse,
    summary="List crime records with filtering, search, and pagination",
)
async def list_crimes(
    filters: CrimeFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: CrimeService = Depends(get_crime_service),
) -> CrimeListResponse:
    """List crime records filtered by status, type, date range, district, FIR link, and keyword search."""
    return await service.list_crimes(
        user=current_user,
        page=filters.page,
        page_size=filters.page_size,
        crime_status=filters.crime_status,
        crime_type_id=filters.crime_type_id,
        district=filters.district,
        fir_id=filters.fir_id,
        assigned_to_id=filters.assigned_to_id,
        reported_by_id=filters.reported_by_id,
        search=filters.search,
        date_from=filters.date_from,
        date_to=filters.date_to,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )


@router.get(
    "/stats",
    response_model=dict,
    summary="Get crime statistics",
)
async def get_crime_stats(
    current_user: User = Depends(get_current_user),
    service: CrimeService = Depends(get_crime_service),
) -> dict:
    """Get aggregate statistics: total crimes, count by status, top districts."""
    return await service.get_crime_stats()


@router.get(
    "/{crime_id}",
    response_model=CrimeResponse,
    summary="Get crime record details",
)
async def get_crime(
    crime_id: str,
    current_user: User = Depends(get_current_user),
    service: CrimeService = Depends(get_crime_service),
) -> CrimeResponse:
    """Get full crime record details with crime type, FIR, and assigned user info."""
    return await service.get_crime(crime_id)


@router.patch(
    "/{crime_id}",
    response_model=CrimeResponse,
    summary="Update crime record",
    dependencies=[Depends(RoleChecker(1, 2, 3))],  # Supervisor, Crime Analyst, Investigator
)
async def update_crime(
    crime_id: str,
    request: CrimeUpdate,
    current_user: User = Depends(get_current_user),
    service: CrimeService = Depends(get_crime_service),
) -> CrimeResponse:
    """Update a crime record's fields. Restricted to authorized roles."""
    await service.update_crime(
        user=current_user,
        crime_id=crime_id,
        data=request.model_dump(exclude_unset=True),
    )
    return await service.get_crime(crime_id)


@router.delete(
    "/{crime_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a crime record",
    dependencies=[Depends(RoleChecker(1))],  # Supervisor only
)
async def delete_crime(
    crime_id: str,
    current_user: User = Depends(get_current_user),
    service: CrimeService = Depends(get_crime_service),
) -> None:
    """Delete a crime record. Restricted to supervisors."""
    await service.delete_crime(user=current_user, crime_id=crime_id)
