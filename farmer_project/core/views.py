from django.shortcuts import render, redirect
from django.shortcuts import render
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .ml_utils import predict_disease, get_disease_details
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .ml_utils import predict_disease, get_disease_details
from .groq_chat import ask_farming_ai
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect
import re
from django.contrib import messages
from django.contrib.auth.models import User
from .models import FarmerProfile
from datetime import datetime, timedelta
import random
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import FarmerProfile, Notification
from .ml_utils import get_crop_calendar
from django.http import JsonResponse
from .models import FarmerProfile
import random
from django.http import JsonResponse
from .utils import generate_farmer_ids
from core.models import FarmerProfile
from django.shortcuts import render
from django.conf import settings
import joblib
import pandas as pd
from groq import Groq
import numpy as np
import os
import joblib
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.db.models import Count
from core.models import FarmerProfile, Notification, AIRequestLog   # adjust if needed
from datetime import date, timedelta



BASE_ML_PATH = os.path.join(
    settings.BASE_DIR,
    "ml",
    "crop_recommendation"
)

BASE_CALENDAR_PATH = os.path.join(
    settings.BASE_DIR,
    "ml",
    "crop_calendar"
)

# ======================
# SPLASH PAGE
# ======================
def splash(request):
    return render(request, "splash.html")


