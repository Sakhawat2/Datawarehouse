# migrate_to_minio.py
import sqlite3
from pathlib import Path
from storage.minio_client import minio_client, MINIO_BUCKET
import io

DB_PATH = "datawarehouse.db"
UPLOAD_ROOT = Path("uploaded_files")

def migrate_existing_files():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT filename, username FROM uploads")
    rows = c.fetchall()
    conn.close()

    for filename, username in rows:
        file_path = UPLOAD_ROOT / username / filename
        if not file_path.exists():
            print(f"⚠️ Skipping missing file: {file_path}")
            continue

        object_name = f"{username}/{filename}"
        with open(file_path, "rb") as f:
            data = io.BytesIO(f.read())
            minio_client.put_object(
                MINIO_BUCKET,
                object_name,
                data,
                length=data.getbuffer().nbytes,
                content_type="application/octet-stream",
            )
        print(f"✅ Uploaded {object_name} to MinIO")

if __name__ == "__main__":
    migrate_existing_files()
