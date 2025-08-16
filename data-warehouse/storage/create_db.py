import sqlite3
import os
import pandas as pd

# Make sure the storage folder exists
os.makedirs("storage", exist_ok=True)

# Connect to the database
conn = sqlite3.connect("sensors.db")
cursor = conn.cursor()


cursor.execute("DROP TABLE IF EXISTS sensors")
# Create the sensors table with start and end timestamps
cursor.execute("""
CREATE TABLE IF NOT EXISTS sensors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT,
    start_timestamp TEXT,
    end_timestamp TEXT,
    value REAL,
    unit TEXT
)
""")

conn.commit()

# === Load CSV and insert into DB ===

# Path to your CSV file
csv_path = os.path.join(os.getcwd(), "sensors", "sensor_data.csv")

# Try reading with fallback encoding
try:
    df = pd.read_csv(csv_path, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(csv_path, encoding="latin1")

# Clean column names and values
df.columns = [col.strip() for col in df.columns]
df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
df["Unit"] = df["Unit"].astype(str).str.strip()

# Insert rows into the database
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO sensors (sensor_id, start_timestamp, end_timestamp, value, unit)
        VALUES (?, ?, ?, ?, ?)
    """, (
        row["Sensor ID"],
        row["Start Timestamp"],
        row["End Timestamp"],
        row["Value"],
        row["Unit"]
    ))

conn.commit()
conn.close()

print("✅ Database created and CSV data loaded successfully.")