# ======================
# LOGIN
# ======================
@csrf_protect
def login_view(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        password = request.POST.get("password")

        try:
            user = User.objects.get(username=user_id)
        except User.DoesNotExist:
            messages.error(request, "User ID not found. Please register.")
            return redirect("login")

        # ✅ AUTHENTICATE CORRECTLY
        user = authenticate(
            request,
            username=user.username,   # MUST be username
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        messages.error(
            request,
            "Incorrect password. <a href='/forgot-password/'>Forgot Password?</a>"
        )
        return redirect("login")

    return render(request, "login.html")

# ======================
# REGISTER
# ======================

def register_view(request):
    if request.method == "POST":
        farmer_id = request.POST.get("farmer_id")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        full_name = request.POST.get("full_name")
        mobile = request.POST.get("mobile")
        pincode = request.POST.get("pincode")
        district = request.POST.get("district")
        state = request.POST.get("state")
        primary_crop = request.POST.get("primary_crop")
        land_area = request.POST.get("land_area")
        photo = request.FILES.get("photo")

        # ✅ BASIC VALIDATION
        if not farmer_id:
            messages.error(request, "Please select a Farmer ID")
            return redirect("register")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        if User.objects.filter(username=farmer_id).exists():
            messages.error(request, "Farmer ID already taken")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("register")

        # ✅ CREATE USER
        user = User.objects.create_user(
            username=farmer_id,
            email=email,
            password=password1
        )

        # Optional (fine to keep)
        user.first_name = full_name
        user.save()

        # ✅ CREATE FARMER PROFILE (FIX HERE 🔥)
        FarmerProfile.objects.create(
            user=user,
            farmer_id=farmer_id,
            full_name=full_name,   # 👈 THIS LINE WAS MISSING
            mobile=mobile,
            pincode=pincode,
            district=district,
            state=state,
            primary_crop=primary_crop,
            land_area=land_area,
            photo=photo
        )

        messages.success(request, "Account created successfully. Please login.")
        return redirect("login")

    return render(request, "register.html")
    return render(request, "register.html")# ======================
# FORGOT PASSWORD – SEND OTP
# ======================
def forgot_password(request):
    if request.method == "POST":
        mobile = request.POST.get("mobile")

        try:
            profile = FarmerProfile.objects.get(mobile=mobile)
        except FarmerProfile.DoesNotExist:
            messages.error(request, "Mobile number not registered")
            return redirect("forgot_password")

        otp = random.randint(100000, 999999)

        # ✅ store as STRING (IMPORTANT FIX)
        request.session["reset_otp"] = str(otp)
        request.session["reset_mobile"] = mobile
        request.session["otp_time"] = timezone.now().isoformat()

        print("DEBUG OTP:", otp)  # remove in production

        messages.success(request, "OTP sent successfully")
        return redirect("verify_otp")

    return render(request, "auth/forgot_password.html")

# ======================
# VERIFY OTP
# ======================
def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        stored_otp = request.session.get("otp")
        otp_time = request.session.get("otp_time")

        if not stored_otp or not otp_time:
            messages.error(request, "OTP expired")
            return redirect("forgot_password")

        otp_time = datetime.fromisoformat(otp_time)

        if timezone.now() - otp_time > timedelta(minutes=10):
            request.session.flush()
            messages.error(request, "OTP expired")
            return redirect("forgot_password")

        if str(entered_otp) == str(stored_otp):
            return redirect("reset_password")

        messages.error(request, "Invalid OTP")

    return render(request, "verify_otp.html")


# ======================
# RESET PASSWORD
# ======================
def reset_password(request):
    # ❌ Block direct access
    if not request.session.get("otp_verified"):
        messages.error(request, "Unauthorized access")
        return redirect("login")

    if request.method == "POST":
        p1 = request.POST.get("password1")
        p2 = request.POST.get("password2")

        # ❌ Password mismatch
        if p1 != p2:
            messages.error(request, "Passwords do not match")
            return redirect("reset_password")

        # 🔐 Strong password rule
        if not re.match(
            r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$',
            p1
        ):
            messages.error(
                request,
                "Password must contain Uppercase, Lowercase, Number & Symbol"
            )
            return redirect("reset_password")

        mobile = request.session.get("reset_mobile")
        if not mobile:
            messages.error(request, "Session expired. Please try again.")
            return redirect("forgot_password")

        # ✅ GET FARMER → USER
        profile = FarmerProfile.objects.get(mobile=mobile)
        user = profile.user

        # ✅ REPLACE OLD PASSWORD WITH NEW PASSWORD
        user.set_password(p1)
        user.save()

        # ✅ VERY IMPORTANT (FIX)
        logout(request)              # 🔥 clears auth backend cache
        request.session.flush()      # 🔥 clears OTP + session data

        messages.success(
            request,
            "Password changed successfully. Please login with new password."
        )
        return redirect("login")

    return render(request, "auth/reset_password.html")


# ======================
# DASHBOARD (ML INTEGRATED)
# ======================
@login_required
def dashboard(request):
    profile = FarmerProfile.objects.filter(user=request.user).first()

    # 🌾 Default: no duration
    crop_duration = None

    # 🔹 TEMP / BASE LOGIC (can be replaced with ML later)
    if profile and profile.primary_crop:
        crop_duration_map = {
            "Rice": 120,
            "Wheat": 140,
            "Maize": 110,
            "Cotton": 180,
            "Papaya": 210,
            "Banana": 300,
            "Groundnut": 110,
        }
        crop_duration = crop_duration_map.get(profile.primary_crop)

    context = {
        # 👋 Farmer name (FROM DATABASE)
        "farmer_name": profile.full_name if profile and profile.full_name else "Farmer",

        # 🆔 Farmer ID
        "farmer_id": request.user.username,

        # 📍 Farmer details
        "district": profile.district if profile and profile.district else "Not provided",
        "primary_crop": profile.primary_crop if profile and profile.primary_crop else "Not selected",
        "land_area": profile.land_area if profile and profile.land_area else "0",

        # ⏱️ REAL crop duration (THIS FIXES AI PREDICTED)
        "crop_duration": crop_duration,

        # 👤 Farmer photo
        "farmer_photo": profile.photo.url if profile and profile.photo else None,
    }

    return render(request, "dashboard.html", context)


# ======================
# NOTIFICATION COUNT API
# ======================
@login_required
def notification_count(request):
    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return JsonResponse({"count": count})

@login_required
def alert_list(request):
    alerts = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")[:5]

    data = []
    for alert in alerts:
        data.append({
            "message": alert.message,
            "time": alert.created_at.strftime("%d %b %H:%M")
        })

    return JsonResponse({"alerts": data})
def crop_recommendation(request):
    recommended_crops = []
    crop_duration = None
    harvest_date = None
    source = "ML Model"

    if request.method == "POST":
        # 🔹 SAFE INPUT FETCHING
        soil = request.POST.get("soil_type")
        season = request.POST.get("season")

        try:
            rainfall = float(request.POST.get("rainfall"))
            temperature = float(request.POST.get("temperature"))
        except (TypeError, ValueError):
            rainfall = 0.0
            temperature = 0.0

        # 🔹 DEFAULT FALLBACK
        DEFAULT_CROP = "Rice"
        DEFAULT_DURATION = 120

        try:
            # ==========================
            # 🔹 TRY ML MODEL FIRST
            # ==========================
            model = joblib.load("ml/crop_model.pkl")
            encoder = joblib.load("ml/encoder.pkl")

            X_cat = encoder.transform([[soil, season]])
            X = np.concatenate([X_cat, [[rainfall, temperature]]], axis=1)

            probs = model.predict_proba(X)
            confidence = float(max(probs[0]))

            if confidence >= 0.7:
                crop = model.predict(X)[0]
                recommended_crops = [crop]
                source = "ML Model"
            else:
                raise Exception("Low confidence")

        except Exception:
            # ==========================
            # 🔹 FALLBACK TO GROQ AI
            # ==========================
            source = "Groq AI"

            client = Groq(api_key=settings.GROQ_API_KEY)

            prompt = f"""
            Suggest ONLY ONE best crop.
            Soil type: {soil}
            Season: {season}
            Rainfall: {rainfall} mm
            Temperature: {temperature} °C
            """

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )

            crop = response.choices[0].message.content.strip()
            recommended_crops = [crop]

            # ✅ LOG AI USAGE (REAL COUNT)
            AIRequestLog.objects.create(
                user=request.user,
                feature="crop_recommendation"
            )

        # ==========================
        # 🔹 ENSURE AT LEAST ONE CROP
        # ==========================
        if not recommended_crops:
            recommended_crops = [DEFAULT_CROP]

        # ==========================
        # 🔹 CROP DURATION LOGIC
        # ==========================
        duration_map = {
            "Rice": 120,
            "Wheat": 140,
            "Maize": 110,
            "Cotton": 180,
            "Papaya": 210,
            "Banana": 300,
        }

        crop_name = recommended_crops[0]
        crop_duration = duration_map.get(crop_name, DEFAULT_DURATION)

        # ==========================
        # 🔹 HARVEST DATE
        # ==========================
        harvest_date = date.today() + timedelta(days=crop_duration)

    return render(request, "crop_recommendation.html", {
        "recommended_crops": recommended_crops,
        "crop_duration": crop_duration,
        "harvest_date": harvest_date,
        "source": source,
        "page_title": "Crop Recommendation"
    })
def disease_detection(request):
    result = None

    if request.method == "POST" and request.FILES.get("leaf"):
        image = request.FILES["leaf"]
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        image_path = fs.path(filename)

        disease, confidence = predict_disease(image_path)
        details = get_disease_details(disease)

        result = {
            "disease": disease,
            "confidence": confidence,
            "details": details
        }

    return render(request, "disease_detection.html", {"result": result})

def plant_doctor(request):
    return render(request, "plant_doctor.html")
def weather_forecast(request):
    # Dummy weather data (API-ready)
    forecast = [
        {"day": "Today", "temp": "32°C", "rain": "No Rain"},
        {"day": "Tomorrow", "temp": "31°C", "rain": "Light Rain"},
        {"day": "Day 3", "temp": "30°C", "rain": "Moderate Rain"},
        {"day": "Day 4", "temp": "29°C", "rain": "Heavy Rain"},
        {"day": "Day 5", "temp": "31°C", "rain": "No Rain"},
        {"day": "Day 6", "temp": "33°C", "rain": "No Rain"},
        {"day": "Day 7", "temp": "34°C", "rain": "Sunny"},
    ]

    return render(request, "weather_forecast.html", {
        "forecast": forecast
    })
def market_prices(request):
    district = request.GET.get("district")

    # Dummy mandi data (API-ready)
    mandi_data = []

    if district:
        mandi_data = [
            {
                "mandi": "APMC " + district,
                "crops": [
                    {"name": "Rice", "price": "₹2,200 / quintal"},
                    {"name": "Maize", "price": "₹1,850 / quintal"},
                    {"name": "Wheat", "price": "₹2,100 / quintal"},
                ]
            },
            {
                "mandi": district + " Rural Mandi",
                "crops": [
                    {"name": "Rice", "price": "₹2,180 / quintal"},
                    {"name": "Groundnut", "price": "₹5,200 / quintal"},
                ]
            }
        ]

    return render(request, "market_prices.html", {
        "mandi_data": mandi_data,
        "district": district
    })
def fertilizer_advice(request):
    result = None

    if request.method == "POST":
        crop = request.POST.get("crop")
        soil = request.POST.get("soil")
        acres = float(request.POST.get("acres"))
        stage = request.POST.get("stage")

        # Basic intelligent rules (can be ML later)
        if crop == "Rice":
            fert = {
                "Urea": f"{int(50 * acres)} kg",
                "DAP": f"{int(25 * acres)} kg",
                "Potash": f"{int(20 * acres)} kg"
            }
            method = "Broadcast & irrigation"
        elif crop == "Wheat":
            fert = {
                "Urea": f"{int(45 * acres)} kg",
                "DAP": f"{int(30 * acres)} kg"
            }
            method = "Top dressing"
        else:
            fert = {
                "NPK": f"{int(40 * acres)} kg"
            }
            method = "Soil application"

        result = {
            "crop": crop,
            "soil": soil,
            "stage": stage,
            "fertilizers": fert,
            "method": method,
            "warning": "Do not exceed recommended dosage"
        }

    return render(request, "fertilizer_advice.html", {"result": result})
def irrigation(request):
    result = None

    if request.method == "POST":
        crop = request.POST.get("crop")
        soil = request.POST.get("soil")
        acres = float(request.POST.get("acres"))
        season = request.POST.get("season")

        # Simple rule-based logic (ML-ready)
        if crop == "Rice":
            daily_water = 120 * acres
            schedule = "Daily irrigation"
        elif crop == "Wheat":
            daily_water = 70 * acres
            schedule = "Once every 3 days"
        else:
            daily_water = 60 * acres
            schedule = "Once every 4 days"

        if soil == "Sandy":
            daily_water += 20 * acres

        result = {
            "crop": crop,
            "soil": soil,
            "season": season,
            "daily": f"{daily_water} liters/day",
            "weekly": f"{daily_water * 7} liters/week",
            "schedule": schedule,
            "alert": "Reduce irrigation if rainfall occurs"
        }

    return render(request, "irrigation.html", {"result": result})
def govt_schemes(request):
    return render(request, "govt_schemes.html")

def ai_assistant(request):
    answer = None
    question = None

    if request.method == "POST":
        question = request.POST.get("question")
        if question:
            answer = ask_farming_ai(question)

    return render(request, "ai_assistant.html", {
        "question": question,
        "answer": answer
    })
@login_required
def profile(request):
    if request.method == "POST":
        request.user.email = request.POST.get("email")
        request.user.save()

    return render(request, "profile.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

def generate_farmer_ids(request):
    ids = []

    while len(ids) < 3:
        fid = f"FARMER{random.randint(100000, 999999)}"
        if not FarmerProfile.objects.filter(farmer_id=fid).exists():
            ids.append(fid)

    return JsonResponse({"ids": ids})
def generate_farmer_ids_view(request):
    ids = []

    while len(ids) < 3:
        fid = f"FARM{random.randint(100000, 999999)}"
        if not User.objects.filter(username=fid).exists():
            ids.append(fid)

    return JsonResponse({"ids": ids})

def trouble_login(request):
    step = request.session.get("step", "mobile")

    # ================= STEP 1: MOBILE =================
    if request.method == "POST" and step == "mobile":
        mobile = request.POST.get("mobile")

        try:
            farmer = FarmerProfile.objects.get(mobile=mobile)

            # Generate OTP
            otp = random.randint(100000, 999999)

            # Store session data
            request.session["otp"] = str(otp)
            request.session["mobile"] = mobile
            request.session["step"] = "otp"

            # TODO: Send OTP via SMS (Fast2SMS / Twilio)
            print("DEBUG OTP:", otp)

            return render(request, "auth/trouble_login.html", {
                "step": "otp"
            })

        except FarmerProfile.DoesNotExist:
            messages.error(request, "User not found. Please create an account.")
            return redirect("register")

    # ================= STEP 2: OTP =================
    if request.method == "POST" and step == "otp":
        entered_otp = request.POST.get("otp")
        saved_otp = request.session.get("otp")
        mobile = request.session.get("mobile")

        if entered_otp == saved_otp:
            farmer = FarmerProfile.objects.get(mobile=mobile)

            # CLEAR OTP
            request.session.flush()

            return render(request, "auth/trouble_login.html", {
                "step": "success",
                "user_id": farmer.farmer_id   # ✅ THIS WAS MISSING
            })
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, "auth/trouble_login.html", {
                "step": "otp"
            })

    # ================= DEFAULT =================
    request.session["step"] = "mobile"
    return render(request, "auth/trouble_login.html", {
        "step": "mobile"
    })
def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()

        stored_otp = request.session.get("reset_otp")
        otp_time = request.session.get("otp_time")

        if not stored_otp or not otp_time:
            messages.error(request, "OTP expired")
            return redirect("forgot_password")

        otp_time = datetime.fromisoformat(otp_time)

        # ⏰ OTP expiry – 5 minutes
        if timezone.now() > otp_time + timedelta(minutes=5):
            request.session.flush()
            messages.error(request, "OTP expired")
            return redirect("forgot_password")

        # ✅ STRING vs STRING comparison (CRITICAL FIX)
        if entered_otp == stored_otp:
            request.session["otp_verified"] = True
            return redirect("reset_password")

        messages.error(request, "Invalid OTP")
        return render(request, "auth/verify_otp.html")

    return render(request, "auth/verify_otp.html")

def contact_doctor(request):
    return render(request, "plant_doctor.html", {
        "page_title": "Plant Doctor"
    })


@login_required
def get_notifications(request):
    qs = Notification.objects.filter(user=request.user)
    unread = qs.filter(is_read=False).count()

    return JsonResponse({
        "unread_count": unread
    })

@login_required
def mark_notifications_read(request):
    if request.method == "POST":
        Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        return JsonResponse({"status": "ok"})
def crop_calendar_ai(request):
    crop = ""
    duration = ""
    harvest = "AI Predicted"
    source = "ML"

    # ✅ GET REGION FROM FARMER PROFILE
    profile = FarmerProfile.objects.get(user=request.user)
    region = f"{profile.district}, {profile.state}"

    if request.method == "POST":
        crop_input = request.POST.get("crop")

        # 🔹 Load trained ML model
        model = joblib.load(
            os.path.join(BASE_CALENDAR_PATH, "crop_calendar_model.pkl")
        )

        try:
            # ✅ ML prediction
            duration = model.predict([[crop_input]])[0]
            crop = crop_input

        except Exception:
            # ❌ ML failed → Groq fallback
            source = "Groq AI"
            client = Groq(api_key=settings.GROQ_API_KEY)

            prompt = f"""
            For crop {crop_input} grown in {region},
            give estimated growing duration in days.
            Give only number.
            """

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )

            duration = response.choices[0].message.content.strip()
            crop = crop_input

    return render(request, "crop_calendar.html", {
        "crop": crop,
        "region": region,
        "duration": duration,
        "harvest": harvest,
        "source": source
    })

