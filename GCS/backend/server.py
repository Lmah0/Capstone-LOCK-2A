""" Main server for Ground Control Station (GCS) backend. """
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import random
from contextlib import asynccontextmanager
from typing import List
import os
from database import get_all_objects, delete_object, record_telemetry_data
from dotenv import load_dotenv
import datetime

load_dotenv(dotenv_path="../../.env")

active_connections: List[WebSocket] = []

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
def get_all_objects_endpoint():
    """Retrieve a list of all recorded objects with their classifications and timestamps"""
    try:
        return get_all_objects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve objects: {str(e)}")

@app.delete("/delete/object/{object_id}")
def delete_object_endpoint(object_id: str):
    """Delete a recorded object from the DynamoDB table by its ID"""
    try:
        success = delete_object(object_id)
        if success:
            return {"status": 200}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete object")
    except Exception :
        raise HTTPException(status_code=500, detail=f"Failed to delete object: {str(e)}")
    
@app.post("/setFollowDistance")
def set_follow_distance(request: dict = Body(...)):
    """Set the follow distance"""
    try:
        distance = request.get("distance")
        if distance is None:
            raise HTTPException(status_code=400, detail="Missing 'distance' in body")
        print(f"Follow distance set to: {distance} meters")
        return {"status": 200, "message": f"Follow distance set to {distance} meters"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set follow distance: {str(e)}")

@app.post("/setFlightMode")
def set_flight_mode(request: dict = Body(...)):
    """Set the flight mode"""
    try:
        mode = request.get("mode")
        if not mode:
            raise HTTPException(status_code=400, detail="Missing 'mode' in body")
        print(f"Flight mode set to: {mode}")
        return {"status": 200, "message": f"Flight mode set to {mode}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set flight mode: {str(e)}")

@app.post("/stopFollowing")
def stop_following():
    """Stop following the target"""
    try:
        print("Stopped following the target.")
        return {"status": 200, "message": "Stopped following the target."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop following: {str(e)}")
    
@app.post("/record")
def record(request: dict = Body(...)):
    """Record tracked object data"""
    data = request.get("data")
    if not data:
        raise HTTPException(status_code=400, detail="Missing 'data' in body")
    try:
        record_telemetry_data(data, classification='Unknown')
        return {"status": 200, "message": "Data recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record data: {str(e)}")


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
            "timestamp": datetime.datetime.now().timestamp(),
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
    except WebSocketDisconnect:
        print(f"Client disconnected.")
    except Exception as e:
        error_response = {"status": 500, "error": str(e)}
        try:
            await websocket.send_text(json.dumps(error_response))
        except:
            pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv('GCS_BACKEND_PORT')), reload=True)