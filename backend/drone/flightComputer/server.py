"""Flight Computer Server running on the raspberry pi onboard the drone."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import random
from contextlib import asynccontextmanager
from typing import List
import os
from dotenv import load_dotenv
import datetime
import threading
import socket
import time
from mavlinkMessages.connect import connect_to_vehicle, verify_connection
from mavlinkMessages.commandToLocation import move_to_location
from mavlinkMessages.mode import set_mode

load_dotenv(dotenv_path="../../../.env")

active_connections: List[WebSocket] = []

vehicle_connection = None

vehicle_ip = "udp:127.0.0.1:5006" # Need to run mavproxy module on 5006

vehicle_data = {
    "last_time": -1.0,
    "latitude": -1.0,
    "longitude": -1.0,
    "rth_altitude": -1.0,
    "dlat": -1.0, # Ground X speed (Latitude, positive north)
    "dlon": -1.0, # Ground Y Speed (Longitude, positive east)
    "dalt": -1.0, # Ground Z speed (Altitude, positive down)
    "heading": -1.0,
    "roll": -1.0,
    "pitch": -1.0,
    "yaw": -1.0,
    "flight_mode": -1
}

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def send_data_to_connections(message: dict):
    """Send message to all connected WebSocket clients"""
    for websocket in active_connections:
        try:
            await websocket.send_text(json.dumps(message))
        except:
            if websocket in active_connections:
                active_connections.remove(websocket)

async def send_telemetry_data():
    while True:
        await send_data_to_connections(vehicle_data)
        await asyncio.sleep(1)

def setFlightMode(mode: str):
    """Set the flight mode of the drone"""
    if not mode:
        raise ValueError("Flight mode cannot be empty")
    try:
        set_mode(vehicle_connection, mode)
        print(f"Setting flight mode to: {mode}")
    except Exception as e:
        raise RuntimeError(f"Failed to set flight mode: {e}")

def setFollowDistance(distance: float):
    # TODO: Deferring the implementation of this until later
    """Set the follow distance of the drone"""
    if not distance or distance <= 0:
        raise ValueError("Follow distance must be a positive number")
    try:
        print(f"Setting follow distance to: {distance} meters")
    except Exception as e:
        raise RuntimeError(f"Failed to set follow distance: {e}")

def stopFollowingTarget():
    # TODO: Deferring the implementation of this until later
    """Stop following the target"""
    try:
        print("Stopping following the target")
    except Exception as e:
        raise RuntimeError(f"Failed to stop following target: {e}")
    
def moveToLocation(location):
    """Move the drone to a specified location"""
    if not location or "lat" not in location or "lon" not in location or "alt" not in location:
        raise ValueError("Invalid location data")
    try:
        print(f"Moving to location - lat: {location['lat']}, lon: {location['lon']}, alt: {location['alt']}")        
        move_to_location(vehicle_connection, location["lat"], location["lon"], location["alt"])
    except Exception as e:
        raise RuntimeError(f"Failed to move to location: {e}")

@app.websocket("/ws/flight-computer")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for GCS frontend to send commands and receive telemetry"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()    
            msg = json.loads(data)
            cmd = msg.get("command")
            # Handle commands
            if cmd =="move_to_location":
                moveToLocation(msg.get("location"))
            elif cmd == "set_flight_mode":
                setFlightMode(msg.get("mode"))
            elif cmd == "set_follow_distance":
                setFollowDistance(msg.get("distance"))
            elif cmd == "stop_following":
                stopFollowingTarget()
            else:
                raise HTTPException(status_code=400, detail="Unknown command")

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

def update_vehicle_position_from_flight_controller():
    """Update vehicle position from flight controller data"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(("127.0.0.1", 5005))
    
    while True:
        data = sock.recvfrom(1024)
        items = data[0].decode()[1:-1].split(",")
        message_time = float(items[0])

        if message_time <= vehicle_data["last_time"]:
            continue

        elif len(items) == len(vehicle_data):
            vehicle_data["last_time"] = message_time

            for i, key in enumerate(list(vehicle_data.keys())[1:], start=1):
                vehicle_data[key] = float(items[i])
                print*(f"Updated {key} to {vehicle_data[key]}")
        else:
            print(f"Received data item does not match expected length...")

if __name__ == "__main__":
    flight_controller_thread = threading.Thread(target=update_vehicle_position_from_flight_controller, daemon=True)
    flight_controller_thread.start()
    time.sleep(0.5) # Give some time for the thread to start
    
    print(f"Attempting to connect to vehicle on: {vehicle_ip}")
    vehicle_connection = connect_to_vehicle(vehicle_ip)
    print("Vehicle connection established.")
    try:
        verify_connection(vehicle_connection)
        print("Vehicle connection verfied.")
    except Exception as e:
        print(f"Error verifying vehicle connection: {e}")
        exit(1)
    
    uvicorn.run("server:app", host="0.0.0.0", port=5555, reload=True)
