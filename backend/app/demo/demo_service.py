"""Demo Service — returns hard-coded sample data for Demo Mode.

All data comes from demo_data.py and never touches the database.
Supports all entity types that the chat ServiceRouter handles.
"""

from typing import Any

from app.demo.demo_data import (
    DEMO_INFO, FIR_DATA, VICTIM_DATA, ACCUSED_DATA, EVIDENCE_DATA,
    TRANSACTION_DATA, HISTORY_DATA, HOTSPOT_DATA, HOTSPOT_MAP_DATA,
    NETWORK_DATA, DASHBOARD_DATA, PREDICTION_DATA, USERS_DATA,
    AUDIT_LOGS_DATA, SETTINGS_DATA, DISTRICTS,
)


class DemoService:
    """Returns realistic demo data for every entity type.

    All methods return data in the same format as the production
    ServiceRouter handlers, so the frontend receives identical shapes.
    """

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _filter(items: list[dict], key: str, value: Any) -> list[dict]:
        """Filter a list of dicts by key-value match (case-insensitive)."""
        if not value:
            return items
        return [i for i in items if str(i.get(key, "")).lower() == str(value).lower()]

    @staticmethod
    def _search(items: list[dict], term: str, fields: list[str]) -> list[dict]:
        """Search across multiple fields."""
        if not term:
            return items
        term_lower = term.lower()
        return [
            i for i in items
            if any(term_lower in str(i.get(f, "")).lower() for f in fields)
        ]

    # ── FIR ──────────────────────────────────────────────────────

    def list_firs(self, search: str = "") -> dict:
        items = self._search(FIR_DATA, search, ["fir_number", "title", "description"])
        return {"items": items, "total": len(items), "total_pages": max(1, len(items) // 15 + 1)}

    def get_fir(self, fir_id: int) -> dict:
        for f in FIR_DATA:
            if f["fir_id"] == fir_id or str(f["fir_number"]).endswith(str(fir_id)):
                return f
        return FIR_DATA[0]

    def get_statistics(self) -> dict:
        total = len(FIR_DATA)
        solved = sum(1 for f in FIR_DATA if f["status"] in ("Solved", "Closed"))
        pending = sum(1 for f in FIR_DATA if f["status"] == "Pending")
        investigating = sum(1 for f in FIR_DATA if f["status"] == "Under Investigation")
        high_pri = sum(1 for f in FIR_DATA if f["priority"] in ("High", "Critical"))
        return {
            "total_firs": total,
            "solved_count": solved,
            "pending_count": pending,
            "under_investigation_count": investigating,
            "high_priority_count": high_pri,
        }

    # ── Victims ──────────────────────────────────────────────────

    def list_victims(self, search: str = "") -> dict:
        items = self._search(VICTIM_DATA, search, ["full_name", "phone", "email"])
        return {"items": items, "total": len(items)}

    # ── Accused ──────────────────────────────────────────────────

    def list_accused(self, search: str = "") -> dict:
        items = self._search(ACCUSED_DATA, search, ["full_name", "phone", "email"])
        return {"items": items, "total": len(items)}

    # ── Evidence ─────────────────────────────────────────────────

    def list_evidence(self, fir_id: int = 0) -> dict:
        if fir_id:
            items = self._filter(EVIDENCE_DATA, "fir_id", fir_id)
        else:
            items = EVIDENCE_DATA
        return {"items": items, "total": len(items)}

    # ── Financial ────────────────────────────────────────────────

    def list_transactions(self, search: str = "") -> dict:
        items = self._search(TRANSACTION_DATA, search, ["bank_name", "transaction_reference"])
        return {"items": items, "total": len(items)}

    # ── Crime History ────────────────────────────────────────────

    def list_history(self) -> dict:
        return {"items": HISTORY_DATA, "total": len(HISTORY_DATA)}

    # ── Hotspots ─────────────────────────────────────────────────

    def get_hotspots(self, time_range: str = "30d", search: str = "") -> dict:
        items = self._search(HOTSPOT_DATA, search, ["district", "city", "area"])
        high_risk = sum(1 for h in items if h["risk_level"] == "High")
        return {
            "hotspots": items,
            "total_hotspots": len(items),
            "high_risk_count": high_risk,
            "medium_risk_count": sum(1 for h in items if h["risk_level"] == "Medium"),
            "low_risk_count": sum(1 for h in items if h["risk_level"] == "Low"),
            "unique_districts": len(set(h["district"] for h in items)),
            "unique_cities": len(set(h["city"] for h in items)),
            "total_crimes": sum(h["crime_count"] for h in items),
        }

    def get_hotspot_detail(self, district: str) -> dict:
        for h in HOTSPOT_DATA:
            if h["district"].lower() == district.lower():
                return {
                    **h,
                    "monthly_trend": [
                        {"month": "Jan", "count": 10}, {"month": "Feb", "count": 15},
                        {"month": "Mar", "count": 12}, {"month": "Apr", "count": 18},
                        {"month": "May", "count": 22}, {"month": "Jun", "count": 20},
                    ],
                    "crime_types": [
                        {"crime_type": "Theft", "count": 25},
                        {"crime_type": "Burglary", "count": 18},
                        {"crime_type": "Assault", "count": 12},
                        {"crime_type": "Robbery", "count": 8},
                        {"crime_type": "Cyber Crime", "count": 6},
                    ],
                    "ai_insight": f"{district} shows elevated crime activity. "
                                  f"Patrol presence recommended during evening hours.",
                }
        return None

    def get_hotspot_map(self) -> list[dict]:
        return HOTSPOT_MAP_DATA

    # ── Network Graph ────────────────────────────────────────────

    def build_graph(self, fir_number: str = "") -> dict:
        if fir_number:
            # Filter nodes/edges related to the specific FIR
            fir_id = None
            for f in FIR_DATA:
                if f["fir_number"] == fir_number:
                    fir_id = f["fir_id"]
                    break
            if fir_id:
                related_nodes = {f"fir:{fir_id}"}
                related_edges = []
                for e in NETWORK_DATA["edges"]:
                    if e["from"] == f"fir:{fir_id}" or e["to"] == f"fir:{fir_id}":
                        related_edges.append(e)
                        related_nodes.add(e["from"])
                        related_nodes.add(e["to"])
                nodes = [n for n in NETWORK_DATA["nodes"] if n["id"] in related_nodes]
                return {"nodes": nodes, "edges": related_edges,
                        "statistics": {"total_nodes": len(nodes), "total_edges": len(related_edges)}}
        return NETWORK_DATA

    # ── Dashboard ────────────────────────────────────────────────

    def get_dashboard(self) -> dict:
        return DASHBOARD_DATA

    # ── Prediction ───────────────────────────────────────────────

    def get_prediction(self) -> dict:
        return PREDICTION_DATA

    # ── Users ────────────────────────────────────────────────────

    def list_users(self) -> dict:
        return {"items": USERS_DATA, "total": len(USERS_DATA)}

    # ── Audit Logs ───────────────────────────────────────────────

    def list_audit_logs(self) -> dict:
        return {"items": AUDIT_LOGS_DATA, "total": len(AUDIT_LOGS_DATA)}

    # ── Settings ─────────────────────────────────────────────────

    def get_settings(self) -> dict:
        return SETTINGS_DATA

    # ── Demo Info ────────────────────────────────────────────────

    def get_demo_info(self) -> dict:
        return DEMO_INFO
