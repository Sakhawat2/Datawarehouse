import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from api.sensor import sensor_router
from api.video import video_router
from admin.stats import get_storage_stats

from app import models, database, auth
from app.schemas import UserCreate, UserLogin

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Data Warehouse MVP",
    description="Centralized hub for sensor, video, and file data ingestion.",
    version="1.0.0"
)

# Mount static files
app.mount("/admin", StaticFiles(directory="admin", html=True), name="admin")

# Routers
app.include_router(sensor_router, prefix="/api/sensor")
app.include_router(video_router, prefix="/api/video")

# Root endpoint
@app.get("/")
def home():
    return {"message": "🚀 Welcome to the Data Warehouse API"}

# Admin stats
@app.get("/api/admin/stats")
def admin_stats():
    return JSONResponse(get_storage_stats())

# List videos
@app.get("/api/admin/videos")
def list_video_files():
    video_dir = "storage/videos"
    if not os.path.exists(video_dir):
        return []
    files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
    return JSONResponse(files)

# Signup
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

# Login
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(auth.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = auth.create_access_token({"sub": user.username, "role": db_user.role})
    return {"access_token": token, "token_type": "bearer"}

# Protected route (example)
@app.get("/api/protected")
def protected(current_user: models.User = Depends(auth.get_current_active_user)):
    return {"msg": f"Welcome {current_user.username}, your role is {current_user.role}"}
