import os
import csv
import logging
from fastapi import FastAPI, Depends, HTTPException
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
