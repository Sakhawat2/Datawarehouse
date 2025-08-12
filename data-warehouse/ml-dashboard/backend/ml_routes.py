from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import pandas as pd
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#router = APIRouter()
router = APIRouter(prefix="/ml")

#@router.get("/ml/sensor")
@router.get("/sensor")
def get_sensor_data(
    sensor_id: str = Query(..., description="Sensor ID to filter"),
    start: str = Query(..., description="Start timestamp"),
    end: str = Query(..., description="End timestamp")
):
    file_path = "storage/storage/sensors/sensor_data.csv"

    # Check file exists
    if not os.path.isfile(file_path):
        logger.error(f"CSV file not found at: {file_path}")
        raise HTTPException(status_code=500, detail="Sensor data file not found.")

    # Read CSV
    try:
        df = pd.read_csv(file_path, parse_dates=["Timestamp"])
    except Exception as e:
        logger.exception("Failed to read CSV file.")
        raise HTTPException(status_code=500, detail="Error reading the data file.")

    # Validate required columns
    required_columns = ["Sensor ID", "Timestamp"]
    if not all(col in df.columns for col in required_columns):
        logger.warning(f"Missing required columns in CSV: {df.columns}")
        raise HTTPException(status_code=400, detail="CSV is missing required columns.")

    # Filter data
    try:
        filtered = df[
            (df["Sensor ID"] == sensor_id) &
            (df["Timestamp"] >= pd.to_datetime(start)) &
            (df["Timestamp"] <= pd.to_datetime(end))
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
        filtered.to_csv(export_path, index=False)
        logger.info(f"Exported filtered data to: {export_path}")
    except Exception as e:
        logger.exception("Failed to write filtered data to file.")
        raise HTTPException(status_code=500, detail="Failed to export filtered data.")

    return FileResponse(export_path, media_type="text/csv", filename=f"{sensor_id}_dataset.csv")
