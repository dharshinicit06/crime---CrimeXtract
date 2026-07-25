from pathlib import Path
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)
from sklearn.model_selection import train_test_split

# ---------------------------------------
# Paths
# ---------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = BASE_DIR / "dataset" / "processed_dataset.csv"
MODEL_DIR = BASE_DIR / "models"

MODEL_DIR.mkdir(exist_ok=True)

# ---------------------------------------
# Load Dataset
# ---------------------------------------

df = pd.read_csv(DATA_PATH)

print(f"Dataset Loaded : {df.shape}")

# ---------------------------------------
# Features & Target
# ---------------------------------------

X = df[
    [
        "State",
        "District",
        "Year",
        "Crime_Type",
        "Chargesheeted",
        "Convictions",
        "Population",
    ]
]

y = df["Cases_Reported"]

# ---------------------------------------
# Split Dataset
# ---------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
)

print(f"Training Samples : {len(X_train)}")
print(f"Testing Samples  : {len(X_test)}")

# ---------------------------------------
# Train Model
# ---------------------------------------

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

print("\nTraining Model...")

model.fit(X_train, y_train)

print("Training Completed!")

# ---------------------------------------
# Prediction
# ---------------------------------------

predictions = model.predict(X_test)

# ---------------------------------------
# Evaluation
# ---------------------------------------

mae = mean_absolute_error(y_test, predictions)
mse = mean_squared_error(y_test, predictions)
rmse = mse ** 0.5
r2 = r2_score(y_test, predictions)

print("\n========== MODEL PERFORMANCE ==========")

print(f"MAE  : {mae:.2f}")
print(f"RMSE : {rmse:.2f}")
print(f"R²   : {r2:.4f}")

# ---------------------------------------
# Save Model
# ---------------------------------------

MODEL_PATH = MODEL_DIR / "crime_prediction_model.pkl"

joblib.dump(model, MODEL_PATH)

print("\nModel Saved Successfully!")

print(MODEL_PATH)