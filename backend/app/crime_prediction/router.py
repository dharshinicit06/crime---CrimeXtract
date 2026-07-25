"""Crime Prediction API endpoint — returns rule-based predictions."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
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
    return await service.get_predictions()
