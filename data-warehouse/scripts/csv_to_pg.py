import csv, uuid
from datetime import datetime
from app.database import SessionLocal, engine
from app import models


models.Base.metadata.create_all(bind=engine)


def get_or_create_sensor(db, name: str):
s = db.query(models.Sensor).filter(models.Sensor.name==name).first()
if s: return s
s = models.Sensor(name=name)
db.add(s); db.commit(); db.refresh(s)
return s


CSV_PATH = 'storage/sensors/sensor_data.csv'


def parse_dt(s):
# supports 'YYYY-MM-DDTHH:MM' and with seconds; assumes naive is UTC
try:
return datetime.fromisoformat(s.replace('Z',''))
except Exception:
# try common fallback
return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


with SessionLocal() as db:
with open(CSV_PATH, newline='', encoding='latin1') as f:
reader = csv.DictReader(f)
for row in reader:
sid = row.get('Sensor ID') or row.get('sensor_id')
start = row.get('Start Timestamp') or row.get('start_timestamp')
end = row.get('End Timestamp') or row.get('end_timestamp')
val = row.get('Value') or row.get('value')
unit = row.get('Unit') or row.get('unit')
if not sid or not start or val is None:
continue
sensor = get_or_create_sensor(db, sid)
db.add(models.SensorReading(
sensor_id=sensor.id,
ts=parse_dt(start),
ts_end=parse_dt(end) if end else None,
value=float(val),
unit=unit
))
db.commit()
print('✅ Migration complete')