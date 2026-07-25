"""Helper script to create network analysis module files."""
import os

os.makedirs("app/network_analysis", exist_ok=True)

# services.py
svc = r'''"""Criminal Network Analysis service — builds graph JSON from entity relationships."""

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.models import Accused, FIRAccusedLink
from app.crime.models import Crime
from app.fir.models import FIR
from app.financial_transaction.models import FinancialTransaction
from app.location.models import Location
from app.victim.models import Victim
from app.logging import get_logger

logger = get_logger(__name__)


class NetworkAnalysisService:
    """Builds a graph of criminal relationships from all entity tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, Any]] = []
        self._edge_counter = 0

    def _add_node(
        self, node_id: str, label: str, node_type: str,
        group: str | None = None, metadata: dict | None = None,
    ) -> None:
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": node_type,
                "group": group or node_type,
                "metadata": metadata or {},
            }

    def _add_edge(
        self, source: str, target: str, label: str,
        weight: float = 1.0, metadata: dict | None = None,
    ) -> None:
        self._edge_counter += 1
        self.edges.append({
            "id": f"e{self._edge_counter}",
            "source": source,
            "target": target,
            "label": label,
            "weight": weight,
            "metadata": metadata or {},
        })

    def _extract_phones(self, text_val: str | None) -> list[str]:
        """Extract Indian phone numbers from text."""
        if not text_val:
            return []
        pattern = r'\b[6789]\d{9}\b'
        return list(set(re.findall(pattern, text_val)))

    async def build_graph(self, fir_id: str | None = None) -> dict[str, Any]:
        """Build the full criminal network graph.

        Args:
            fir_id: Optional FIR ID to scope the graph to a single case.
                     If None, builds graph from all data.
        """
        self.nodes = {}
        self.edges = []
        self._edge_counter = 0

        # --- 1. Load FIRs (central hub entities) ---
        fir_query = select(FIR)
        if fir_id:
            fir_query = fir_query.where(FIR.id == fir_id)
        r = await self.session.execute(fir_query)
        firs = list(r.scalars().all())

        for fir in firs:
            self._add_node(
                node_id=f"fir:{fir.id}",
                label=f"FIR {fir.fir_number}",
                node_type="fir",
                group="case",
                metadata={
                    "fir_number": fir.fir_number,
                    "status": fir.status.value if hasattr(fir.status, 'value') else str(fir.status),
                    "title": fir.title,
                },
            )

        if not firs:
            return self._graph_response("No FIRs found")

        fir_ids = [f.id for f in firs]

        # --- 2. Load Victims & link to FIRs ---
        r = await self.session.execute(
            select(Victim).where(Victim.fir_id.in_(fir_ids))
        )
        victims = list(r.scalars().all())
        for v in victims:
            nid = f"victim:{v.id}"
            self._add_node(
                nid, v.name, "victim", "person",
                {"age": v.age, "gender": v.gender, "contact": v.contact},
            )
            self._add_edge(f"fir:{v.fir_id}", nid, "has_victim")

            phones = self._extract_phones(v.contact) + self._extract_phones(v.address)
            for phone in phones:
                pid = f"phone:{phone}"
                self._add_node(pid, phone, "phone", "contact", {"source": f"victim:{v.id}"})
                self._add_edge(nid, pid, "has_phone")

        # --- 3. Load Accused & link to FIRs ---
        r = await self.session.execute(
            select(FIRAccusedLink).where(FIRAccusedLink.fir_id.in_(fir_ids))
        )
        links = list(r.scalars().all())
        link_accused_ids = list(set(l.accused_id for l in links))

        if link_accused_ids:
            r = await self.session.execute(
                select(Accused).where(Accused.id.in_(link_accused_ids))
            )
            accused_map = {a.id: a for a in r.scalars().all()}

            for link in links:
                accused = accused_map.get(link.accused_id)
                if not accused:
                    continue
                nid = f"accused:{accused.id}"
                self._add_node(
                    nid, accused.name, "accused", "person",
                    {"alias": accused.alias, "risk_score": accused.risk_score,
                     "gang_links": accused.gang_links},
                )
                self._add_edge(
                    f"fir:{link.fir_id}", nid, "has_accused",
                    metadata={"role": link.role},
                )

        # --- 4. Load Locations & link to FIRs ---
        loc_ids = [f.location_id for f in firs if f.location_id]
        if loc_ids:
            r = await self.session.execute(
                select(Location).where(Location.id.in_(loc_ids))
            )
            loc_map = {loc.id: loc for loc in r.scalars().all()}

            for fir in firs:
                if fir.location_id and fir.location_id in loc_map:
                    loc = loc_map[fir.location_id]
                    nid = f"location:{loc.id}"
                    label = f"{loc.district or loc.city}, {loc.state}"
                    self._add_node(
                        nid, label, "location", "place",
                        {"city": loc.city, "district": loc.district, "state": loc.state},
                    )
                    self._add_edge(f"fir:{fir.id}", nid, "occurred_at")

        # --- 5. Load Crimes & link to FIRs ---
        r = await self.session.execute(
            select(Crime).where(Crime.fir_id.in_(fir_ids))
        )
        crimes = list(r.scalars().all())
        for c in crimes:
            nid = f"crime:{c.id}"
            self._add_node(
                nid, f"{c.crime_number}: {c.title}", "crime", "incident",
                {"district": c.district,
                 "status": c.crime_status.value if hasattr(c.crime_status, 'value') else str(c.crime_status)},
            )
            self._add_edge(f"fir:{c.fir_id}", nid, "involves_crime")

        # --- 6. Load Financial Transactions (Bank Accounts) ---
        r = await self.session.execute(
            select(FinancialTransaction).where(FinancialTransaction.fir_id.in_(fir_ids))
        )
        txs = list(r.scalars().all())
        for tx in txs:
            sid = f"bank_account:{tx.id}:sender"
            self._add_node(
                sid, tx.sender, "bank_account", "financial",
                {"bank": tx.bank, "amount": tx.amount, "type": "sender"},
            )
            self._add_edge(f"fir:{tx.fir_id}", sid, "sender_is")

            rid = f"bank_account:{tx.id}:receiver"
            self._add_node(
                rid, tx.receiver, "bank_account", "financial",
                {"bank": tx.bank, "amount": tx.amount, "type": "receiver"},
            )
            self._add_edge(f"fir:{tx.fir_id}", rid, "receiver_is")

            weight = min(tx.amount / 10000, 10.0) if tx.amount else 1.0
            self._add_edge(
                sid, rid, "transferred_to",
                weight=weight,
                metadata={"amount": tx.amount, "date": str(tx.transaction_date)},
            )

        logger.info(
            "Network graph built: %d nodes, %d edges (filter=%s)",
            len(self.nodes), len(self.edges), fir_id or "all",
        )
        return self._graph_response()

    def _graph_response(self, message: str | None = None) -> dict[str, Any]:
        resp = {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
        }
        if message:
            resp["metadata"] = {"message": message}
        return resp
'''

