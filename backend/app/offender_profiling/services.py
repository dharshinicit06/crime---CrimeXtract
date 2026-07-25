"""Offender Profiling service — orchestrates modular scorers and compiles profiles."""

from collections import Counter, defaultdict
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accused.models import Accused, FIRAccusedLink
from app.crime.models import CrimeType
from app.crime_history.models import CrimeHistory, ConvictionStatus
from app.evidence.models import Evidence
from app.fir.models import FIR, InvestigationStatus
from app.location.models import Location
from app.victim.models import FIRVictimLink, Victim
from app.exceptions.handlers import NotFoundException
from app.logging import get_logger
from app.offender_profiling.scorers import DEFAULT_SCORERS

logger = get_logger(__name__)


class OffenderProfilingService:
    """Orchestrates modular scoring to produce a comprehensive offender profile."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_profile(self, accused_id: str) -> dict[str, Any]:
        """Build a complete offender profile with all related data."""
        # 1. Load accused
        try:
            accused_id_int = int(accused_id)
        except ValueError:
            raise NotFoundException(
                message=f"Invalid accused ID '{accused_id}'",
                error_code="INVALID_ID",
            )
        accused = await self.session.get(Accused, accused_id_int)
        if not accused:
            raise NotFoundException(
                message=f"Accused '{accused_id}' not found",
                error_code="ACCUSED_NOT_FOUND",
            )

        # 2. Run all modular scorers
        scorer_results = []
        total_weighted = 0.0
        for scorer in DEFAULT_SCORERS:
            result = await scorer.compute(accused_id, self.session)
            scorer_results.append(result)
            total_weighted += result["normalized_score"]

        risk_score = round(total_weighted, 2)
        if risk_score >= 75:
            risk_level = "critical"
            recommendation = "High risk offender — recommend intensive surveillance, travel monitoring, and financial tracking. Consider preventive detention."
        elif risk_score >= 50:
            risk_level = "high"
            recommendation = "Elevated risk — recommend regular monitoring, associate tracking, and periodic reporting."
        elif risk_score >= 25:
            risk_level = "medium"
            recommendation = "Moderate risk — maintain standard surveillance and update records regularly."
        else:
            risk_level = "low"
            recommendation = "Low risk — routine monitoring sufficient."

        # 3. Load FIRs and related data
        r = await self.session.execute(
            select(FIRAccusedLink).where(FIRAccusedLink.accused_id == accused_id_int)
        )
        fir_links = list(r.scalars().all())
        fir_ids = list(set(l.fir_id for l in fir_links))

        fir_details = []
        firs_by_id = {}
        all_firs = []
        ct_map = {}
        if fir_ids:
            r = await self.session.execute(
                select(FIR).where(FIR.fir_id.in_(fir_ids))
            )
            all_firs = list(r.scalars().all())
            firs_by_id = {f.fir_id: f for f in all_firs}

            ct_ids = list(set(f.crime_type_id for f in all_firs if f.crime_type_id))
            ct_map = {}
            if ct_ids:
                r = await self.session.execute(
                    select(CrimeType).where(CrimeType.crime_type_id.in_(ct_ids))
                )
                ct_map = {ct.crime_type_id: ct for ct in r.scalars().all()}

            for link in fir_links:
                fir = firs_by_id.get(link.fir_id)
                if fir:
                    ct = ct_map.get(fir.crime_type_id) if fir.crime_type_id else None
                    fir_details.append({
                        "fir_id": str(fir.fir_id),
                        "fir_number": fir.fir_number,
                        "title": fir.title,
                        "status": fir.investigation_status.value if hasattr(fir.investigation_status, "value") else str(fir.investigation_status or 'N/A'),
                        "incident_date": fir.incident_date,
                        "crime_category": ct.crime_name if ct else None,
                    })

        # Crime history records
        r = await self.session.execute(
            select(CrimeHistory).where(CrimeHistory.accused_id == accused_id_int)
        )
        hist_records = list(r.scalars().all())

        crime_cats = set()
        for f in all_firs:
            if f.crime_type_id:
                ct = ct_map.get(f.crime_type_id)
                if ct:
                    crime_cats.add(ct.crime_name)
        for h in hist_records:
            if h.crime_type:
                crime_cats.add(h.crime_type)

        # Statistics
        total_firs = len(fir_ids)
        active_firs = sum(1 for f in all_firs if f.investigation_status in (
            InvestigationStatus.PENDING, InvestigationStatus.UNDER_INVESTIGATION
        ))
        solved_firs = sum(1 for f in all_firs if f.investigation_status in (
            InvestigationStatus.SOLVED, InvestigationStatus.CLOSED
        ))
        pending_firs = sum(1 for f in all_firs if f.investigation_status == InvestigationStatus.PENDING)

        # Evidence count
        r = await self.session.execute(
            select(func.count(Evidence.evidence_id)).where(Evidence.fir_id.in_(fir_ids))
        ) if fir_ids else None
        total_evidence = r.scalar() if r else 0

        # Victim count
        r = await self.session.execute(
            select(func.count(func.distinct(FIRVictimLink.victim_id))).where(FIRVictimLink.fir_id.in_(fir_ids))
        ) if fir_ids else None
        total_victims = r.scalar() if r else 0

        # Location data
        loc_ids = list(set(f.location_id for f in all_firs if f.location_id))
        locations_data = []
        if loc_ids:
            r = await self.session.execute(
                select(Location).where(Location.location_id.in_(loc_ids))
            )
            locs = list(r.scalars().all())
            loc_counter = Counter()
            for f in all_firs:
                if f.location_id:
                    loc_counter[f.location_id] += 1
            for loc in locs:
                locations_data.append({
                    "district": loc.district,
                    "city": loc.city,
                    "area": loc.area,
                    "fir_count": loc_counter.get(loc.location_id, 0),
                })

        unique_districts = len(set(l["district"] for l in locations_data))
        most_common_district = max(locations_data, key=lambda x: x["fir_count"])["district"] if locations_data else None

        # Co-accused count
        r = await self.session.execute(
            select(FIRAccusedLink.accused_id).where(
                FIRAccusedLink.fir_id.in_(fir_ids),
                FIRAccusedLink.accused_id != accused_id_int,
            )
        ) if fir_ids else None
        co_accused_ids = list(set(r.scalars().all())) if r else []

        # Crime frequency info
        all_dates = []
        for h in hist_records:
            if h.arrest_date:
                all_dates.append(h.arrest_date)
        for f in all_firs:
            if f.incident_date:
                all_dates.append(f.incident_date)

        crime_freq = {
            "total_firs": total_firs,
            "total_crime_history": len(hist_records),
            "unique_crime_categories": sorted(crime_cats),
            "first_offense_date": min(all_dates) if all_dates else None,
            "last_offense_date": max(all_dates) if all_dates else None,
            "months_active": (max(all_dates) - min(all_dates)).days // 30 if len(all_dates) >= 2 else None,
        }

        # Reasoning summary
        reasoning_parts = [f"[{sr['name']}] {sr['reasoning']}" for sr in scorer_results]

        offender_flags = {
            "is_repeat_offender": bool(accused.is_repeat_offender) if accused.is_repeat_offender else False,
            "risk_score": float(accused.risk_score) if accused.risk_score else None,
        }

        logger.info(
            "Offender profile built for %s: risk_score=%.1f, level=%s",
            accused.full_name, risk_score, risk_level,
        )

        return {
            "accused_id": str(accused.accused_id),
            "name": accused.full_name,
            "alias": None,
            "age": accused.age,
            "gender": accused.gender.value if accused.gender else None,
            "phone": accused.phone,
            "address": accused.address,
            "occupation": accused.occupation,
            "district": locations_data[0]["district"] if locations_data else None,
            "city": locations_data[0]["city"] if locations_data else None,
            "is_active": True,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "statistics": {
                "total_firs": total_firs,
                "active_firs": active_firs,
                "solved_firs": solved_firs,
                "pending_firs": pending_firs,
                "total_victims": total_victims,
                "total_evidence": total_evidence,
                "repeat_offender_score": offender_flags["risk_score"],
                "unique_locations": unique_districts,
                "most_common_district": most_common_district,
                "co_accused_count": len(co_accused_ids),
            },
            "crime_frequency": crime_freq,
            "crime_categories": sorted(crime_cats),
            "previous_firs": fir_details,
            "locations": locations_data,
            "scorer_results": scorer_results,
            "reasoning_summary": " | ".join(reasoning_parts),
        }

    async def get_timeline(self, accused_id: str) -> dict[str, Any]:
        """Build chronological timeline for an accused."""
        try:
            accused_id_int = int(accused_id)
        except ValueError:
            raise NotFoundException(
                message=f"Invalid accused ID '{accused_id}'",
                error_code="INVALID_ID",
            )
        accused = await self.session.get(Accused, accused_id_int)
        if not accused:
            raise NotFoundException(
                message=f"Accused '{accused_id}' not found",
                error_code="ACCUSED_NOT_FOUND",
            )

        events = []

        # Accused creation
        if accused.created_at:
            events.append({
                "date": str(accused.created_at),
                "event_type": "record_created",
                "title": "Accused record created",
                "description": f"Record created for {accused.full_name}",
                "reference_id": str(accused.accused_id),
            })

        # FIRs linked to this accused
        r = await self.session.execute(
            select(FIRAccusedLink).where(FIRAccusedLink.accused_id == accused_id_int)
        )
        fir_links = list(r.scalars().all())
        fir_ids = list(set(l.fir_id for l in fir_links))

        if fir_ids:
            r = await self.session.execute(
                select(FIR).where(FIR.fir_id.in_(fir_ids)).order_by(FIR.incident_date)
            )
            firs = list(r.scalars().all())
            for fir in firs:
                events.append({
                    "date": str(fir.incident_date) if fir.incident_date else None,
                    "event_type": "fir_registered",
                    "title": f"FIR {fir.fir_number}",
                    "description": fir.title or "No title",
                    "status": fir.investigation_status.value if hasattr(fir.investigation_status, "value") else str(fir.investigation_status or "Pending"),
                    "reference_id": str(fir.fir_id),
                })

        # Crime history events
        r = await self.session.execute(
            select(CrimeHistory).where(CrimeHistory.accused_id == accused_id_int).order_by(CrimeHistory.arrest_date)
        )
        hist_records = list(r.scalars().all())
        for h in hist_records:
            events.append({
                "date": str(h.arrest_date) if h.arrest_date else None,
                "event_type": "crime_history",
                "title": f"Crime: {h.crime_type or 'Unknown'}",
                "description": f"Status: {h.conviction_status.value if h.conviction_status else 'Unknown'}",
                "status": h.conviction_status.value if hasattr(h.conviction_status, "value") else str(h.conviction_status or "Unknown"),
                "reference_id": str(h.history_id) if h.history_id else None,
            })

        # Evidence events
        if fir_ids:
            r = await self.session.execute(
                select(Evidence).where(Evidence.fir_id.in_(fir_ids)).order_by(Evidence.collected_date)
            )
            evidence_items = list(r.scalars().all())
            for ev in evidence_items:
                events.append({
                    "date": str(ev.collected_date) if ev.collected_date else None,
                    "event_type": "evidence_collected",
                    "title": f"Evidence: {ev.evidence_name or 'Unknown'}",
                    "description": f"Type: {ev.evidence_type.value if ev.evidence_type else 'Unknown'}",
                    "status": None,
                    "reference_id": str(ev.evidence_id),
                })

        # Sort by date descending (most recent first)
        events.sort(key=lambda e: e["date"] or "", reverse=True)

        return {
            "accused_id": str(accused.accused_id),
            "name": accused.full_name,
            "events": events,
            "total_events": len(events),
        }
