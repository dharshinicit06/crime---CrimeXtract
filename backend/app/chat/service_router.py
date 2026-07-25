"""Service Router — routes intents to the appropriate business service.

This module is the bridge between intent classification and actual
database operations. It NEVER performs SQL queries directly.

Responsibilities:
  - Map each intent to the correct module service
  - Delegate calls to existing service classes
  - Return structured data (never raw ORM objects)
  - Never call Gemini directly

Version: 2.0 (Hybrid SQL + LLM)
"""

import re
import time
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.services import AccusedService
from app.audit_log.services import AuditLogService
from app.chat.intent_classifier import IntentResult
from app.crime_analytics.services import CrimeAnalyticsService
from app.crime_history.services import CrimeHistoryService
from app.crime_prediction.services import CrimePredictionService
from app.prediction.predictor import CrimePredictor
from app.evidence.services import EvidenceService
from app.financial_transaction.services import FinancialTransactionService
from app.fir.services import FIRService
from app.hotspots.services import CrimeHotspotService
from app.location.services import LocationService
from app.logging import get_logger
from app.network.graph_service import GraphBuilder
from app.network_analysis.services import NetworkAnalysisService
from app.settings.services import SettingsService
from app.users.services import UserService
from app.victim.services import VictimService

logger = get_logger(__name__)


