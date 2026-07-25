"""Modular scoring components for offender risk assessment.

Each scorer is a standalone class implementing a `ScorerInterface`:
    - name: str (class attribute)
    - weight: float
    - async compute(accused_id, session) -> ScorerResult
"""

import math
from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.models import Accused, FIRAccusedLink
from app.crime.models import CrimeType, CrimeSeverity
from app.crime_history.models import CrimeHistory, ConvictionStatus
from app.fir.models import FIR


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
        fir_q = select(func.count(FIRAccusedLink.accused_id)).where(
            FIRAccusedLink.accused_id == accused_id
        )
        hist_q = select(func.count(CrimeHistory.history_id)).where(
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
                f"record(s) � total {total} offense(s)."
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
        CrimeSeverity.LOW: 20,
        CrimeSeverity.MEDIUM: 40,
        CrimeSeverity.HIGH: 70,
        CrimeSeverity.CRITICAL: 100,
    }

    async def compute(self, accused_id: str, session: AsyncSession) -> dict[str, Any]:
        # Get FIRs linked to this accused
        fir_ids_subq = (
            select(FIRAccusedLink.fir_id)
            .where(FIRAccusedLink.accused_id == accused_id)
            .subquery()
        )
        q = (
            select(CrimeType.severity)
            .select_from(FIR)
            .join(CrimeType, FIR.crime_type_id == CrimeType.crime_type_id)
            .where(FIR.fir_id.in_(fir_ids_subq))
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
            .join(FIR, FIRAccusedLink.fir_id == FIR.fir_id)
            .where(FIRAccusedLink.accused_id == accused_id)
        )
        r = await session.execute(fir_q)
        latest_fir_date = r.scalar()

        # Check in crime history (use arrest_date as the closest match to "crime date")
        hist_q = (
            select(func.max(CrimeHistory.arrest_date))
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
    """Scores based on repeat offender flag and address patterns in the accused record."""

    name = "gang_affiliation"
    weight = 0.20

    async def compute(self, accused_id: str, session: AsyncSession) -> dict[str, Any]:
        accused = await session.get(Accused, accused_id)
        if not accused:
            return {
                "name": self.name,
                "weight": self.weight,
                "raw_score": 0.0,
                "normalized_score": 0.0,
                "reasoning": "Accused not found.",
            }

        # Use is_repeat_offender flag as proxy for gang-like behavior
        if accused.is_repeat_offender:
            raw = 60.0
            reason = f"Accused is flagged as repeat offender."
        else:
            raw = 0.0
            reason = "No gang affiliation or repeat offender flag on record."

        return {
            "name": self.name,
            "weight": self.weight,
            "raw_score": round(raw, 2),
            "normalized_score": round(raw * self.weight, 2),
            "reasoning": reason,
        }


class RepeatOffenderScorer(ScorerInterface):
    """Scores based on conviction status in crime history and repeat offender flag."""

    name = "repeat_offender"
    weight = 0.15

    async def compute(self, accused_id: str, session: AsyncSession) -> dict[str, Any]:
        q = select(CrimeHistory).where(CrimeHistory.accused_id == accused_id)
        r = await session.execute(q)
        records = list(r.scalars().all())

        repeat_count = sum(1 for rec in records if rec.conviction_status == ConvictionStatus.CONVICTED)
        conviction_count = repeat_count
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
            reasons.append(f"{repeat_count} of {total} records with conviction")
        if not reasons:
            reasons.append("No convictions on record")

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
