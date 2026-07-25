"""Criminal Network Analysis service - builds graph JSON from entity relationships."""

import re
from collections import Counter, defaultdict
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.models import Accused, FIRAccusedLink
from app.crime.models import CrimeType
from app.fir.models import FIR
from app.evidence.models import Evidence
from app.financial_transaction.models import FinancialTransaction
from app.location.models import Location
from app.victim.models import FIRVictimLink, Victim
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
        # Avoid duplicate edges between same source-target
        for e in self.edges:
            if e["source"] == source and e["target"] == target:
                e["weight"] += weight
                return
        self._edge_counter += 1
        self.edges.append({
            "id": f"e{self._edge_counter}",
            "source": source,
            "target": target,
            "label": label,
            "weight": max(0.5, min(weight, 10.0)),
            "metadata": metadata or {},
        })

    def _extract_phones(self, text_val: str | None) -> list[str]:
        if not text_val:
            return []
        pattern = r'\b[6789]\d{9}\b'
        return list(set(re.findall(pattern, text_val)))

    _VEHICLE_PATTERNS = [
        r'\b[A-Z]{2}[ -]?[0-9]{1,2}[ -]?[A-Z]{1,2}[ -]?[0-9]{1,4}\b',
        r'\bvehicle[ :#]?([A-Z0-9 -]+)\b',
        r'\breg[ :]?(?:no|number)[ :]?([A-Z0-9 -]+)\b',
        r'\b(?:car|bike|motorcycle|scooter|van|truck|auto)\b',
    ]

    def _extract_vehicles(self, text_val: str | None) -> list[str]:
        if not text_val:
            return []
        found = []
        for pattern in self._VEHICLE_PATTERNS:
            matches = re.findall(pattern, text_val, re.IGNORECASE)
            found.extend([m.strip().upper() for m in matches if m.strip()])
        return list(set(found))

    async def build_graph(self, fir_id: str | None = None) -> dict[str, Any]:
        """Build the full criminal network graph with co-accused relationships."""
        self.nodes = {}
        self.edges = []
        self._edge_counter = 0

        # --- 1. Load FIRs ---
        fir_query = select(FIR)
        if fir_id:
            try:
                fir_query = fir_query.where(FIR.fir_id == int(fir_id))
            except ValueError:
                fir_query = fir_query.where(FIR.fir_number == fir_id)
        r = await self.session.execute(fir_query)
        firs = list(r.scalars().all())

        for fir in firs:
            self._add_node(
                node_id=f"fir:{fir.fir_id}",
                label=f"FIR {fir.fir_number}",
                node_type="fir",
                group="case",
                metadata={
                    "fir_number": fir.fir_number,
                    "status": fir.investigation_status.value if hasattr(fir.investigation_status, 'value') else str(fir.investigation_status or 'N/A'),
                    "title": fir.title,
                    "priority": fir.priority.value if hasattr(fir.priority, 'value') else None,
                },
            )

        if not firs:
            return self._graph_response("No FIRs found")

        fir_ids = [f.fir_id for f in firs]

        # --- 2. Load Victims ---
        r = await self.session.execute(
            select(FIRVictimLink).where(FIRVictimLink.fir_id.in_(fir_ids))
        )
        victim_links = list(r.scalars().all())
        victim_ids = list(set(l.victim_id for l in victim_links))
        victim_map: dict[int, Victim] = {}
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
            contact_str = v.phone or v.email or ''
            self._add_node(
                nid, v.full_name, "victim", "person",
                {"age": v.age, "gender": v.gender.value if v.gender else None, "contact": contact_str},
            )
            self._add_edge(f"fir:{link.fir_id}", nid, "has_victim")

            phones = self._extract_phones(contact_str) + self._extract_phones(v.address)
            for phone in phones:
                pid = f"phone:{phone}"
                self._add_node(pid, phone, "phone", "contact", {"source": f"victim:{v.victim_id}"})
                self._add_edge(nid, pid, "has_phone")

        # --- 3. Load Accused & link to FIRs ---
        r = await self.session.execute(
            select(FIRAccusedLink).where(FIRAccusedLink.fir_id.in_(fir_ids))
        )
        links = list(r.scalars().all())
        link_accused_ids = list(set(l.accused_id for l in links))

        accused_map: dict[int, Accused] = {}
        if link_accused_ids:
            r = await self.session.execute(
                select(Accused).where(Accused.accused_id.in_(link_accused_ids))
            )
            accused_map = {a.accused_id: a for a in r.scalars().all()}

            # Track which FIRs each accused is linked to (for co-accused edges)
            accused_firs: dict[int, list[int]] = defaultdict(list)
            for link in links:
                accused_firs[link.accused_id].append(link.fir_id)

            for link in links:
                accused = accused_map.get(link.accused_id)
                if not accused:
                    continue
                nid = f"accused:{accused.accused_id}"
                risk = float(accused.risk_score) if accused.risk_score else 0.0
                self._add_node(
                    nid, accused.full_name, "accused", "person",
                    {
                        "full_name": accused.full_name,
                        "age": accused.age,
                        "gender": accused.gender.value if accused.gender else None,
                        "risk_score": round(risk, 2),
                        "phone": accused.phone,
                        "fir_count": len(accused_firs[accused.accused_id]),
                    },
                )
                self._add_edge(f"fir:{link.fir_id}", nid, "has_accused")

            # --- Co-accused edges: accused linked to same FIR ---
            fir_accused_map: dict[int, list[int]] = defaultdict(list)
            for link in links:
                fir_accused_map[link.fir_id].append(link.accused_id)

            for fir_id_link, accused_ids in fir_accused_map.items():
                unique_ids = list(set(accused_ids))
                for i in range(len(unique_ids)):
                    for j in range(i + 1, len(unique_ids)):
                        a1 = f"accused:{unique_ids[i]}"
                        a2 = f"accused:{unique_ids[j]}"
                        if a1 in self.nodes and a2 in self.nodes:
                            self._add_edge(a1, a2, "co-accused", weight=2.0)

            # --- Cross-FIR edges: accused linked to multiple FIRs ---
            for accused_id, fir_list in accused_firs.items():
                if len(fir_list) >= 2:
                    nid = f"accused:{accused_id}"
                    if nid in self.nodes:
                        for f_id in fir_list:
                            self._add_edge(f"fir:{f_id}", nid, "linked_fir", weight=1.5)

            # Extract phones from accused
            for accused in accused_map.values():
                anid = f"accused:{accused.accused_id}"
                if anid not in self.nodes:
                    continue
                phones = self._extract_phones(accused.phone) + self._extract_phones(accused.address)
                for phone in phones:
                    pid = f"phone:{phone}"
                    self._add_node(pid, phone, "phone", "contact", {"source": f"accused:{accused.accused_id}"})
                    self._add_edge(anid, pid, "has_phone")

        # --- 4. Load Locations ---
        loc_ids = [f.location_id for f in firs if f.location_id]
        if loc_ids:
            r = await self.session.execute(
                select(Location).where(Location.location_id.in_(loc_ids))
            )
            loc_map = {loc.location_id: loc for loc in r.scalars().all()}
            for fir in firs:
                if fir.location_id and fir.location_id in loc_map:
                    loc = loc_map[fir.location_id]
                    nid = f"location:{loc.location_id}"
                    label = f"{loc.district or loc.city}, {loc.area}"
                    self._add_node(
                        nid, label, "location", "place",
                        {"city": loc.city, "district": loc.district, "area": loc.area},
                    )
                    self._add_edge(f"fir:{fir.fir_id}", nid, "occurred_at")

        # --- 5. Load Crime Types ---
        crime_type_ids = list(set(f.crime_type_id for f in firs if f.crime_type_id))
        crime_type_map: dict[int, CrimeType] = {}
        if crime_type_ids:
            r = await self.session.execute(
                select(CrimeType).where(CrimeType.crime_type_id.in_(crime_type_ids))
            )
            crime_type_map = {ct.crime_type_id: ct for ct in r.scalars().all()}
        for fir in firs:
            if fir.crime_type_id and fir.crime_type_id in crime_type_map:
                ct = crime_type_map[fir.crime_type_id]
                nid = f"crime_type:{ct.crime_type_id}"
                self._add_node(
                    nid, ct.crime_name, "crime_type", "category",
                    {"severity": ct.severity.value if ct.severity else None},
                )
                self._add_edge(f"fir:{fir.fir_id}", nid, "involves_crime")

        # --- 6. Evidence Nodes + Vehicles from Evidence ---
        r = await self.session.execute(
            select(Evidence).where(Evidence.fir_id.in_(fir_ids))
        )
        evidence_items = list(r.scalars().all())
        for ev in evidence_items:
            # Add explicit evidence node
            ev_nid = f"evidence:{ev.evidence_id}"
            ev_label = ev.evidence_name or f"Evidence #{ev.evidence_id}"
            ev_type_label = ev.evidence_type.value if hasattr(ev.evidence_type, 'value') else str(ev.evidence_type or 'General')
            self._add_node(
                ev_nid, ev_label, "evidence", "document",
                {
                    "evidence_id": ev.evidence_id,
                    "evidence_type": ev_type_label,
                    "description": (ev.description or "")[:100],
                    "status": ev.status.value if hasattr(ev.status, 'value') else str(ev.status or 'N/A'),
                },
            )
            self._add_edge(f"fir:{ev.fir_id}", ev_nid, "has_evidence")

            # Extract vehicles from evidence description
            vehicles = self._extract_vehicles(ev.evidence_name) + self._extract_vehicles(ev.description)
            for v in vehicles:
                vid = f"vehicle:{v}"
                self._add_node(vid, v, "vehicle", "asset", {"source": f"evidence:{ev.evidence_id}"})
                self._add_edge(ev_nid, vid, "has_vehicle")

        # --- 7. Financial Transaction Nodes ---
        r = await self.session.execute(
            select(FinancialTransaction).where(FinancialTransaction.fir_id.in_(fir_ids))
        )
        txs = list(r.scalars().all())
        for tx in txs:
            # Explicit financial transaction node
            tx_nid = f"financial:{tx.transaction_id}"
            tx_label = f"{tx.bank_name or 'Bank'} #{tx.transaction_id}"
            tx_amount = float(tx.amount) if tx.amount else 0.0
            tx_type = tx.transaction_type.value if hasattr(tx.transaction_type, 'value') else str(tx.transaction_type or 'Unknown')
            self._add_node(
                tx_nid, tx_label, "financial_transaction", "financial",
                {
                    "transaction_id": tx.transaction_id,
                    "bank": tx.bank_name,
                    "amount": tx_amount,
                    "type": tx_type,
                    "account": tx.account_number or "N/A",
                    "date": str(tx.transaction_date) if tx.transaction_date else None,
                },
            )
            self._add_edge(f"fir:{tx.fir_id}", tx_nid, "has_financial")

            # Link accused to their financial transactions (Financial ↔ Accused)
            if tx.accused_id:
                accused_nid = f"accused:{tx.accused_id}"
                if accused_nid in self.nodes:
                    self._add_edge(accused_nid, tx_nid, "financial_link", weight=1.5)

            # Also keep bank_account node for backward compatibility
            sid = f"bank_account:{tx.transaction_id}:account"
            account_label = tx.account_number or f"acct_{tx.transaction_id}"
            self._add_node(
                sid, account_label, "bank_account", "financial",
                {"bank": tx.bank_name, "amount": str(tx.amount) if tx.amount else None,
                 "type": tx_type},
            )
            self._add_edge(tx_nid, sid, "uses_account")

        # Compute statistics
        stats = self._compute_statistics(accused_map, links, fir_ids)

        logger.info(
            "Network graph built: %d nodes, %d edges (filter=%s)",
            len(self.nodes), len(self.edges), fir_id or "all",
        )
        return self._graph_response(statistics=stats)

    def _compute_statistics(
        self,
        accused_map: dict[int, Accused],
        links: list,
        fir_ids: list[int],
    ) -> dict:
        """Compute network statistics from built graph."""
        # Count unique accused linked to 2+ FIRs
        accused_fir_count: dict[int, int] = Counter(l.accused_id for l in links)
        repeat_offenders = sum(1 for c in accused_fir_count.values() if c >= 2)

        # Count relation types
        edge_labels = [e["label"] for e in self.edges]
        top_label = Counter(edge_labels).most_common(1)
        top_association = top_label[0][0] if top_label else ""

        # Find connected components (BFS)
        visited = set()
        components = []
        adjacency: dict[str, list[str]] = defaultdict(list)
        for e in self.edges:
            adjacency[e["source"]].append(e["target"])
            adjacency[e["target"]].append(e["source"])

        for node_id in self.nodes:
            if node_id in visited:
                continue
            component = []
            stack = [node_id]
            while stack:
                n = stack.pop()
                if n in visited:
                    continue
                visited.add(n)
                component.append(n)
                for neighbor in adjacency.get(n, []):
                    if neighbor not in visited:
                        stack.append(neighbor)
            if component:
                components.append(component)

        largest = max(len(c) for c in components) if components else 0
        active = len(components)

        return {
            "total_criminals": len(accused_map),
            "total_connections": len(self.edges),
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "largest_network": largest,
            "active_networks": active,
            "top_association": top_association,
            "repeat_offenders": repeat_offenders,
        }

    def _graph_response(
        self,
        message: str | None = None,
        statistics: dict | None = None,
    ) -> dict[str, Any]:
        resp = {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
        }
        if statistics:
            resp["statistics"] = statistics
        if message:
            resp["metadata"] = {"message": message}
        return resp
