import asyncio
import websockets
import base64
import cv2
import os
from dotenv import load_dotenv
from fastapi import WebSocket

load_dotenv(dotenv_path="../.env")

INTERNAL_WS_PORT = os.getenv('GCS_BACKEND_PORT')
INTERNAL_WS_URL = f"ws://localhost:{INTERNAL_WS_PORT}/ws/ai-frame-reader" 
_websocket_client: WebSocket = None

async def connect_to_server():
    """Establishes a persistent connection to the gcs server"""
    global _websocket_client
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"Connecting to internal server at {INTERNAL_WS_URL}...")
            _websocket_client = await websockets.connect(INTERNAL_WS_URL) 
            print("Successfully connected to gcs server.")
            return _websocket_client
        except ConnectionRefusedError:
            retry_count += 1
            print(f"Connection refused (attempt {retry_count}/{max_retries}). Server may not be running. Retrying in 3s...")
            await asyncio.sleep(3)
        except Exception as e:
            retry_count += 1
            print(f"Connection error (attempt {retry_count}/{max_retries}): {e}. Retrying in 5s...")
            await asyncio.sleep(5)

    print("Failed to connect after maximum retries")
    return None

async def send_frame_to_server(frame):
    """Encodes the CV2 frame and sends it over the internal WebSocket connection"""
    global _websocket_client
    
    # Attempt to reconnect if connection is lost
    if _websocket_client is None:
        _websocket_client = await connect_to_server()
        
    if _websocket_client is None:
        print("Cannot send frame: No connection to server")
        return

    try:
        # 1. Convert frame to JPEG bytes
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        if not success:
            print("Failed to encode frame as JPEG")
            return
        
        # 2. Encode JPEG bytes as base64 string
        base64_string = base64.b64encode(buffer.tobytes()).decode('utf-8')

        # 3. Send the base64 string (TEXT) over the websocket
        await _websocket_client.send(base64_string)
        print("Frame sent successfully")

    except websockets.ConnectionClosed:
        print("Gcs server connection closed. Will reconnect on next send...")
        _websocket_client = None
    except Exception as e:
        print(f"Error sending frame: {e}")
        _websocket_client = None