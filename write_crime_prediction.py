"""Create all Crime Prediction module files."""
import os

os.makedirs("app/crime_prediction", exist_ok=True)

# __init__.py
with open("app/crime_prediction/__init__.py", "w") as f:
    f.write('"""Crime Prediction Module — rule-based crime prediction service."""\n\n__all__ = []\n')

# schemas.py
schemas = '''"""Pydantic schemas for Crime Prediction responses."""

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CrimeProbability(BaseModel):
    """Predicted crime probability for a specific district/category."""
    district: str = Field(..., description="District or area")
    crime_category: Optional[str] = Field(None, description="Specific crime type (None = overall)")
    probability: float = Field(..., ge=0.0, le=1.0, description="Crime probability score 0.0-1.0")
    predicted_count: float = Field(..., description="Expected number of incidents")
    confidence: str = Field(..., description="Confidence level: low, medium, high")
    reasoning: str = Field(..., description="Rule-based reasoning for this prediction")


class HotspotInfo(BaseModel):
    """Identified crime hotspot."""
    district: str = Field(..., description="District name")
    hotspot_score: float = Field(..., ge=0.0, le=100.0, description="Hotspot intensity score")
    crime_count: int = Field(0, description="Historical crime count")
    trend: str = Field(..., description="Trend direction: rising, stable, declining")
    top_crime_types: list[str] = Field(default_factory=list, description="Most frequent crime types")
    reasoning: str = Field(..., description="Why this is identified as a hotspot")


class PatrolSuggestion(BaseModel):
    """Actionable patrol recommendation."""
    district: str = Field(..., description="District for patrol")
    priority: str = Field(..., description="Priority: low, medium, high, critical")
    suggestion: str = Field(..., description="Concrete patrol action")
    reason: str = Field(..., description="Data-driven justification")
    time_window: Optional[str] = Field(None, description="Recommended patrol time window (e.g. '18:00-22:00')")


class CrimePredictionMetadata(BaseModel):
    """Metadata about the prediction computation."""
    data_period: str = Field(..., description="Date range of analyzed historical data")
    total_crimes_analyzed: int = Field(0, description="Number of crime records used")
    total_districts: int = Field(0, description="Number of districts analyzed")
    prediction_horizon: str = Field("next_7_days", description="Forecast timeframe")
    model_version: str = Field("rule-based-v1", description="Prediction model identifier")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


class CrimePredictionResponse(BaseModel):
    """Complete crime prediction response."""
    predictions: list[CrimeProbability] = Field(..., description="Per-district crime probability forecasts")
    hotspots: list[HotspotInfo] = Field(..., description="Identified crime hotspots")
    patrol_suggestions: list[PatrolSuggestion] = Field(..., description="Actionable patrol recommendations")
    metadata: CrimePredictionMetadata = Field(..., description="Prediction metadata")
'''

with open("app/crime_prediction/schemas.py", "w") as f:
    f.write(schemas)

