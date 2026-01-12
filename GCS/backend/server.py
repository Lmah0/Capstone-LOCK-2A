""" Main server for Ground Control Station (GCS) backend. """
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio
import json
import websockets
from contextlib import asynccontextmanager
from typing import List
import os
from database import get_all_objects, delete_object, record_telemetry_data
from dotenv import load_dotenv
import queue
import base64
import cv2
from decimal import Decimal
from datetime import datetime

load_dotenv(dotenv_path="../../.env")

AI_CMDS_LIST = ["click", "stop_tracking", "reselect_object", "mouse_move"]

active_connections: List[WebSocket] = []
flight_comp_ws: WebSocket = None
ai_command_connections: List[WebSocket] = []  # For AI processor to receive frontend commands

video_frame_queue = queue.Queue(maxsize=3)

is_recording = False
recording_data = []
recording_interval = 10 # every 10th heartbeat
heartbeat_counter = 0


def append_record_data(data):
    """Record tracked object data"""
    if not data:
        return

    required_fields = ("timestamp", "latitude", "longitude")
    # Check if all required fields are present in the single data point
    missing = [f for f in required_fields if data.get(f) is None]
    if missing:
        return
    
    obj_position = {
        'ts': datetime.fromtimestamp(data['timestamp']).isoformat() + 'Z',
        'lat': Decimal(str(data.get('latitude', 0))),
        'lon': Decimal(str(data.get('longitude', 0))),
        'alt': Decimal(str(data.get('altitude', 0))),
        'speed': Decimal(str(data.get('speed', 0))),
        'heading': Decimal(str(data.get('heading', 0))),
    }
    recording_data.append(obj_position)


async def flight_computer_background_task():
    """Background task that connects to flight computer and listens for telemetry"""
    global flight_comp_ws, heartbeat_counter
    flight_comp_url = os.getenv('FLIGHT_COMP_URL')
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
                        # Only record every Nth heartbeat
                        heartbeat_counter += 1
                        if heartbeat_counter >= recording_interval: # TODO: NEEDS TO BE MOVED AFTER GEO ALGORITHM
                            append_record_data(data)
                            heartbeat_counter = 0
                        
                        await send_data_to_connections(data)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Flight computer connection error: {e}, retrying in 5s")
            flight_comp_ws = None
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if (True): # change to false if just testing ai stuff w/o flight computer
        task = asyncio.create_task(flight_computer_background_task())
        yield
        # Shutdown
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
    if not mode:
        raise HTTPException(status_code=400, detail="Missing 'mode' in body")
    try:
        await send_to_flight_comp({"command": "set_flight_mode", "mode": mode})
        return {"status": 200, "message": f"Flight mode set to {mode}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set flight mode: {str(e)}")

@app.post("/stopFollowing")
async def stop_following():
    """Stop following the target"""
    try:
        await send_to_flight_comp({"command": "stop_following"})
        record_telemetry_data(recording_data, classification='Unknown')
        return {"status": 200, "message": "Stopped following the target."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop following: {str(e)}")

# -- Flight Computer Communication Endpoints --

@app.post("/recording")
def toggle_recording():
    """Toggle recording state"""
    global is_recording
    is_recording = not is_recording
    if not is_recording and recording_data:
        # Save recorded data when stopping
        try:
            record_telemetry_data(recording_data, classification='Unknown')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save recording data: {str(e)}")
    return {"is_recording": is_recording}

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

# -- AI Integration Sockets --
@app.websocket("/ws/ai-commands")
async def websocket_ai_commands_endpoint(websocket: WebSocket):
    """WebSocket endpoint for AI processor to receive frontend commands (clicks, stop, etc.)"""
    await websocket.accept()
    ai_command_connections.append(websocket)
    print("AI Processor connected to command channel")
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        print("AI Processor disconnected from command channel")
    except Exception as e:
        print(f"Error in AI command channel: {e}")
    finally:
        if websocket in ai_command_connections:
            ai_command_connections.remove(websocket)
            
@app.websocket("/ws/ai-frame-reader")
async def websocket_ai_frame_reader_endpoint(websocket: WebSocket):
    """ Internal WebSocket endpoint to receive JPEG-encoded frames from the Detector Algorithm """
    await websocket.accept()
    print("AI Frame Producer Connected.")
    try:
        # Expecting raw bytes (base64 encoded JPEG buffer)
        while True:
            # Receive base64 string from the AI process
            base64_frame_data = await websocket.receive_text()
            
            # Decode the base64 string back into raw JPEG bytes
            jpeg_bytes = base64.b64decode(base64_frame_data)
            
            # Put the new frame into the queue for the MJPEG streamer
            try:
                # Clear old frames to ensure minimum latency
                while not video_frame_queue.empty():
                    video_frame_queue.get_nowait()
                    
                video_frame_queue.put(jpeg_bytes, block=False)
            except queue.Full:
                # If queue is full, just drop the frame to prioritize newer ones (low latency)
                pass 
            
    except WebSocketDisconnect:
        print("AI Frame Producer disconnected.")
    except Exception as e:
        print(f"Error in /ws/ai_frame: {e}")
    finally:
        pass

@app.websocket("/ws/camera-source")
async def websocket_camera_source_endpoint(websocket: WebSocket):
    """Mock camera stream - reads video file and streams frames to AI processor"""
    await websocket.accept()
    print("AI Processor connected to camera source")
    # Video file path - this mocks the camera feed
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    VIDEO_PATH = os.path.join(BASE_DIR, "Detection", "Spike_1.0", "video.mp4")
    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print(f"Error: Could not open video file at {VIDEO_PATH}")
        await websocket.close()
        return

    try:
        while True:
            ret, frame = cap.read()

            # Loop video when it ends
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    break

            # Encode frame as JPEG
            success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            if not success:
                continue

            # Send as base64 string
            base64_frame = base64.b64encode(buffer.tobytes()).decode('utf-8')
            await websocket.send_text(base64_frame)

            # Control frame rate (~30 fps)
            await asyncio.sleep(1/30)

    except WebSocketDisconnect:
        print("AI Processor disconnected from camera source")
    except Exception as e:
        print(f"Error in camera source: {e}")
    finally:
        cap.release()

async def generate_video_frames():
    """Reads JPEG frames from the queue and formats them for MJPEG streaming."""
    frame_boundary = b'--frame\r\n'
    content_type = b'Content-Type: image/jpeg\r\n\r\n'

    while True:
        try:
            # 1. Wait for a new frame
            jpeg_frame = await asyncio.to_thread(video_frame_queue.get, timeout=1)

            # 2. Yield the MJPEG format
            yield frame_boundary
            yield content_type
            yield jpeg_frame
            yield b'\r\n'

        except queue.Empty:
            # If the queue is empty after the timeout, wait briefly and loop again
            await asyncio.sleep(0.01)

        except Exception as e:
            print(f"Error yielding frame: {e}")
            break

@app.get("/video_feed")
async def video_feed():
    """Stream video frames via MJPEG"""
    media_type = 'multipart/x-mixed-replace; boundary=frame'
    return StreamingResponse(
        generate_video_frames(),
        media_type=media_type 
    )

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv('GCS_BACKEND_PORT')), reload=True)