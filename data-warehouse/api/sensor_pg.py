# api/sensor_pg.py
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import asc
from datetime import datetime, timedelta

from app.database import get_db
from app import models
from app.auth import get_current_active_user  # returns ORM User from DB

router = APIRouter()

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _parse_dt(val: str | None) -> datetime:
    """
    Accepts HTML datetime-local value (e.g. '2025-10-20T10:00')
    or ISO strings; falls back to utcnow() if invalid/empty.
    """
    if not val:
        return datetime.utcnow()
    try:
        # HTML datetime-local: 'YYYY-MM-DDTHH:MM' (no timezone)
        return datetime.fromisoformat(val)
    except Exception:
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/api/sensors")
def list_sensors(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_active_user),
):
    """
    Return available sensors.
    - Admin: all sensors
    - User : only sensors they own
    """
    try:
        q = db.query(models.Sensor)
        if not user.is_admin:
            q = q.filter(models.Sensor.owner_id == user.id)
        sensors = q.order_by(asc(models.Sensor.name)).all()
        return [{"id": str(s.id), "name": s.name} for s in sensors]
    except Exception as e:
        print("❌ list_sensors error:", e)
        raise HTTPException(status_code=500, detail="Database query failed")


@router.get("/api/sensors/{sensor_id}/readings")
def get_sensor_readings(
    sensor_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_active_user),
):
    """
    Return readings for a single sensor.
    - Admin: any sensor
    - User : only if they own the sensor
    """
    if sensor_id in (None, "", "undefined"):
        raise HTTPException(status_code=400, detail="Invalid or missing sensor_id")

    # Ensure sensor exists and authorization
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    if not user.is_admin and sensor.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this sensor")

    try:
        rows = (
            db.query(models.SensorReading)
            .filter(models.SensorReading.sensor_id == sensor_id)
            .order_by(models.SensorReading.ts)
            .all()
        )
        return [
            {
                "id": r.id,
                "sensor_name": sensor.name,
                "start_time": r.ts.isoformat() if r.ts else None,
                "end_time": r.ts_end.isoformat() if r.ts_end else None,
                "value": r.value,
                "unit": r.unit or "",
            }
            for r in rows
        ]
    except Exception as e:
        print("❌ get_sensor_readings error:", e)
        raise HTTPException(status_code=500, detail="Database query failed")


@router.post("/api/sensors/add")
def add_sensor_reading(
    sensor_name: str = Form(...),
    value: float = Form(...),
    unit: str = Form(""),
    ts: str | None = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_active_user),
):
    """
    Add a new reading.
    - Creates the sensor for this user if it doesn't exist.
    - ts is optional (defaults to now). ts_end = ts + 1 minute.
    """
    try:
        # Find or create sensor for this user
        sensor = (
            db.query(models.Sensor)
            .filter(models.Sensor.name == sensor_name, models.Sensor.owner_id == user.id)
            .first()
        )
        if not sensor:
            sensor = models.Sensor(name=sensor_name, owner_id=user.id)
            db.add(sensor)
            db.commit()
            db.refresh(sensor)

        start_time = _parse_dt(ts)
        end_time = start_time + timedelta(minutes=1)

        reading = models.SensorReading(
            sensor_id=sensor.id,
            owner_id=user.id,
            ts=start_time,
            ts_end=end_time,
            value=value,
            unit=unit,
        )
        db.add(reading)
        db.commit()
        db.refresh(reading)

        return {
            "status": "success",
            "message": f"Reading added for {sensor_name}",
            "id": reading.id,
            "sensor_id": str(sensor.id),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("❌ add_sensor_reading error:", e)
        raise HTTPException(status_code=500, detail="Failed to add reading")


@router.put("/api/sensors/update/{reading_id}")
def update_sensor_reading(
    reading_id: int,
    value: float = Form(...),
    unit: str = Form(""),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_active_user),
):
    """
    Update value/unit of a reading.
    - Owner or admin only.
    """
    try:
        r = db.query(models.SensorReading).filter(models.SensorReading.id == reading_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Reading not found")
        if not (user.is_admin or r.owner_id == user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        r.value = value
        r.unit = unit
        db.commit()
        db.refresh(r)
        return {"status": "success", "message": "Reading updated"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("❌ update_sensor_reading error:", e)
        raise HTTPException(status_code=500, detail="Failed to update reading")


@router.delete("/api/sensors/delete/{reading_id}")
def delete_sensor_reading(
    reading_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_active_user),
):
    """
    Delete a reading.
    - Owner or admin only.
    """
    try:
        r = db.query(models.SensorReading).filter(models.SensorReading.id == reading_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Reading not found")
        if not (user.is_admin or r.owner_id == user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        db.delete(r)
        db.commit()
        return {"status": "success", "message": "Reading deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("❌ delete_sensor_reading error:", e)
        raise HTTPException(status_code=500, detail="Failed to delete reading")