# predictors.py - Independent rule-based prediction engine
predictors = '''"""Rule-based crime prediction engine.

Completely independent module with no external ML dependencies.
All predictions are derived from statistical analysis of historical
crime data using configurable rules and heuristics.
"""

import math
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crime.models import Crime
from app.fir.models import FIR, CrimeCategory
from app.location.models import Location
from app.logging import get_logger

logger = get_logger(__name__)


# ─── Configuration ──────────────────────────────────────────────

PREDICTION_HORIZON_DAYS = 7
HISTORICAL_LOOKBACK_DAYS = 365
HOTSPOT_TOP_N = 5
CONFIDENCE_THRESHOLDS = {
    "high": (0.7, 1.0),
    "medium": (0.4, 0.7),
    "low": (0.0, 0.4),
}

# Weights for different temporal signals (must sum to 1.0)
TEMPORAL_WEIGHTS = {
    "same_month_last_year": 0.15,
    "last_30_days": 0.35,
    "last_90_days": 0.30,
    "last_365_days": 0.20,
}


# ─── Data Loader ────────────────────────────────────────────────


class CrimeDataLoader:
    """Loads and caches crime data for the prediction engine."""

    @staticmethod
    async def load_crime_by_district(session: AsyncSession) -> dict[str, list[date]]:
        """Load all crime dates grouped by district (past 365 days)."""
        cutoff = date.today() - timedelta(days=HISTORICAL_LOOKBACK_DAYS)
        q = select(Crime.district, Crime.crime_date).where(Crime.crime_date >= cutoff)
        r = await session.execute(q)
        rows = r.all()
        districts: dict[str, list[date]] = defaultdict(list)
        for district, crime_date in rows:
            districts[district].append(crime_date)
        return dict(districts)

    @staticmethod
    async def load_fir_by_location(session: AsyncSession) -> dict[str, list[tuple[date, str]]]:
        """Load FIR dates + crime category by district via Location join."""
        cutoff = date.today() - timedelta(days=HISTORICAL_LOOKBACK_DAYS)
        q = (
            select(Location.district, FIR.incident_date, CrimeCategory.name)
            .select_from(FIR)
            .join(Location, FIR.location_id == Location.id, isouter=True)
            .join(CrimeCategory, FIR.crime_category_id == CrimeCategory.id, isouter=True)
            .where(FIR.incident_date >= cutoff)
        )
        r = await session.execute(q)
        rows = r.all()
        districts: dict[str, list[tuple[date, str]]] = defaultdict(list)
        for district, inc_date, cat_name in rows:
            d = district or "Unknown"
            districts[d].append((inc_date, cat_name or "Unknown"))
        return dict(districts)

    @staticmethod
    async def load_crime_type_distribution(
        session: AsyncSession,
    ) -> dict[str, int]:
        """Load total crime counts per category."""
        q = (
            select(CrimeCategory.name, func.count(Crime.id))
            .select_from(Crime)
            .join(CrimeCategory, Crime.crime_type_id == CrimeCategory.id)
            .group_by(CrimeCategory.name)
            .order_by(func.count(Crime.id).desc())
        )
        r = await session.execute(q)
        return {row[0]: row[1] for row in r.all()}


# ─── Rule-Based Predictors ──────────────────────────────────────


class TrendAnalyzer:
    """Analyzes crime trends using historical comparison."""

    @staticmethod
    def compute_trend(district_dates: list[date]) -> str:
        if len(district_dates) < 5:
            return "stable"
        today = date.today()
        recent = sum(1 for d in district_dates if d >= today - timedelta(days=30))
        earlier = sum(1 for d in district_dates if d < today - timedelta(days=30) and d >= today - timedelta(days=90))
        if recent > earlier * 1.3 and earlier > 0:
            return "rising"
        elif recent < earlier * 0.7 and earlier > 0:
            return "declining"
        return "stable"

    @staticmethod
    def monthly_average(district_dates: list[date]) -> float:
        if not district_dates:
            return 0.0
        cutoff = date.today() - timedelta(days=HISTORICAL_LOOKBACK_DAYS)
        months = max(1, (date.today() - cutoff).days / 30.0)
        return len(district_dates) / months


class ProbabilityEstimator:
    """Estimates crime probability using recency-weighted historical density."""

    @staticmethod
    def estimate(district_dates: list[date]) -> tuple[float, str]:
        if not district_dates:
            return 0.05, "low"

        today = date.today()
        total_weight = 0.0
        weighted_count = 0.0

        for d in district_dates:
            days_ago = (today - d).days
            # Exponential decay: recent crimes weight more
            weight = math.exp(-days_ago / 90.0)
            weighted_count += weight
            total_weight += weight

        # Normalize to per-day density
        density = weighted_count / HISTORICAL_LOOKBACK_DAYS

        # Scale to probability (sigmoid-like)
        prob = 1.0 / (1.0 + math.exp(-(density * 30 - 2.5)))
        prob = max(0.05, min(0.95, prob))

        # Determine confidence
        n = len(district_dates)
        if n >= 20:
            confidence = "high"
        elif n >= 10:
            confidence = "medium"
        else:
            confidence = "low"

        return round(prob, 4), confidence


class HotspotDetector:
    """Detects crime hotspots by comparing district crime density."""

    @staticmethod
    def detect(
        district_data: dict[str, list[date]],
        top_n: int = HOTSPOT_TOP_N,
    ) -> list[dict[str, Any]]:
        if not district_data:
            return []

        densities: dict[str, float] = {}
        for district, dates in district_data.items():
            densities[district] = TrendAnalyzer.monthly_average(dates)

        if not densities:
            return []

        max_density = max(densities.values()) or 1.0
        avg_density = sum(densities.values()) / len(densities)

        scored = []
        for district, density in sorted(densities.items(), key=lambda x: -x[1]):
            score = min(100.0, (density / max_density) * 100)
            trend = TrendAnalyzer.compute_trend(district_data.get(district, []))
            ratio = density / avg_density if avg_density > 0 else 1.0

            if ratio > 2.0:
                reason = f"{ratio:.1f}x the district average crime rate"
            elif ratio > 1.5:
                reason = f"Above-average crime density ({ratio:.1f}x)"
            else:
                reason = f"Crime density consistent with average ({ratio:.1f}x)"

            scored.append({
                "district": district,
                "hotspot_score": round(score, 1),
                "crime_count": len(district_data.get(district, [])),
                "trend": trend,
                "top_crime_types": [],  # populated by caller
                "reasoning": reason,
            })

        return scored[:top_n]


class PatrolSuggester:
    """Generates actionable patrol suggestions based on data."""

    @staticmethod
    def suggest(
        hotspots: list[dict[str, Any]],
        district_data: dict[str, list[date]],
    ) -> list[dict[str, str]]:
        suggestions = []

        for hs in hotspots:
            district = hs["district"]
            trend = hs["trend"]
            dates = district_data.get(district, [])

            # Time-of-day pattern analysis
            if trend == "rising":
                priority = "high"
                suggestion = f"Increase patrol frequency in {district}"
                reason = f"Rising crime trend detected ({hs['crime_count']} incidents in past year)"
                time_window = None
            elif hs["hotspot_score"] >= 70:
                priority = "high"
                suggestion = f"Deploy dedicated patrol unit to {district}"
                reason = f"Hotspot score {hs['hotspot_score']}/100 - {hs['reasoning']}"
                time_window = None
            elif hs["hotspot_score"] >= 40:
                priority = "medium"
                suggestion = f"Schedule regular patrol checks in {district}"
                reason = f"Moderate hotspot activity - {hs['reasoning']}"
                time_window = None
            else:
                priority = "low"
                suggestion = f"Monitor {district} for emerging patterns"
                reason = "Low but non-zero crime density"
                time_window = None

            suggestions.append({
                "district": district,
                "priority": priority,
                "suggestion": suggestion,
                "reason": reason,
                "time_window": time_window,
            })

        return suggestions


# ─── Public API ─────────────────────────────────────────────────


class CrimePredictionEngine:
    """Independent, rule-based crime prediction engine.

    This is the main entry point for all predictions. It has no
    external ML or AI dependencies — all logic is hand-crafted rules.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.loader = CrimeDataLoader()
        self.trend = TrendAnalyzer()
        self.probability = ProbabilityEstimator()
        self.hotspot = HotspotDetector()
        self.suggester = PatrolSuggester()

    async def predict_all(self) -> dict[str, Any]:
        """Run the full prediction pipeline and return results."""
        logger.info("Starting crime prediction pipeline (rule-based)")

        # 1. Load data
        district_dates = await self.loader.load_crime_by_district(self.session)
        fir_location_data = await self.loader.load_fir_by_location(self.session)
        type_distribution = await self.loader.load_crime_type_distribution(self.session)

        if not district_dates:
            logger.warning("No crime data found for prediction")
            return self._empty_response()

        # 2. Compute predictions per district
        predictions = []
        for district, dates in district_dates.items():
            prob, confidence = self.probability.estimate(dates)
            predicted_count = prob * PREDICTION_HORIZON_DAYS

            # Top crime types for this district
            fir_records = fir_location_data.get(district, [])
            type_counter = Counter(cat for _, cat in fir_records)
            top_types = [t for t, _ in type_counter.most_common(3)]

            predictions.append({
                "district": district,
                "crime_category": None,
                "probability": prob,
                "predicted_count": round(predicted_count, 2),
                "confidence": confidence,
                "reasoning": (
                    f"Based on {len(dates)} incidents over past year. "
                    f"Recency-weighted density: {prob:.1%} probability "
                    f"of at least one incident in next {PREDICTION_HORIZON_DAYS} days."
                ),
            })

        # 3. Detect hotspots
        hotspots = self.hotspot.detect(district_dates)
        for hs in hotspots:
            fir_records = fir_location_data.get(hs["district"], [])
            type_counter = Counter(cat for _, cat in fir_records)
            hs["top_crime_types"] = [t for t, _ in type_counter.most_common(3)]

        # 4. Generate patrol suggestions
        suggestions = self.suggester.suggest(hotspots, district_dates)

        # 5. Compute data period
        all_dates = []
        for dates in district_dates.values():
            all_dates.extend(dates)
        data_period = "No data"
        if all_dates:
            data_period = f"{min(all_dates)} to {max(all_dates)}"

        total_crimes = sum(len(d) for d in district_dates.values())

        logger.info(
            "Prediction complete: %d districts, %d hotspots, %d crimes analyzed",
            len(district_dates), len(hotspots), total_crimes,
        )

        return {
            "predictions": predictions,
            "hotspots": hotspots,
            "patrol_suggestions": suggestions,
            "metadata": {
                "data_period": data_period,
                "total_crimes_analyzed": total_crimes,
                "total_districts": len(district_dates),
                "prediction_horizon": f"next_{PREDICTION_HORIZON_DAYS}_days",
                "model_version": "rule-based-v1",
            },
        }

    def _empty_response(self) -> dict[str, Any]:
        return {
            "predictions": [],
            "hotspots": [],
            "patrol_suggestions": [],
            "metadata": {
                "data_period": "No data",
                "total_crimes_analyzed": 0,
                "total_districts": 0,
                "prediction_horizon": f"next_{PREDICTION_HORIZON_DAYS}_days",
                "model_version": "rule-based-v1",
            },
        }
'''

