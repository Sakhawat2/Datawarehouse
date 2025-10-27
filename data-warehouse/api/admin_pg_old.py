# api/admin_pg.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models
import os

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

# ✅ 1. Sensor count (used in your JS)
@router.get("/sensor-count")
def sensor_count(db: Session = Depends(get_db)):
    sensors = db.query(models.Sensor.type, func.count(models.Sensor.id)).group_by(models.Sensor.type).all()
    return {t or "Unknown": c for t, c in sensors}

# ✅ 2. Video storage (used in your JS)
@router.get("/video-storage")
def video_storage(db: Session = Depends(get_db)):
    videos = db.query(models.Video.filename, models.Video.size_mb).all()
    buckets = {"Small": 0, "Medium": 0, "Large": 0}
    files = {}
    for name, size in videos:
        files[name] = size
        if size < 10:
            buckets["Small"] += 1
        elif size < 100:
            buckets["Medium"] += 1
        else:
            buckets["Large"] += 1
    return {"buckets": buckets, "files": files}

# ✅ 3. Storage breakdown (used in your JS)
@router.get("/storage-breakdown")
def storage_breakdown():
    base_folder = "storage"
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
        breakdown[label] = round(size / (1024 * 1024), 2)  # Convert to MB

    return breakdown
