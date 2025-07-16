# api/sensor.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3
import os
import csv

sensor_router = APIRouter()

DB_PATH = "storage/storage/sensors.db"
CSV_DIR = "storage/sensors"
CSV_FILE = os.path.join(CSV_DIR, "sensor_data.csv")

class SensorData(BaseModel):
    sensor_id: str
    timestamp: str
    value: float
    unit: str

@sensor_router.post("/")
def submit_sensor_data(data: SensorData):
    # ✅ Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensors (sensor_id, timestamp, value, unit)
        VALUES (?, ?, ?, ?)
    """, (data.sensor_id, data.timestamp, data.value, data.unit))
    conn.commit()
    conn.close()

    # ✅ Save to CSV
    os.makedirs(CSV_DIR, exist_ok=True)
    write_header = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Sensor ID", "Timestamp", "Value", "Unit"])
        writer.writerow([data.sensor_id, data.timestamp, data.value, data.unit])

    return {"message": "Sensor data stored in SQLite and CSV"}

@sensor_router.get("/")
def retrieve_sensor_data(start: str = None, end: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT * FROM sensors WHERE 1=1"
    params = []

    if start:
        query += " AND timestamp >= ?"
        params.append(start)
    if end:
        query += " AND timestamp <= ?"
        params.append(end)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return {"data": rows}
