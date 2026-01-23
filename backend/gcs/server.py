"""Main server for Ground Control Station (GCS) backend."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio
import json
import websockets
from contextlib import asynccontextmanager
from typing import List, Dict, Optional
import os

# from database import get_all_objects, delete_object, record_telemetry_data
from dotenv import load_dotenv
from videoStreaming.FrameTelemetrySynchronizer import FrameTelemetrySynchronizer
from videoStreaming.receiveVideoStream import video_telemetry_sync_task
import queue
import threading

load_dotenv(dotenv_path="../../.env")

AI_CMDS_LIST = ["click", "stop_tracking", "reselect_object", "mouse_move"]

active_connections: List[WebSocket] = []
flight_comp_ws: WebSocket = None
ai_command_connections: List[WebSocket] = []  # For AI processor to receive frontend commands

# Larger queue for video frames to handle bursts
drone_frame_queue = queue.Queue()
# Video stream configuration
STREAM_URL = "udp://192.168.1.66:5000"  # Video from drone
TIMESTAMP_PORT = 5001  # Timestamps from drone


# Global synchronizer for frames and telemetry
frame_telemetry_sync = FrameTelemetrySynchronizer()


async def flight_computer_background_task():
    """Background task that connects to flight computer and listens for telemetry"""
    global flight_comp_ws
    print("Starting flight computer background task...")
    flight_comp_url = os.getenv(
        "FLIGHT_COMP_URL", "ws://192.168.1.66:5555/ws/flight-computer"
    )
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

                        # Extract timestamp from telemetry data
                        telemetry_timestamp = data.get("timestamp")

                        if telemetry_timestamp:
                            # Add to synchronizer
                            frame_telemetry_sync.add_telemetry(
                                telemetry_timestamp, data
                            )

                        # Forward to frontend
                        await send_data_to_connections(data)

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Flight computer connection error: {e}, retrying in 5s")
            flight_comp_ws = None
            await asyncio.sleep(5)


stop_event = threading.Event() # Event to signal video and telemetry sync background tasks to stop when shutting down

async def video_telemetry_synchronization_background_task():
    """Async wrapper for video receiver"""
    loop = asyncio.get_running_loop()

    # Run task to synchronize video frames with telemetry
    await loop.run_in_executor(
        None,
        video_telemetry_sync_task,
        STREAM_URL,
        TIMESTAMP_PORT,
        frame_telemetry_sync,
        drone_frame_queue,
        stop_event,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting GCS backend server...")
    tasks = []

    if True:  # change to false if just testing ai stuff w/o flight computer
        # Start flight computer telemetry receiver
        tasks.append(asyncio.create_task(flight_computer_background_task()))

        # Start video and timestamp synchronization task
        tasks.append(asyncio.create_task(video_telemetry_synchronization_background_task()))

        yield

        print("Shutting down GCS backend server...")
        stop_event.set()

        # Shutdown
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    else:
        yield


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


# # -- Database Endpoints --
# @app.get("/objects")
# def get_all_objects_endpoint():
#     """Retrieve a list of all recorded objects with their classifications and timestamps"""
#     try:
#         return get_all_objects()
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, detail=f"Failed to retrieve objects: {str(e)}"
#         )


# @app.delete("/delete/object/{object_id}")
# def delete_object_endpoint(object_id: str):
#     """Delete a recorded object from the DynamoDB table by its ID"""
#     try:
#         success = delete_object(object_id)
#         if success:
#             return {"status": 200}
#         else:
#             raise HTTPException(status_code=500, detail="Failed to delete object")
#     except Exception:
#         raise HTTPException(status_code=500, detail=f"Failed to delete object")


# @app.post("/record")
# def record(request: dict = Body(...)):
#     """Record tracked object data"""
#     data = request.get("data")
#     if not data:
#         raise HTTPException(status_code=400, detail="Missing 'data'")

#     required_fields = ("timestamp", "latitude", "longitude")
#     # Validate point data
#     for idx, point in enumerate(data):
#         missing = [f for f in required_fields if point.get(f) is None]
#         if missing:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Missing fields {missing} in data point at index {idx}",
#             )
#     try:
#         record_telemetry_data(data, classification="Unknown")
#         return {"status": 200, "message": "Data recorded successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to record data: {str(e)}")


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


@app.websocket("/ws/gcs")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for GCS frontend to send commands and receive telemetry"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            try:
                data = json.loads(message)
                command_type = data.get("type")

                # Relay AI-related commands to the AI processor
                if command_type in AI_CMDS_LIST:
                    await send_data_to_connections(data, ai_command_connections)

            except json.JSONDecodeError:
                pass

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


# -- AI Integration Sockets --
@app.websocket("/ws/ai-commands")
async def websocket_ai_commands_endpoint(websocket: WebSocket):
    """WebSocket endpoint for AI processor to receive frontend commands"""
    await websocket.accept()
    ai_command_connections.append(websocket)
    print("AI Processor connected to command channel")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("AI Processor disconnected from command channel")
    except Exception as e:
        print(f"Error in AI command channel: {e}")
    finally:
        if websocket in ai_command_connections:
            ai_command_connections.remove(websocket)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8766, reload=True)
