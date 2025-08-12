import pandas as pd
import sqlite3

CSV_PATH = "storage/storage/sensors/sensor_data.csv"

def ingest_to_sqlite():
    df = pd.read_csv(CSV_PATH)
    conn = sqlite3.connect("storage/storage/sensors/sensor.db")
    df.to_sql("sensor_logs", conn, if_exists="replace", index=False)
    print(f"✅ Ingested {len(df)} rows to sensor_logs")

if __name__ == "__main__":
    ingest_to_sqlite()
