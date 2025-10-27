import csv, os, uuid
CSV_PATH = os.path.join('storage','sensors','sensor_data.csv')
FIELDS = ['id','Sensor ID','Start Timestamp','End Timestamp','Value','Unit']


def ensure_header():
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
if not os.path.exists(CSV_PATH):
with open(CSV_PATH,'w',newline='',encoding='utf-8') as f:
csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def read_all():
ensure_header()
with open(CSV_PATH, newline='', encoding='latin1') as f:
reader = csv.DictReader(f)
rows = [dict(r) for r in reader]
return rows


def append_row(row: dict):
ensure_header()
row = { **{k:'' for k in FIELDS}, **row }
row['id'] = row.get('id') or str(uuid.uuid4())
with open(CSV_PATH,'a',newline='',encoding='utf-8') as f:
w = csv.DictWriter(f, fieldnames=FIELDS)
w.writerow(row)
return row


def write_all(rows):
ensure_header()
with open(CSV_PATH,'w',newline='',encoding='utf-8') as f:
w = csv.DictWriter(f, fieldnames=FIELDS)
w.writeheader(); w.writerows(rows)