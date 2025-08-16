from fastapi import APIRouter
import sqlite3

router = APIRouter()

@router.get("/admin/sensors")
def get_sensor_data():
    conn = sqlite3.connect("storage/sensors.db")
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
