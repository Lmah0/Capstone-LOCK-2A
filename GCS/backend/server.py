from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import random
from contextlib import asynccontextmanager
from typing import List
import os
from websocket_commands import setup_command_registry
from database import get_all_objects, delete_object as db_delete_object
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")

active_connections: List[WebSocket] = []
flight_mode = ""
follow_distance = 10  # meters

# Initialize command registry
command_registry = setup_command_registry()

@asynccontextmanager
async def lifespan(app: FastAPI):
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
    allow_origins=[f"http://localhost:{os.getenv('GCS_FRONTEND_PORT')}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/objects")
async def get_all_objects_endpoint():
    """Retrieve a list of all recorded objects with their classifications and timestamps"""
    try:
        return get_all_objects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve objects: {str(e)}")

@app.delete("/object/{object_id}")
async def delete_object_endpoint(object_id: str):
    """Delete a recorded object from the DynamoDB table by its ID"""
    try:
        success = db_delete_object(object_id)
        if success:
            return {"status": 200}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete object")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete object: {str(e)}")


async def send_data_to_connections(message: dict):
    """Send message to all connected WebSocket clients"""
    for websocket in active_connections:
        try:
            await websocket.send_text(json.dumps(message))
        except:
            if websocket in active_connections:
                active_connections.remove(websocket)

async def send_telemetry_data():
    """Background task that sends data"""
    while True:
        basic_telemetry = {
            "type": "telemetry",
            "latitude": random.uniform(40.7123, 60.7133),
            "longitude": random.uniform(-74.0065, -60.0055),
            "altitude": random.uniform(145.0, 155.0),
            "speed": random.uniform(20.0, 30.0),
            "heading": random.randint(0, 360),
            "roll": random.uniform(-5.0, 5.0),
            "pitch": random.uniform(-5.0, 5.0),
            "yaw": random.uniform(-5.0, 5.0),
            "battery_remaining": random.uniform(30.0, 100.0),
            "battery_voltage": random.uniform(10.1, 80.6)

        }
        await send_data_to_connections(basic_telemetry)
        await asyncio.sleep(1)

@app.websocket("/ws/gcs")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for GCS frontend to send commands and receive telemetry"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()      
            response = await command_registry.handle_message(data, websocket)     
            if response:
                await websocket.send_text(json.dumps(response))
                
    except WebSocketDisconnect:
        print(f"Client disconnected.")
    except Exception as e:
        error_response = {"error": str(e), "status": "error"}
        try:
            await websocket.send_text(json.dumps(error_response))
        except:
            pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv('GCS_BACKEND_PORT')), reload=True)