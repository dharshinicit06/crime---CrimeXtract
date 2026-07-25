"""ML Prediction API endpoint — exposes the trained RandomForest model."""

import asyncio

from fastapi import APIRouter, HTTPException, Request

from app.logging import get_logger
from app.ml.schemas import PredictionRequest, PredictionResponse
from app.ml.services import predict_cases
from app.rate_limit import ml_limiter

logger = get_logger(__name__)

router = APIRouter(prefix="/ml", tags=["ml-prediction"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict crime case count using the trained ML model",
    description=(
        "Accepts crime-related features and returns a predicted number of cases "
        "using the pre-trained RandomForestRegressor model."
    ),
)
@ml_limiter
async def predict(
    request: Request,
    req: PredictionRequest,
) -> PredictionResponse:
    """Predict the number of crime cases based on input features."""

    logger.info(
        "Prediction request received",
        extra={
            "state": req.state,
            "district": req.district,
            "year": req.year,
            "crime_type": req.crime_type,
            "chargesheeted": req.chargesheeted,
            "convictions": req.convictions,
            "population": req.population,
        },
    )

    try:
        predicted = await asyncio.to_thread(
            predict_cases,
            state=req.state,
            district=req.district,
            year=req.year,
            crime_type=req.crime_type,
            chargesheeted=req.chargesheeted,
            convictions=req.convictions,
            population=req.population,
        )

    except ValueError as exc:
        logger.warning(
            "Prediction validation failed",
            extra={"error": str(exc)},
        )
        raise HTTPException(status_code=400, detail=str(exc))

    except RuntimeError as exc:
        logger.error(
            "ML model unavailable",
            extra={"error": str(exc)},
        )
        raise HTTPException(status_code=503, detail=str(exc))

    logger.info(
        "Prediction completed",
        extra={"predicted_cases": predicted},
    )

    return PredictionResponse(
        predicted_cases=predicted
    )