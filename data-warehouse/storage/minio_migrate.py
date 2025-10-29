"""
📦 MinIO Migration Tool
-----------------------
Migrate all files stored locally under `uploaded_files/<username>/`
into MinIO, keeping the existing SQLite metadata intact.

You can safely run this multiple times — already-migrated files will be skipped.
"""

import os
import sqlite3
from pathlib import Path
from minio import Minio
from minio.error import S3Error
from storage.minio_client import minio_client, MINIO_BUCKET

# Adjust if your app stores metadata elsewhere
DB_PATH = "datawarehouse.db"
UPLOAD_ROOT = Path("uploaded_files")

def migrate_local_files_to_minio():
    print("🚀 Starting MinIO migration...")

    # Ensure MinIO bucket exists
    found = minio_client.bucket_exists(MINIO_BUCKET)
    if not found:
        minio_client.make_bucket(MINIO_BUCKET)
        print(f"🪣 Created bucket: {MINIO_BUCKET}")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Ensure the uploads table exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            size_mb REAL DEFAULT 0,
            username TEXT NOT NULL
        )
    """)

    # Fetch all uploaded files
    c.execute("SELECT filename, username FROM uploads")
    rows = c.fetchall()

    if not rows:
        print("⚠️ No files found in SQLite uploads table.")
        conn.close()
        return

    migrated = 0
    skipped = 0

    for filename, username in rows:
        local_path = UPLOAD_ROOT / username / filename

        if not local_path.exists():
            print(f"❌ Missing local file: {local_path}")
            continue

        object_name = f"{username}/{filename}"

        # Skip if file already exists in MinIO
        try:
            minio_client.stat_object(MINIO_BUCKET, object_name)
            print(f"⏭️ Skipped (already exists): {object_name}")
            skipped += 1
            continue
        except S3Error as e:
            if e.code != "NoSuchKey":
                print(f"⚠️ Error checking {object_name}: {e}")
                continue

        # Upload to MinIO
        try:
            minio_client.fput_object(
                MINIO_BUCKET,
                object_name,
                str(local_path),
                content_type="application/octet-stream",
            )
            print(f"✅ Uploaded to MinIO: {object_name}")
            migrated += 1
        except Exception as e:
            print(f"❌ Failed to upload {local_path}: {e}")

    conn.close()
    print(f"\n✅ Migration complete!")
    print(f"   → Migrated: {migrated} files")
    print(f"   → Skipped:  {skipped} already in MinIO")


if __name__ == "__main__":
    migrate_local_files_to_minio()
