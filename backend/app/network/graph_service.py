"""Graph Service — builds criminal relationship graph from MySQL data.

Creates a graph JSON for the interactive network visualization with:
  Node types: FIR, Accused, Victim, Evidence, Location, Transaction
  Edge types: INVOLVED_IN, VICTIM_OF, EVIDENCE_FOR, OCCURRED_AT, MONEY_TRANSFER
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.models import Accused, FIRAccusedLink
from app.evidence.models import Evidence
from app.financial_transaction.models import FinancialTransaction
from app.fir.models import FIR
from app.location.models import Location
from app.victim.models import FIRVictimLink, Victim
from app.logging import get_logger

logger = get_logger(__name__)


class GraphBuilder:
    """Builds a criminal network graph from MySQL relationships."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.nodes: list[dict[str, Any]] = []
        self.edges: list[dict[str, Any]] = []
        self._node_ids: set[str] = set()
        self._edge_key: set[tuple[str, str, str]] = set()

    def _add_node(self, node_id: str, label: str, node_type: str,
                   metadata: dict | None = None) -> None:
        if node_id not in self._node_ids:
            self._node_ids.add(node_id)
            self.nodes.append({
                "id": node_id,
                "label": label,
                "type": node_type,
                "metadata": metadata or {},
            })

    def _add_edge(self, source: str, target: str, label: str) -> None:
        key = (source, target, label)
        if key not in self._edge_key:
            self._edge_key.add(key)
            self.edges.append({
                "source": source,
                "target": target,
                "label": label,
            })

    async def build_graph(self, fir_number: str) -> dict[str, Any]:
        """Build graph for a single FIR by its FIR number."""
        self.nodes = []
        self.edges = []
        self._node_ids.clear()
        self._edge_key.clear()

        # ── 1. Lookup FIR by number ────────────────────────────
        q = select(FIR).where(FIR.fir_number == fir_number)
        r = await self.session.execute(q)
        fir = r.scalar_one_or_none()

        if not fir:
            return {"nodes": [], "edges": [], "error": f"FIR {fir_number} not found"}

        fir_id = fir.fir_id
        fir_nid = f"fir:{fir_id}"

        self._add_node(
            fir_nid, fir_number, "FIR",
            {"status": fir.investigation_status.value if hasattr(fir.investigation_status, 'value') else str(fir.investigation_status or ''),
             "title": fir.title or "", "priority": fir.priority.value if hasattr(fir.priority, 'value') else str(fir.priority or '')},
        )

        # ── 2. Accused → INVOLVED_IN ──────────────────────────
        r = await self.session.execute(
            select(FIRAccusedLink).where(FIRAccusedLink.fir_id == fir_id)
        )
        links = list(r.scalars().all())
        accused_ids = [l.accused_id for l in links]

        if accused_ids:
            r = await self.session.execute(
                select(Accused).where(Accused.accused_id.in_(accused_ids))
            )
            accused_map = {a.accused_id: a for a in r.scalars().all()}

            for link in links:
                accused = accused_map.get(link.accused_id)
                if not accused:
                    continue
                nid = f"accused:{accused.accused_id}"
                self._add_node(
                    nid, accused.full_name, "Accused",
                    {"age": accused.age, "phone": accused.phone,
                     "risk_score": float(accused.risk_score) if accused.risk_score else 0},
                )
                self._add_edge(fir_nid, nid, "INVOLVED_IN")

        # ── 3. Victims → VICTIM_OF ────────────────────────────
        r = await self.session.execute(
            select(FIRVictimLink).where(FIRVictimLink.fir_id == fir_id)
        )
        victim_links = list(r.scalars().all())
        victim_ids = [l.victim_id for l in victim_links]

        if victim_ids:
            r = await self.session.execute(
                select(Victim).where(Victim.victim_id.in_(victim_ids))
            )
            victim_map = {v.victim_id: v for v in r.scalars().all()}

            for link in victim_links:
                v = victim_map.get(link.victim_id)
                if not v:
                    continue
                nid = f"victim:{v.victim_id}"
                self._add_node(nid, v.full_name, "Victim",
                               {"age": v.age, "phone": v.phone})
                self._add_edge(nid, fir_nid, "VICTIM_OF")

        # ── 4. Evidence → EVIDENCE_FOR ────────────────────────
        r = await self.session.execute(
            select(Evidence).where(Evidence.fir_id == fir_id)
        )
        evidence_items = list(r.scalars().all())

        for ev in evidence_items:
            nid = f"evidence:{ev.evidence_id}"
            ev_type = ev.evidence_type.value if hasattr(ev.evidence_type, 'value') else str(ev.evidence_type or 'General')
            self._add_node(nid, ev.evidence_name or f"Evidence #{ev.evidence_id}", "Evidence",
                           {"type": ev_type, "description": (ev.description or "")[:100]})
            self._add_edge(nid, fir_nid, "EVIDENCE_FOR")

        # ── 5. Location → OCCURRED_AT ──────────────────────────
        if fir.location_id:
            r = await self.session.execute(
                select(Location).where(Location.location_id == fir.location_id)
            )
            loc = r.scalar_one_or_none()
            if loc:
                nid = f"location:{loc.location_id}"
                label = f"{loc.district}, {loc.area}" if loc.district else loc.area
                self._add_node(nid, label, "Location",
                               {"city": loc.city, "district": loc.district, "area": loc.area})
                self._add_edge(fir_nid, nid, "OCCURRED_AT")

        # ── 6. Financial Transactions → MONEY_TRANSFER ────────
        r = await self.session.execute(
            select(FinancialTransaction).where(FinancialTransaction.fir_id == fir_id)
        )
        txs = list(r.scalars().all())

        for tx in txs:
            nid = f"transaction:{tx.transaction_id}"
            label = f"{tx.bank_name or 'Bank'} #{tx.transaction_id}"
            self._add_node(nid, label, "Transaction",
                           {"bank": tx.bank_name, "amount": float(tx.amount) if tx.amount else 0,
                            "type": tx.transaction_type.value if hasattr(tx.transaction_type, 'value') else str(tx.transaction_type or '')})
            self._add_edge(nid, fir_nid, "MONEY_TRANSFER")

            # Also link accused to their transactions
            if tx.accused_id:
                accused_nid = f"accused:{tx.accused_id}"
                if accused_nid in self._node_ids:
                    self._add_edge(accused_nid, nid, "MONEY_TRANSFER")

        logger.info("Graph built for FIR %s: %d nodes, %d edges",
                     fir_number, len(self.nodes), len(self.edges))

        return {
            "fir_number": fir_number,
            "nodes": self.nodes,
            "edges": self.edges,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
        }
