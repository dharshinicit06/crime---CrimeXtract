"""Pydantic schemas for Location CRUD operations - matching actual MySQL locations table."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginationParams


class LocationCreate(BaseModel):
    """Payload for creating a new location record."""
    district: str = Field(..., max_length=100, description="District name")
    city: str = Field(..., max_length=100, description="City name")
    area: str = Field(..., max_length=150, description="Area/locality name")
    pincode: Optional[str] = Field(None, max_length=10, description="Postal code")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude (-180 to 180)")


class LocationUpdate(BaseModel):
    """Payload for updating a location record."""
    district: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    area: Optional[str] = Field(None, max_length=150)
    pincode: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class LocationFilterParams(PaginationParams):
    """Query parameters for filtering location records."""
    district: Optional[str] = Field(None, description="Filter by district")
    city: Optional[str] = Field(None, description="Filter by city")
    area: Optional[str] = Field(None, description="Filter by area")
    search: Optional[str] = Field(None, description="Search by district, city, or area")
    pincode: Optional[str] = Field(None, description="Filter by pincode")


class LocationResponse(BaseModel):
    """Full location record response matching the actual locations table."""
    location_id: int
    district: str
    city: str
    area: str
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LocationListResponse(BaseModel):
    """Paginated location list response."""
    items: list[LocationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LocationUsageResponse(BaseModel):
    """Usage counts for a location across modules."""
    location_id: int
    fir_count: int = 0
    evidence_count: int = 0
    accused_count: int = 0
    victim_count: int = 0


class DistrictStat(BaseModel):
    district: str
    count: int


class CityStat(BaseModel):
    city: str
    count: int


class NewestLocation(BaseModel):
    location_id: int
    district: str
    city: str
    area: str
    created_at: Optional[str] = None


class LocationStatisticsResponse(BaseModel):
    """Aggregate location statistics."""
    total_locations: int = 0
    unique_districts: int = 0
    unique_cities: int = 0
    by_district: list[DistrictStat] = []
    by_city: list[CityStat] = []
    newest: list[NewestLocation] = []
