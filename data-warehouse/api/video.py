from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os

from fastapi.staticfiles import StaticFiles

video_router = APIRouter()

@video_router.post("/")
async def upload_video(file: UploadFile = File(...)):
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only video files are allowed.")

    os.makedirs("storage/videos", exist_ok=True)
    file_path = os.path.join("storage/videos", file.filename)

    try:
        with open(file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    return {
        "message": "✅ Video uploaded successfully",
        "filename": file.filename,
        "path": file_path
    }
@video_router.get("/{filename}")
def get_video(filename: str):
    file_path = os.path.join("storage/videos", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(file_path, media_type="video/mp4")

