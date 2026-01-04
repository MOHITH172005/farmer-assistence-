# ml/crop_calendar_model.py

import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor

# -----------------------------
# PATH HANDLING (FIXED)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "crop_calendar_data.csv")
MODEL_PATH = os.path.join(BASE_DIR, "crop_calendar_model.pkl")

# -----------------------------
# LOAD DATA
# -----------------------------
data = pd.read_csv(CSV_PATH)

X = data[["sowing_month"]]
y = data["crop_duration_days"]

# -----------------------------
# TRAIN MODEL
# -----------------------------
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# -----------------------------
# SAVE MODEL
# -----------------------------
joblib.dump(model, MODEL_PATH)

print("✅ Crop Calendar ML model trained & saved successfully")
print("📁 Model path:", MODEL_PATH)
