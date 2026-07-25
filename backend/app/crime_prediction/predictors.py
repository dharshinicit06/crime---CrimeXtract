"""Rule-based crime prediction engine."""

import math
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crime.models import CrimeType
from app.fir.models import FIR
from app.location.models import Location
from app.logging import get_logger

logger = get_logger(__name__)

PREDICTION_HORIZON_DAYS = 7
HISTORICAL_LOOKBACK_DAYS = 365
HOTSPOT_TOP_N = 5


class CrimeDataLoader:
    @staticmethod
    async def load_fir_by_district(session):
        """Load FIR incidents grouped by district using incident_date."""
        cutoff = date.today() - timedelta(days=HISTORICAL_LOOKBACK_DAYS)
        q = (
            select(Location.district, FIR.incident_date)
            .select_from(FIR)
            .join(Location, FIR.location_id == Location.location_id, isouter=True)
            .where(FIR.incident_date >= cutoff)
        )
        r = await session.execute(q)
        rows = r.all()
        districts = defaultdict(list)
        for district, inc_date in rows:
            d = district or 'Unknown'
            districts[d].append(inc_date)
        return dict(districts)

    @staticmethod
    async def load_fir_by_location(session):
        cutoff = date.today() - timedelta(days=HISTORICAL_LOOKBACK_DAYS)
        q = (
            select(Location.district, FIR.incident_date, CrimeType.crime_name)
            .select_from(FIR)
            .join(Location, FIR.location_id == Location.location_id, isouter=True)
            .join(CrimeType, FIR.crime_type_id == CrimeType.crime_type_id, isouter=True)
            .where(FIR.incident_date >= cutoff)
        )
        r = await session.execute(q)
        rows = r.all()
        districts = defaultdict(list)
        for district, inc_date, crime_name in rows:
            d = district or 'Unknown'
            districts[d].append((inc_date, crime_name or 'Unknown'))
        return dict(districts)


class TrendAnalyzer:
    @staticmethod
    def compute_trend(district_dates):
        if len(district_dates) < 5:
            return 'stable'
        today = date.today()
        recent = sum(1 for d in district_dates if d >= today - timedelta(days=30))
        earlier = sum(1 for d in district_dates if d < today - timedelta(days=30) and d >= today - timedelta(days=90))
        if recent > earlier * 1.3 and earlier > 0:
            return 'rising'
        elif recent < earlier * 0.7 and earlier > 0:
            return 'declining'
        return 'stable'

    @staticmethod
    def monthly_average(district_dates):
        if not district_dates:
            return 0.0
        cutoff = date.today() - timedelta(days=HISTORICAL_LOOKBACK_DAYS)
        months = max(1, (date.today() - cutoff).days / 30.0)
        return len(district_dates) / months


class ProbabilityEstimator:
    @staticmethod
    def estimate(district_dates):
        if not district_dates:
            return 0.05, 'low'
        today = date.today()
        total_weight = 0.0
        weighted_count = 0.0
        for d in district_dates:
            days_ago = (today - d).days
            weight = math.exp(-days_ago / 90.0)
            weighted_count += weight
            total_weight += weight
        density = weighted_count / HISTORICAL_LOOKBACK_DAYS
        prob = 1.0 / (1.0 + math.exp(-(density * 30 - 2.5)))
        prob = max(0.05, min(0.95, prob))
        n = len(district_dates)
        if n >= 20:
            confidence = 'high'
        elif n >= 10:
            confidence = 'medium'
        else:
            confidence = 'low'
        return round(prob, 4), confidence


class HotspotDetector:
    @staticmethod
    def detect(district_data, top_n=HOTSPOT_TOP_N):
        if not district_data:
            return []
        densities = {}
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
                reason = f'{ratio:.1f}x the district average crime rate'
            elif ratio > 1.5:
                reason = f'Above-average crime density ({ratio:.1f}x)'
            else:
                reason = f'Crime density consistent with average ({ratio:.1f}x)'
            scored.append({
                'district': district,
                'hotspot_score': round(score, 1),
                'crime_count': len(district_data.get(district, [])),
                'trend': trend,
                'top_crime_types': [],
                'reasoning': reason,
            })
        return scored[:top_n]


