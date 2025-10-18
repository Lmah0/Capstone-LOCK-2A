# Backend for GCS

### 🏗️ **How It Works**

#### **Type-Based Data Routing**
- Each message includes a "type" field (battery, telemetry, connection)
- Frontend WebSocketProvider routes data based on type
- Components only update when their specific data type is received


### 🛡️ **Connection Management**
- **Active Connections**: List of all connected WebSocket clients
- **Automatic Cleanup**: Disconnected clients are automatically removed
- **Reconnection**: Frontend automatically attempts reconnect on connection loss

### WebSocket Endpoint
```
ws://localhost:8766/ws/gcs
```