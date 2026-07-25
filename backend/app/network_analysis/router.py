"""Criminal Network Analysis API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.models import Accused, FIRAccusedLink
from app.dependencies import get_current_user, get_db_session
from app.auth.models import User
from app.fir.models import FIR
from app.network_analysis.schemas import (
    CriminalNetworkDetail,
    GraphResponse,
    NetworkStatistics,
)
from app.network_analysis.services import NetworkAnalysisService

router = APIRouter(prefix="/network", tags=["criminal-network-analysis"])


def get_network_service(
    session: AsyncSession = Depends(get_db_session),
) -> NetworkAnalysisService:
    return NetworkAnalysisService(session=session)


@router.get(
    "",
    response_model=GraphResponse,
    summary="Build criminal network graph",
)
@router.get(
    "/",
    response_model=GraphResponse,
    summary="Build criminal network graph",
    include_in_schema=False,
)
async def get_network(
    fir_id: Optional[str] = Query(None, description="Scope graph to a single FIR ID or number"),
    current_user: User = Depends(get_current_user),
    service: NetworkAnalysisService = Depends(get_network_service),
) -> GraphResponse:
    """Build and return the criminal network graph.
    Returns nodes (Accused, Victim, FIR, Location, Crime type, Phone, Vehicle, Bank Account)
    and edges representing relationships. Includes co-accused and cross-FIR edges.
    Compatible with vis-network, Sigma.js, D3.js, and Cytoscape.js.
    """
    return await service.build_graph(fir_id=fir_id)


@router.get(
    "/summary",
    response_model=NetworkStatistics,
    summary="Criminal network summary statistics",
)
async def get_network_summary(
    current_user: User = Depends(get_current_user),
    service: NetworkAnalysisService = Depends(get_network_service),
) -> NetworkStatistics:
    """Return high-level criminal network statistics without the full graph."""
    graph = await service.build_graph()
    if graph.get("statistics"):
        return NetworkStatistics(**graph["statistics"])
    return NetworkStatistics(
        total_nodes=graph["total_nodes"],
        total_edges=graph["total_edges"],
    )


@router.get(
    "/criminal/{accused_id}",
    response_model=CriminalNetworkDetail,
    summary="Get subgraph focused on a single criminal",
)
async def get_criminal_network(
    accused_id: int,
    current_user: User = Depends(get_current_user),
    service: NetworkAnalysisService = Depends(get_network_service),
) -> CriminalNetworkDetail:
    """Return a subgraph focused on a single accused person and their connections."""
    r = await service.session.execute(
        select(Accused).where(Accused.accused_id == accused_id)
    )
    accused = r.scalar_one_or_none()
    if not accused:
        raise HTTPException(status_code=404, detail=f"Accused with ID {accused_id} not found")

    # Get their linked FIR IDs
    r = await service.session.execute(
        select(FIRAccusedLink.fir_id).where(FIRAccusedLink.accused_id == accused_id)
    )
    linked_fir_ids = [row[0] for row in r.all()]

    if not linked_fir_ids:
        return CriminalNetworkDetail(
            accused={
                "accused_id": accused.accused_id,
                "full_name": accused.full_name,
                "age": accused.age,
                "gender": accused.gender.value if accused.gender else None,
                "phone": accused.phone,
                "risk_score": float(accused.risk_score) if accused.risk_score else 0.0,
                "is_repeat_offender": bool(accused.is_repeat_offender) if accused.is_repeat_offender else False,
            },
            total_nodes=0,
            total_edges=0,
            co_accused_count=0,
            fir_count=0,
            total_crime_count=0,
        )

    # Get the FIRs
    r = await service.session.execute(
        select(FIR).where(FIR.fir_id.in_(linked_fir_ids))
    )
    firs = list(r.scalars().all())

    # Build subgraph from the first linked FIR to capture all relevant connections
    # Use the first FIR ID as scope; this captures co-accused + shared entities
    first_fir_id = str(linked_fir_ids[0])
    graph = await service.build_graph(fir_id=first_fir_id)

    # Count co-accused (other accused sharing same FIRs)
    r = await service.session.execute(
        select(FIRAccusedLink.accused_id).where(
            FIRAccusedLink.fir_id.in_(linked_fir_ids),
            FIRAccusedLink.accused_id != accused_id,
        )
    )
    co_accused_ids = list(set(r.scalars().all()))

    return CriminalNetworkDetail(
        accused={
            "accused_id": accused.accused_id,
            "full_name": accused.full_name,
            "age": accused.age,
            "gender": accused.gender.value if accused.gender else None,
            "phone": accused.phone,
            "risk_score": float(accused.risk_score) if accused.risk_score else 0.0,
            "is_repeat_offender": bool(accused.is_repeat_offender) if accused.is_repeat_offender else False,
        },
        nodes=graph["nodes"],
        edges=graph["edges"],
        total_nodes=graph["total_nodes"],
        total_edges=graph["total_edges"],
        co_accused_count=len(co_accused_ids),
        fir_count=len(firs),
        total_crime_count=len(firs),
    )
