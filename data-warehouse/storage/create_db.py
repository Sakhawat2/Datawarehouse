import sqlite3
import os

# Make sure the storage folder exists
os.makedirs("storage", exist_ok=True)

# Connect to the database
conn = sqlite3.connect("storage/sensors.db")
cursor = conn.cursor()

# Create the sensors table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sensors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT,
    timestamp TEXT,
    value REAL,
    unit TEXT
)
""")

conn.commit()
conn.close()

print("✅ Database initialized and table created!")
