from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from api.sensor import sensor_router
from api.video import video_router
from admin.stats import get_storage_stats
import os

app = FastAPI(
    title="Data Warehouse MVP",
    description="Centralized hub for sensor, video, and file data ingestion.",
    version="1.0.0"
)

# Mount static files for dashboard
app.mount("/admin", StaticFiles(directory="admin", html=True), name="admin")

# Include routers
app.include_router(sensor_router, prefix="/api/sensor")
app.include_router(video_router, prefix="/api/video")

# Root endpoint
@app.get("/")
def home():
    return {"message": "🚀 Welcome to the Data Warehouse API"}

# Stats endpoint (moved to /api/admin/stats)
@app.get("/api/admin/stats")
def admin_stats():
    return JSONResponse(get_storage_stats())

# Video list endpoint (moved to /api/admin/videos)
@app.get("/api/admin/videos")
def list_video_files():
    video_dir = "storage/videos"
    if not os.path.exists(video_dir):
        return []
    files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
    return JSONResponse(files)
