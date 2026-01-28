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
from videoStreaming.SendVideoStreamGst import start_video_streaming
from dotenv import load_dotenv
import datetime
import threading
import socket
import time
from mavlinkMessages.mode import set_mode
from mavlinkMessages.connect import connect_to_vehicle, verify_connection
from mavlinkMessages.commandToLocation import move_to_location

load_dotenv(dotenv_path="../../.env")

active_connections: List[WebSocket] = []

vehicle_connection = None
vehicle_ip = "udp:127.0.0.1:5006"   # Need to run MAVProxy module on 5006

vehicle_data = {
    "last_time": -1.0,
    "latitude": -1.0,
    "longitude": -1.0,
    "rth_altitude": -1.0,
    "dlat": -1.0,  # Ground X speed (Latitude, positive north)
    "dlon": -1.0,  # Ground Y Speed (Longitude, positive east)
    "dalt": -1.0,  # Ground Z speed (Altitude, positive down)
    "heading": -1.0,
    "roll": -1.0,
    "pitch": -1.0,
    "yaw": -1.0,
    "flight_mode": -1,
}

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
        # Simulated telemetry data (replace with real vehicle data later)
        basic_telemetry = {
            "timestamp": datetime.datetime.now().timestamp(),
            "latitude": random.uniform(40.7123, 60.7133),
            "longitude": random.uniform(-74.0065, -60.0055),
            "altitude": random.uniform(145.0, 155.0),
            "dlat": random.uniform(0.1, 5.0),
            "dlon": random.uniform(0.1, 5.0),
            "dalt": random.uniform(0.1, 5.0),
            "heading": random.randint(0, 360),
            "roll": random.uniform(-5.0, 5.0),
            "pitch": random.uniform(-5.0, 5.0),
            "yaw": random.uniform(-5.0, 5.0),
            "flight_mode": -1,
            "battery_remaining": random.uniform(30.0, 100.0),
            "battery_voltage": random.uniform(10.1, 80.6),
        }
        await send_data_to_connections(basic_telemetry)
        await asyncio.sleep(1)


def return_telemetry_data():
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
        "battery_voltage": random.uniform(10.1, 80.6),
    }
    return basic_telemetry


def setFlightMode(mode: str):
    """Set the flight mode of the drone"""
    global vehicle_connection
    print(f"Received request to set flight mode: {mode}")
    if not mode:
        raise ValueError("Flight mode cannot be empty.")
    if vehicle_connection is None:
        raise RuntimeError("Vehicle connection is not established.")
    try:
        print(f"Setting flight mode to: {mode}")
    except Exception as e:
        print(f"Failed to set flight mode: {e}")
        raise RuntimeError(f"Failed to set flight mode: {e}")


def setFollowDistance(distance: float):
    """Set the follow distance of the drone (TODO)"""
    if not distance or distance <= 0:
        raise ValueError("Follow distance must be a positive number")
    try:
        print(f"Setting follow distance to: {distance} meters")
    except Exception as e:
        raise RuntimeError(f"Failed to set follow distance: {e}")


def stopFollowingTarget():
    """Stop following the target (TODO)"""
    print("Stopping following the target")

def moveToLocation(location):
    """Move the drone to a specified location"""
    global vehicle_connection
    if not location or "lat" not in location or "lon" not in location or "alt" not in location:
        raise ValueError("Invalid location data")
    print(f"Moving to location - lat: {location['lat']}, lon: {location['lon']}, alt: {location['alt']}")
    move_to_location(vehicle_connection, location["lat"], location["lon"], location["alt"])


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
            if cmd == "move_to_location":
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
        print("Client disconnected.")
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
        else:
            print("Received data item does not match expected length...")

# --------------------------------------------------------------------------------------
# FastAPI setup
# --------------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize vehicle connection and background tasks"""
    global vehicle_connection

    # Start flight controller thread
    flight_controller_thread = threading.Thread(
        target=update_vehicle_position_from_flight_controller, daemon=True
    )
    flight_controller_thread.start()
    time.sleep(0.5)  # Allow thread to start

    # Connect to vehicle
    print(f"Attempting to connect to vehicle on: {vehicle_ip}")
    vehicle_connection = connect_to_vehicle(vehicle_ip)
    print("Vehicle connection established.")

    try:
        if verify_connection(vehicle_connection):
            print("Vehicle connection verified.")
        else:
            raise RuntimeError("Vehicle connection could not be verified")
    except Exception as e:
        print(f"Error verifying vehicle connection: {e}")
        raise RuntimeError("Could not verify vehicle connection") from e

    # Start telemetry
    telemetry_task = asyncio.create_task(send_telemetry_data())

    yield  # Hand over control to FastAPI

    # Shutdown
    telemetry_task.cancel()
    try:
        await telemetry_task
    except asyncio.CancelledError:
        pass
    print("Server shutdown complete.")

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5555, reload=True)