class PatrolSuggester:
    @staticmethod
    def suggest(hotspots):
        suggestions = []
        for hs in hotspots:
            district = hs['district']
            trend = hs['trend']
            if trend == 'rising':
                suggestions.append({'district': district, 'priority': 'high', 'suggestion': f'Increase patrol frequency in {district}', 'reason': f'Rising crime trend ({hs["crime_count"]} incidents in past year)', 'time_window': None})
            elif hs['hotspot_score'] >= 70:
                suggestions.append({'district': district, 'priority': 'high', 'suggestion': f'Deploy dedicated patrol unit to {district}', 'reason': f'Hotspot score {hs["hotspot_score"]}/100', 'time_window': None})
            elif hs['hotspot_score'] >= 40:
                suggestions.append({'district': district, 'priority': 'medium', 'suggestion': f'Schedule regular patrol checks in {district}', 'reason': 'Moderate hotspot activity', 'time_window': None})
            else:
                suggestions.append({'district': district, 'priority': 'low', 'suggestion': f'Monitor {district}', 'reason': 'Low crime density', 'time_window': None})
        return suggestions


class CrimePredictionEngine:
    def __init__(self, session):
        self.session = session
        self.loader = CrimeDataLoader()
        self.probability = ProbabilityEstimator()
        self.hotspot = HotspotDetector()
        self.suggester = PatrolSuggester()

    async def predict_all(self):
        logger.info('Starting crime prediction pipeline (rule-based)')
        district_dates = await self.loader.load_fir_by_district(self.session)
        fir_location_data = await self.loader.load_fir_by_location(self.session)
        if not district_dates:
            return self._empty_response()
        predictions = []
        for district, dates in district_dates.items():
            prob, confidence = self.probability.estimate(dates)
            predicted_count = prob * PREDICTION_HORIZON_DAYS
            predictions.append({
                'district': district,
                'crime_category': None,
                'probability': prob,
                'predicted_count': round(predicted_count, 2),
                'confidence': confidence,
                'reasoning': f'Based on {len(dates)} incidents. Probability: {prob:.1%} in next {PREDICTION_HORIZON_DAYS} days.',
            })
        hotspots = self.hotspot.detect(district_dates)
        for hs in hotspots:
            fir_records = fir_location_data.get(hs['district'], [])
            type_counter = Counter(cat for _, cat in fir_records)
            hs['top_crime_types'] = [t for t, _ in type_counter.most_common(3)]
        suggestions = self.suggester.suggest(hotspots)
        all_dates = [d for dates in district_dates.values() for d in dates]
        data_period = f'{min(all_dates)} to {max(all_dates)}' if all_dates else 'No data'
        total_crimes = sum(len(d) for d in district_dates.values())
        logger.info('Prediction complete: %d districts, %d hotspots, %d crimes', len(district_dates), len(hotspots), total_crimes)
        return {
            'predictions': predictions,
            'hotspots': hotspots,
            'patrol_suggestions': suggestions,
            'metadata': {
                'data_period': data_period,
                'total_crimes_analyzed': total_crimes,
                'total_districts': len(district_dates),
                'prediction_horizon': 'next_7_days',
                'model_version': 'rule-based-v1',
                'generated_at': str(datetime.now()),
            },
        }

    def _empty_response(self) -> dict:
        return {
            'predictions': [],
            'hotspots': [],
            'patrol_suggestions': [],
            'metadata': {
                'data_period': 'No data',
                'total_crimes_analyzed': 0,
                'total_districts': 0,
                'prediction_horizon': 'next_7_days',
                'model_version': 'rule-based-v1',
                'generated_at': str(datetime.now()),
            },
        }
