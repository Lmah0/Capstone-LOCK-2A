# Backend for GCS

## Running the Backend Server
To run the backend server run the following command:
```bash
cd GCS/backend && ./start.sh
```

This will:
- Create a virtual environment if it does not already exist
- Activate the virtual environment
- Install python dependencies
- Start the server on port 8766

## WebSocket Architecture

### 🎯 **Core Problem Solved**

**Without Subscriptions (Inefficient)**:
```
Backend sends ALL data → Frontend → All Components
- Battery component receives: battery + telemetry + GPS + system data ❌
- GPS component receives: battery + telemetry + GPS + system data ❌
- Telemetry component receives: battery + telemetry + GPS + system data ❌
```

**With Subscriptions (Efficient)**:
```
Backend sends ONLY requested data → Frontend → Specific Components
- Battery component receives: battery data only ✅
- GPS component receives: GPS data only ✅ 
- Telemetry component receives: telemetry data only ✅
```

### 🏗️ **How It Works**

```
GCS Frontend Application
│
└── Single WebSocket Connection
    │
    ├── Battery Component → subscribe(['battery']) → gets battery updates every 10s
    └── Telemetry Component → subscribe(['telemetry']) → gets telemetry every 2s
    :
    :
```

### 🔧 **Key Design Decisions**

#### 1. **Component-Level Subscriptions**
- Each React component subscribes only to data it actually needs
- Reduces unnecessary re-renders and state updates
- Components can subscribe to multiple data types if needed

#### 2. **Different Update Frequencies**
```python
# Backend sends data at optimal intervals
battery_data    # Every 10 seconds (slow-changing)
telemetry_data  # Every 2 seconds (moderate)
```

#### 3. **Immediate Data on Subscribe**
- When component subscribes, it gets current data immediately
- No waiting for next broadcast cycle
- Better user experience with instant data display


### 📊 **Bandwidth Savings**

#### Subscription Approach:
```
Only send what's subscribed to:
- Battery: 1 message/10sec = 0.1 msg/sec
- GPS: 1 message/1sec = 1 msg/sec  
- Telemetry: 1 message/2sec = 0.5 msg/sec
- Total: 1.6 msg/sec (68% reduction)
```

### 🔄 **Message Flow**

#### 1. Component Subscription
```typescript
// Battery component only wants battery data
useEffect(() => {
  if (connected) {
    subscribe(['battery']);
  }
}, [connected]);
```

#### 2. Backend Subscription Handling
```python
# Only sends to subscribers of each data type
await send_to_subscribers('battery', battery_data)
```

#### 3. Frontend Data Routing
```typescript
// WebSocketProvider routes data to specific state
switch (data.type) {
  case 'battery':
    setBatteryData(data);  // Only battery component re-renders
    break;
  case 'gps':
    setGpsData(data);      // Only GPS component re-renders
    break;
}
```

### 🛡️ **Error Handling**
- **Connection drops**: Automatic reconnection with subscription restoration
- **Component unmount**: Subscriptions automatically cleaned up
- **Backend restart**: Frontend reconnects and re-subscribes

### 🚀 **API Usage**

#### WebSocket Endpoint
```
ws://localhost:8766/ws/gcs
```

### 💡 **Benefits**
1. **Reduced Bandwidth** - Only send needed data
2. **Better Performance** - Components only re-render when their data changes  
3. **Flexible** - Easy to add new data types or change update frequencies
4. **Efficient** - One connection handles all component subscriptions
5. **Real-time** - Immediate data delivery on subscription