# api/sensor.py

from fastapi import APIRouter, Request
from pydantic import BaseModel
import sqlite3

sensor_router = APIRouter()

DB_PATH = "storage/storage/sensors.db"

class SensorData(BaseModel):
    sensor_id: str
    timestamp: str
    value: float
    unit: str

@sensor_router.post("/")
def submit_sensor_data(data: SensorData):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensors (sensor_id, timestamp, value, unit)
        VALUES (?, ?, ?, ?)
    """, (data.sensor_id, data.timestamp, data.value, data.unit))
    conn.commit()
    conn.close()
    return {"message": "Sensor data stored successfully"}

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
