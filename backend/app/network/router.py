"""Criminal Network Graph API — returns graph JSON for a given FIR number."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.auth.models import User
from app.network.graph_service import GraphBuilder
from app.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/network", tags=["criminal-network-graph"])


@router.get("/{fir_number}", summary="Build criminal network graph for an FIR")
async def get_network_graph(
    fir_number: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Build and return a criminal network graph for a given FIR number.

    Returns nodes (FIR, Accused, Victim, Evidence, Location, Transaction)
    and edges (INVOLVED_IN, VICTIM_OF, EVIDENCE_FOR, OCCURRED_AT, MONEY_TRANSFER).
    Compatible with React Flow, Cytoscape.js, and vis-network.
    """
    builder = GraphBuilder(session)
    result = await builder.build_graph(fir_number)

    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    return result
