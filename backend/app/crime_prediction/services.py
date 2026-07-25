"""Crime Prediction service — delegates to the independent prediction engine."""

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
