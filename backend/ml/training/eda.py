from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR.parent / "dataset" / "dataset.csv"

df = pd.read_csv(DATASET_PATH)

print("First 5 rows:")
print(df.head())

print("\nDataset Info:")
print(df.info())

print("\nStatistics:")
print(df.describe())

print("\nMissing Values:")
print(df.isnull().sum())

print("\nDataset Shape:")
print(df.shape)

print("\nColumn Names:")
print(df.columns.tolist())