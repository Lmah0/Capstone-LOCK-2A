""" Main server for Ground Control Station (GCS) backend. """
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import websockets
import traceback
from contextlib import asynccontextmanager
from typing import List
import os
import cv2
import time
from database import get_all_objects, delete_object, record_telemetry_data
from ai.AI import ENGINE, STATE, CURSOR_HANDLER, process_frame
import webRTCStream
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")

VIDEO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai', 'video.mp4')

active_connections: List[WebSocket] = []
flight_comp_ws: WebSocket = None

flight_comp_url = "ws://10.13.58.79:5555/ws/flight-computer"

async def flight_computer_background_task():
    """Background task that connects to flight computer and listens for telemetry"""
    global flight_comp_ws

    while True:
        try:
            async with websockets.connect(flight_comp_url) as ws:
                flight_comp_ws = ws
                print("Connected to flight computer")   
                async for message in ws:
                    try:
                        data = json.loads(message)
                        data["tracking"] = STATE.tracking # Add tracking state
                        if STATE.tracked_class is not None and ENGINE.model is not None:
                            data["tracked_class"] = ENGINE.model.names[STATE.tracked_class]
                        else:
                            data["tracked_class"] = None
                        await send_data_to_connections(data)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Flight computer connection error: {e}, retrying in 5s")
            flight_comp_ws = None
            await asyncio.sleep(5)

async def video_streaming_task():
    """Background task that reads video, processes through AI, and streams via WebRTC"""
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"ERROR: Could not open video file: {VIDEO_PATH}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_delay = 1.0 / fps
    try:
        while True:
            frame_start = time.time()
            ret, frame = cap.read()    
            if not ret:
                # Loop video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            # Process frame through AI
            cursor = CURSOR_HANDLER.cursor_pos
            click = CURSOR_HANDLER.click_pos
            
            annotated_frame = await process_frame(frame, cursor, click)

            if click is not None:
                CURSOR_HANDLER.clear_click()
                print("Click cleared")
        
            # Send to WebRTC stream
            if annotated_frame is not None:
                webRTCStream.push_frame(annotated_frame)
            
            # Maintain video FPS
            elapsed = time.time() - frame_start
            sleep_time = max(0, frame_delay - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            
    except asyncio.CancelledError:
        print("Video streaming task cancelled")
        raise
    except Exception as e:
        print(f"Video streaming error: {e}")
        traceback.print_exc()
    finally:
        cap.release()
        print("Video capture released")

async def follows_background_task():
    """Background task that manages following target logic"""
    while True:
        if STATE.tracking:
            follows_altitude = 15.0 # Hard coding the follows altitude to 15 meters (50 ft) for now
            if STATE.last_target_lat is not None and STATE.last_target_lon is not None:
                try:
                    await send_to_flight_comp({
                        "command": "move_to_location",
                        "location": {
                            "lat": STATE.last_target_lat,
                            "lon": STATE.last_target_lon,
                            "alt": follows_altitude
                        }
                    })
                    print(f"Sent follow command to flight computer: lat {STATE.last_target_lat}, lon {STATE.last_target_lon}, alt {follows_altitude}")
                except Exception as e:
                    print(f"Failed to send follow command: {e}")
        await asyncio.sleep(2) # Send follows commands every 2 seconds for now

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background tasks
    flight_comp_task = asyncio.create_task(flight_computer_background_task())
    webrtc_task = asyncio.create_task(webRTCStream.start_webrtc_server())
    video_task = asyncio.create_task(video_streaming_task())
    follows_task = asyncio.create_task(follows_background_task())
    
    yield
    
    # Shutdown
    flight_comp_task.cancel()
    webrtc_task.cancel()
    video_task.cancel()
    follows_task.cancel()

    try:
        await asyncio.wait_for(
            asyncio.gather(flight_comp_task, webrtc_task, video_task, follows_task, return_exceptions=True), timeout=2.0
        )
    except asyncio.TimeoutError:
        print("Warning: Some tasks did not shut down cleanly")
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
async def send_data_to_connections(message: dict, websockets_list: List[WebSocket] = active_connections):
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

# -- Websocket communication --

# -- Database Endpoints --
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
        raise HTTPException(status_code=500, detail=f"Failed to delete object")

@app.post("/record")
async def record(request: dict = Body(...)):
    """Record tracked object data"""
    data = request.get("data")
    if not data:
        raise HTTPException(status_code=400, detail="Missing 'data'")

    required_fields = ("timestamp", "latitude", "longitude")
    # Validate point data
    for idx, point in enumerate(data):
        missing = [f for f in required_fields if point.get(f) is None]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing fields {missing} in data point at index {idx}")
    
    try:
        # Get classification name if tracking, otherwise use "unknown"
        classification = "unknown"
        if STATE.tracked_class is not None:
            classification = ENGINE.model.names[STATE.tracked_class]
        
        record_telemetry_data(data, classification=classification)
        return {"status": 200, "message": "Data recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record data: {str(e)}")

# -- Database Endpoints --

# -- Flight Computer Communication Endpoints --
@app.post("/setFollowDistance")
async def set_follow_distance(request: dict = Body(...)):
    """Set the follow distance"""
    distance = request.get("distance")
    if distance is None:
        raise HTTPException(status_code=400, detail="Missing 'distance' in body")
    try:
        await send_to_flight_comp({"command": "set_follow_distance", "distance": distance})
        return {"status": 200, "message": f"Follow distance set to {distance} meters"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set follow distance: {str(e)}")

@app.post("/setFlightMode")
async def set_flight_mode(request: dict = Body(...)):
    """Set the flight mode"""
    mode = request.get("mode")
    print(f"Received frontend request to set flight mode: {mode}")
    if not mode:
        raise HTTPException(status_code=400, detail="Missing 'mode' in body")
    try:
        await send_to_flight_comp({"command": "set_flight_mode", "mode": mode})
        return {"status": 200, "message": f"Flight mode set to {mode}"}
    except Exception as e:
        print("Sent request to change mode but failed at the flight computer.")
        raise HTTPException(status_code=500, detail=f"Failed to set flight mode: {str(e)}")

@app.post("/stopFollowing")
async def stop_following():
    """Stop following the target"""
    try:
        STATE.reset_tracking()
        await send_to_flight_comp({"command": "stop_following"}) # sets back to loiter
        return {"status": 200, "message": "Stopped following the target."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop following: {str(e)}")

# -- Flight Computer Communication Endpoints --

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
                # Handle mouse movements and clicks for AI
                if command_type == "mouse_move":
                    CURSOR_HANDLER.update_cursor(data.get("x"), data.get("y"))
                elif command_type == "click":
                    CURSOR_HANDLER.register_click(data.get("x"), data.get("y"))
                    print(f"Registered click at ({data.get('x')}, {data.get('y')})")

            except json.JSONDecodeError:
                pass  # Just keep connection alive if not valid JSON

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