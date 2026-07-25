"""Predictive Crime Analytics — Linear Regression crime forecasting.

Uses scikit-learn's LinearRegression to forecast monthly crime counts
from historical FIR data stored in MySQL. Also provides hotspot trend
forecasts and seasonal pattern analysis.

No database schema changes. All data comes from existing FIR + Location tables.
"""

from collections import defaultdict
from datetime import datetime
from math import sqrt
from typing import Any

import numpy as np
from sklearn.linear_model import LinearRegression
from sqlalchemy import extract, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.fir.models import FIR
from app.location.models import Location
from app.logging import get_logger

logger = get_logger(__name__)


class CrimePredictor:
    """Linear Regression based crime forecaster."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def forecast(
        self, months_ahead: int = 3, district: str | None = None,
    ) -> dict[str, Any]:
        monthly_data = await self._get_monthly_counts(district)
        if not monthly_data:
            return {"predictions": [], "hotspot_trends": [], "seasonal_patterns": [],
                    "confidence": 0.0, "total_predicted": 0, "total_historical": 0,
                    "generated_at": datetime.utcnow().isoformat()}

        months_array = np.array([m["month_index"] for m in monthly_data]).reshape(-1, 1)
        counts_array = np.array([m["count"] for m in monthly_data])
        total_historical = int(counts_array.sum())
        last_month_index = monthly_data[-1]["month_index"]

        model = LinearRegression()
        model.fit(months_array, counts_array)

        future_indices = np.array([last_month_index + i + 1 for i in range(months_ahead)]).reshape(-1, 1)
        predictions_raw = model.predict(future_indices)
        predictions_raw = np.maximum(predictions_raw, 0)

        residuals = counts_array - model.predict(months_array)
        rse = sqrt(np.sum(residuals ** 2) / max(len(residuals) - 2, 1))
        confidence = max(0.0, min(1.0, 1.0 - (rse / max(np.mean(counts_array), 1))))

        predictions = []
        for i, idx in enumerate(future_indices.flatten()):
            year = int(idx // 12) + 2000
            month_num = int(idx % 12) + 1
            month_label = f"{year:04d}-{month_num:02d}"
            pred_val = float(predictions_raw[i])
            interval_mult = 1.0 + (i * 0.3)
            margin = rse * 1.96 * interval_mult
            predictions.append({
                "month": month_label, "predicted_count": round(pred_val, 1),
                "lower_bound": round(max(pred_val - margin, 0), 1),
                "upper_bound": round(pred_val + margin, 1), "historical_count": None,
            })

        historical_by_month = {}
        for m in monthly_data:
            year = int(m["month_index"] // 12) + 2000
            month_num = int(m["month_index"] % 12) + 1
            key = f"{year:04d}-{month_num:02d}"
            historical_by_month[key] = m["count"]
        for p in predictions:
            if p["month"] in historical_by_month:
                p["historical_count"] = float(historical_by_month[p["month"]])

        hotspot_trends = await self._get_hotspot_trends()
        seasonal_patterns = await self._get_seasonal_patterns(district)
        total_predicted = round(sum(p["predicted_count"] for p in predictions[:1]), 1)

        return {
            "predictions": predictions, "hotspot_trends": hotspot_trends,
            "seasonal_patterns": seasonal_patterns, "confidence": round(confidence, 4),
            "total_predicted": total_predicted, "total_historical": total_historical,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _get_monthly_counts(self, district=None):
        stmt = select(extract("year", FIR.incident_date).label("yr"),
                      extract("month", FIR.incident_date).label("mn"),
                      func.count(FIR.fir_id).label("cnt"))
        if district:
            stmt = stmt.join(Location, FIR.location_id == Location.location_id).where(
                func.lower(Location.district) == district.lower())
        stmt = stmt.group_by(text("yr, mn")).order_by(text("yr ASC, mn ASC"))
        r = await self.session.execute(stmt)
        return [{"month_index": (int(row.yr) - 2000) * 12 + (int(row.mn) - 1),
                 "year": int(row.yr), "month": int(row.mn), "count": row.cnt,
                 "label": f"{int(row.yr):04d}-{int(row.mn):02d}"} for row in r.all()]

    async def _get_hotspot_trends(self):
        stmt = select(func.coalesce(Location.district, "Unknown").label("district"),
                      func.count(FIR.fir_id).label("cnt")).join(
            Location, FIR.location_id == Location.location_id, isouter=True
        ).group_by(Location.district).order_by(text("cnt DESC")).limit(10)
        r = await self.session.execute(stmt)
        trends = []
        for row in r.all():
            district_name = row.district or "Unknown"
            monthly = await self._get_monthly_counts(district_name)
            if len(monthly) < 3:
                continue
            recent = monthly[-3:]
            x = np.array([m["month_index"] for m in recent]).reshape(-1, 1)
            y = np.array([m["count"] for m in recent])
            local_model = LinearRegression()
            local_model.fit(x, y)
            next_pred = float(max(local_model.predict([[recent[-1]["month_index"] + 1]])[0], 0))
            slope = local_model.coef_[0]
            trend = "rising" if slope > 0.3 else ("declining" if slope < -0.3 else "stable")
            risk = min(100, max(0, (row.cnt / 5) + (10 if trend == "rising" else 0)))
            trends.append({"district": district_name, "current_count": row.cnt,
                           "predicted_next_month": round(next_pred, 1), "trend": trend,
                           "risk_score": round(risk, 1)})
        return trends

    async def _get_seasonal_patterns(self, district=None):
        season_map = {12: "Winter", 1: "Winter", 2: "Winter",
                      3: "Summer", 4: "Summer", 5: "Summer",
                      6: "Monsoon", 7: "Monsoon", 8: "Monsoon",
                      9: "Autumn", 10: "Autumn", 11: "Autumn"}
        stmt = select(extract("month", FIR.incident_date).label("mn"),
                      func.count(FIR.fir_id).label("cnt"))
        if district:
            stmt = stmt.join(Location, FIR.location_id == Location.location_id).where(
                func.lower(Location.district) == district.lower())
        stmt = stmt.group_by(text("mn")).order_by(text("mn ASC"))
        r = await self.session.execute(stmt)
        seasonal = defaultdict(list)
        for row in r.all():
            seasonal[season_map.get(int(row.mn), "Unknown")].append(row.cnt)
        patterns, prev_avg = [], None
        for season in ["Winter", "Summer", "Monsoon", "Autumn"]:
            counts = seasonal.get(season, [])
            if not counts:
                continue
            avg = sum(counts) / len(counts)
            change = round(((avg - prev_avg) / prev_avg * 100), 1) if prev_avg else None
            patterns.append({"season": season, "average_crimes": round(avg, 1),
                             "peak_crime_type": None, "change_percent": change})
            prev_avg = avg
        return patterns
