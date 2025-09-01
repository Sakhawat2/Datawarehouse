# type: ignore
import os
import csv
import logging
from fastapi import FastAPI, Depends, HTTPException,Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Core app modules
from app import models, database, auth
from app.schemas import UserCreate, UserLogin

# Routers
from api.sensor import sensor_router
from api.video import video_router
from ml_dashboard.backend.ml_routes import router as ml_router

# Admin logic
from admin.stats import get_storage_stats

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

# Initialize FastAPI app
app = FastAPI(
    title="Data Warehouse MVP",
    description="Centralized hub for sensor, video, and file data ingestion.",
    version="1.0.0"
)

# Enable CORS (optional but recommended)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static admin dashboard
app.mount("/admin", StaticFiles(directory="admin", html=True), name="admin")

# Include routers
app.include_router(sensor_router, prefix="/api/sensor")
app.include_router(video_router, prefix="/api/video")
app.include_router(ml_router)  # ML route already has prefix="/ml"

# 📦 Helper: Extract unique sensor IDs from CSV
def get_unique_sensors(csv_path: str):
    sensors = set()
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sensors.add(row['Sensor ID'])
    return sorted(sensors)

# 🌐 ML endpoint: List available sensors
@app.get("/ml/sensors")
def list_sensors():
    csv_path = "storage/sensors/sensor_data.csv"
    sensors = get_unique_sensors(csv_path)
    logger.info(f"Found sensors: {sensors}")
    return JSONResponse(sensors)

# 🏠 Root endpoint
@app.get("/")
def home():
    return {"message": "🚀 Welcome to the Data Warehouse API"}

# 📊 Admin stats
@app.get("/api/admin/stats")
def admin_stats():
    return JSONResponse(get_storage_stats())

# 🎥 List videos
@app.get("/api/admin/videos")
def list_video_files():
    video_dir = "storage/videos"
    if not os.path.exists(video_dir):
        return []
    files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
    return JSONResponse(files)

# 👤 Signup
@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(auth.get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = models.User(
        username=user.username,
        hashed_password=auth.hash_password(user.password),
        role=user.role
    )
    db.add(new_user)
    db.commit()
    return {"msg": "User created successfully"}

# 🔐 Login
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(auth.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = auth.create_access_token({"sub": user.username, "role": db_user.role})
    return {"access_token": token, "token_type": "bearer"}

# 🔒 Protected route
@app.get("/api/protected")
def protected(current_user: models.User = Depends(auth.get_current_active_user)):
    return {"msg": f"Welcome {current_user.username}, your role is {current_user.role}"}


# Sensor distribution
@app.get("/api/admin/sensor-distribution")
def sensor_distribution():
    import pandas as pd
    file_path = "storage/sensors/sensor_data.csv"
    if not os.path.exists(file_path):
        return []

    df = pd.read_csv(file_path, encoding='latin1', on_bad_lines='skip')
    df.columns = df.columns.str.strip()
    counts = df["Sensor ID"].value_counts().to_dict()
    return counts


# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# New
CSV_PATH = os.path.join("storage", "sensors", "sensor_data.csv")
# Simulated sensor data
@app.get("/sensor-data")
def get_sensor_data(sensor: str = Query(...)):
    labels = []
    values = []

    try:
        with open(CSV_PATH, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["Sensor ID"] == sensor:
                    labels.append(row["Start Timestamp"])
                    values.append(float(row["Value"]))
    except FileNotFoundError:
        return JSONResponse(content={"error": "CSV file not found"}, status_code=500)

    if not labels:
        return JSONResponse(content={"error": "Sensor not found"}, status_code=404)

    return {
        "name": sensor,
        "labels": labels,
        "data": values
    }

@app.get("/sensors")
def get_sensors():
    sensors = set()
    try:
        with open(CSV_PATH, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                sensors.add(row["Sensor ID"])
    except FileNotFoundError:
        return JSONResponse(content={"error": "CSV file not found"}, status_code=500)

    return list(sensors)

# Storage 
@app.get("/storage-breakdown")
def get_storage_breakdown():
    base_folder = "storage"  # or your actual folder
    categories = {
        "Sensor DB": "sensor_db",
        "Video Files": "videos",
        "Other Files": "others"
    }

    breakdown = {}
    for label, folder in categories.items():
        path = os.path.join(base_folder, folder)
        size = 0
        if os.path.exists(path):
            for f in os.listdir(path):
                fp = os.path.join(path, f)
                if os.path.isfile(fp):
                    size += os.path.getsize(fp)
        breakdown[label] = round(size / (1024 * 1024), 2)  # MB

    return breakdown
    

