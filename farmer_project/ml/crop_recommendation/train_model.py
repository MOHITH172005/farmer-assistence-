import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

# 1️⃣ Load dataset
df = pd.read_csv("crop_dataset.csv")

X = df[["soil", "season", "rainfall", "temperature"]]
y = df["crop"]

# 2️⃣ Preprocessing
categorical_features = ["soil", "season"]
numeric_features = ["rainfall", "temperature"]

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ("num", "passthrough", numeric_features),
    ]
)

# 3️⃣ ML Model
model = RandomForestClassifier(
    n_estimators=150,
    random_state=42
)

# 4️⃣ Pipeline
pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)

# 5️⃣ Train model
pipeline.fit(X, y)

# 6️⃣ Save model & encoder
joblib.dump(pipeline, "crop_model.pkl")
joblib.dump(preprocessor, "encoder.pkl")

print("✅ Crop Recommendation ML model trained & saved successfully")
