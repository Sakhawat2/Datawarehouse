# api/video.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os

video_router = APIRouter()
VIDEO_DIR = "storage/videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

@video_router.post("/")
async def upload_video(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only video files are allowed.")

    # Save file
    file_path = os.path.join(VIDEO_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {
        "message": "✅ Video uploaded successfully",
        "filename": file.filename,
        "path": file_path
    }

@video_router.get("/{filename}")
def get_video(filename: str):
    file_path = os.path.join(VIDEO_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(file_path, media_type="video/mp4", filename=filename)