with open("app/network_analysis/services.py", "w") as f:
    f.write(svc)

# router.py
rt = r'''"""Criminal Network Analysis API endpoint — returns graph JSON."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_db_session
from app.auth.models import User
from app.network_analysis.schemas import GraphResponse
from app.network_analysis.services import NetworkAnalysisService

router = APIRouter(prefix="/network", tags=["criminal-network-analysis"])


def get_network_service(
    session: AsyncSession = Depends(get_db_session),
) -> NetworkAnalysisService:
    return NetworkAnalysisService(session=session)


@router.get(
    "/",
    response_model=GraphResponse,
    summary="Build criminal network graph",
)
async def get_network(
    fir_id: Optional[str] = Query(None, description="Scope graph to a single FIR ID"),
    current_user: User = Depends(get_current_user),
    service: NetworkAnalysisService = Depends(get_network_service),
) -> GraphResponse:
    """Build and return the criminal network graph.

    Returns nodes (Accused, Victim, Phone, Crime, Location, Bank Account)
    and edges representing their relationships. Optionally scoped to an FIR.
    Compatible with Sigma.js, D3.js, and Cytoscape.js.
    """
    return await service.build_graph(fir_id=fir_id)
'''

with open("app/network_analysis/router.py", "w") as f:
    f.write(rt)

print("Both services.py and router.py created OK")
