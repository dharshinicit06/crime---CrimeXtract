"""Victim API endpoints with RBAC, filtering, and pagination."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import RoleChecker, get_current_user, get_db_session
from app.auth.models import User
from app.victim.schemas import VictimCreate, VictimFilterParams, VictimListResponse, VictimResponse, VictimUpdate
from app.victim.services import VictimService

router = APIRouter(prefix="/victims", tags=["victim-management"])


def get_victim_service(session: AsyncSession = Depends(get_db_session)) -> VictimService:
    return VictimService(session=session)


@router.post("", response_model=VictimResponse, status_code=status.HTTP_201_CREATED, summary="Create a new victim record")
@router.post("/", response_model=VictimResponse, status_code=status.HTTP_201_CREATED, summary="Create a new victim record", include_in_schema=False)
async def create_victim(
    request: VictimCreate,
    fir_id: Optional[int] = Query(None, description="FIR ID to link this victim to (optional)"),
    current_user: User = Depends(get_current_user),
    service: VictimService = Depends(get_victim_service),
) -> VictimResponse:
    """Create a new victim.
    If fir_id is provided, the victim is also linked to that FIR via the junction table.
    Multiple victims per FIR are supported.
    """
    return await service.create_victim(fir_id=str(fir_id) if fir_id else None, data=request.model_dump())


@router.get("", response_model=VictimListResponse, summary="List victims with filtering and pagination")
@router.get("/", response_model=VictimListResponse, summary="List victims with filtering and pagination", include_in_schema=False)
async def list_victims(filters: VictimFilterParams = Depends(), current_user: User = Depends(get_current_user), service: VictimService = Depends(get_victim_service)) -> VictimListResponse:
    """List victims filtered by FIR ID and/or keyword search."""
    return await service.list_victims(fir_id=filters.fir_id, search=filters.search, page=filters.page, page_size=filters.page_size, sort_by=filters.sort_by, sort_order=filters.sort_order)


@router.get("/{victim_id}", response_model=VictimResponse, summary="Get victim details")
async def get_victim(victim_id: int, current_user: User = Depends(get_current_user), service: VictimService = Depends(get_victim_service)) -> VictimResponse:
    """Get a victim record by ID."""
    return await service.get_victim(victim_id)


@router.patch("/{victim_id}", response_model=VictimResponse, summary="Update victim details")
async def update_victim(victim_id: int, request: VictimUpdate, current_user: User = Depends(get_current_user), service: VictimService = Depends(get_victim_service)) -> VictimResponse:
    """Update a victim record's fields."""
    return await service.update_victim(victim_id=victim_id, data=request.model_dump(exclude_unset=True))


@router.delete("/{victim_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a victim record",    dependencies=[Depends(RoleChecker(1))]  # Supervisor only)
)
async def delete_victim(victim_id: int, current_user: User = Depends(get_current_user), service: VictimService = Depends(get_victim_service)) -> None:
    """Delete a victim record. Restricted to supervisors."""
    await service.delete_victim(victim_id=victim_id)
