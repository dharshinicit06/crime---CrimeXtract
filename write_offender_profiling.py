"""Create all Offender Profiling module Python files."""

import os

os.makedirs("app/offender_profiling", exist_ok=True)

# __init__.py
with open("app/offender_profiling/__init__.py", "w") as f:
    f.write('"""Offender Profiling Module — modular risk assessment and profiling."""\n\n__all__ = []\n')

# schemas.py
schemas = r'''"""Pydantic schemas for Offender Profiling responses."""

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field


class ScorerResult(BaseModel):
    """Output from a single modular scorer."""
    name: str = Field(..., description="Scorer name (e.g. 'crime_frequency', 'gang_affiliation')")
    weight: float = Field(..., description="Weight assigned to this scorer (0.0 - 1.0)")
    raw_score: float = Field(..., description="Raw computed value before normalization")
    normalized_score: float = Field(..., description="Normalized contribution (0 - 100)")
    reasoning: str = Field(..., description="Human-readable explanation for this score")


class CrimeFrequencyInfo(BaseModel):
    """Crime frequency breakdown."""
    total_firs: int = Field(0, description="Total FIRs linked to this offender")
    total_crime_history: int = Field(0, description="Total crime history records")
    unique_crime_categories: list[str] = Field(default_factory=list, description="Distinct crime types")
    first_offense_date: Optional[date] = Field(None, description="Date of first known offense")
    last_offense_date: Optional[date] = Field(None, description="Date of most recent offense")
    months_active: Optional[int] = Field(None, description="Span in months between first and last offense")


class GangLinkInfo(BaseModel):
    """Gang affiliation details extracted from records."""
    raw_gang_links: Optional[str] = Field(None, description="Raw gang_links field from Accused record")
    gangs_mentioned: list[str] = Field(default_factory=list, description="Parsed gang names")
    has_gang_affiliation: bool = Field(False, description="Whether any gang links were found")


class PreviousFirInfo(BaseModel):
    """Summary of a linked FIR."""
    fir_id: str
    fir_number: str
    title: str
    status: str
    role: Optional[str] = None
    incident_date: Optional[date] = None
    crime_category: Optional[str] = None


class OffenderProfile(BaseModel):
    """Complete offender profiling response."""
    accused_id: str
    name: str
    alias: Optional[str] = None
    is_active: bool = True

    # Risk score (0-100, composite)
    risk_score: float = Field(..., description="Composite risk score (0-100)")
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")

    # Breakdown
    crime_frequency: CrimeFrequencyInfo = Field(default_factory=CrimeFrequencyInfo)
    crime_categories: list[str] = Field(default_factory=list)
    previous_firs: list[PreviousFirInfo] = Field(default_factory=list)
    gang_links: GangLinkInfo = Field(default_factory=GangLinkInfo)

    # Modular scoring detail
    scorer_results: list[ScorerResult] = Field(default_factory=list, description="Results from each modular scorer")
    reasoning_summary: str = Field(..., description="Consolidated reasoning for the risk assessment")
'''

with open("app/offender_profiling/schemas.py", "w") as f:
    f.write(schemas)

