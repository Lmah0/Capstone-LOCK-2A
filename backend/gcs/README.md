# Backend for Ground Control Station (GCS)

The GCS backend serves as the central relay hub between the flight computer and the frontend interface. It handles real-time telemetry data streaming, command processing, and data persistence.

## **File Structure & Details**

### **server.py** - Main Application Server
**Purpose**: FastAPI application that serves as the central communication hub

### **database.py** - Data Persistence Layer
**Purpose**: Centralized database operations for DynamoDB integration

---

### **Data Flow Architecture**

#### **Telemetry Stream** (Real-time Data)
```
Flight Computer → GCS Backend → GCS Frontend
      Sends          Relay       React State
    Telemetry         Hub          Updates
```

---


## videoStreaming
- `receiveVideoStream.py` - Python file used for receiving a video stream over UDP. Also, provides the ability to benchmark FFMPEG and video quality of the stream.
- `benchmarkVideoStream.py` - Python file containing helper functions to benchmark FFMPEG stream and video quality.

---

### **Starting the Server**:
```bash
# From project root
./start-backend.sh gcs

# Or directly
cd GCS/backend
python server.py
```

---