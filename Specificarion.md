# **Data Warehouse Project Specification (Minimal Viable Version)**  
The Data warehouse will be a Centralized Data Hub where unifies sensor, video, and file storage in one place. It will provides structured datasets for training models (e.g., sensor analytics, video processing). In addition, Teaches modular architecture, API design, and scalable storage solutions.

By this project, we will Build a Scalable API, Solve Real Storage Challenges and Empower Future Projects

## **1. Core Objectives**  
✅ **API** to ingest and retrieve:  
- Sensor data (time-series)  
- Video streams/files  
✅ **Storage** for structured and unstructured data  
✅ **Admin Dashboard** with storage analytics  

---

## **2. Functional Requirements**  

### **2.1 API Endpoints**  
| **Endpoint**       | **Method** | **Description**                     | **Data Format**          |  
|--------------------|------------|-------------------------------------|--------------------------|  
| `/api/sensor`      | POST       | Submit sensor readings              | JSON/CSV                 |  
| `/api/sensor`      | GET        | Retrieve sensor data (time-filtered) | JSON                     |  
| `/api/video`       | POST       | Upload video chunks                 | Multipart/form-data      |  
| `/api/video/{id}`  | GET        | Stream/download video               | Video stream (MP4/H.264) |  
| `/api/files`       | GET        | List available files                | JSON                     |  

### **2.2 Storage**  
| **Data Type**  | **Minimal Solution**       | **Future Upgrade**       |  
|---------------|----------------------------|--------------------------|  
| Sensor Data   | SQLite/CSV files           | InfluxDB/TimescaleDB     |  
| Videos        | Local filesystem           | MinIO/S3                 |  
| Metadata      | JSON files                 | PostgreSQL               |  

### **2.3 Admin Dashboard**  
- **Real-time Graphs** (Chart.js or similar):  
  - Total storage used (MB/GB)  
  - Data type distribution (sensors/videos/files)  
- **Basic Controls**:  
  - Delete old data  
  - View system health  

---

## **3. Technical Specifications**  

### **3.1 Stack (Minimal)**  
| **Component**       | **Technology**              |  
|---------------------|-----------------------------|  
| Backend Framework   | FastAPI (Python) or Express (Node.js) |  
| Sensor Storage      | SQLite                      |  
| Video Storage       | Local disk (organized folders) |  
| Dashboard Frontend  | HTML + Chart.js (no React/Vue) |  
| Deployment          | Single-machine (Docker optional) |  

### **3.2 Example API Payloads**  
**Sensor Submission (POST `/api/sensor`)**  
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "sensor_id": "temp_sensor_1",
  "value": 25.4,
  "unit": "°C"
}
```

**Video Upload (POST `/api/video`)**  
```http
Content-Type: multipart/form-data
-- Form Data --
video: <binary_file.mp4>
metadata: '{"camera_id": "cam_1", "timestamp": "..."}'
```

---

## **4. Non-Functional Requirements**  
- **Latency**: <500ms response time for sensor data  
- **Scalability**: Support 100+ concurrent sensor submissions  
- **Video Handling**: Accept chunks up to 100MB  
- **Security**: Basic API key authentication (if exposed to internet)  

---

## **5. Project Structure (Simplified)**  
```
data-warehouse/
├── api/
│   ├── sensor.py       # Sensor routes
│   └── video.py        # Video handling
├── storage/
│   ├── sensors.db      # SQLite database
│   └── videos/         # Video files
├── admin/
│   ├── index.html      # Dashboard UI
│   └── stats.py       # Data aggregation
└── main.py            # App entry point
```

---

## **6. Deliverables**  
1. **Working API** (testable via Postman/cURL)  
2. **Storage System** with sample sensor/video data  
3. **Dashboard** showing:  
   - Total storage used  
   - Data type pie chart  
4. **Documentation** (1-page setup guide)  

---

## **7. Upgrade Path**  
1. **Phase 1 (MVP)**:  
   - SQLite + local filesystem  
   - Basic dashboard  
2. **Phase 2**:  
   - Add authentication (API keys)  
   - Switch to InfluxDB + S3  
3. **Phase 3**:  
   - Real-time streaming (WebSocket)  
   - AI metadata tagging  

---