# scorers.py
scorers = r'''"""Modular scoring components for offender risk assessment.

Each scorer is a standalone class implementing a `ScorerInterface`:
    - name: str (class attribute)
    - weight: float
    - async compute(accused_id, session) -> ScorerResult
"""

import math
from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.models import Accused, FIRAccusedLink
from app.crime.models import Crime
from app.crime_history.models import CrimeHistory, Disposition
from app.fir.models import FIR, CrimeCategory, CrimeCategorySeverity, FirStatus


class ScorerInterface(ABC):
    """Abstract base for all risk scorers."""

    name: str = ""
    weight: float = 1.0

    @abstractmethod
    async def compute(
        self, accused_id: str, session: AsyncSession
    ) -> dict[str, Any]:
        """Compute a score contribution and return result dict."""
        ...


class CrimeFrequencyScorer(ScorerInterface):
    """Scores based on the total number of FIRs and crime history records."""

    name = "crime_frequency"
    weight = 0.25

    async def compute(self, accused_id: str, session: AsyncSession) -> dict[str, Any]:
        fir_q = select(func.count(FIRAccusedLink.id)).where(
            FIRAccusedLink.accused_id == accused_id
        )
        hist_q = select(func.count(CrimeHistory.id)).where(
            CrimeHistory.accused_id == accused_id
        )
        fir_count = (await session.execute(fir_q)).scalar() or 0
        hist_count = (await session.execute(hist_q)).scalar() or 0
        total = fir_count + hist_count

        # Score: 0 for no crimes, up to 100 for 10+ crimes (logarithmic)
        if total == 0:
            raw = 0.0
            reason = "No known criminal records."
        else:
            raw = min(100, math.log2(total + 1) * 20)
            reason = (
                f"Linked to {fir_count} FIR(s) and {hist_count} historical "
                f"record(s) — total {total} offense(s)."
            )

        return {
            "name": self.name,
            "weight": self.weight,
            "raw_score": round(raw, 2),
            "normalized_score": round(raw * self.weight, 2),
            "reasoning": reason,
        }


class CrimeSeverityScorer(ScorerInterface):
    """Scores based on severity of crime categories involved."""

    name = "crime_severity"
    weight = 0.20

    _SEVERITY_MAP = {
        CrimeCategorySeverity.PETTY: 20,
        CrimeCategorySeverity.LESS_SERIOUS: 40,
        CrimeCategorySeverity.SERIOUS: 70,
        CrimeCategorySeverity.HEINOUS: 100,
    }

    async def compute(self, accused_id: str, session: AsyncSession) -> dict[str, Any]:
        from sqlalchemy import select as sel

        # Get FIRs linked to this accused
        fir_ids_subq = (
            sel(FIRAccusedLink.fir_id)
            .where(FIRAccusedLink.accused_id == accused_id)
            .subquery()
        )
        q = (
            sel(CrimeCategory.severity)
            .select_from(FIR)
            .join(CrimeCategory, FIR.crime_category_id == CrimeCategory.id)
            .where(FIR.id.in_(sel(fir_ids_subq)))
            .distinct()
        )
        r = await session.execute(q)
        severities = [row[0] for row in r.all()]

        if not severities:
            return {
                "name": self.name,
                "weight": self.weight,
                "raw_score": 0.0,
                "normalized_score": 0.0,
                "reasoning": "No linked FIRs to evaluate crime severity.",
            }

        max_sev = max(severities, key=lambda s: self._SEVERITY_MAP.get(s, 0))
        raw = float(self._SEVERITY_MAP.get(max_sev, 0))
        sev_names = ", ".join(s.value for s in set(severities))
        reason = (
            f"Crime severity levels involved: {sev_names}. "
            f"Highest severity: {max_sev.value}."
        )

        return {
            "name": self.name,
            "weight": self.weight,
            "raw_score": raw,
            "normalized_score": round(raw * self.weight, 2),
            "reasoning": reason,
        }


class RecencyScorer(ScorerInterface):
    """Scores based on how recent the criminal activity is."""

    name = "recency"
    weight = 0.20

    async def compute(self, accused_id: str, session: AsyncSession) -> dict[str, Any]:
        today = date.today()

        # Check in FIRs via links
        fir_q = (
            select(func.max(FIR.incident_date))
            .select_from(FIRAccusedLink)
            .join(FIR, FIRAccusedLink.fir_id == FIR.id)
            .where(FIRAccusedLink.accused_id == accused_id)
        )
        r = await session.execute(fir_q)
        latest_fir_date = r.scalar()

        # Check in crime history
        hist_q = (
            select(func.max(CrimeHistory.crime_date))
            .where(CrimeHistory.accused_id == accused_id)
        )
        r = await session.execute(hist_q)
        latest_hist_date = r.scalar()

        candidates = [d for d in [latest_fir_date, latest_hist_date] if d is not None]
        if not candidates:
            return {
                "name": self.name,
                "weight": self.weight,
                "raw_score": 0.0,
                "normalized_score": 0.0,
                "reasoning": "No offense dates available.",
            }

        latest = max(candidates)
        days_since = (today - latest).days

        # Score decreases with time: 100 (today) -> 0 (5+ years ago)
        raw = max(0, 100 - (days_since / 365.25) * 20)

        reason = (
            f"Most recent offense was {days_since} day(s) ago "
            f"({latest.isoformat()}). "
            f"{'Recent activity indicates active threat.' if days_since < 365 else 'No recent activity.'}"
        )

        return {
            "name": self.name,
            "weight": self.weight,
            "raw_score": round(raw, 2),
            "normalized_score": round(raw * self.weight, 2),
            "reasoning": reason,
        }


class GangAffiliationScorer(ScorerInterface):
    """Scores based on gang links present in the accused record."""

    name = "gang_affiliation"
    weight = 0.20

    async def compute(self, accused_id: str, session: AsyncSession) -> dict[str, Any]:
        accused = await session.get(Accused, accused_id)
        if not accused or not accused.gang_links:
            return {
                "name": self.name,
                "weight": self.weight,
                "raw_score": 0.0,
                "normalized_score": 0.0,
                "reasoning": "No gang affiliations recorded.",
            }

        # Score based on how many gangs are mentioned
        gang_text = accused.gang_links.lower()
        gang_list = [g.strip() for g in accused.gang_links.split(",") if g.strip()]
        num_gangs = len(gang_list)

        raw = min(100, num_gangs * 30)  # 1 gang = 30, 2 = 60, 3+ = 90-100
        reason = (
            f"Gang affiliation detected: {accused.gang_links}. "
            f"{num_gangs} gang(s) mentioned."
        )

        return {
            "name": self.name,
            "weight": self.weight,
            "raw_score": round(raw, 2),
            "normalized_score": round(raw * self.weight, 2),
            "reasoning": reason,
        }


class RepeatOffenderScorer(ScorerInterface):
    """Scores based on repeat offense flags in crime history."""

    name = "repeat_offender"
    weight = 0.15

    async def compute(self, accused_id: str, session: AsyncSession) -> dict[str, Any]:
        q = select(CrimeHistory).where(CrimeHistory.accused_id == accused_id)
        r = await session.execute(q)
        records = list(r.scalars().all())

        repeat_count = sum(1 for rec in records if rec.is_repeat_offense)
        conviction_count = sum(
            1 for rec in records if rec.disposition == Disposition.CONVICTED
        )
        total = len(records)

        if total == 0:
            return {
                "name": self.name,
                "weight": self.weight,
                "raw_score": 0.0,
                "normalized_score": 0.0,
                "reasoning": "No crime history records.",
            }

        # Score components: repeat ratio + conviction ratio
        repeat_ratio = repeat_count / total if total > 0 else 0
        convict_ratio = conviction_count / total if total > 0 else 0
        raw = (repeat_ratio * 60) + (convict_ratio * 40)

        reasons = []
        if repeat_count > 0:
            reasons.append(f"{repeat_count} of {total} records flagged as repeat offense(s)")
        if conviction_count > 0:
            reasons.append(f"{conviction_count} prior conviction(s)")
        if not reasons:
            reasons.append("No repeat offense flags or convictions on record")

        return {
            "name": self.name,
            "weight": self.weight,
            "raw_score": round(raw, 2),
            "normalized_score": round(raw * self.weight, 2),
            "reasoning": "; ".join(reasons),
        }


# Registry of all available scorers
DEFAULT_SCORERS: list[ScorerInterface] = [
    CrimeFrequencyScorer(),
    CrimeSeverityScorer(),
    RecencyScorer(),
    GangAffiliationScorer(),
    RepeatOffenderScorer(),
]
'''