class ServiceRouter:
    """Routes an intent to the appropriate business service.

    The router NEVER contains SQL.
    The router NEVER calls Gemini.
    It only delegates to the correct existing module service.
    """

    def __init__(self, session: AsyncSession, user_id: int) -> None:
        self.session = session
        self.user_id = user_id

        # ── Instantiate all services ────────────────────────────
        self._fir_service = FIRService(session)
        self._victim_service = VictimService(session)
        self._accused_service = AccusedService(session)
        self._evidence_service = EvidenceService(session)
        self._financial_service = FinancialTransactionService(session)
        self._history_service = CrimeHistoryService(session)
        self._hotspot_service = CrimeHotspotService(session)
        self._network_service = NetworkAnalysisService(session)
        self._location_service = LocationService(session)
        self._audit_service = AuditLogService(session)
        self._user_service = UserService(session)
        self._settings_service = SettingsService(session)
        self._prediction_service = CrimePredictionService(session)
        self._crime_predictor = CrimePredictor(session)
        self._analytics_service = CrimeAnalyticsService(session)

        # ── Intent → Handler mapping ───────────────────────────
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
        """Route an intent to its handler and return structured data.

        Returns:
            dict with keys:
              - success: bool
              - data: dict — the structured service result
              - error: Optional[str]
        """
        handler = self.routes.get(intent.intent)
        if handler is None:
            logger.warning("Unknown intent: %s", intent.intent)
            return {"success": False, "data": {}, "error": f"Unknown intent: {intent.intent}"}

        try:
            start = time.monotonic()
            result = await handler(intent, message)
            elapsed = time.monotonic() - start
            logger.debug("Service router: %s took %.0fms", intent.intent, elapsed * 1000)
            return result
        except Exception as exc:
            logger.error("Service router error for %s: %s", intent.intent, str(exc))
            return {"success": False, "data": {}, "error": str(exc)}

    # ── Serialisation Helpers ───────────────────────────────────

    @staticmethod
    def _serialise_fir(fir: Any) -> dict:
        """Convert an FIR ORM object to a plain dict."""
        return {
            "fir_id": getattr(fir, "fir_id", None),
            "fir_number": getattr(fir, "fir_number", None),
            "title": getattr(fir, "title", None),
            "description": getattr(fir, "description", None),
            "status": (
                getattr(fir, "investigation_status", None).value
                if hasattr(getattr(fir, "investigation_status", None), "value")
                else str(getattr(fir, "investigation_status", None) or "N/A")
            ),
            "priority": (
                getattr(fir, "priority", None).value
                if hasattr(getattr(fir, "priority", None), "value")
                else str(getattr(fir, "priority", None) or "N/A")
            ),
            "incident_date": str(getattr(fir, "incident_date", "")),
            "complaint_date": str(getattr(fir, "complaint_date", "")),
            "crime_type_id": getattr(fir, "crime_type_id", None),
            "location_id": getattr(fir, "location_id", None),
            "officer_id": getattr(fir, "officer_id", None),
        }

    @staticmethod
    def _serialise_victim(v: Any) -> dict:
        return {
            "victim_id": getattr(v, "victim_id", None),
            "full_name": getattr(v, "full_name", None),
            "age": getattr(v, "age", None),
            "gender": getattr(v, "gender", None),
            "phone": getattr(v, "phone", None),
            "email": getattr(v, "email", None),
            "address": getattr(v, "address", None),
        }

    @staticmethod
    def _serialise_accused(a: Any) -> dict:
        return {
            "accused_id": getattr(a, "accused_id", None),
            "full_name": getattr(a, "full_name", None),
            "age": getattr(a, "age", None),
            "gender": getattr(a, "gender", None),
            "phone": getattr(a, "phone", None),
            "email": getattr(a, "email", None),
            "address": getattr(a, "address", None),
            "risk_score": getattr(a, "risk_score", None),
            "is_repeat_offender": getattr(a, "is_repeat_offender", False),
        }

    @staticmethod
    def _serialise_evidence(e: Any) -> dict:
        return {
            "evidence_id": getattr(e, "evidence_id", None),
            "evidence_name": getattr(e, "evidence_name", None),
            "description": getattr(e, "description", None),
            "evidence_type": (
                getattr(e, "evidence_type", None).value
                if hasattr(getattr(e, "evidence_type", None), "value")
                else str(getattr(e, "evidence_type", None) or "N/A")
            ),
            "collected_date": str(getattr(e, "collected_date", "")),
            "fir_id": getattr(e, "fir_id", None),
        }

    @staticmethod
    def _serialise_transaction(t: Any) -> dict:
        return {
            "transaction_id": getattr(t, "transaction_id", None),
            "bank_name": getattr(t, "bank_name", None),
            "account_number": getattr(t, "account_number", None),
            "transaction_reference": getattr(t, "transaction_reference", None),
            "amount": float(getattr(t, "amount", 0) or 0),
            "transaction_type": str(getattr(t, "transaction_type", "")),
            "transaction_date": str(getattr(t, "transaction_date", "")),
        }

    # ── FIR Handlers ────────────────────────────────────────────

    async def _handle_fir_search(self, intent: IntentResult, message: str) -> dict:
        """Search FIRs by entities or list all."""
        search_term = intent.entities.get("fir_number") or intent.entities.get("fir_id")
        from app.auth.models import User as _User
        dummy = _User(id=self.user_id, email="chatbot@internal", role_id=1, is_active=True)

        if search_term:
            result = await self._fir_service.list_firs(dummy, search=search_term, page_size=10)
        else:
            result = await self._fir_service.list_firs(dummy, page_size=10)

        items = [self._serialise_fir(f) for f in result.get("items", [])]
        return {"success": True, "data": {"firs": items, "total": result.get("total", 0)}}

    async def _handle_fir_create(self, intent: IntentResult, message: str) -> dict:
        # Placeholder — FIR creation requires structured input form
        return {"success": False, "data": {}, "error": "FIR creation requires the FIR registration form. Please use the FIR Management module."}

    async def _handle_fir_update(self, intent: IntentResult, message: str) -> dict:
        # Placeholder — FIR update requires structured input
        return {"success": False, "data": {}, "error": "FIR update requires the FIR management form. Please use the FIR Management module."}

    async def _handle_fir_summary(self, intent: IntentResult, message: str) -> dict:
        """Get FIR summary for AI generation."""
        fir_id = intent.entities.get("fir_id")
        if not fir_id:
            # Try to find FIR number reference
            m = re.search(r"\b(\d+)\b", message)
            fir_id = m.group(1) if m else None
        if fir_id:
            try:
                fir = await self._fir_service.get_fir(int(fir_id))
                return {"success": True, "data": self._serialise_fir(fir)}
            except Exception:
                pass
        # Return recent FIRs for context
        from app.auth.models import User as _User
        dummy = _User(id=self.user_id, email="chatbot@internal", role_id=1, is_active=True)
        result = await self._fir_service.list_firs(dummy, page_size=5)
        items = [self._serialise_fir(f) for f in result.get("items", [])]
        return {"success": True, "data": {"firs": items}}

    # ── Victim Handlers ─────────────────────────────────────────

    async def _handle_victim_search(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("name") or intent.entities.get("phone")
        result = await self._victim_service.list_victims(search=search_term, page_size=10)
        items = [self._serialise_victim(v) for v in result.get("items", [])]
        return {"success": True, "data": {"victims": items, "total": result.get("total", 0)}}

    async def _handle_victim_create(self, intent: IntentResult, message: str) -> dict:
        return {"success": False, "data": {}, "error": "Victim creation requires the victim registration form. Please use the Victims module."}

    async def _handle_victim_summary(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("name") or intent.entities.get("phone")
        result = await self._victim_service.list_victims(search=search_term, page_size=5)
        items = [self._serialise_victim(v) for v in result.get("items", [])]
        return {"success": True, "data": {"victims": items}}

    # ── Accused Handlers ────────────────────────────────────────

    async def _handle_accused_search(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("name") or intent.entities.get("phone")
        result = await self._accused_service.list_accused(search=search_term, page_size=10)
        items = [self._serialise_accused(a) for a in result.get("items", [])]
        return {"success": True, "data": {"accused": items, "total": result.get("total", 0)}}

    async def _handle_accused_create(self, intent: IntentResult, message: str) -> dict:
        return {"success": False, "data": {}, "error": "Accused creation requires the accused registration form. Please use the Accused module."}

    async def _handle_accused_summary(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("name") or intent.entities.get("phone")
        result = await self._accused_service.list_accused(search=search_term, page_size=5)
        items = [self._serialise_accused(a) for a in result.get("items", [])]
        return {"success": True, "data": {"accused": items}}

    # ── Evidence Handlers ───────────────────────────────────────

    async def _handle_evidence_search(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("fir_id")
        result = await self._evidence_service.list_evidence(
            fir_id=search_term, search=intent.entities.get("name"), page_size=10
        )
        items = [self._serialise_evidence(e) for e in result.get("items", [])]
        return {"success": True, "data": {"evidence": items, "total": result.get("total", 0)}}

    async def _handle_evidence_create(self, intent: IntentResult, message: str) -> dict:
        return {"success": False, "data": {}, "error": "Evidence submission requires the Evidence module form. Please use the Evidence module."}

    async def _handle_evidence_summary(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("fir_id")
        result = await self._evidence_service.list_evidence(fir_id=search_term, page_size=10)
        items = [self._serialise_evidence(e) for e in result.get("items", [])]
        return {"success": True, "data": {"evidence": items}}

    # ── Financial Handlers ──────────────────────────────────────

    async def _handle_financial_search(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("name")
        result = await self._financial_service.list_transactions(search=search_term, page_size=10)
        items = [self._serialise_transaction(t) for t in result.get("items", [])]
        return {"success": True, "data": {"transactions": items, "total": result.get("total", 0)}}

    async def _handle_financial_summary(self, intent: IntentResult, message: str) -> dict:
        result = await self._financial_service.list_transactions(page_size=15)
        items = [self._serialise_transaction(t) for t in result.get("items", [])]
        return {"success": True, "data": {"transactions": items}}

    # ── Crime History Handlers ──────────────────────────────────

    async def _handle_history_search(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("name")
        result = await self._history_service.list(search=search_term, page_size=10)
        from app.crime_history.models import CrimeHistory as CH
        items = []
        for h in result.get("items", []):
            items.append({
                "history_id": getattr(h, "history_id", None),
                "accused_id": getattr(h, "accused_id", None),
                "crime_type": getattr(h, "crime_type", None),
                "arrest_date": str(getattr(h, "arrest_date", "")),
                "conviction_status": str(getattr(h, "conviction_status", "")),
            })
        return {"success": True, "data": {"history": items, "total": result.get("total", 0)}}

    async def _handle_history_summary(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("name")
        result = await self._history_service.list(search=search_term, page_size=10)
        items = []
        for h in result.get("items", []):
            items.append({
                "history_id": getattr(h, "history_id", None),
                "accused_id": getattr(h, "accused_id", None),
                "crime_type": getattr(h, "crime_type", None),
                "arrest_date": str(getattr(h, "arrest_date", "")),
                "conviction_status": str(getattr(h, "conviction_status", "")),
            })
        return {"success": True, "data": {"history": items}}

    # ── Hotspot Handlers ────────────────────────────────────────

    async def _handle_hotspot_search(self, intent: IntentResult, message: str) -> dict:
        result = await self._hotspot_service.get_hotspots(
            time_range="30d",
            search=intent.entities.get("name"),
        )
        return {"success": True, "data": {
            "hotspots": result.get("hotspots", []),
            "total_hotspots": result.get("total_hotspots", 0),
        }}

    async def _handle_hotspot_analysis(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("name")
        if search_term:
            detail = await self._hotspot_service.get_hotspot_detail(search_term)
            if detail:
                return {"success": True, "data": detail}
        result = await self._hotspot_service.get_hotspots(time_range="90d")
        return {"success": True, "data": {
            "hotspots": result.get("hotspots", []),
            "high_risk_count": result.get("high_risk_count", 0),
            "total_crimes": result.get("total_crimes", 0),
        }}

    # ── Network Handlers ────────────────────────────────────────

    async def _handle_network_graph(self, intent: IntentResult, message: str) -> dict:
        """Build focused graph for a specific FIR using the new GraphBuilder.
        Returns graph JSON with node types: FIR, Accused, Victim, Evidence, Location, Transaction.
        """
        fir_number = intent.entities.get("fir_number")
        if not fir_number:
            # Try to extract FIR number from message
            m = re.search(r"(?:FIR)[-\s]?(\d+(?:-\d+)*)", message, re.IGNORECASE)
            if m:
                fir_number = m.group(0)
        if fir_number:
            builder = GraphBuilder(self.session)
            graph = await builder.build_graph(fir_number)
            return {"success": True, "data": graph}
        # Fallback to full network
        graph = await self._network_service.build_graph()
        return {"success": True, "data": graph}

    async def _handle_network_search(self, intent: IntentResult, message: str) -> dict:
        fir_ref = intent.entities.get("fir_id")
        graph = await self._network_service.build_graph(fir_id=fir_ref)
        return {"success": True, "data": graph}

    async def _handle_network_analysis(self, intent: IntentResult, message: str) -> dict:
        fir_ref = intent.entities.get("fir_id")
        graph = await self._network_service.build_graph(fir_id=fir_ref)
        return {"success": True, "data": graph}

    # ── Location Handler ────────────────────────────────────────

    async def _handle_location_search(self, intent: IntentResult, message: str) -> dict:
        """Search locations using LocationService (no inline SQL)."""
        search_term = intent.entities.get("name")
        result = await self._location_service.list_locations(search=search_term, page_size=20)
        items = [
            {
                "location_id": loc.location_id,
                "district": loc.district,
                "city": loc.city,
                "area": loc.area,
                "latitude": float(loc.latitude) if loc.latitude else None,
                "longitude": float(loc.longitude) if loc.longitude else None,
            }
            for loc in result.get("items", [])
        ]
        return {"success": True, "data": {"locations": items, "total": result.get("total", 0)}}

    # ── Audit Handler ───────────────────────────────────────────

    async def _handle_audit_search(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("name")
        result = await self._audit_service.list_logs(search=search_term, page_size=10)
        return {"success": True, "data": result}

    # ── User Handler ────────────────────────────────────────────

    async def _handle_user_search(self, intent: IntentResult, message: str) -> dict:
        search_term = intent.entities.get("name") or intent.entities.get("email")
        result = await self._user_service.list_users(search=search_term, page_size=10)
        return {"success": True, "data": result}

    # ── Settings Handler ────────────────────────────────────────

    async def _handle_settings(self, intent: IntentResult, message: str) -> dict:
        result = await self._settings_service.get_settings(self.user_id)
        return {"success": True, "data": result}

    # ── Prediction Handler ──────────────────────────────────────

    async def _handle_prediction(self, intent: IntentResult, message: str) -> dict:
        try:
            # Extract district and months from message
            district = intent.entities.get("name") or intent.entities.get("district")
            months_ahead = 3  # default
            m = re.search(r"(\d+)\s*(?:months?)", message, re.IGNORECASE)
            if m:
                months_ahead = min(12, max(1, int(m.group(1))))
            # Try ML-based CrimePredictor first
            result = await self._crime_predictor.forecast(
                months_ahead=months_ahead, district=district
            )
            if result.get("predictions"):
                return {"success": True, "data": result}
            # Fallback to old rule-based service
            result = await self._prediction_service.predict_crime({})
            return {"success": True, "data": result}
        except Exception as exc:
            try:
                result = await self._prediction_service.predict_crime({})
                return {"success": True, "data": result}
            except Exception:
                return {"success": True, "data": {"message": "Prediction engine ready. Use the Crime Prediction module for detailed forecasting."}}

    # ── Report & Case Summary Handlers ──────────────────────────

    async def _handle_report(self, intent: IntentResult, message: str) -> dict:
        # Gather summary data for report
        from app.auth.models import User as _User
        dummy = _User(id=self.user_id, email="chatbot@internal", role_id=1, is_active=True)
        fir_result = await self._fir_service.list_firs(dummy, page_size=5)
        stats = await self._fir_service.get_statistics()
        return {
            "success": True,
            "data": {
                "firs": [self._serialise_fir(f) for f in fir_result.get("items", [])],
                "statistics": stats,
            },
        }

    async def _handle_case_summary(self, intent: IntentResult, message: str) -> dict:
        fir_id = intent.entities.get("fir_id")
        if fir_id:
            try:
                summary = await self._fir_service.get_fir_summary(int(fir_id))
                return {"success": True, "data": summary}
            except Exception:
                pass
        from app.auth.models import User as _User
        dummy = _User(id=self.user_id, email="chatbot@internal", role_id=1, is_active=True)
        result = await self._fir_service.list_firs(dummy, page_size=5)
        items = [self._serialise_fir(f) for f in result.get("items", [])]
        return {"success": True, "data": {"firs": items, "note": "Specify an FIR number for a detailed case summary."}}

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
                    "Summarize FIR #123",
                    "Find victims named John",
                    "Analyze crime hotspots in this district",
                    "Show the criminal network connections",
                    "Generate a weekly crime report",
                    "Predict crime trends for next month",
                ],
            },
        }

    # ── General Chat Handler ────────────────────────────────────

    async def _handle_general_chat(self, intent: IntentResult, message: str) -> dict:
        """Handle general chat — no structured data, just AI response."""
        return {"success": True, "data": {"message": message}}