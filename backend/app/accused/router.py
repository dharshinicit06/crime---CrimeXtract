"""Accused API endpoints with RBAC, filtering, and FIR linking."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.schemas import (
    AccusedCreate,
    AccusedFilterParams,
    AccusedListResponse,
    AccusedResponse,
    AccusedUpdate,
    FIRAccusedLinkCreate,
    FIRAccusedLinkResponse,
)
from app.accused.services import AccusedService
from app.dependencies import (
    RoleChecker,
    get_current_user,
    get_db_session,
)
from app.auth.models import User

router = APIRouter(
    prefix="/accused",
    tags=["accused-management"],
)


def get_accused_service(
    session: AsyncSession = Depends(get_db_session),
) -> AccusedService:
    """Return accused service."""
    return AccusedService(session=session)


@router.post(
    "",
    response_model=AccusedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new accused record",
)
@router.post(
    "/",
    response_model=AccusedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new accused record",
    include_in_schema=False,
)
async def create_accused(
    request: AccusedCreate,
    current_user: User = Depends(get_current_user),
    service: AccusedService = Depends(get_accused_service),
) -> AccusedResponse:
    """Create an accused."""
    return await service.create_accused(data=request.model_dump())


@router.get(
    "",
    response_model=AccusedListResponse,
    summary="List accused with filtering and pagination",
)
@router.get(
    "/",
    response_model=AccusedListResponse,
    summary="List accused with filtering and pagination",
    include_in_schema=False,
)
async def list_accused(
    filters: AccusedFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: AccusedService = Depends(get_accused_service),
) -> AccusedListResponse:
    """List accused records."""
    return await service.list_accused(
    search=filters.search,
    fir_id=filters.fir_id,
    min_risk_score=filters.min_risk_score,
    max_risk_score=filters.max_risk_score,
    page=filters.page,
    page_size=filters.page_size,
    sort_by=filters.sort_by,
    sort_order=filters.sort_order,
)
        


@router.get(
    "/{accused_id}",
    response_model=AccusedResponse,
    summary="Get accused details",
)
async def get_accused(
    accused_id: int,
    current_user: User = Depends(get_current_user),
    service: AccusedService = Depends(get_accused_service),
) -> AccusedResponse:
    """Get accused details."""
    return await service.get_accused(accused_id)


@router.patch(
    "/{accused_id}",
    response_model=AccusedResponse,
    summary="Update accused details",
)
async def update_accused(
    accused_id: int,
    request: AccusedUpdate,
    current_user: User = Depends(get_current_user),
    service: AccusedService = Depends(get_accused_service),
) -> AccusedResponse:
    """Update accused."""
    return await service.update_accused(
        accused_id=accused_id,
        data=request.model_dump(exclude_unset=True),
    )


@router.delete(
    "/{accused_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an accused record",
    dependencies=[Depends(RoleChecker(1))],  # Supervisor/Admin
)
async def delete_accused(
    accused_id: int,
    current_user: User = Depends(get_current_user),
    service: AccusedService = Depends(get_accused_service),
) -> None:
    """Delete accused."""
    await service.delete_accused(accused_id)


@router.post(
    "/{accused_id}/firs",
    response_model=FIRAccusedLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link accused to an FIR",
)
async def link_to_fir(
    accused_id: int,
    request: FIRAccusedLinkCreate,
    current_user: User = Depends(get_current_user),
    service: AccusedService = Depends(get_accused_service),
) -> FIRAccusedLinkResponse:
    """Link accused with FIR."""
    return await service.link_to_fir(
        accused_id=accused_id,
        fir_id=request.fir_id,
    )


@router.get(
    "/{accused_id}/firs",
    response_model=list[FIRAccusedLinkResponse],
    summary="List FIRs linked to an accused",
)
async def list_fir_links(
    accused_id: int,
    current_user: User = Depends(get_current_user),
    service: AccusedService = Depends(get_accused_service),
) -> list[FIRAccusedLinkResponse]:
    """List FIR links."""
    return await service.list_fir_links(accused_id)


@router.delete(
    "/firs/{fir_id}/{accused_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink accused from an FIR",
    dependencies=[Depends(RoleChecker(1))],
)
async def unlink_from_fir(
    fir_id: int,
    accused_id: int,
    current_user: User = Depends(get_current_user),
    service: AccusedService = Depends(get_accused_service),
) -> None:
    await service.unlink_from_fir(
        fir_id=fir_id,
        accused_id=accused_id,
    )