with open("app/offender_profiling/scorers.py", "w") as f:
    f.write(scorers)

# services.py
services = r'''"""Offender Profiling service — orchestrates modular scorers and compiles profiles."""

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.accused.models import Accused, FIRAccusedLink
from app.crime.models import Crime
from app.crime_history.models import CrimeHistory
from app.exceptions.handlers import NotFoundException
from app.fir.models import FIR, CrimeCategory
from app.logging import get_logger
from app.offender_profiling.scorers import DEFAULT_SCORERS

logger = get_logger(__name__)


class OffenderProfilingService:
    """Orchestrates modular scoring to produce a comprehensive offender profile."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_profile(self, accused_id: str) -> dict[str, Any]:
        """Build a complete offender profile for the given accused ID."""
        # 1. Load accused with links
        accused = await self.session.get(Accused, accused_id)
        if not accused:
            raise NotFoundException(
                message=f"Accused '{accused_id}' not found",
                error_code="ACCUSED_NOT_FOUND",
            )

        # 2. Run all modular scorers
        scorer_results = []
        total_weighted = 0.0
        total_weight = 0.0

        for scorer in DEFAULT_SCORERS:
            result = await scorer.compute(accused_id, self.session)
            scorer_results.append(result)
            total_weighted += result["normalized_score"]
            total_weight += scorer.weight

        # Composite risk score (0-100)
        risk_score = round(total_weighted, 2)
        if risk_score >= 75:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"

        # 3. Crime frequency breakdown
        fir_q = select(FIRAccusedLink).where(
            FIRAccusedLink.accused_id == accused_id
        )
        r = await self.session.execute(fir_q)
        fir_links = list(r.scalars().all())
        fir_ids = [l.fir_id for l in fir_links]
        fir_ids_set = set(fir_ids)

        fir_details = []
        crime_cats: set[str] = set()
        if fir_ids_set:
            r = await self.session.execute(
                select(FIR)
                .options(selectinload(FIR.crime_category))
                .where(FIR.id.in_(fir_ids_set))
            )
            firs = list(r.scalars().all())
            fir_map = {f.id: f for f in firs}
            for link in fir_links:
                fir = fir_map.get(link.fir_id)
                if fir:
                    fir_details.append({
                        "fir_id": fir.id,
                        "fir_number": fir.fir_number,
                        "title": fir.title,
                        "status": fir.status.value if hasattr(fir.status, "value") else str(fir.status),
                        "role": link.role,
                        "incident_date": fir.incident_date,
                        "crime_category": fir.crime_category.name if fir.crime_category else None,
                    })
                    if fir.crime_category:
                        crime_cats.add(fir.crime_category.name)

        # Crime history records
        hist_q = select(CrimeHistory).where(CrimeHistory.accused_id == accused_id)
        r = await self.session.execute(hist_q)
        hist_records = list(r.scalars().all())
        hist_offense_types = set(h.offense_type for h in hist_records)
        crime_cats.update(hist_offense_types)

        crime_freq = {
            "total_firs": len(fir_ids_set),
            "total_crime_history": len(hist_records),
            "unique_crime_categories": sorted(crime_cats),
            "first_offense_date": None,
            "last_offense_date": None,
            "months_active": None,
        }

        all_dates = []
        for h in hist_records:
            all_dates.append(h.crime_date)
        for f in firs:
            if hasattr(f, "incident_date") and f.incident_date:
                all_dates.append(f.incident_date)

        if all_dates:
            crime_freq["first_offense_date"] = min(all_dates)
            crime_freq["last_offense_date"] = max(all_dates)
            delta = max(all_dates) - min(all_dates)
            crime_freq["months_active"] = delta.days // 30

        # 4. Gang links
        gang_info = {
            "raw_gang_links": accused.gang_links,
            "gangs_mentioned": (
                [g.strip() for g in accused.gang_links.split(",") if g.strip()]
                if accused.gang_links else []
            ),
            "has_gang_affiliation": bool(accused.gang_links),
        }

        # 5. Reasoning summary
        reasoning_parts = []
        for sr in scorer_results:
            reasoning_parts.append(f"[{sr['name']}] {sr['reasoning']}")
        reasoning_summary = " | ".join(reasoning_parts)

        logger.info(
            "Offender profile built for %s (%s): risk_score=%.1f, level=%s",
            accused.name, accused_id, risk_score, risk_level,
        )

        return {
            "accused_id": accused.id,
            "name": accused.name,
            "alias": accused.alias,
            "is_active": accused.is_active,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "crime_frequency": crime_freq,
            "crime_categories": sorted(crime_cats),
            "previous_firs": fir_details,
            "gang_links": gang_info,
            "scorer_results": scorer_results,
            "reasoning_summary": reasoning_summary,
        }
'''

