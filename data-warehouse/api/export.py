# api/export.py
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import io, csv

from app.database import get_db
from app import models

router = APIRouter(prefix="/api/export", tags=["Export"])

# Helper: parse timestamp safely
def parse_dt(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


@router.get("/readings")
def export_readings_csv(
    sensor_ids: str = Query(..., description="Comma-separated sensor UUIDs"),
    start: datetime = Query(...),
    end: datetime = Query(...),
    resample: str = Query("", description="Optional: 1min, 1h, 1d"),
    db: Session = Depends(get_db)
):
    """
    Exports sensor readings as CSV between the given time range.
    """
    ids = [s.strip() for s in sensor_ids.split(',') if s.strip()]
    if not ids:
        return {"error": "No sensor IDs provided"}

    q = db.query(
        models.SensorReading.sensor_id,
        models.SensorReading.ts,
        models.SensorReading.value
    ).filter(
        models.SensorReading.sensor_id.in_(ids),
        models.SensorReading.ts >= start,
        models.SensorReading.ts <= end
    )

    # Optional: simple time bucket resampling
    if resample:
        unit_map = {'1min': 'minute', '1h': 'hour', '1d': 'day'}
        unit = unit_map.get(resample, 'minute')
        q = db.query(
            models.SensorReading.sensor_id.label('sensor_id'),
            func.date_trunc(unit, models.SensorReading.ts).label('bucket'),
            func.avg(models.SensorReading.value).label('value')
        ).filter(
            models.SensorReading.sensor_id.in_(ids),
            models.SensorReading.ts >= start,
            models.SensorReading.ts <= end
        ).group_by('sensor_id', 'bucket').order_by('bucket')

    rows = q.all()

    # Write to CSV
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Sensor ID", "Timestamp", "Value"])
    for r in rows:
        ts = getattr(r, "bucket", getattr(r, "ts", None))
        writer.writerow([str(r.sensor_id), ts.isoformat(), float(r.value)])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"}
    )
