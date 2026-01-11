"""Main server for Ground Control Station (GCS) backend."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from videoStreaming import setup_video_stream, return_video_stream
import uvicorn
import asyncio
import json
import websockets
from contextlib import asynccontextmanager
from typing import List
import os
from database import get_all_objects, delete_object, record_telemetry_data
from dotenv import load_dotenv
import time
from collections import deque

load_dotenv(dotenv_path="../../.env")

active_connections: List[WebSocket] = []
flight_comp_ws: WebSocket = None


async def flight_computer_background_task():
    """Background task that connects to flight computer and listens for telemetry"""
    global flight_comp_ws
    flight_comp_url = os.getenv("FLIGHT_COMP_URL")
    if not flight_comp_url:
        raise RuntimeError("FLIGHT_COMP_URL not set in environment variables")

    while True:
        try:
            async with websockets.connect(flight_comp_url) as ws:
                flight_comp_ws = ws
                print("Connected to flight computer")
                async for message in ws:
                    try:
                        data = json.loads(message)
                        await send_data_to_connections(data)
                        await handle_telemetry_video_synchronization(data)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Flight computer connection error: {e}, retrying in 5s")
            flight_comp_ws = None
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    telemetry_task = asyncio.create_task(flight_computer_background_task())
    video_task = asyncio.create_task(video_monitor_task())
    yield
    # Shutdown logic
    telemetry_task.cancel()
    video_task.cancel()
    try:
        await telemetry_task
        await video_task
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


# -- Websocket communication --
async def send_data_to_connections(
    message: dict, websockets_list: List[WebSocket] = active_connections
):
    """Send message to all connected WebSocket clients"""
    for websocket in websockets_list:
        try:
            await websocket.send_text(json.dumps(message))
        except:
            if websocket in websockets_list:
                websockets_list.remove(websocket)


async def send_to_flight_comp(message: dict):
    """Send a JSON command to the flight computer."""
    global flight_comp_ws
    if flight_comp_ws is None:
        raise RuntimeError("Flight computer not connected")

    try:
        await flight_comp_ws.send(json.dumps(message))
    except Exception as e:
        print(f"Failed to send to flight comp: {e}")
        flight_comp_ws = None
        raise


telemetry_buffer = deque(maxlen=100)


# -- Websocket communication --
async def handle_telemetry_video_synchronization(message: dict):
    """
    Called by  telemetry task.
    Stores telemetry with its flight controller timestamp.
    """
    telemetry_buffer.append(message)


def get_synced_telemetry(frame_timestamp):
    """
    Finds the telemetry packet closest to the frame's timestamp.
    """
    if not telemetry_buffer:
        return None

    # Find the packet with the minimum time difference
    closest_packet = min(
        telemetry_buffer, key=lambda x: abs(x["last_time"] - frame_timestamp)
    )

    # If the gap is too large (>200ms), ignore it
    if abs(closest_packet["last_time"] - frame_timestamp) > 0.2:
        return None

    return closest_packet


# -- Database Endpoints --
@app.get("/objects")
def get_all_objects_endpoint():
    """Retrieve a list of all recorded objects with their classifications and timestamps"""
    try:
        return get_all_objects()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve objects: {str(e)}"
        )


@app.delete("/delete/object/{object_id}")
def delete_object_endpoint(object_id: str):
    """Delete a recorded object from the DynamoDB table by its ID"""
    try:
        success = delete_object(object_id)
        if success:
            return {"status": 200}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete object")
    except Exception:
        raise HTTPException(status_code=500, detail=f"Failed to delete object")


@app.post("/record")
def record(request: dict = Body(...)):
    """Record tracked object data"""
    data = request.get("data")
    if not data:
        raise HTTPException(status_code=400, detail="Missing 'data'")

    required_fields = ("timestamp", "latitude", "longitude")
    # Validate point data
    for idx, point in enumerate(data):
        missing = [f for f in required_fields if point.get(f) is None]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing fields {missing} in data point at index {idx}",
            )
    try:
        record_telemetry_data(data, classification="Unknown")
        return {"status": 200, "message": "Data recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record data: {str(e)}")


async def video_monitor_task():
    global latest_frame_object
    cap = setup_video_stream()

    for frame in return_video_stream(cap):
        # Timestamp the frame the moment it is received
        frame_time = time.time()

        # Find the telemetry that matches frame based on timestamp
        synced_data = get_synced_telemetry(frame_time)

        if synced_data:
            # Pair found!
            # Attach telemetry as metadata to the frame object
            frame.metadata = synced_data
        latest_frame_object = frame
        # PERFORM FURTHER PROCESSING HERE IF NEEDED
        await asyncio.sleep(0)


# -- Database Endpoints --


# -- Flight Computer Communication Endpoints --
@app.post("/setFollowDistance")
async def set_follow_distance(request: dict = Body(...)):
    """Set the follow distance"""
    distance = request.get("distance")
    if distance is None:
        raise HTTPException(status_code=400, detail="Missing 'distance' in body")
    try:
        await send_to_flight_comp(
            {"command": "set_follow_distance", "distance": distance}
        )
        return {"status": 200, "message": f"Follow distance set to {distance} meters"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to set follow distance: {str(e)}"
        )


@app.post("/setFlightMode")
async def set_flight_mode(request: dict = Body(...)):
    """Set the flight mode"""
    mode = request.get("mode")
    if not mode:
        raise HTTPException(status_code=400, detail="Missing 'mode' in body")
    try:
        await send_to_flight_comp({"command": "set_flight_mode", "mode": mode})
        return {"status": 200, "message": f"Flight mode set to {mode}"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to set flight mode: {str(e)}"
        )


@app.post("/stopFollowing")
async def stop_following():
    """Stop following the target"""
    try:
        await send_to_flight_comp({"command": "stop_following"})
        return {"status": 200, "message": "Stopped following the target."}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to stop following: {str(e)}"
        )


# -- Flight Computer Communication Endpoints --


@app.websocket("/ws/gcs")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for GCS frontend to send commands and receive telemetry"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Just keep the connection alive
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
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=int(os.getenv("GCS_BACKEND_PORT")),
        reload=True,
    )