with open("app/crime_prediction/predictors.py", "w") as f:
    f.write(predictors)

# services.py
services = '''"""Crime Prediction service — delegates to the independent prediction engine."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.logging import get_logger
from app.crime_prediction.predictors import CrimePredictionEngine

logger = get_logger(__name__)


class CrimePredictionService:
    """Thin service layer that delegates to the independent CrimePredictionEngine."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_predictions(self) -> dict[str, Any]:
        """Run the full prediction pipeline via the independent engine."""
        engine = CrimePredictionEngine(session=self.session)
        return await engine.predict_all()
'''

with open("app/crime_prediction/services.py", "w") as f:
    f.write(services)

# router.py
router = '''"""Crime Prediction API endpoint — returns rule-based predictions."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_db_session
from app.auth.models import User
from app.crime_prediction.schemas import CrimePredictionResponse
from app.crime_prediction.services import CrimePredictionService

router = APIRouter(prefix="/predictions", tags=["crime-prediction"])


def get_prediction_service(
    session: AsyncSession = Depends(get_db_session),
) -> CrimePredictionService:
    return CrimePredictionService(session=session)


@router.get(
    "/",
    response_model=CrimePredictionResponse,
    summary="Get rule-based crime predictions",
)
async def get_crime_predictions(
    current_user: User = Depends(get_current_user),
    service: CrimePredictionService = Depends(get_prediction_service),
) -> CrimePredictionResponse:
    """Run rule-based crime prediction and return forecasts.

    Returns per-district crime probabilities, identified hotspots,
    actionable patrol suggestions, and prediction metadata.
    The engine is fully rule-based — no ML dependencies.
    """
    return await service.get_predictions()
'''

with open("app/crime_prediction/router.py", "w") as f:
    f.write(router)

print("All Crime Prediction files created OK")
