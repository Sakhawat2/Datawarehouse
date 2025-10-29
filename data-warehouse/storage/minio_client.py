# storage/minio_client.py
from minio import Minio
from minio.error import S3Error
import os

# ───────────────────────────────────────────────
# 🔧 Configuration (you can change or use env vars)
# ───────────────────────────────────────────────
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "datawarehouse")

# ───────────────────────────────────────────────
# 🚀 Initialize MinIO Client
# ───────────────────────────────────────────────
minio_client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,  # keep False for localhost (HTTP)
)

# ───────────────────────────────────────────────
# 🪣 Ensure bucket exists
# ───────────────────────────────────────────────
try:
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)
        print(f"✅ Created bucket '{MINIO_BUCKET}'")
    else:
        print(f"🪣 Bucket '{MINIO_BUCKET}' already exists")
except S3Error as e:
    print("⚠️ MinIO bucket check error:", e)
