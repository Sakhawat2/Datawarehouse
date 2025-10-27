import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import random
import datetime as dt
from sqlalchemy.orm import Session
from app import models, database

# ─────────────────────────────────────────────
#  Seed data for sensors, readings, and videos
# ─────────────────────────────────────────────

def seed_data():
    db: Session = database.SessionLocal()

    print("🌱 Seeding demo data...")

    # Wipe existing tables (optional for dev/testing)
    db.query(models.SensorReading).delete()
    db.query(models.Sensor).delete()
    if hasattr(models, "Video"):
        db.query(models.Video).delete()
    db.commit()

    # ─────── Sensors ───────
    sensors = [
        models.Sensor(name="Temp Sensor 1", type="Temperature"),
        models.Sensor(name="Humidity Sensor 1", type="Humidity"),
        models.Sensor(name="Pressure Sensor 1", type="Pressure"),
    ]
    db.add_all(sensors)
    db.commit()

    # ─────── Sensor Readings ───────
    readings = []
    now = dt.datetime.utcnow()

    for sensor in sensors:
        for i in range(20):
            readings.append(
                models.SensorReading(
                    sensor_id=sensor.id,
                    timestamp=now - dt.timedelta(minutes=i * 5),
                    value=round(random.uniform(20.0, 80.0), 2),
                )
            )
    db.add_all(readings)
    db.commit()

    # ─────── Videos (optional) ───────
    if hasattr(models, "Video"):
        videos = [
            models.Video(filename="video_1.mp4", size_mb=random.uniform(5, 25)),
            models.Video(filename="video_2.mp4", size_mb=random.uniform(30, 75)),
            models.Video(filename="video_3.mp4", size_mb=random.uniform(120, 200)),
        ]
        db.add_all(videos)
        db.commit()

    print("✅ Done! Demo data inserted successfully.")
    db.close()


if __name__ == "__main__":
    seed_data()
