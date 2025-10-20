from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import random
from contextlib import asynccontextmanager
from typing import List
import boto3
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))

active_connections: List[WebSocket] = []
flight_mode = ""
follow_distance = 10  # meters

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
async def get_all_objects():
    response = table.scan()
    items = response.get('Items', [])
    object_list = []
    for item in items:
        # Get the first timestamp from positions array
        first_timestamp = None
        positions = item.get('positions', [])
        if positions and len(positions) > 0:
            first_timestamp = positions[0].get('ts')
        
        object_data = {
            "objectID": item['objectID'], 
            "classification": item['class'],
            "timestamp": first_timestamp
        }
        object_list.append(object_data)
    
    return object_list

@app.delete("/object/{object_id}")
async def delete_object(object_id: str):
    try:
        table.delete_item(Key={'objectID': object_id})
        return {"status": 200}
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

def setFlightMode(mode):
    print(f"Setting flight mode to: {mode}")

def setFollowDistance(distance):
    print(f"Setting follow distance to: {distance} meters")

async def handleControlCommmand(message):
    command = message.get("command")
    data = message.get("data", {})

    if command == "set_flight_mode":
        setFlightMode(data.get("mode"))       
    elif command == "set_follow_distance":
        setFollowDistance(data.get("distance"))

async def send_telemetry_data():
    """Background task that sends data"""
    while True:
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
        await send_data_to_connections(basic_telemetry)
    
        battery_data = {
            "type": "battery",
            "percentage": max(0, 100 - (random.randint(0, 10))),
            "usage": 100 - random.randint(5, 85)
        }
        await send_data_to_connections(battery_data)

        connection_data = {
            "type": "connection",
            "connected": True
        }
        await send_data_to_connections(connection_data)    
        await asyncio.sleep(2)

@app.websocket("/ws/gcs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()   # Accept the connection
    active_connections.append(websocket)  
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received: {data}")       
            try:
                message = json.loads(data)
                if message.get("type") == "control":
                    await handleControlCommmand(message)
                elif message.get("type") == "record":
                    record_data = message.get("data", {})
                    table.put_item(Item=record_data)               
            except json.JSONDecodeError:
                pass
            
    except WebSocketDisconnect:
        print(f"Client disconnected.")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv('GCS_BACKEND_PORT')), reload=True)