def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        # 🔍 DEBUG (TEMPORARY – CHECK TERMINAL)
        print("ADMIN LOGIN ATTEMPT:", repr(username))

        if username.upper() != "FARMERADMIN":
            messages.error(request, "Invalid Admin ID")
            return render(request, "admin_panel/login.html")

        user = authenticate(request, username="FARMERADMIN", password=password)

        if user is None:
            messages.error(request, "Invalid Password")
            return render(request, "admin_panel/login.html")

        login(request, user)
        return redirect("admin_dashboard")

    return render(request, "admin_panel/login.html")

def is_admin(user):
    return user.is_authenticated and user.username == "FARMERADMIN"


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    if not is_admin(request.user):
        return redirect("admin_login")

    context = {
        "total_farmers": FarmerProfile.objects.count(),
        "total_users": User.objects.count(),
        "ai_requests": Notification.objects.count(),
        "weather_requests": 0,  # placeholder
        "ml_usage": 0,          # placeholder
    }
    return render(request, "admin_panel/dashboard.html", context)
def admin_forgot_password(request):
    if request.method == "POST":
        username = request.POST.get("username")

        print("DEBUG USERNAME FROM FORM:", username)  # 👈 ADD THIS

        if username != "FARMERADMIN":
            messages.error(request, "Invalid Admin ID")
            return redirect("admin_forgot_password")

        otp = random.randint(100000, 999999)

        request.session["admin_otp"] = str(otp)
        request.session["admin_user"] = "FARMERADMIN"

        print("\n" + "=" * 40)
        print("🔐 ADMIN RESET OTP:", otp)
        print("=" * 40 + "\n")

        return redirect("admin_verify_otp")

    return render(request, "admin_panel/forgot.html")

