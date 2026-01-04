import os
import joblib
import datetime

# -----------------------------
# BASE DIRECTORY
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# -----------------------------
# CROP CALENDAR MODEL
# -----------------------------
MODEL_PATH = os.path.join(BASE_DIR, "ml", "crop_calendar_model.pkl")

# Load model safely
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    model = None


def get_crop_calendar(crop, sowing_month):
    """
    Predict crop duration and return calendar info
    """

    if model:
        duration_days = int(model.predict([[sowing_month]])[0])
    else:
        # fallback if model missing
        duration_days = 120

    today = datetime.date.today()
    harvest_date = today + datetime.timedelta(days=duration_days)

    return {
        "crop": crop,
        "sowing_month": sowing_month,
        "duration_days": duration_days,
        "harvest_date": harvest_date.strftime("%d %B %Y")
    }


# -----------------------------
# DISEASE PREDICTION (TEMPORARY)
# -----------------------------
def predict_disease(image_path):
    """
    TEMPORARY dummy disease prediction.
    Later this will be replaced with CNN / Deep Learning.
    """

    # Fake prediction (for now)
    disease = "Leaf Blight"
    confidence = 91.8

    return disease, confidence


# -----------------------------
# DISEASE KNOWLEDGE BASE
# -----------------------------
DISEASE_INFO = {
    "Healthy": {
        "solution": "Your crop is healthy. Continue regular irrigation and fertilization.",
        "fertilizers": ["Urea", "DAP"],
        "medicine": "Not required",
        "prevention": "Maintain balanced nutrition."
    },
    "Leaf Blight": {
        "solution": "Remove infected leaves and improve drainage.",
        "fertilizers": ["Potash", "Zinc Sulphate"],
        "medicine": "Mancozeb Spray",
        "prevention": "Avoid water stagnation."
    },
    "Brown Spot": {
        "solution": "Apply fungicide and avoid overcrowding.",
        "fertilizers": ["NPK 19-19-19"],
        "medicine": "Carbendazim",
        "prevention": "Proper spacing & clean field."
    },
    "Powdery Mildew": {
        "solution": "Spray sulphur-based fungicide.",
        "fertilizers": ["DAP", "Sulphur"],
        "medicine": "Wettable Sulphur",
        "prevention": "Avoid excess nitrogen."
    },
    "Rust": {
        "solution": "Apply systemic fungicide immediately.",
        "fertilizers": ["Potash"],
        "medicine": "Propiconazole",
        "prevention": "Crop rotation."
    }
}


def get_disease_details(disease):
    return DISEASE_INFO.get(disease, {})
