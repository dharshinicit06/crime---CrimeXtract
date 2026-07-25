"""Tool layer — wraps existing backend services for the CrimeAI chatbot.

Each tool function calls the corresponding service and returns a
serialisable dict that can be passed to Gemini for summarisation.
"""

import time
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.services import AccusedService
from app.crime_analytics.services import CrimeAnalyticsService
from app.fir.services import FIRService
from app.logging import get_logger
from app.ml.services import predict_cases
from app.network_analysis.services import NetworkAnalysisService
from app.offender_profiling.services import OffenderProfilingService

logger = get_logger(__name__)


class ChatTools:
    """Calls existing backend services on behalf of the chatbot.

    Each method returns a dict with at minimum a ``success`` boolean
    and either ``data`` or ``error``.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._fir_service = FIRService(session)
        self._analytics_service = CrimeAnalyticsService(session)
        self._network_service = NetworkAnalysisService(session)
        self._offender_service = OffenderProfilingService(session)
        self._accused_service = AccusedService(session)

    # ── FIR tools ───────────────────────────────────────────────

    async def get_fir_data(self, fir_id: Optional[str] = None, search: Optional[str] = None) -> dict[str, Any]:
        """Retrieve FIR data by ID or search term."""
        start = time.monotonic()
        try:
            if fir_id:
                fir = await self._fir_service.get_fir(fir_id)
                result = {"success": True, "data": self._serialise_fir(fir)}
            elif search:
                from app.auth.models import User as _User
                dummy = _User(id=0, email="chatbot@internal", role_id=1, is_active=True)
                paginated = await self._fir_service.list_firs(dummy, search=search, page_size=5)
                result = {
                    "success": True,
                    "data": {
                        "firs": [self._serialise_fir(f) for f in paginated.get("items", [])],
                        "total": paginated.get("total", 0),
                    },
                }
            else:
                result = {"success": False, "error": "Provide fir_id or search term"}
        except Exception as exc:
            logger.warning("FIR tool failed", extra={"error": str(exc)})
            result = {"success": False, "error": f"FIR data unavailable: {exc}"}

        elapsed = time.monotonic() - start
        logger.debug("get_fir_data took %.0fms", elapsed * 1000)
        return result

    # ── Analytics tools ─────────────────────────────────────────

    async def get_crime_statistics(self) -> dict[str, Any]:
        """Aggregate crime summary statistics."""
        start = time.monotonic()
        try:
            data = await self._analytics_service.summary()
            result = {"success": True, "data": data}
        except Exception as exc:
            logger.warning("Analytics summary tool failed", extra={"error": str(exc)})
            result = {"success": False, "error": f"Statistics unavailable: {exc}"}
        elapsed = time.monotonic() - start
        logger.debug("get_crime_statistics took %.0fms", elapsed * 1000)
        return result

    async def get_hotspots(self, limit: int = 5) -> dict[str, Any]:
        """Top crime hotspot districts."""
        start = time.monotonic()
        try:
            data = await self._analytics_service.top_hotspots(limit=limit)
            result = {"success": True, "data": data}
        except Exception as exc:
            logger.warning("Hotspots tool failed", extra={"error": str(exc)})
            result = {"success": False, "error": f"Hotspot data unavailable: {exc}"}
        elapsed = time.monotonic() - start
        logger.debug("get_hotspots took %.0fms", elapsed * 1000)
        return result

    async def get_crime_by_type(self) -> dict[str, Any]:
        """FIRs grouped by crime type."""
        try:
            data = await self._analytics_service.crime_by_type()
            return {"success": True, "data": data}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def get_solved_vs_pending(self) -> dict[str, Any]:
        """Solved vs pending case breakdown."""
        try:
            data = await self._analytics_service.solved_vs_pending()
            return {"success": True, "data": data}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ── Network Analysis tool ───────────────────────────────────

    async def get_network(self, fir_id: Optional[str] = None) -> dict[str, Any]:
        """Criminal network graph data, optionally scoped to an FIR."""
        start = time.monotonic()
        try:
            data = await self._network_service.build_graph(fir_id=fir_id)
            result = {"success": True, "data": data}
        except Exception as exc:
            logger.warning("Network tool failed", extra={"error": str(exc)})
            result = {"success": False, "error": f"Network data unavailable: {exc}"}
        elapsed = time.monotonic() - start
        logger.debug("get_network took %.0fms", elapsed * 1000)
        return result

    # ── Offender Profiling tool ─────────────────────────────────

    async def get_offender_profile(self, accused_id: str) -> dict[str, Any]:
        """Risk profile for a given accused/offender."""
        start = time.monotonic()
        try:
            data = await self._offender_service.get_profile(accused_id)
            result = {"success": True, "data": data}
        except Exception as exc:
            logger.warning("Offender profile tool failed", extra={"error": str(exc)})
            result = {"success": False, "error": f"Offender profile unavailable: {exc}"}
        elapsed = time.monotonic() - start
        logger.debug("get_offender_profile took %.0fms", elapsed * 1000)
        return result

    # ── ML Prediction tool ──────────────────────────────────────

    async def predict_crime(self, **kwargs: Any) -> dict[str, Any]:
        """Run ML model to predict crime case count."""
        start = time.monotonic()
        try:
            predicted = predict_cases(**kwargs)
            result = {"success": True, "data": {"predicted_cases": predicted}}
        except Exception as exc:
            logger.warning("ML prediction tool failed", extra={"error": str(exc)})
            result = {"success": False, "error": f"Prediction unavailable: {exc}"}
        elapsed = time.monotonic() - start
        logger.debug("predict_crime took %.0fms", elapsed * 1000)
        return result

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _serialise_fir(fir: Any) -> dict[str, Any]:
        """Convert a FIR ORM object to a plain dict for Gemini context."""
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
        }
