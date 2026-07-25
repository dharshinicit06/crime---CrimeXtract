"""Pydantic schemas for ML-based crime prediction requests/responses."""

from pydantic import BaseModel, Field, field_validator


class PredictionRequest(BaseModel):
    """Single crime prediction request."""

    state: str = Field(..., min_length=1, description="State name (e.g. 'Karnataka')")
    district: str = Field(..., min_length=1, description="District name (e.g. 'Bengaluru Urban')")
    year: int = Field(..., ge=2000, le=2100, description="Target year for prediction")
    crime_type: str = Field(..., min_length=1, description="Crime type (e.g. 'Murder', 'Robbery')")
    chargesheeted: int = Field(..., ge=0, description="Number of chargesheeted cases")
    convictions: int = Field(..., ge=0, description="Number of convictions")
    population: int = Field(..., ge=1, description="Population of the district")

    @field_validator("convictions")
    @classmethod
    def convictions_not_exceed_chargesheeted(cls, v, info):
        chargesheeted = info.data.get("chargesheeted")
        if chargesheeted is not None and v > chargesheeted:
            raise ValueError("convictions cannot exceed chargesheeted")
        return v


class PredictionResponse(BaseModel):
    """Response containing the predicted crime case count."""

    predicted_cases: float = Field(
        ..., ge=0.0, description="Predicted number of crime cases"
    )
