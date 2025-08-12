import requests
import pandas as pd

def fetch_sensor(sensor_id, start, end):
    url = "http://localhost:8000/ml/sensor"
    params = {"sensor_id": sensor_id, "start": start, "end": end}
    r = requests.get(url, params=params)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["data"])
    df.to_csv(f"{sensor_id}_sensor.csv", index=False)
    print(f"✅ Sensor data exported: {sensor_id}_sensor.csv")

def fetch_video(video_id):
    url = f"http://localhost:8000/ml/video/{video_id}"
    r = requests.get(url)
    with open(f"{video_id}.mp4", "wb") as f:
        f.write(r.content)
    print(f"🎞️ Video downloaded: {video_id}.mp4")

# Example usage
if __name__ == "__main__":
    fetch_sensor("accel_01", "2023-04-01T00:00:00", "2023-04-01T01:00:00")
    fetch_video("fall_event_42")