with open("app/offender_profiling/services.py", "w") as f:
    f.write(services)

# router.py
router = r'''"""Offender Profiling API endpoint — returns comprehensive risk profile."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_db_session
from app.auth.models import User
from app.offender_profiling.schemas import OffenderProfile
from app.offender_profiling.services import OffenderProfilingService

router = APIRouter(prefix="/offender", tags=["offender-profiling"])


def get_profiling_service(
    session: AsyncSession = Depends(get_db_session),
) -> OffenderProfilingService:
    return OffenderProfilingService(session=session)


@router.get(
    "/{accused_id}",
    response_model=OffenderProfile,
    summary="Get offender risk profile",
    responses={
        404: {"description": "Accused not found"},
    },
)
async def get_offender_profile(
    accused_id: str,
    current_user: User = Depends(get_current_user),
    service: OffenderProfilingService = Depends(get_profiling_service),
) -> OffenderProfile:
    """Build and return a comprehensive offender risk profile.

    Combines multiple modular scorers (crime frequency, severity, recency,
    gang affiliation, repeat offender) into a single composite risk score
    (0-100) with detailed reasoning for each component.
    """
    return await service.get_profile(accused_id=accused_id)
'''

with open("app/offender_profiling/router.py", "w") as f:
    f.write(router)

print("All Offender Profiling files created OK")
