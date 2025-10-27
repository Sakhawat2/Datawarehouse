# server.py
import logging
import os
import datetime
import io
import csv
import zipfile
from fastapi import (
    FastAPI, Form, Depends, HTTPException, UploadFile, File
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, database
from app.database import engine
from app.auth import (
    create_access_token,
    hash_password,
    verify_password,
    get_current_active_user as get_current_user
)
from fastapi import Depends

from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

SECRET_KEY = "your-secret-key"        # replace with the one from app.auth
ALGORITHM = "HS256"

# ───────────────────────────────────────────────
# ✅ Initialize uploads database
# ───────────────────────────────────────────────

import sqlite3

DB_PATH = "datawarehouse.db"  # adjust if your DB file name is different

# ✅ Ensure uploads table exists
def init_uploads_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            size_mb REAL DEFAULT 0,
            username TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_uploads_table()



# 🔐 Define oauth2_scheme globally so Depends() can use it
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Routers
from api.sensor_pg import router as sensor_pg_router
from api.export import router as export_router



# ───────────────────────────────────────────────
# App setup
# ───────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="📦 Data Warehouse API",
    description="Centralized platform for sensor, video, and storage management.",
    version="2.3.0",
)

models.Base.metadata.create_all(bind=engine)

# ───────────────────────────────────────────────
# Database setup
# ───────────────────────────────────────────────
models.Base.metadata.create_all(bind=engine)


# ───────────────────────────────────────────────
# Middleware
# ───────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────────────────────────────
# 🗂️ Static File Mounts (Admin + User)
# ───────────────────────────────────────────────
# Admin dashboard and related pages
app.mount("/admin", StaticFiles(directory="admin", html=True), name="admin")

# ✅ NEW: User dashboard pages moved to /admin/user/
# You can access user UI now at http://localhost:8000/user/user.html
app.mount("/user", StaticFiles(directory="admin/user", html=True), name="user")

# ✅ Uploaded file previews
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploaded_files", StaticFiles(directory=UPLOAD_DIR), name="uploaded_files")

# Routers
app.include_router(sensor_pg_router)
app.include_router(export_router)

# ───────────────────────────────────────────────
# Root & Health
# ───────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "🚀 Data Warehouse API is running!",
        "docs": "/docs",
        "admin_ui": "/admin/",
        "user_ui": "/user/user.html"
    }

@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "database": "unreachable"}


# ───────────────────────────────────────────────
# 📊 Admin Dashboard Endpoints
# ───────────────────────────────────────────────
@app.get("/api/admin/storage-usage")
def get_storage_usage():
    base_folder = "storage"
    usage = {"sensors": 0.0, "videos": 0.0, "others": 0.0}

    if not os.path.exists(base_folder):
        return JSONResponse({"error": "Storage folder not found"}, status_code=404)

    for root, _, files in os.walk(base_folder):
        for file in files:
            try:
                size_mb = os.path.getsize(os.path.join(root, file)) / (1024 * 1024)
                if "videos" in root:
                    usage["videos"] += size_mb
                elif "sensor" in root or file.endswith((".db", ".csv")):
                    usage["sensors"] += size_mb
                else:
                    usage["others"] += size_mb
            except Exception:
                continue

    total = sum(usage.values())
    return {"total_storage_mb": round(total, 2),
            "details": {k: round(v, 2) for k, v in usage.items()}}


@app.get("/api/admin/sensor-count")
def get_sensor_count():
    db: Session = database.SessionLocal()
    try:
        results = (
            db.query(models.Sensor.name, func.count(models.SensorReading.id))
            .outerjoin(models.SensorReading, models.Sensor.id == models.SensorReading.sensor_id)
            .group_by(models.Sensor.id)
            .all()
        )
        return {name: int(count) for name, count in results}
    finally:
        db.close()


