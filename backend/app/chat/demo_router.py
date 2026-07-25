"""Demo Router — drop-in replacement for ServiceRouter in Demo Mode.

Maintains the exact same ``route(intent, message)`` interface as
ServiceRouter so that ChatService can swap between production and
demo routing with a single condition check.

All data comes from DemoService (hard-coded sample data).
No database queries are executed.
No existing services are modified.
"""

import re
from typing import Any, Optional

from app.chat.intent_classifier import IntentResult
from app.demo.demo_service import DemoService
from app.logging import get_logger

logger = get_logger(__name__)


class DemoRouter:
    """Routes an intent to DemoService — same interface as ServiceRouter.

    Returns::
        {"success": bool, "data": dict, "error": Optional[str]}

    All return shapes match what ServiceRouter produces so the
    ChatService pipeline works identically.
    """

    def __init__(self) -> None:
        self._demo = DemoService()

        self.routes: dict[str, Any] = {
            "FIR_SEARCH": self._handle_fir_search,
            "FIR_CREATE": self._handle_fir_create,
            "FIR_UPDATE": self._handle_fir_update,
            "FIR_SUMMARY": self._handle_fir_summary,
            "VICTIM_SEARCH": self._handle_victim_search,
            "VICTIM_CREATE": self._handle_victim_create,
            "VICTIM_SUMMARY": self._handle_victim_summary,
            "ACCUSED_SEARCH": self._handle_accused_search,
            "ACCUSED_CREATE": self._handle_accused_create,
            "ACCUSED_SUMMARY": self._handle_accused_summary,
            "EVIDENCE_SEARCH": self._handle_evidence_search,
            "EVIDENCE_CREATE": self._handle_evidence_create,
            "EVIDENCE_SUMMARY": self._handle_evidence_summary,
            "FINANCIAL_SEARCH": self._handle_financial_search,
            "FINANCIAL_SUMMARY": self._handle_financial_summary,
            "CRIME_HISTORY_SEARCH": self._handle_history_search,
            "CRIME_HISTORY_SUMMARY": self._handle_history_summary,
            "HOTSPOT_SEARCH": self._handle_hotspot_search,
            "HOTSPOT_ANALYSIS": self._handle_hotspot_analysis,
            "NETWORK_GRAPH": self._handle_network_graph,
            "NETWORK_SEARCH": self._handle_network_search,
            "NETWORK_ANALYSIS": self._handle_network_analysis,
            "LOCATION_SEARCH": self._handle_location_search,
            "AUDIT_SEARCH": self._handle_audit_search,
            "USER_SEARCH": self._handle_user_search,
            "SETTINGS": self._handle_settings,
            "CRIME_PREDICTION": self._handle_prediction,
            "REPORT_GENERATION": self._handle_report,
            "CASE_SUMMARY": self._handle_case_summary,
            "HELP": self._handle_help,
            "GENERAL_CHAT": self._handle_general_chat,
        }

    async def route(
        self, intent: IntentResult, message: str
    ) -> dict[str, Any]:
        """Route an intent to its handler and return structured data."""
        handler = self.routes.get(intent.intent)
        if handler is None:
            logger.warning("DemoRouter: unknown intent %s", intent.intent)
            return {"success": False, "data": {}, "error": f"Unknown intent: {intent.intent}"}
        try:
            return await handler(intent, message)
        except Exception as exc:
            logger.error("DemoRouter error for %s: %s", intent.intent, str(exc))
            return {"success": False, "data": {}, "error": str(exc)}

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _extract_fir_id(intent: IntentResult, message: str) -> Optional[int]:
        fir_id = intent.entities.get("fir_id")
        if fir_id:
            try:
                return int(fir_id)
            except (ValueError, TypeError):
                pass
        m = re.search(r"(?:FIR)[-\s]?(\d+(?:-\d+)*)", message, re.IGNORECASE)
        if m:
            parts = m.group(1).split("-")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                pass
        m = re.search(r"\b(\d+)\b", message)
        if m:
            return int(m.group(1))
        return None

    @staticmethod
    def _extract_search_term(intent: IntentResult, message: str) -> str:
        for key in ("name", "fir_number", "phone", "email", "district"):
            val = intent.entities.get(key)
            if val:
                return val
        for prefix in ("show", "find", "search", "list", "get"):
            if message.lower().startswith(prefix):
                rest = message[len(prefix):].strip().lstrip(" ").strip()
                if rest and "for" not in rest.lower()[:10]:
                    return rest[:50]
        return ""

    # ── FIR Handlers ────────────────────────────────────────────

    async def _handle_fir_search(self, intent: IntentResult, message: str) -> dict:
        search_term = self._extract_search_term(intent, message)
        fir_id = self._extract_fir_id(intent, message)
        if fir_id:
            fir = self._demo.get_fir(fir_id)
            return {"success": True, "data": {"firs": [fir], "total": 1}}
        result = self._demo.list_firs(search_term)
        return {"success": True, "data": {"firs": result.get("items", []), "total": result.get("total", 0)}}

    async def _handle_fir_create(self, intent: IntentResult, message: str) -> dict:
        return {"success": False, "data": {}, "error": "FIR creation requires the FIR registration form. Please use the FIR Management module."}

    async def _handle_fir_update(self, intent: IntentResult, message: str) -> dict:
        return {"success": False, "data": {}, "error": "FIR update requires the FIR management form. Please use the FIR Management module."}

    async def _handle_fir_summary(self, intent: IntentResult, message: str) -> dict:
        fir_id = self._extract_fir_id(intent, message)
        if fir_id:
            fir = self._demo.get_fir(fir_id)
            return {"success": True, "data": fir}
        result = self._demo.list_firs()
        return {"success": True, "data": {"firs": result.get("items", [])[:5]}}

    # ── Victim Handlers ─────────────────────────────────────────

    async def _handle_victim_search(self, intent: IntentResult, message: str) -> dict:
        search_term = self._extract_search_term(intent, message)
        result = self._demo.list_victims(search_term)
        return {"success": True, "data": {"victims": result.get("items", []), "total": result.get("total", 0)}}

    async def _handle_victim_create(self, intent: IntentResult, message: str) -> dict:
        return {"success": False, "data": {}, "error": "Victim creation requires the victim registration form. Please use the Victims module."}

    async def _handle_victim_summary(self, intent: IntentResult, message: str) -> dict:
        search_term = self._extract_search_term(intent, message)
        result = self._demo.list_victims(search_term)
        return {"success": True, "data": {"victims": result.get("items", [])[:5]}}

    # ── Accused Handlers ────────────────────────────────────────

    async def _handle_accused_search(self, intent: IntentResult, message: str) -> dict:
        search_term = self._extract_search_term(intent, message)
        result = self._demo.list_accused(search_term)
        return {"success": True, "data": {"accused": result.get("items", []), "total": result.get("total", 0)}}

    async def _handle_accused_create(self, intent: IntentResult, message: str) -> dict:
        return {"success": False, "data": {}, "error": "Accused creation requires the accused registration form. Please use the Accused module."}

    async def _handle_accused_summary(self, intent: IntentResult, message: str) -> dict:
        search_term = self._extract_search_term(intent, message)
        result = self._demo.list_accused(search_term)
        return {"success": True, "data": {"accused": result.get("items", [])[:5]}}

    # ── Evidence Handlers ───────────────────────────────────────

    async def _handle_evidence_search(self, intent: IntentResult, message: str) -> dict:
        fir_id = self._extract_fir_id(intent, message)
        result = self._demo.list_evidence(fir_id or 0)
        return {"success": True, "data": {"evidence": result.get("items", []), "total": result.get("total", 0)}}

    async def _handle_evidence_create(self, intent: IntentResult, message: str) -> dict:
        return {"success": False, "data": {}, "error": "Evidence submission requires the Evidence module form. Please use the Evidence module."}

    async def _handle_evidence_summary(self, intent: IntentResult, message: str) -> dict:
        fir_id = self._extract_fir_id(intent, message)
        result = self._demo.list_evidence(fir_id or 0)
        return {"success": True, "data": {"evidence": result.get("items", [])}}

    # ── Financial Handlers ──────────────────────────────────────

    async def _handle_financial_search(self, intent: IntentResult, message: str) -> dict:
        search_term = self._extract_search_term(intent, message)
        result = self._demo.list_transactions(search_term)
        items = result.get("items", [])
        total_amount = sum(t.get("amount", 0) for t in items)
        return {"success": True, "data": {"transactions": items, "total": result.get("total", 0), "total_amount": total_amount}}

    async def _handle_financial_summary(self, intent: IntentResult, message: str) -> dict:
        result = self._demo.list_transactions()
        return {"success": True, "data": {"transactions": result.get("items", [])[:10]}}

    # ── Crime History Handlers ──────────────────────────────────

    async def _handle_history_search(self, intent: IntentResult, message: str) -> dict:
        result = self._demo.list_history()
        return {"success": True, "data": {"history": result.get("items", []), "total": result.get("total", 0)}}

    async def _handle_history_summary(self, intent: IntentResult, message: str) -> dict:
        result = self._demo.list_history()
        return {"success": True, "data": {"history": result.get("items", [])[:10]}}

    # ── Hotspot Handlers ────────────────────────────────────────

    async def _handle_hotspot_search(self, intent: IntentResult, message: str) -> dict:
        search_term = self._extract_search_term(intent, message)
        result = self._demo.get_hotspots(search=search_term)
        return {"success": True, "data": {"hotspots": result.get("hotspots", []), "total_hotspots": result.get("total_hotspots", 0)}}

    async def _handle_hotspot_analysis(self, intent: IntentResult, message: str) -> dict:
        search_term = self._extract_search_term(intent, message)
        if search_term:
            detail = self._demo.get_hotspot_detail(search_term)
            if detail:
                return {"success": True, "data": detail}
        result = self._demo.get_hotspots()
        return {"success": True, "data": {"hotspots": result.get("hotspots", []), "high_risk_count": result.get("high_risk_count", 0), "total_crimes": result.get("total_crimes", 0)}}

    # ── Network Handlers ────────────────────────────────────────

    async def _handle_network_graph(self, intent: IntentResult, message: str) -> dict:
        fir_number = intent.entities.get("fir_number")
        if not fir_number:
            m = re.search(r"(?:FIR)[-\s]?(\d+(?:-\d+)*)", message, re.IGNORECASE)
            if m:
                fir_number = m.group(0)
        graph = self._demo.build_graph(fir_number or "")
        return {"success": True, "data": graph}

    async def _handle_network_search(self, intent: IntentResult, message: str) -> dict:
        return await self._handle_network_graph(intent, message)

    async def _handle_network_analysis(self, intent: IntentResult, message: str) -> dict:
        return await self._handle_network_graph(intent, message)

    # ── Location Handler ────────────────────────────────────────

    async def _handle_location_search(self, intent: IntentResult, message: str) -> dict:
        search_term = self._extract_search_term(intent, message)
        result = self._demo.get_hotspots(search=search_term)
        locations = [
            {
                "location_id": i + 1,
                "district": h["district"],
                "city": h.get("city", ""),
                "area": f"{h['district']} Area",
                "latitude": h.get("latitude"),
                "longitude": h.get("longitude"),
            }
            for i, h in enumerate(result.get("hotspots", []))
        ]
        return {"success": True, "data": {"locations": locations, "total": len(locations)}}

    # ── Audit Handler ───────────────────────────────────────────

    async def _handle_audit_search(self, intent: IntentResult, message: str) -> dict:
        result = self._demo.list_audit_logs()
        return {"success": True, "data": result}

    # ── User Handler ────────────────────────────────────────────

    async def _handle_user_search(self, intent: IntentResult, message: str) -> dict:
        search_term = self._extract_search_term(intent, message)
        result = self._demo.list_users()
        if search_term:
            items = [u for u in result.get("items", []) if search_term.lower() in u.get("full_name", "").lower()]
        else:
            items = result.get("items", [])
        return {"success": True, "data": {"items": items, "total": len(items)}}

    # ── Settings Handler ────────────────────────────────────────

    async def _handle_settings(self, intent: IntentResult, message: str) -> dict:
        return {"success": True, "data": self._demo.get_settings()}

    # ── Prediction Handler ──────────────────────────────────────

    async def _handle_prediction(self, intent: IntentResult, message: str) -> dict:
        return {"success": True, "data": self._demo.get_prediction()}

    # ── Report & Case Summary ───────────────────────────────────

    async def _handle_report(self, intent: IntentResult, message: str) -> dict:
        firs_result = self._demo.list_firs()
        stats = self._demo.get_statistics()
        return {
            "success": True,
            "data": {
                "firs": firs_result.get("items", [])[:5],
                "statistics": stats,
            },
        }

    async def _handle_case_summary(self, intent: IntentResult, message: str) -> dict:
        fir_id = self._extract_fir_id(intent, message)
        if fir_id:
            fir = self._demo.get_fir(fir_id)
            return {"success": True, "data": fir}
        result = self._demo.list_firs()
        return {"success": True, "data": {"firs": result.get("items", [])[:5], "note": "Specify an FIR number for a detailed case summary."}}

    # ── Help Handler ────────────────────────────────────────────

    async def _handle_help(self, intent: IntentResult, message: str) -> dict:
        return {
            "success": True,
            "data": {
                "capabilities": [
                    "Search FIRs, victims, accused, evidence",
                    "Analyze crime hotspots and trends",
                    "Explore criminal networks and connections",
                    "View financial transactions and patterns",
                    "Get crime predictions and forecasts",
                    "Generate investigation reports and summaries",
                    "Search audit logs and user activity",
                    "Manage settings and preferences",
                ],
                "examples": [
                    "Show me recent FIRs",
                    "Summarize FIR #1 (demo data)",
                    "Find accused named Arjun",
                    "Analyze crime hotspots in Bengaluru",
                    "Show the criminal network connections",
                    "Generate a weekly crime report",
                    "Predict crime trends for next month",
                ],
            },
        }

    # ── General Chat Handler ────────────────────────────────────

    async def _handle_general_chat(self, intent: IntentResult, message: str) -> dict:
        return {"success": True, "data": {"message": message}}
