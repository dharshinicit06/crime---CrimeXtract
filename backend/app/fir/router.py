"""FIR API endpoints with RBAC."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    RoleChecker,
    get_current_user,
    get_db_session,
)
from app.auth.models import User
from app.fir.schemas import (
    FIRCreate,
    FIRDetailResponse,
    FIRFilterParams,
    FIRListResponse,
    FIRStatistics,
    FIRUpdate,
)
from app.fir.services import FIRService
from app.crime.models import CrimeType
from app.crime.schemas import CrimeTypeResponse
from app.fir.models import InvestigationStatus

router = APIRouter(prefix="/firs", tags=["fir-management"])


def get_fir_service(
    session: AsyncSession = Depends(get_db_session),
) -> FIRService:
    return FIRService(session=session)


# ─── Static Reference Routes (MUST come BEFORE /{fir_id}) ─────────


@router.get(
    "/crime-types",
    response_model=list[CrimeTypeResponse],
    summary="List crime types",
)
async def list_crime_types(
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> list[CrimeTypeResponse]:
    """List all crime types."""
    return await service.list_crime_types()


@router.get(
    "/locations",
    response_model=list[dict],
    summary="List locations (district/city)",
)
async def list_locations(
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> list[dict]:
    """List locations."""
    return await service.list_locations()


@router.get(
    "/officers",
    response_model=list[dict],
    summary="List officers",
)
async def list_officers(
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> list[dict]:
    """List officers for assignment."""
    return await service.list_officers()


# ─── FIR CRUD ───────────────────────────────────────────────────


@router.post(
    "/",
    response_model=FIRDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new FIR",
)
async def create_fir(
    request: FIRCreate,
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> FIRDetailResponse:
    """Create a new FIR."""
    fir = await service.create_fir(
        user=current_user,
        data=request.model_dump(),
    )
    return await service.get_fir(fir.fir_id)


@router.get(
    "/",
    response_model=FIRListResponse,
    summary="List FIRs with filtering and pagination",
)
async def list_firs(
    filters: FIRFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> FIRListResponse:
    """List FIRs with search, status/priority filters, and pagination."""
    return await service.list_firs(
        user=current_user,
        page=filters.page,
        page_size=filters.page_size,
        status=filters.status,
        priority=filters.priority,
        search=filters.search,
        date_from=filters.date_from,
        date_to=filters.date_to,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )


@router.get(
    "/statistics",
    response_model=FIRStatistics,
    summary="Get FIR statistics",
)
async def get_fir_statistics(
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> FIRStatistics:
    """Return FIR statistics for KPI cards."""
    return await service.get_statistics()


# ─── Dynamic FIR Routes ─────────────────────────────────────────


@router.get(
    "/{fir_id}",
    response_model=FIRDetailResponse,
    summary="Get FIR details",
)
async def get_fir(
    fir_id: int,
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> FIRDetailResponse:
    """Get full FIR details."""
    return await service.get_fir(fir_id)


@router.patch(
    "/{fir_id}",
    response_model=FIRDetailResponse,
    summary="Update FIR fields",
)
async def update_fir(
    fir_id: int,
    request: FIRUpdate,
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> FIRDetailResponse:
    """Update FIR fields."""
    await service.update_fir(
        user=current_user,
        fir_id=fir_id,
        data=request.model_dump(exclude_unset=True),
    )
    return await service.get_fir(fir_id)


@router.delete(
    "/{fir_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an FIR",
)
async def delete_fir(
    fir_id: int,
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> None:
    """Delete an FIR."""
    await service.delete_fir(user=current_user, fir_id=fir_id)


# ─── Assign Officer ─────────────────────────────────────────────


@router.post(
    "/{fir_id}/assign",
    response_model=FIRDetailResponse,
    summary="Assign investigating officer",
)
async def assign_officer(
    fir_id: int,
    officer_id: int,
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> FIRDetailResponse:
    """Assign an investigating officer to an FIR."""
    await service.assign_officer(
        user=current_user, fir_id=fir_id, officer_id=officer_id
    )
    return await service.get_fir(fir_id)


# ─── Status Transitions ─────────────────────────────────────────


@router.post(
    "/{fir_id}/status",
    response_model=FIRDetailResponse,
    summary="Update FIR investigation status",
)
async def update_fir_status(
    fir_id: int,
    status: InvestigationStatus,
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> FIRDetailResponse:
    """Update the investigation status of an FIR."""
    await service.update_fir(
        user=current_user,
        fir_id=fir_id,
        data={"investigation_status": status},
    )
    return await service.get_fir(fir_id)


# ─── FIR Summary ────────────────────────────────────────────────


@router.get(
    "/{fir_id}/summary",
    summary="Get FIR summary with context",
)
async def get_fir_summary(
    fir_id: int,
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> dict:
    """Return a summary of the FIR including crime type name, district, and officer name."""
    return await service.get_fir_summary(fir_id)


# ─── FIR Timeline ───────────────────────────────────────────────


@router.get(
    "/{fir_id}/timeline",
    summary="Get FIR investigation timeline",
)
async def get_fir_timeline(
    fir_id: int,
    current_user: User = Depends(get_current_user),
    service: FIRService = Depends(get_fir_service),
) -> list[dict]:
    """Return timeline of events for an FIR."""
    return await service.get_fir_timeline(fir_id)