def admin_reset_password(request):
    if not request.session.get("admin_verified"):
        return redirect("admin_login")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")

        if password != confirm:
            messages.error(request, "Passwords do not match")
            return redirect("admin_reset_password")

        admin_user = User.objects.get(username="FARMERADMIN")
        admin_user.set_password(password)
        admin_user.save()

        request.session.flush()
        messages.success(request, "Password reset successful. Please login.")
        return redirect("admin_login")

    return render(request, "admin_panel/reset.html")
def admin_verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        saved_otp = request.session.get("admin_otp")

        if not saved_otp:
            return redirect("admin_forgot_password")

        if entered_otp == saved_otp:
            # ✅ OTP VERIFIED
            request.session["admin_verified"] = True
            return redirect("admin_reset_password")
        else:
            return render(request, "admin_panel/verify_otp.html", {
                "error": "Invalid OTP"
            })

    return render(request, "admin_panel/verify_otp.html")
def admin_splash(request):
    return render(request, "admin_panel/splash.html")
@login_required
def admin_dashboard(request):
    if request.user.username != "FARMERADMIN":
        return redirect("admin_login")

    context = {
        "farmers": FarmerProfile.objects.count(),
        "total_farmers": FarmerProfile.objects.count(),   # ✅ TOTAL REGISTERED FARMERS
        "users": User.objects.count(),
        "ai_requests": AIRequestLog.objects.count(),
        "weather_requests": AIRequestLog.objects.filter(feature="weather").count(),
        "ml_usage": AIRequestLog.objects.filter(feature="ml").count(),
        "total_farmers": FarmerProfile.objects.count(),
        "active_farmers": FarmerProfile.objects.count(),  # optional
        "weather_requests": AIRequestLog.objects.filter(
            feature="weather"
        ).count(),

        # 🤖 AI REQUESTS (ALL FEATURES)
        "ai_requests": AIRequestLog.objects.count(),
    
    }
    return render(request, "admin_panel/dashboard.html", context)
@login_required
def weather_view(request):
    # ✅ Log weather usage
    AIRequestLog.objects.create(
        user=request.user,
        feature="weather"
    )

    # your existing weather API logic here...
    return render(request, "weather.html")

@login_required
def admin_farmers(request):
    if not request.user.is_superuser:
        return redirect("login")

    farmers = FarmerProfile.objects.all()
    return render(request, "admin_panel/farmers.html", {
        "farmers": farmers
    })
@login_required
def toggle_farmer(request, id):
    farmer = FarmerProfile.objects.get(id=id)
    farmer.is_active = not farmer.is_active
    farmer.save()
    return redirect("admin_farmers")
@login_required
def delete_farmer(request, id):
    farmer = FarmerProfile.objects.get(id=id)
    farmer.user.delete()   # deletes both user + farmer profile
    return redirect("admin_farmers")

