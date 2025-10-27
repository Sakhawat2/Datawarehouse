from fastapi import APIRouter, UploadFile, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.storage.minio_client import client, BUCKET
from app.authz import require_role
import uuid


video_router = APIRouter(prefix='/api/video', tags=['Videos'])


@video_router.post('/')
async def upload_video(file: UploadFile, user=Depends(require_role('user'))):
key = f"{uuid.uuid4()}-{file.filename}"
size = 0
data = await file.read()
size = len(data)
client.put_object(BUCKET, key, io.BytesIO(data), length=size, content_type=file.content_type)
# save DB row (id, key, size, owner_id)
return { 'message': 'uploaded', 'key': key }


@video_router.get('/{key}')
async def get_video(key: str):
try:
obj = client.get_object(BUCKET, key)
return StreamingResponse(obj, media_type='video/mp4')
except Exception:
raise HTTPException(404, 'Not found')


@video_router.delete('/{key}')
async def delete_video(key: str, user=Depends(require_role('admin'))):
client.remove_object(BUCKET, key)
return { 'message': 'deleted' }