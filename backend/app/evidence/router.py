"""Evidence API endpoints with RBAC, filtering, and pagination."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    RoleChecker,
    get_current_user,
    get_db_session,
)
from app.auth.models import User
from app.evidence.schemas import (
    EvidenceCreate,
    EvidenceFilterParams,
    EvidenceListResponse,
    EvidenceResponse,
    EvidenceUpdate,
)
from app.evidence.services import EvidenceService

router = APIRouter(
    prefix="/evidence",
    tags=["evidence-management"],
)


def get_evidence_service(
    session: AsyncSession = Depends(get_db_session),
) -> EvidenceService:
    """Return EvidenceService instance."""
    return EvidenceService(session=session)


@router.post(
    "/",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new evidence record",
)
async def create_evidence(
    fir_id: int,
    request: EvidenceCreate,
    current_user: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceResponse:
    """Create a new evidence record."""
    return await service.create_evidence(
        fir_id=str(fir_id),
        collected_by_id=current_user.id,
        data=request.model_dump(),
    )


@router.get(
    "/",
    response_model=EvidenceListResponse,
    summary="List evidence with filtering and pagination",
)
async def list_evidence(
    filters: EvidenceFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceListResponse:
    """List evidence records."""
    return await service.list_evidence(
        fir_id=filters.fir_id,
        evidence_type=filters.evidence_type,
        search=filters.search,
        page=filters.page,
        page_size=filters.page_size,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )


@router.get(
    "/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Get evidence details",
)
async def get_evidence(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceResponse:
    """Get an evidence record."""
    return await service.get_evidence(evidence_id)


@router.patch(
    "/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Update evidence details",
)
async def update_evidence(
    evidence_id: int,
    request: EvidenceUpdate,
    current_user: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceResponse:
    """Update an evidence record."""
    return await service.update_evidence(
        evidence_id=evidence_id,
        data=request.model_dump(exclude_unset=True),
    )


@router.delete(
    "/{evidence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an evidence record",
    dependencies=[Depends(RoleChecker(1))],
)
async def delete_evidence(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> None:
    """Delete an evidence record."""
    await service.delete_evidence(evidence_id=evidence_id)