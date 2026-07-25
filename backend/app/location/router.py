"""Location API endpoints with role-based access control.

Permissions:
  - Admin (role_id=1): Full CRUD
  - Investigator (role_id=2): View + Create
  - Analyst (role_id=3): Read only
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import RoleChecker, get_current_user, get_db_session
from app.auth.models import User
from app.location.schemas import (
    LocationCreate, LocationFilterParams, LocationListResponse,
    LocationResponse, LocationUpdate, LocationUsageResponse,
    LocationStatisticsResponse,
)
from app.location.services import LocationService

router = APIRouter(prefix="/locations", tags=["location-management"])


def get_location_service(session: AsyncSession = Depends(get_db_session)) -> LocationService:
    return LocationService(session=session)


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED, summary="Create a new location",
    dependencies=[Depends(RoleChecker(1, 2))])
async def create_location(
    request: LocationCreate,
    current_user: User = Depends(get_current_user),
    service: LocationService = Depends(get_location_service),
) -> LocationResponse:
    """Create a new location. Admin or Investigator only."""
    return await service.create_location(data=request.model_dump())


@router.get("/", response_model=LocationListResponse, summary="List locations with filtering and pagination")
async def list_locations(
    filters: LocationFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: LocationService = Depends(get_location_service),
) -> LocationListResponse:
    """List locations with filters and search. Any authenticated user."""
    return await service.list_locations(
        city=filters.city,
        district=filters.district,
        area=filters.area,
        search=filters.search,
        pincode=filters.pincode,
        page=filters.page,
        page_size=filters.page_size,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )


@router.get("/statistics", response_model=LocationStatisticsResponse, summary="Get location statistics")
async def location_statistics(
    current_user: User = Depends(get_current_user),
    service: LocationService = Depends(get_location_service),
) -> LocationStatisticsResponse:
    """Return aggregate location statistics: total, by district, by city, newest."""
    return await service.get_statistics()


@router.get("/{location_id}", response_model=LocationResponse, summary="Get location details")
async def get_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    service: LocationService = Depends(get_location_service),
) -> LocationResponse:
    """Get a location by ID. Any authenticated user."""
    return await service.get_location(location_id)


@router.patch("/{location_id}", response_model=LocationResponse, summary="Update location details",
    dependencies=[Depends(RoleChecker(1, 2))])
async def update_location(
    location_id: int,
    request: LocationUpdate,
    current_user: User = Depends(get_current_user),
    service: LocationService = Depends(get_location_service),
) -> LocationResponse:
    """Update a location. Admin or Investigator only."""
    return await service.update_location(location_id=location_id, data=request.model_dump(exclude_unset=True))


@router.get("/{location_id}/usage", response_model=LocationUsageResponse, summary="Get location usage counts")
async def location_usage(
    location_id: int,
    current_user: User = Depends(get_current_user),
    service: LocationService = Depends(get_location_service),
) -> LocationUsageResponse:
    """Return usage counts for a location: FIRs, evidence, accused, victims."""
    return await service.get_location_usage(location_id=location_id)


@router.delete("/{location_id}", response_model=dict, summary="Delete a location",
    dependencies=[Depends(RoleChecker(1))])
async def delete_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    service: LocationService = Depends(get_location_service),
) -> dict:
    """Delete a location. Admin only. Checks FIR references first."""
    await service.delete_location(location_id=location_id)
    return {"message": "Location deleted successfully", "location_id": location_id}
