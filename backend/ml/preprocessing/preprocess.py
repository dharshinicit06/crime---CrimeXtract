from pathlib import Path
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder

# ----------------------------------------
# Paths
# ----------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = BASE_DIR / "dataset" / "dataset.csv"
MODEL_DIR = BASE_DIR / "models"

MODEL_DIR.mkdir(exist_ok=True)

# ----------------------------------------
# Load Dataset
# ----------------------------------------

df = pd.read_csv(DATASET_PATH)

# For development use only first 5000 rows
df = df.head(5000)

print(f"Dataset Loaded : {df.shape}")

# ----------------------------------------
# Encode categorical columns
# ----------------------------------------

encoders = {}

categorical_columns = [
    "State",
    "District",
    "Crime_Type"
]

for column in categorical_columns:
    encoder = LabelEncoder()
    df[column] = encoder.fit_transform(df[column])

    encoders[column] = encoder

print("\nCategorical columns encoded successfully.")

# ----------------------------------------
# Save Encoders
# ----------------------------------------

ENCODER_PATH = MODEL_DIR / "label_encoders.pkl"

joblib.dump(encoders, ENCODER_PATH)

print(f"\nEncoders saved at:\n{ENCODER_PATH}")

# ----------------------------------------
# Preview
# ----------------------------------------

print("\nProcessed Dataset")

print(df.head())

# ----------------------------------------
# Save processed dataset (optional)
# ----------------------------------------

PROCESSED_PATH = BASE_DIR / "dataset" / "processed_dataset.csv"

df.to_csv(PROCESSED_PATH, index=False)

print(f"\nProcessed dataset saved at:\n{PROCESSED_PATH}")