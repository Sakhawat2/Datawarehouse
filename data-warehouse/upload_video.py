import requests

file_path = r"C:\Users\sakat\Pictures\Camera Roll\NewVideo.mp4"
url = "http://localhost:8000/api/video/"

with open(file_path, "rb") as f:
    response = requests.post(url, files={"file": ("NewVideo.mp4", f, "video/mp4")})

try:
    print(response.json())
except requests.exceptions.JSONDecodeError:
    print("⚠️ Server returned non-JSON response:")
    print(response.status_code, response.text)