@app.get("/api/admin/video-storage")
def get_video_storage():
    video_dir = "storage/videos"
    size_buckets = {"Small (<10MB)": 0, "Medium (10–100MB)": 0, "Large (>100MB)": 0}
    file_sizes = {}

    if not os.path.exists(video_dir):
        return {"buckets": size_buckets, "files": file_sizes}

    for filename in os.listdir(video_dir):
        path = os.path.join(video_dir, filename)
        if os.path.isfile(path):
            size_mb = round(os.path.getsize(path) / (1024 * 1024), 2)
            file_sizes[filename] = size_mb
            if size_mb < 10:
                size_buckets["Small (<10MB)"] += 1
            elif size_mb < 100:
                size_buckets["Medium (10–100MB)"] += 1
            else:
                size_buckets["Large (>100MB)"] += 1

    return {"buckets": size_buckets, "files": file_sizes}


# ───────────────────────────────────────────────
# 📈 Sensor Data API (for frontend)
# ───────────────────────────────────────────────

from fastapi import Depends, Form, HTTPException, APIRouter
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse, StreamingResponse
import datetime, io, csv, zipfile
from app.database import get_db
from app import models
from app.auth import get_current_active_user

router = APIRouter()

# ✅ Get all sensors (admin sees all, user sees only their own)
@app.get("/api/sensors")
def get_sensors(user: models.User = Depends(get_current_active_user)):
    db = database.SessionLocal()
    try:
        query = db.query(models.Sensor)
        if not user.is_admin:
            query = query.filter(models.Sensor.owner_id == user.id)
        sensors = query.all()
        return [{"id": str(s.id), "name": s.name} for s in sensors]
    finally:
        db.close()



# ✅ Get all sensor readings (admin sees all, user sees only their own)
@app.get("/api/sensors/all-readings")
def get_all_readings(user: models.User = Depends(get_current_active_user)):
    """Return all sensor readings — admin sees all, user sees their own."""
    db: Session = database.SessionLocal()
    try:
        # Base query
        query = (
            db.query(
                models.SensorReading.id,
                models.SensorReading.ts,
                models.SensorReading.ts_end,
                models.SensorReading.value,
                models.SensorReading.unit,
                models.Sensor.name.label("sensor_name"),
            )
            .join(models.Sensor, models.SensorReading.sensor_id == models.Sensor.id)
            .order_by(models.SensorReading.ts.desc())
        )

        # Admin vs normal user filter
        if not user.is_admin:
            query = query.filter(models.Sensor.owner_id == user.id)

        results = query.all()

        if not results:
            return []

        return [
            {
                "id": str(r.id),
                "sensor_name": r.sensor_name or "Unknown",
                "start_time": r.ts.isoformat() if r.ts else None,
                "end_time": r.ts_end.isoformat() if r.ts_end else None,
                "value": r.value,
                "unit": r.unit or "",
            }
            for r in results
        ]

    except Exception as e:
        print("❌ Error loading all readings:", e)
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        db.close()



