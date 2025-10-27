import os
import sys
import sqlite3
from datetime import datetime
from sqlalchemy.orm import Session

# ✅ Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import models, database

SQLITE_DB = "storage/sensors.db"

def parse_dt(ts: str):
    """Convert string timestamp to Python datetime (safe parse)."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        # fallback if SQLite stored weird string format
        try:
            return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


def import_sqlite_data():
    if not os.path.exists(SQLITE_DB):
        print(f"❌ SQLite DB not found at {SQLITE_DB}")
        return

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()

    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in sqlite_cursor.fetchall()]
    print(f"📋 Found tables: {tables}")

    if "sensors" not in tables:
        print("❌ No table named 'sensors' found. Aborting.")
        sqlite_conn.close()
        return

    # Load all data
    sqlite_cursor.execute("SELECT * FROM sensors")
    rows = sqlite_cursor.fetchall()
    columns = [col[0] for col in sqlite_cursor.description]
    print(f"📦 Found {len(rows)} sensor rows.")
    print(f"🧩 Columns in SQLite: {columns}")

    db: Session = database.SessionLocal()
    sensor_cache = {}
    inserted_readings = 0

    for row in rows:
        row_dict = dict(zip(columns, row))
        sensor_id = row_dict["sensor_id"]
        start_ts = parse_dt(row_dict["start_timestamp"])
        end_ts = parse_dt(row_dict["end_timestamp"])
        value = row_dict["value"]
        unit = row_dict["unit"]

        # ✅ Create or reuse sensor
        if sensor_id not in sensor_cache:
            sensor_obj = models.Sensor(name=sensor_id)
            db.add(sensor_obj)
            db.commit()
            db.refresh(sensor_obj)
            sensor_cache[sensor_id] = sensor_obj.id

        # ✅ Insert reading using correct field names (ts, ts_end)
        reading = models.SensorReading(
            sensor_id=sensor_cache[sensor_id],
            ts=start_ts,
            ts_end=end_ts,
            value=value,
            unit=unit,
        )
        db.add(reading)
        inserted_readings += 1

    db.commit()
    db.close()
    sqlite_conn.close()

    print(f"✅ Migration complete!")
    print(f"📈 Imported {len(sensor_cache)} unique sensors and {inserted_readings} readings into PostgreSQL.")


if __name__ == "__main__":
    import_sqlite_data()
