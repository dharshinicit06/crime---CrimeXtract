from pathlib import Path
import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "crime_prediction_model.pkl"
ENCODER_PATH = BASE_DIR / "models" / "label_encoders.pkl"

# Load trained model
model = joblib.load(MODEL_PATH)

# Load encoders
encoders = joblib.load(ENCODER_PATH)


def predict_cases(
    state,
    district,
    year,
    crime_type,
    chargesheeted,
    convictions,
    population,
):
    state = encoders["State"].transform([state])[0]
    district = encoders["District"].transform([district])[0]
    crime_type = encoders["Crime_Type"].transform([crime_type])[0]

    data = pd.DataFrame({
        "State": [state],
        "District": [district],
        "Year": [year],
        "Crime_Type": [crime_type],
        "Chargesheeted": [chargesheeted],
        "Convictions": [convictions],
        "Population": [population],
    })

    prediction = model.predict(data)[0]

    return round(float(prediction), 2)