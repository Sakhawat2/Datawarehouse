from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
import sqlite3
import csv
import os
import datetime
from api.sensor_admin import router as sensor_admin_router
from api.export import router as export_router

app.include_router(sensor_admin_router)
app.include_router(export_router)

sensor_router = APIRouter()

DB_PATH = "storage/sensors.db"
CSV_DIR = "storage/sensors"
CSV_FILE = os.path.join(CSV_DIR, "sensor_data.csv")

class SensorData(BaseModel):
    sensor_id: str
    start_timestamp: str
    end_timestamp: str
    value: float
    unit: str

# 📝 Create new sensor entry
@sensor_router.post("/")
def submit_sensor_data(data: SensorData):
    try:
        datetime.datetime.fromisoformat(data.start_timestamp)
        datetime.datetime.fromisoformat(data.end_timestamp)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    os.makedirs(CSV_DIR, exist_ok=True)

    # Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensors (sensor_id, start_timestamp, end_timestamp, value, unit)
        VALUES (?, ?, ?, ?, ?)
    """, (data.sensor_id, data.start_timestamp, data.end_timestamp, data.value, data.unit))
    conn.commit()
    conn.close()

    # Save to CSV
    write_header = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Sensor ID", "Start Timestamp", "End Timestamp", "Value", "Unit"])
        writer.writerow([data.sensor_id, data.start_timestamp, data.end_timestamp, data.value, data.unit])

    return {"message": "✅ Sensor data stored in SQLite and CSV"}

# 📊 Read sensor entries (optional filters)
@sensor_router.get("/")
def retrieve_sensor_data(start: str = None, end: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT rowid, sensor_id, start_timestamp, end_timestamp, value, unit FROM sensors WHERE 1=1"
    params = []

    if start:
        query += " AND start_timestamp >= ?"
        params.append(start)
    if end:
        query += " AND end_timestamp <= ?"
        params.append(end)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return {"data": rows}

# 📋 Admin view: latest 100 entries
@sensor_router.get("/admin/sensors")
def get_sensor_data_for_admin():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sensor_id, start_timestamp, end_timestamp, value, unit
        FROM sensors
        ORDER BY start_timestamp DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    conn.close()

    data = [
        {
            "Sensor ID": row[0],
            "Start Timestamp": row[1],
            "End Timestamp": row[2],
            "Value": row[3],
            "Unit": row[4]
        }
        for row in rows
    ]
    return data

# 🔧 Update existing entry by row ID
@sensor_router.put("/update/{entry_id}")
def update_sensor_entry(
    entry_id: int = Path(..., description="Row ID of the entry to update"),
    updated: SensorData = None
):
    try:
        datetime.datetime.fromisoformat(updated.start_timestamp)
        datetime.datetime.fromisoformat(updated.end_timestamp)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sensors
        SET sensor_id = ?, start_timestamp = ?, end_timestamp = ?, value = ?, unit = ?
        WHERE rowid = ?
    """, (updated.sensor_id, updated.start_timestamp, updated.end_timestamp, updated.value, updated.unit, entry_id))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"No entry found with ID {entry_id}")
    conn.commit()
    conn.close()

    return {"message": f"✅ Entry {entry_id} updated successfully"}

# 🧹 Purge entries before a date
@sensor_router.delete("/purge/")
def purge_old_sensor_data(before: str = Query(...)):
    try:
        datetime.datetime.fromisoformat(before)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sensors WHERE end_timestamp < ?", (before,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return {"message": f"🧹 Deleted {deleted} entries before {before}"}

# 🗑 Delete entries by sensor ID
@sensor_router.delete("/delete-by-id/")
def delete_sensor_entries(sensor_id: str = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sensors WHERE sensor_id = ?", (sensor_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return {"message": f"🗑 Deleted {deleted} entries for sensor ID '{sensor_id}'"}

# 🗑 Delete a specific sensor entry by row ID
@sensor_router.delete("/{entry_id}/")
def delete_sensor_entry_by_id(entry_id: int = Path(...)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sensors WHERE rowid = ?", (entry_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"No entry found with ID {entry_id}")
    return {"message": f"🗑 Entry {entry_id} deleted successfully"}
