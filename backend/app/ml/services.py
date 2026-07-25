"""ML prediction service — loads the trained model once and exposes prediction logic."""

from pathlib import Path

import joblib
import pandas as pd

from app.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# Resolve ML model paths
# __file__ = backend/app/ml/services.py
# =============================================================================

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ML_DIR = _BACKEND_DIR / "ml"

_MODEL_PATH = _ML_DIR / "models" / "crime_prediction_model.pkl"
_ENCODER_PATH = _ML_DIR / "models" / "label_encoders.pkl"

# =============================================================================
# Load model and encoders (only once)
# =============================================================================

try:
    model = joblib.load(_MODEL_PATH)
    encoders = joblib.load(_ENCODER_PATH)

    logger.info(
        "ML models loaded successfully",
        extra={
            "model_path": str(_MODEL_PATH),
            "encoder_path": str(_ENCODER_PATH),
            "encoders": list(encoders.keys()),
        },
    )

except Exception:
    model = None
    encoders = None

    logger.exception("Failed to load ML models")


# =============================================================================
# Validation Helpers
# =============================================================================

def _validate_field(field_name: str, value: str) -> str | None:
    """
    Validate that a categorical value exists in the trained encoder.
    """

    if encoders is None:
        return "ML models are not loaded."

    if field_name not in encoders:
        return f"Encoder '{field_name}' not found."

    try:
        encoders[field_name].transform([value])
        return None

    except ValueError:
        allowed = list(encoders[field_name].classes_)

        return (
            f"Unknown {field_name}: '{value}'. "
            f"Allowed values: "
            + ", ".join(sorted(allowed[:20]))
            + (" ..." if len(allowed) > 20 else "")
        )


# =============================================================================
# Prediction Function
# =============================================================================

def predict_cases(
    state: str,
    district: str,
    year: int,
    crime_type: str,
    chargesheeted: int,
    convictions: int,
    population: int,
) -> float:
    """
    Predict crime cases using the trained RandomForest model.
    """

    if model is None or encoders is None:
        raise RuntimeError(
            "ML models are not loaded. Check server startup logs."
        )

    # Validate categorical inputs
    for field_name, value in (
        ("State", state),
        ("District", district),
        ("Crime_Type", crime_type),
    ):
        error = _validate_field(field_name, value)
        if error:
            raise ValueError(error)

    # Encode categorical features
    state_encoded = encoders["State"].transform([state])[0]
    district_encoded = encoders["District"].transform([district])[0]
    crime_encoded = encoders["Crime_Type"].transform([crime_type])[0]

    # Create DataFrame in same order used during training
    input_df = pd.DataFrame(
        {
            "State": [state_encoded],
            "District": [district_encoded],
            "Year": [year],
            "Crime_Type": [crime_encoded],
            "Chargesheeted": [chargesheeted],
            "Convictions": [convictions],
            "Population": [population],
        }
    )

    prediction = model.predict(input_df)[0]
    prediction = round(float(prediction), 2)

    logger.info(
        "Prediction completed",
        extra={
            "state": state,
            "district": district,
            "year": year,
            "crime_type": crime_type,
            "prediction": prediction,
        },
    )

    return prediction