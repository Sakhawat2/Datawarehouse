from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import pandas as pd
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml")

@router.get("/sensor")
def get_sensor_data(
    sensor_id: str = Query(..., description="Sensor ID to filter"),
    start: str = Query(..., description="Start timestamp"),
    end: str = Query(..., description="End timestamp")
):
    file_path = os.path.join("storage", "sensors", "sensor_data.csv")

    # Check file exists
    if not os.path.isfile(file_path):
        logger.error(f"CSV file not found at: {file_path}")
        raise HTTPException(status_code=500, detail="Sensor data file not found.")

    # Read CSV
    try:
        df = pd.read_csv(file_path, encoding='latin1', on_bad_lines='skip')
        df.columns = df.columns.str.strip()  # Clean column names
        logger.info(f"Cleaned CSV columns: {df.columns.tolist()}")

        # Validate required columns
        required_columns = {"Sensor ID", "Start Timestamp", "End Timestamp", "Value", "Unit"}
        actual_columns = set(df.columns)
        missing = required_columns - actual_columns

        if missing:
            logger.warning(f"Missing required columns in CSV: {missing}")
            raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

        # Convert timestamps
        df["Start Timestamp"] = pd.to_datetime(df["Start Timestamp"], errors="coerce")
        df["End Timestamp"] = pd.to_datetime(df["End Timestamp"], errors="coerce")

    except Exception as e:
        logger.exception("Failed to read CSV file.")
        raise HTTPException(status_code=500, detail="Error reading the data file.")

    # Filter data
    try:
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)

        filtered = df[
            (df["Sensor ID"] == sensor_id) &
            (df["Start Timestamp"] >= start_dt) &
            (df["End Timestamp"] <= end_dt)
        ]
    except Exception as e:
        logger.exception("Error while filtering data.")
        raise HTTPException(status_code=400, detail="Invalid filter parameters.")

    if filtered.empty:
        logger.info(f"No data found for sensor {sensor_id} in specified time range.")
        raise HTTPException(status_code=404, detail="No data for given parameters.")

    # Export filtered data
    export_path = f"storage/temp/{sensor_id}_filtered_dataset.csv"
    try:
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        filtered.to_csv(export_path, index=False)
        logger.info(f"Exported filtered data to: {export_path}")
    except Exception as e:
        logger.exception("Failed to write filtered data to file.")
        raise HTTPException(status_code=500, detail="Failed to export filtered data.")

    return FileResponse(export_path, media_type="text/csv", filename=f"{sensor_id}_dataset.csv")


@router.get("/sensor/timestamps")
def get_sensor_timestamps(sensor_id: str):
    file_path = "storage/sensors/sensor_data.csv"

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Sensor data file not found.")

    try:
        df = pd.read_csv(file_path, encoding='latin1', on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        df["Start Timestamp"] = pd.to_datetime(df["Start Timestamp"], errors="coerce")
        df = df.dropna(subset=["Start Timestamp"])
    except Exception as e:
        logger.exception("Failed to process CSV for timestamps.")
        raise HTTPException(status_code=500, detail="Error reading the data file.")

    if "Sensor ID" not in df.columns:
        raise HTTPException(status_code=400, detail="Missing 'Sensor ID' column.")

    sensor_df = df[df["Sensor ID"] == sensor_id]
    if sensor_df.empty:
        raise HTTPException(status_code=404, detail="No data for given sensor.")

    min_time = sensor_df["Start Timestamp"].min()
    max_time = sensor_df["Start Timestamp"].max()

    return {
        "sensor_id": sensor_id,
        "start": min_time.isoformat(),
        "end": max_time.isoformat()
    }
