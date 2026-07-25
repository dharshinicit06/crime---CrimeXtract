"""Crime Hotspots service - derives hotspot data dynamically from FIR & Location tables."""

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import case, extract, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.crime.models import CrimeType
from app.fir.models import FIR, InvestigationStatus, Priority
from app.location.models import Location
from app.logging import get_logger

logger = get_logger(__name__)


class CrimeHotspotService:
    """Computes crime hotspot data dynamically from FIR and Location tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _compute_risk_score(
        self,
        crime_count: int,
        high_priority_count: int,
        pending_count: int,
        recent_count: int,
    ) -> float:
        """Compute hotspot risk score using weighted formula.
        
        Score = Crime_Count * 10 + High_Priority * 20 + Pending * 15 + Recent_30d * 25
        Max realistic score ~ 1000, clamped at 1000 for normalization.
        """
        score = (
            crime_count * 10
            + high_priority_count * 20
            + pending_count * 15
            + recent_count * 25
        )
        return min(float(score), 1000.0)

    def _risk_level(self, score: float) -> str:
        if score >= 300:
            return "High"
        if score >= 150:
            return "Medium"
        return "Low"

    async def get_hotspots(
        self,
        time_range: str = "all",
        crime_type_id: Optional[int] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        """List all hotspot districts with risk scores and filtered options."""
        today = date.today()

        # Build base subquery: FIRs grouped by district with counts
        thirty_days_ago = today - timedelta(days=30)

        # Columns for aggregation
        district_col = func.coalesce(Location.district, "Unknown")
        city_col = func.coalesce(Location.city, "")
        area_col = func.coalesce(Location.area, "")
        lat_col = func.avg(Location.latitude)
        lng_col = func.avg(Location.longitude)
        last_incident_col = func.max(FIR.incident_date)

        crime_count_col = func.count(FIR.fir_id)
        high_priority_col = func.sum(
    case(
        (
            FIR.priority.in_([Priority.HIGH, Priority.CRITICAL]),
            1,
        ),
        else_=0,
    )
)
        pending_col = func.sum(
    case(
        (
            FIR.investigation_status.in_(
                [
                    InvestigationStatus.PENDING,
                    InvestigationStatus.UNDER_INVESTIGATION,
                ]
            ),
            1,
        ),
        else_=0,
    )
)
        recent_col = func.sum(
    case(
        (
            FIR.incident_date >= thirty_days_ago,
            1,
        ),
        else_=0,
    )
)
        # Build query
        stmt = select(
            district_col.label("district"),
            city_col.label("city"),
            area_col.label("area"),
            crime_count_col.label("crime_count"),
            high_priority_col.label("priority_count"),
            pending_col.label("pending_count"),
            recent_col.label("recent_count"),
            last_incident_col.label("last_incident"),
            lat_col.label("latitude"),
            lng_col.label("longitude"),
        ).join(
            Location, FIR.location_id == Location.location_id, isouter=True
        ).group_by(
            Location.district, Location.city, Location.area
        ).order_by(text("crime_count DESC"))

        # Apply time range filter (only when not "all")
        if time_range == "7d":
            cutoff = today - timedelta(days=7)
            stmt = stmt.where(FIR.incident_date >= cutoff)
        elif time_range == "30d":
            cutoff = today - timedelta(days=30)
            stmt = stmt.where(FIR.incident_date >= cutoff)
        elif time_range == "90d":
            cutoff = today - timedelta(days=90)
            stmt = stmt.where(FIR.incident_date >= cutoff)
        # When time_range == "all", no WHERE filter is applied

        if crime_type_id is not None and crime_type_id > 0:
            stmt = stmt.where(FIR.crime_type_id == crime_type_id)

        if priority:
            try:
                priority_enum = Priority(priority)
                stmt = stmt.where(FIR.priority == priority_enum)
            except ValueError:
                pass

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                func.coalesce(Location.district, "").like(search_pattern)
                | func.coalesce(Location.city, "").like(search_pattern)
                | func.coalesce(Location.area, "").like(search_pattern)
            )

        r = await self.session.execute(stmt)
        rows = r.all()

        hotspots = []
        high_count = medium_count = low_count = 0
        total_crimes = 0

        for row in rows:
            score = self._compute_risk_score(
                crime_count=row.crime_count or 0,
                high_priority_count=row.priority_count or 0,
                pending_count=row.pending_count or 0,
                recent_count=row.recent_count or 0,
            )
            level = self._risk_level(score)
            if level == "High":
                high_count += 1
            elif level == "Medium":
                medium_count += 1
            else:
                low_count += 1
            total_crimes += row.crime_count or 0

            hotspots.append({
                "district": row.district or "Unknown",
                "city": row.city or "",
                "area": row.area or "",
                "crime_count": row.crime_count or 0,
                "risk_score": round(score, 1),
                "risk_level": level,
                "priority_count": row.priority_count or 0,
                "pending_count": row.pending_count or 0,
                "recent_count": row.recent_count or 0,
                "last_incident": str(row.last_incident) if row.last_incident else None,
                "latitude": row.latitude,
                "longitude": row.longitude,
            })

        unique_districts = len(set(h["district"] for h in hotspots))
        unique_cities = len(set(h["city"] for h in hotspots if h["city"]))

        return {
            "hotspots": hotspots,
            "total_hotspots": len(hotspots),
            "high_risk_count": high_count,
            "medium_risk_count": medium_count,
            "low_risk_count": low_count,
            "total_crimes": total_crimes,
            "unique_districts": unique_districts,
            "unique_cities": unique_cities,
        }

    async def get_hotspot_detail(self, district: str) -> Optional[dict]:
        """Get detailed information for a specific hotspot district."""
        # Get basic stats for this district
        thirty_days_ago = date.today() - timedelta(days=30)

        base_query = select(FIR).join(
            Location, FIR.location_id == Location.location_id
        ).where(
            func.coalesce(Location.district, "") == district
        )

        r = await self.session.execute(base_query)
        firs = list(r.scalars().all())

        if not firs:
            # Try case-insensitive
            base_query = select(FIR).join(
                Location, FIR.location_id == Location.location_id
            ).where(
                func.coalesce(Location.district, "").like(district)
            )
            r = await self.session.execute(base_query)
            firs = list(r.scalars().all())

        if not firs:
            return None

        # Get location info
        loc_query = select(
            func.coalesce(Location.district, district),
            func.coalesce(Location.city, ""),
            func.coalesce(Location.area, ""),
            func.avg(Location.latitude),
            func.avg(Location.longitude),
        ).where(
            func.coalesce(Location.district, "").like(district)
        ).group_by(Location.district, Location.city, Location.area)

        r = await self.session.execute(loc_query)
        loc_row = r.first()

        # Crime type breakdown
        crime_type_query = select(
            func.coalesce(CrimeType.crime_name, "Unknown").label("crime_type"),
            func.count(FIR.fir_id).label("cnt"),
        ).join(
            CrimeType, FIR.crime_type_id == CrimeType.crime_type_id, isouter=True
        ).join(
            Location, FIR.location_id == Location.location_id
        ).where(
            func.coalesce(Location.district, "").like(district)
        ).group_by(CrimeType.crime_name).order_by(text("cnt DESC"))

        r = await self.session.execute(crime_type_query)
        crime_types = [
            {"crime_type": row.crime_type, "count": row.cnt}
            for row in r.all()
        ]

        # Status breakdown
        status_query = select(
            FIR.investigation_status.label("status"),
            func.count(FIR.fir_id).label("cnt"),
        ).join(
            Location, FIR.location_id == Location.location_id
        ).where(
            func.coalesce(Location.district, "").like(district)
        ).group_by(FIR.investigation_status).order_by(text("cnt DESC"))

        r = await self.session.execute(status_query)
        status_breakdown = [
            {
                "status": row.status.value if hasattr(row.status, "value") else str(row.status or "Unknown"),
                "count": row.cnt,
            }
            for row in r.all()
        ]

        # Monthly trend
        trend_query = select(
            extract("year", FIR.incident_date).label("yr"),
            extract("month", FIR.incident_date).label("mn"),
            func.count(FIR.fir_id).label("cnt"),
        ).join(
            Location, FIR.location_id == Location.location_id
        ).where(
            func.coalesce(Location.district, "").like(district)
        ).group_by(
    extract("year", FIR.incident_date),
    extract("month", FIR.incident_date),
).order_by(
    extract("year", FIR.incident_date),
    extract("month", FIR.incident_date),
)

        r = await self.session.execute(trend_query)
        month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_trend = []
        for row in r.all():
            monthly_trend.append({
                "month": f"{int(row.yr)}-{month_names[int(row.mn)] if int(row.mn) <= 12 else row.mn}",
                "count": row.cnt,
            })

        # Recent FIRs (last 5)
        recent_firs = []
        for fir in sorted(firs, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]:
            recent_firs.append({
                "fir_number": fir.fir_number,
                "title": fir.title,
                "incident_date": str(fir.incident_date) if fir.incident_date else None,
                "investigation_status": fir.investigation_status.value if fir.investigation_status else None,
                "priority": fir.priority.value if fir.priority else None,
            })

        # Compute risk score
        crime_count = len(firs)
        high_priority = sum(
            1 for f in firs if f.priority in (Priority.HIGH, Priority.CRITICAL)
        )
        pending = sum(
            1 for f in firs
            if f.investigation_status in (
                InvestigationStatus.PENDING,
                InvestigationStatus.UNDER_INVESTIGATION,
            )
        )
        recent = sum(
            1 for f in firs
            if f.incident_date and f.incident_date >= thirty_days_ago
        )
        score = self._compute_risk_score(crime_count, high_priority, pending, recent)

        # Generate AI insight
        insight = self._generate_insight(
            district=district,
            crime_count=crime_count,
            high_priority=high_priority,
            pending=pending,
            recent=recent,
            top_crime_type=crime_types[0]["crime_type"] if crime_types else "Unknown",
            has_rising_trend=len(monthly_trend) >= 2 and monthly_trend[-1]["count"] > monthly_trend[-2]["count"],
        )

        return {
            "district": loc_row[0] if loc_row else district,
            "city": loc_row[1] if loc_row else "",
            "area": loc_row[2] if loc_row else "",
            "latitude": loc_row[3] if loc_row else None,
            "longitude": loc_row[4] if loc_row else None,
            "crime_count": crime_count,
            "risk_score": round(score, 1),
            "risk_level": self._risk_level(score),
            "crime_types": crime_types,
            "status_breakdown": status_breakdown,
            "monthly_trend": monthly_trend,
            "recent_firs": recent_firs,
            "ai_insight": insight,
        }

    async def get_hotspot_map(self) -> dict:
        """Get GIS-ready map data points from all locations with FIRs."""
        stmt = select(
            func.coalesce(Location.district, "Unknown").label("district"),
            func.coalesce(Location.city, "").label("city"),
            func.coalesce(Location.area, "").label("area"),
            func.avg(Location.latitude).label("latitude"),
            func.avg(Location.longitude).label("longitude"),
            func.count(FIR.fir_id).label("crime_count"),
        ).join(
            FIR, FIR.location_id == Location.location_id
        ).where(
            Location.latitude.isnot(None),
            Location.longitude.isnot(None),
        ).group_by(
            Location.district, Location.city, Location.area
        ).order_by(text("crime_count DESC"))

        r = await self.session.execute(stmt)
        rows = r.all()

        points = []
        for row in rows:
            if not row.latitude or not row.longitude:
                continue
            crime_count = row.crime_count or 0
            score = self._compute_risk_score(crime_count, 0, 0, 0)
            level = self._risk_level(score)
            points.append({
                "district": row.district or "Unknown",
                "city": row.city or "",
                "area": row.area or "",
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "crime_count": crime_count,
                "risk_score": round(score, 1),
                "risk_level": level,
            })

        return {"points": points, "total_points": len(points)}

    def _generate_insight(
        self,
        district: str,
        crime_count: int,
        high_priority: int,
        pending: int,
        recent: int,
        top_crime_type: str,
        has_rising_trend: bool,
    ) -> str:
        """Generate a human-readable AI insight for a hotspot district."""
        parts = []

        if crime_count > 50:
            parts.append(f"{district} is a high-crime area with {crime_count} registered cases.")
        elif crime_count > 20:
            parts.append(f"{district} has recorded {crime_count} cases, requiring ongoing monitoring.")
        else:
            parts.append(f"{district} has {crime_count} reported incidents.")

        if high_priority > 0:
            parts.append(f"Of these, {high_priority} cases are marked High or Critical priority.")

        pending_pct = round((pending / crime_count) * 100, 1) if crime_count > 0 else 0
        if pending_pct > 60:
            parts.append(f"Resolution rate is low with {pending} cases ({pending_pct}%) still under investigation.")
        elif pending_pct > 30:
            parts.append(f"{pending} cases ({pending_pct}%) remain open.")

        if recent > 0:
            if recent >= 10:
                parts.append(f"⚠️ ALERT: {recent} new cases filed in the last 30 days, indicating a rising trend.")
            else:
                parts.append(f"{recent} new case{'s' if recent != 1 else ''} reported in the last 30 days.")

        if top_crime_type and top_crime_type != "Unknown":
            ct_parts = [ct for ct in [top_crime_type] if ct.lower() != "unknown"]
            if ct_parts:
                parts.append(f"The most common crime type is '{ct_parts[0]}'.")

        if has_rising_trend:
            parts.append("Crime trend is rising — recommend increased patrol allocation.")

        if not parts:
            parts.append(f"{district} has limited crime data available.")

        return " ".join(parts)

    async def get_hotspot_insights(self) -> dict:
        """Generate AI insights for all hotspot districts.
        Uses data already available from get_hotspots() to avoid N+1 queries.
        """
        hotspots_data = await self.get_hotspots()
        insights = []

        # Get top crime types for top hotspots in a single batch query
        top_districts = [h["district"] for h in hotspots_data.get("hotspots", [])[:10]]
        crime_type_map = {}
        if top_districts:
            ct_query = select(
                func.coalesce(Location.district, "Unknown").label("district"),
                func.coalesce(CrimeType.crime_name, "Unknown").label("crime_type"),
                func.count(FIR.fir_id).label("cnt"),
            ).join(
                Location, FIR.location_id == Location.location_id, isouter=True
            ).join(
                CrimeType, FIR.crime_type_id == CrimeType.crime_type_id, isouter=True
            ).where(
                func.coalesce(Location.district, "").in_(top_districts)
            ).group_by(
                Location.district, CrimeType.crime_name
            ).order_by(
                Location.district, text("cnt DESC")
            )
            r = await self.session.execute(ct_query)
            for row in r.all():
                d = row.district or "Unknown"
                if d not in crime_type_map:
                    crime_type_map[d] = row.crime_type or "Unknown"

        for hotspot in hotspots_data.get("hotspots", [])[:10]:
            district = hotspot["district"]
            insight_text = self._generate_insight(
                district=district,
                crime_count=hotspot["crime_count"],
                high_priority=hotspot["priority_count"],
                pending=hotspot["pending_count"],
                recent=hotspot["recent_count"],
                top_crime_type=crime_type_map.get(district, "Various"),
                has_rising_trend=False,
            )
            insights.append({
                "district": district,
                "insight": insight_text,
                "impact": "danger" if hotspot["risk_level"] == "High"
                         else "warning" if hotspot["risk_level"] == "Medium"
                         else "info",
            })

        return {"insights": insights}
