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

@router.get("/api/admin/sensor-timeline")
async def get_sensor_timeline():
    # Dummy data for testing
    timestamps = [(datetime.now() - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M") for i in range(10)][::-1]
    datasets = [
        {
            "label": "Sensor A",
            "values": [12, 15, 14, 18, 20, 22, 21, 19, 17, 16]
        },
        {
            "label": "Sensor B",
            "values": [8, 9, 11, 10, 13, 12, 14, 13, 12, 11]
        }
    ]
    return { "timestamps": timestamps, "datasets": datasets }