# ✅ Add new sensor reading (FormData)
@router.post("/api/sensors/add")
def add_sensor_reading(
    sensor_name: str = Form(...),
    value: float = Form(...),
    unit: str = Form(""),
    ts: str = Form(None),
    user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Find or create the sensor
        sensor = (
            db.query(models.Sensor)
            .filter(models.Sensor.name == sensor_name)
            .filter(models.Sensor.owner_id == user.id)
            .first()
        )
        if not sensor:
            sensor = models.Sensor(name=sensor_name, owner_id=user.id)
            db.add(sensor)
            db.commit()
            db.refresh(sensor)

        # Parse timestamp
        if ts:
            try:
                start_time = datetime.datetime.fromisoformat(ts)
            except ValueError:
                start_time = datetime.datetime.utcnow()
        else:
            start_time = datetime.datetime.utcnow()

        end_time = start_time + datetime.timedelta(minutes=1)

        reading = models.SensorReading(
            sensor_id=sensor.id,
            owner_id=user.id,
            ts=start_time,
            ts_end=end_time,
            value=value,
            unit=unit,
        )
        db.add(reading)
        db.commit()

        return {"message": "✅ Sensor reading added successfully!"}

    except Exception as e:
        db.rollback()
        print("❌ Error adding reading:", e)
        raise HTTPException(status_code=500, detail="Database error")


# ✅ Update reading
@router.put("/api/sensors/update/{reading_id}")
def update_sensor_reading(
    reading_id: int,
    value: float = Form(...),
    unit: str = Form(""),
    db: Session = Depends(get_db)
):
    reading = db.query(models.SensorReading).filter(models.SensorReading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")

    reading.value = value
    reading.unit = unit
    db.commit()
    db.refresh(reading)
    return {"message": "✅ Reading updated successfully"}


# ✅ Delete reading
@router.delete("/api/sensors/delete/{reading_id}")
def delete_sensor_reading(reading_id: int, db: Session = Depends(get_db)):
    reading = db.query(models.SensorReading).filter(models.SensorReading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")

    db.delete(reading)
    db.commit()
    return {"message": "✅ Reading deleted successfully"}


# ✅ Export CSV / ZIP
@router.get("/api/export/sensor-data")
def export_sensor_data(sensor_ids: str, start: str, end: str, db: Session = Depends(get_db)):
    try:
        start_dt = datetime.datetime.fromisoformat(start)
        end_dt = datetime.datetime.fromisoformat(end)
        sensor_id_list = [s.strip() for s in sensor_ids.split(",") if s.strip()]

        if not sensor_id_list:
            raise HTTPException(status_code=400, detail="No sensors selected.")

        sensor_data = {}
        for sid in sensor_id_list:
            rows = (
                db.query(
                    models.Sensor.name.label("sensor_name"),
                    models.SensorReading.ts,
                    models.SensorReading.ts_end,
                    models.SensorReading.value,
                    models.SensorReading.unit,
                )
                .join(models.Sensor, models.SensorReading.sensor_id == models.Sensor.id)
                .filter(models.SensorReading.sensor_id == sid)
                .filter(models.SensorReading.ts >= start_dt)
                .filter(models.SensorReading.ts <= end_dt)
                .order_by(models.SensorReading.ts)
                .all()
            )
            if rows:
                sensor_data[rows[0].sensor_name] = rows

        if not sensor_data:
            raise HTTPException(status_code=404, detail="No data found in this range.")

        if len(sensor_data) == 1:
            name, rows = list(sensor_data.items())[0]
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Sensor Name", "Start Time", "End Time", "Value", "Unit"])
            for r in rows:
                writer.writerow([
                    r.sensor_name,
                    r.ts.strftime("%Y-%m-%d %H:%M:%S"),
                    r.ts_end.strftime("%Y-%m-%d %H:%M:%S") if r.ts_end else "",
                    r.value,
                    r.unit,
                ])
            output.seek(0)
            filename = f"{name}_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        # Multiple → ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for name, rows in sensor_data.items():
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(["Sensor Name", "Start Time", "End Time", "Value", "Unit"])
                for r in rows:
                    writer.writerow([
                        r.sensor_name,
                        r.ts.strftime("%Y-%m-%d %H:%M:%S"),
                        r.ts_end.strftime("%Y-%m-%d %H:%M:%S") if r.ts_end else "",
                        r.value,
                        r.unit,
                    ])
                zipf.writestr(f"{name}.csv", csv_buffer.getvalue())

        zip_buffer.seek(0)
        zip_filename = f"sensors_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )
    except Exception as e:
        print("❌ CSV Export Error:", e)
        raise HTTPException(status_code=500, detail=str(e))
    

    # Get only sensors for current user
@app.get("/api/user/sensors")
def get_user_sensors(user: models.User = Depends(get_current_active_user)):
    db = database.SessionLocal()
    try:
        sensors = (
            db.query(models.Sensor)
            .filter(models.Sensor.owner_id == user.id)
            .all()
        )
        return [{"id": str(s.id), "name": s.name} for s in sensors]
    finally:
        db.close()




# video export endpoint could be added here similarly

from fastapi import UploadFile, File
from fastapi.responses import FileResponse

VIDEO_DIR = "storage/videos"

# ✅ List all videos
VIDEO_DIR = "storage/videos"
os.makedirs(VIDEO_DIR, exist_ok=True)


@app.get("/api/videos")
def list_videos():
    """Return all video files with their sizes"""
    try:
        files = []
        for f in os.listdir(VIDEO_DIR):
            path = os.path.join(VIDEO_DIR, f)
            if os.path.isfile(path):
                size_mb = round(os.path.getsize(path) / (1024 * 1024), 2)
                files.append({"name": f, "size_mb": size_mb})
        return files
    except Exception as e:
        print("❌ Error listing videos:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/videos/watch/{filename}")
def watch_video(filename: str):
    """Stream video file for preview"""
    path = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(path, media_type="video/mp4")


@app.get("/api/videos/download/{filename}")
def download_video(filename: str):
    """Download video file"""
    path = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(path, media_type="application/octet-stream", filename=filename)


@app.post("/api/videos/upload")
def upload_video(file: UploadFile = File(...)):
    """Upload new video"""
    try:
        dest = os.path.join(VIDEO_DIR, file.filename)
        with open(dest, "wb") as buffer:
            buffer.write(file.file.read())
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        print("❌ Upload failed:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.delete("/api/videos/delete/{filename}")
def delete_video(filename: str):
    """Delete video file"""
    try:
        path = os.path.join(VIDEO_DIR, filename)
        if not os.path.exists(path):
            return JSONResponse({"error": "File not found"}, status_code=404)
        os.remove(path)
        return {"status": "success", "message": f"{filename} deleted"}
    except Exception as e:
        print("❌ Error deleting video:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


# ───────────────────────────────────────────────
# ✅ FILE MANAGEMENT ENDPOINTS (Documents / Photos)
# ───────────────────────────────────────────────
from fastapi import UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os, sqlite3

from app.auth import get_current_active_user  # returns ORM User from DB
from app import models

DB_PATH = "datawarehouse.db"         # adjust if your DB path differs
UPLOAD_ROOT = Path("uploaded_files") # per-user folders inside here
UPLOAD_ROOT.mkdir(exist_ok=True)

# Mount static so previews /uploaded_files/<user>/<file> work
try:
    app.mount("/uploaded_files", StaticFiles(directory=str(UPLOAD_ROOT)), name="uploaded_files")
except Exception:
    # already mounted during a reload
    pass

def _ensure_uploads_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            size_mb REAL NOT NULL,
            username TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Call once at import time (safe if run multiple times)
_ensure_uploads_table()

# ✅ Upload file — saves to uploaded_files/<username>/filename + metadata in SQLite
@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
):
    username = current_user.username

    user_dir = UPLOAD_ROOT / username
    user_dir.mkdir(exist_ok=True, parents=True)

    file_path = user_dir / file.filename
    # write file
    with open(file_path, "wb") as f:
        f.write(await file.read())

    size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO uploads (filename, size_mb, username) VALUES (?, ?, ?)",
        (file.filename, size_mb, username),
    )
    conn.commit()
    conn.close()

    return {"message": "✅ File uploaded successfully!", "filename": file.filename, "size_mb": size_mb}


# ✅ List files — admin sees all, user sees only theirs
@app.get("/api/files")
async def list_files(current_user: models.User = Depends(get_current_active_user)):
    _ensure_uploads_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if current_user.is_admin:
        c.execute("SELECT filename, size_mb, username FROM uploads")
    else:
        c.execute("SELECT filename, size_mb, username FROM uploads WHERE username=?", (current_user.username,))

    rows = c.fetchall()
    conn.close()

    return [{"filename": r[0], "size": r[1], "username": r[2]} for r in rows]


# ✅ Delete file — user can delete own; admin can delete any
@app.delete("/api/files/delete/{filename}")
async def delete_file(filename: str, current_user: models.User = Depends(get_current_active_user)):
    _ensure_uploads_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username FROM uploads WHERE filename=?", (filename,))
    row = c.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="File not found")

    owner = row[0]
    if not (current_user.is_admin or current_user.username == owner):
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized")

    # delete file from disk
    file_path = UPLOAD_ROOT / owner / filename
    if file_path.exists():
        file_path.unlink()

    # delete metadata
    c.execute("DELETE FROM uploads WHERE filename=?", (filename,))
    conn.commit()
    conn.close()

    return {"message": "✅ File deleted successfully"}


# ✅ Download file — admin can download any; users only theirs
@app.get("/api/files/download/{filename}")
async def download_file(filename: str, current_user: models.User = Depends(get_current_active_user)):
    _ensure_uploads_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username FROM uploads WHERE filename=?", (filename,))
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    owner = row[0]
    if not (current_user.is_admin or current_user.username == owner):
        raise HTTPException(status_code=403, detail="Not authorized")

    file_path = UPLOAD_ROOT / owner / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(file_path)


# ✅ File stats for chart (global)
@app.get("/api/files/stats")
def get_file_stats():
    stats = {"Images": 0, "Documents": 0, "Videos": 0, "Others": 0}

    for root, _, files in os.walk(UPLOAD_ROOT):
        for fname in files:
            path = Path(root) / fname
            size_mb = round(path.stat().st_size / (1024 * 1024), 2)
            ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""

            if ext in {"jpg", "jpeg", "png", "gif"}:
                stats["Images"] += size_mb
            elif ext in {"pdf", "doc", "docx", "txt", "xlsx", "pptx"}:
                stats["Documents"] += size_mb
            elif ext in {"mp4", "avi", "mov", "mkv"}:
                stats["Videos"] += size_mb
            else:
                stats["Others"] += size_mb

    return {k: round(v, 2) for k, v in stats.items()}


# ───────────────────────────────────────────────
# AUTHENTICATION (User/Admin)
# ───────────────────────────────────────────────
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.auth import hash_password, verify_password, create_access_token
from app import database, models


@app.post("/api/register")
def register_user(form: OAuth2PasswordRequestForm = Depends()):
    """User registration (non-admin)."""
    db = database.SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.username == form.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        user = models.User(
            username=form.username,
            hashed_password=hash_password(form.password),
            is_admin=False
        )
        db.add(user)
        db.commit()
        return {"message": "User registered successfully"}
    finally:
        db.close()


@app.post("/api/login")
def login_user(form: OAuth2PasswordRequestForm = Depends()):
    db = database.SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == form.username).first()
        if not user or not verify_password(form.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        token = create_access_token({
            "sub": user.username,
            "role": "admin" if user.is_admin else "user"
        })

        return {
            "access_token": token,
            "token_type": "bearer",
            "is_admin": user.is_admin,
            "username": user.username
        }
    finally:
        db.close()



# 👑 Default admin creation
def create_default_admin():
    """Create default admin user if DB is empty."""
    db = database.SessionLocal()
    try:
        user_exists = db.query(models.User).first()
        if not user_exists:
            default_admin = models.User(
                username="admin",
                hashed_password=hash_password("admin123"),
                is_admin=True
            )
            db.add(default_admin)
            db.commit()
            print("✅ Default admin user created: admin / admin123")
    finally:
        db.close()


# ───────────────────────────────────────────────
# USER-SPECIFIC ROUTES
# ───────────────────────────────────────────────



# ✅ Get user's own uploaded files
@app.get("/api/user/files")
def get_user_files(user: models.User = Depends(get_current_active_user)):
    """Return files uploaded by the logged-in user"""
    db: Session = database.SessionLocal()
    try:
        files = db.query(models.File).filter(models.File.owner_id == user.id).order_by(models.File.uploaded_at.desc()).all()
        return [
            {
                "id": str(f.id),
                "filename": f.filename,
                "filetype": f.filetype,
                "size": f.size,
                "uploaded_at": f.uploaded_at,
            }
            for f in files
        ]
    finally:
        db.close()



# ✅ Upload new file
@app.post("/api/files/upload")
def upload_file(file: UploadFile = File(...), user: models.User = Depends(get_current_active_user)):
    db: Session = database.SessionLocal()
    try:
        # read file contents
        content = file.file.read()
        size_mb = len(content) / (1024 * 1024)

        # save metadata
        new_file = models.File(
            filename=file.filename,
            filetype=file.content_type,
            size=round(size_mb, 2),
            owner_id=user.id,
            uploaded_at=datetime.utcnow()
        )
        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        return {"message": "✅ File uploaded successfully!", "file_id": str(new_file.id)}
    except Exception as e:
        db.rollback()
        print("❌ Upload error:", e)
        raise HTTPException(status_code=500, detail="File upload failed.")
    finally:
        db.close()

# ✅ Delete file
@app.delete("/api/files/delete/{file_id}")
def delete_user_file(file_id: str, user: models.User = Depends(get_current_active_user)):
    db: Session = database.SessionLocal()
    try:
        file_entry = db.query(models.File).filter(
            models.File.id == file_id,
            models.File.owner_id == user.id
        ).first()
        if not file_entry:
            raise HTTPException(status_code=404, detail="File not found or not yours")

        db.delete(file_entry)
        db.commit()
        return {"message": "✅ File deleted successfully"}
    except Exception as e:
        db.rollback()
        print("❌ Delete error:", e)
        raise HTTPException(status_code=500, detail="Failed to delete file.")
    finally:
        db.close()


# ✅ Download file (metadata only; for now simulated)
@app.get("/api/files/download/{file_id}")
def download_user_file(file_id: str, user: models.User = Depends(get_current_active_user)):
    db: Session = database.SessionLocal()
    try:
        file_entry = db.query(models.File).filter(
            models.File.id == file_id,
            models.File.owner_id == user.id
        ).first()
        if not file_entry:
            raise HTTPException(status_code=404, detail="File not found")

        # Simulated download (metadata response)
        return {
            "filename": file_entry.filename,
            "filetype": file_entry.filetype,
            "size": file_entry.size,
            "uploaded_at": file_entry.uploaded_at
        }
    finally:
        db.close()

# ───────────────────────────────────────────────
# FILE MANAGEMENT ENDPOINTS
# ───────────────────────────────────────────────
FILES_DIR = "storage/files"
os.makedirs(FILES_DIR, exist_ok=True)


@app.post("/api/files/upload")
def upload_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    """Upload a new file for a specific user"""
    user_folder = os.path.join(FILES_DIR, user.username)
    os.makedirs(user_folder, exist_ok=True)
    save_path = os.path.join(user_folder, file.filename)
    with open(save_path, "wb") as f:
        f.write(file.file.read())
    return {"message": f"{file.filename} uploaded for {user.username}"}


@app.get("/api/files/stats")
def get_file_stats():
    stats = {"images": 0, "documents": 0, "others": 0}
    for root, _, files in os.walk("storage/files"):
        for f in files:
            ext = f.lower().split(".")[-1]
            size_mb = os.path.getsize(os.path.join(root, f)) / (1024 * 1024)
            if ext in ["jpg", "jpeg", "png", "gif"]:
                stats["images"] += size_mb
            elif ext in ["pdf", "docx", "doc", "txt", "xlsx", "pptx"]:
                stats["documents"] += size_mb
            else:
                stats["others"] += size_mb
    return {k: round(v, 2) for k, v in stats.items()}



# ───────────────────────────────────────────────
# 👤 USER PROFILE MANAGEMENT
# ───────────────────────────────────────────────
@app.get("/api/profile")
def get_profile(user=Depends(get_current_user)):
    """Return current user's profile information."""
    return {
        "username": user.username,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@app.put("/api/profile/update-password")
def update_password(
    old_password: str = Form(...),
    new_password: str = Form(...),
    user=Depends(get_current_user)
):
    """Allow users to change their password."""
    db = database.SessionLocal()
    try:
        db_user = db.query(models.User).filter(models.User.id == user.id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify old password
        if not verify_password(old_password, db_user.hashed_password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")

        db_user.hashed_password = hash_password(new_password)
        db.commit()
        return {"message": "✅ Password updated successfully!"}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error updating password: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
    finally:
        db.close()

# ───────────────────────────────────────────────
# Temporary Stub Endpoints for Admin Charts 
# ───────────────────────────────────────────────

@app.get("/api/admin/sensor-timeline")
def get_admin_sensor_timeline():
    """Temporary stub endpoint for admin chart data"""
    return {
        "timeline": [
            {"timestamp": "2025-10-20T10:00:00Z", "value": 10},
            {"timestamp": "2025-10-20T11:00:00Z", "value": 12},
            {"timestamp": "2025-10-20T12:00:00Z", "value": 9},
        ]
    }


# ───────────────────────────────────────────────
# ✅ Default Admin User Creation (same)
# ───────────────────────────────────────────────
def create_default_admin():
    db = database.SessionLocal()
    try:
        user_exists = db.query(models.User).first()
        if not user_exists:
            default_admin = models.User(
                username="admin",
                hashed_password=hash_password("admin123"),
                is_admin=True
            )
            db.add(default_admin)
            db.commit()
            print("✅ Default admin user created: admin / admin123")
    finally:
        db.close()




# ───────────────────────────────────────────────
# Run (manual)
# ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
