from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
from typing import Dict, Set
import random
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    background_task = asyncio.create_task(send_telemetry_data())
    yield
    # Shutdown
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8765"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections with their subscriptions
connections: Dict[WebSocket, Dict] = {}

class SubscriptionManager:
    def __init__(self):
        self.subscriptions: Dict[str, Set[WebSocket]] = {
            'telemetry': set(),
            'battery': set(),
            'connection': set()
        }
    
    def subscribe(self, websocket: WebSocket, data_types: list):
        """Subscribe a client to specific data types"""
        for data_type in data_types:
            if data_type in self.subscriptions:
                self.subscriptions[data_type].add(websocket)
                print(f"Client subscribed to {data_type}")
    
    def unsubscribe(self, websocket: WebSocket):
        """Remove client from all subscriptions"""
        for _, subscribers in self.subscriptions.items():
            subscribers.discard(websocket)
    
    def get_subscribers(self, data_type: str) -> Set[WebSocket]:
        """Get all subscribers for a specific data type"""
        return self.subscriptions.get(data_type, set())

subscription_manager = SubscriptionManager()

async def send_current_telemetry():
    """Send current telemetry data immediately"""
    basic_telemetry = {
        "type": "telemetry",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "heading": 180,
        "altitude": 150.5,
        "speed": 25.3,
        "bearing": 180,
        "roll": 0.0,
        "pitch": 0.0,
        "yaw": 0.0
    }
    await send_to_subscribers('telemetry', basic_telemetry)

async def send_current_battery():
    """Send current battery data immediately"""
    battery_data = {
        "type": "battery",
        "percentage": 85,
        "usage": 45
    }
    await send_to_subscribers('battery', battery_data)

async def send_to_subscribers(data_type: str, message: dict):
    """Send message only to subscribers of specific data type"""
    subscribers = subscription_manager.get_subscribers(data_type)
    if subscribers:
        disconnected = []
        for websocket in subscribers.copy():
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            subscription_manager.unsubscribe(ws)
            connections.pop(ws, None)

@app.websocket("/ws/gcs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()   # Accept the connection
    connections[websocket] = {"subscriptions": []}
    print(f"Client connected. Total connections: {len(connections)}")
    
    try:
        # Keep connection alive
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            print(f"Received: {data}")
            
            try:
                message = json.loads(data)
                
                # Handle subscription requests
                if message.get("type") == "subscribe":
                    data_types = message.get("dataTypes", [])
                    subscription_manager.subscribe(websocket, data_types)
                    connections[websocket]["subscriptions"] = data_types
                    
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "dataTypes": data_types
                    }))
                    
                    # Send current data immediately for subscribed types
                    for data_type in data_types:
                        if data_type == "telemetry":
                            await send_current_telemetry()
                        elif data_type == "battery":
                            await send_current_battery()
                
                # Handle control commands
                elif message.get("type") == "control":
                    command = message.get("command")
                    data = message.get("data", {})
                    
                    if command == "set_flight_mode":
                        flight_mode = data.get("mode")
                        print(f"Setting flight mode to: {flight_mode}")
                        # command drone
                        
                    elif command == "set_follow_distance":
                        distance = data.get("distance")
                        print(f"Setting follow distance to: {distance} meters")
                        # command drone
                    
                    # Send confirmation back to frontend
                    await websocket.send_text(json.dumps({
                        "type": "control_confirmation",
                        "command": command,
                        "status": "success",
                        "data": data
                    }))
                    
            except json.JSONDecodeError:
                # Handle non-JSON messages
                await websocket.send_text(f"Echo: {data}")
            
    except WebSocketDisconnect:
        subscription_manager.unsubscribe(websocket)
        connections.pop(websocket, None)
        print(f"Client disconnected. Total connections: {len(connections)}")

async def send_telemetry_data():
    """Background task that sends different types of data at different intervals"""
    telemetry_counter = 0
    
    while True:
        # Send basic telemetry every 2 seconds
        if telemetry_counter % 2 == 0:
            basic_telemetry = {
                "type": "telemetry",
                "latitude": random.uniform(40.7123, 60.7133),
                "longitude": random.uniform(-74.0065, -60.0055),
                "heading": random.randint(0, 360),
                "altitude": random.uniform(145.0, 155.0),
                "speed": random.uniform(20.0, 30.0),
                "bearing": random.randint(0, 360),
                "roll": random.uniform(-5.0, 5.0),
                "pitch": random.uniform(-5.0, 5.0),
                "yaw": random.uniform(-5.0, 5.0)
            }
            await send_to_subscribers('telemetry', basic_telemetry)
        
        # Send battery data every 10 seconds
        if telemetry_counter % 10 == 0:
            battery_data = {
                "type": "battery",
                "percentage": max(0, 100 - (telemetry_counter // 10)),
                "usage": 100 - random.randint(5, 85)
            }
            await send_to_subscribers('battery', battery_data)

        if telemetry_counter % 3 == 0:
            connection_data = {
                "type": "connection",
                "connected": True
            }
            await send_to_subscribers('connection', connection_data)
        
        telemetry_counter += 1
        await asyncio.sleep(1)  # Base interval of 1 second

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8766, reload=True)