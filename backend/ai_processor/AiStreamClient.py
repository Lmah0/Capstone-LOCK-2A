"""
AiStream - Client library for AI processor to communicate with GCS server.

WEBSOCKET CONNECTIONS MANAGED:
    1. /ws/camera-source:       Receives camera frames from server
    2. /ws/ai-commands:         Receives frontend commands (clicks, mouse moves)
    3. /ws/ai-frame-reader:     Sends processed frames back to server
"""

import asyncio
import websockets
import base64
import cv2
import os
import threading
import time
import json
import numpy as np
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")

# WebSocket URLs
BACKEND_PORT =  os.getenv('GCS_BACKEND_PORT', '8766')
CAMERA_WS_URL = f"ws://backend-gcs:{BACKEND_PORT}/ws/camera-source"
COMMAND_WS_URL = f"ws://backend-gcs:{BACKEND_PORT}/ws/ai-commands"
FRAME_SENDER_WS_URL = f"ws://backend-gcs:{BACKEND_PORT}/ws/ai-frame-reader"

# Global state
_loop = None # async event loop controller, manages the websocket sending
_loop_thread = None # OS thread process controller, prevents the cv2 loop from being blocked by the websocket I/O
_camera_ws = None
_command_ws = None
_frame_sender_ws = None

_current_frame = None # Latest frame from camera
_frame_lock = threading.Lock() 

_pending_click = None # Store click coordinates
_pending_command = None # Queued commands
_mouse_position = (0, 0) # Current mouse position
_command_lock = threading.Lock()

# EVENT LOOP MANAGEMENT
def _start_event_loop():
    """Start the asyncio event loop in a background thread"""
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_forever()

def initialize():
    """Init. Establishes all WebSocket connections."""
    global _loop, _loop_thread

    if _loop_thread is not None:
        print("AiStreamClient already initialized")
        return

    print("Initializing AiStreamClient...")

    # Start event loop in background thread
    _loop_thread = threading.Thread(target=_start_event_loop, daemon=True)
    _loop_thread.start()

    # Wait for loop to start
    time.sleep(0.1)

    # Connect all WebSocket endpoints
    future = asyncio.run_coroutine_threadsafe(_connect_all(), _loop)
    try:
        future.result(timeout=10)
        print("AiStreamClient initialized successfully")
    except Exception as e:
        print(f"Failed to initialize AiStreamClient: {e}")

async def _connect_all():
    """Connect to all WebSocket endpoints as background tasks"""

    asyncio.create_task(_connect_frame_sender())
    asyncio.create_task(_receive_camera_frames())
    asyncio.create_task(_receive_frontend_commands())

# CAMERA FRAME RECEIVER
async def _receive_camera_frames():
    """Connect to camera source and continuously receive frames"""
    global _camera_ws, _current_frame, _frame_lock

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            print(f"Connecting to camera source at {CAMERA_WS_URL}...")
            async with websockets.connect(CAMERA_WS_URL) as ws:
                _camera_ws = ws
                print("Successfully connected to camera source")
                retry_count = 0

                async for message in ws:
                    try:
                        jpeg_bytes = base64.b64decode(message)
                        nparr = np.frombuffer(jpeg_bytes, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                        if frame is not None:
                            with _frame_lock:
                                _current_frame = frame
                    except Exception as e:
                        print(f"Error decoding frame: {e}")
                        continue

        except ConnectionRefusedError:
            retry_count += 1
            print(f"Camera source connection refused (attempt {retry_count}/{max_retries}). Retrying in 3s...")
            await asyncio.sleep(3)
        except Exception as e:
            retry_count += 1
            print(f"Camera source error (attempt {retry_count}/{max_retries}): {e}. Retrying in 3s...")
            await asyncio.sleep(3)

    print("Failed to connect to camera source after maximum retries")
    _camera_ws = None

def get_current_frame():
    """Get the latest frame from the camera source."""
    with _frame_lock:
        if _current_frame is None:
            return None
        return _current_frame.copy()

# COMMAND RECEIVER
async def _receive_frontend_commands():
    """Connect to command channel and receive frontend commands"""
    global _command_ws, _pending_click, _pending_command, _mouse_position, _command_lock

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            print(f"Connecting to command channel at {COMMAND_WS_URL}...")
            async with websockets.connect(COMMAND_WS_URL) as ws:
                _command_ws = ws
                print("Successfully connected to command channel")
                retry_count = 0

                async for message in ws:
                    try:
                        data = json.loads(message)
                        command_type = data.get("type")

                        if command_type == "mouse_move":
                            x = data.get("x")
                            y = data.get("y")
                            if x is not None and y is not None:
                                with _command_lock:
                                    _mouse_position = (int(x), int(y))

                        elif command_type == "click":
                            x = data.get("x")
                            y = data.get("y")
                            if x is not None and y is not None:
                                with _command_lock:
                                    _pending_click = (int(x), int(y))
                                print(f"Received click command: ({x}, {y})")

                        elif command_type in ["stop_tracking", "reselect_object"]:
                            with _command_lock:
                                _pending_command = command_type
                            print(f"Received command: {command_type}")

                    except json.JSONDecodeError as e:
                        # Silently skip malformed messages
                        continue
                    except Exception as e:
                        print(f"Error processing command: {e}")
                        continue

        except ConnectionRefusedError:
            retry_count += 1
            print(f"Command channel connection refused (attempt {retry_count}/{max_retries}). Retrying in 3s...")
            await asyncio.sleep(3)
        except Exception as e:
            retry_count += 1
            print(f"Command channel error (attempt {retry_count}/{max_retries}): {e}. Retrying in 3s...")
            await asyncio.sleep(3)

    print("Failed to connect to command channel after maximum retries")
    _command_ws = None

def get_pending_click():
    """
    Get and clear any pending click from the frontend.
    Returns (x, y) tuple if a click is pending, None otherwise.
    """
    global _pending_click
    with _command_lock:
        click = _pending_click
        _pending_click = None
        return click

def get_pending_command():
    """
    Get and clear any pending command from the frontend.
    Returns frontend command string if pending, None otherwise.
    """
    global _pending_command
    with _command_lock:
        command = _pending_command
        _pending_command = None
        return command

def get_mouse_position():
    """
    Get the current mouse position from the frontend.
    Returns (x, y) tuple.
    """
    with _command_lock:
        return _mouse_position

# FRAME SENDER
async def _connect_frame_sender():
    """Establish persistent connection to send frames to server"""
    global _frame_sender_ws
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            print(f"Connecting to frame sender at {FRAME_SENDER_WS_URL}...")
            async with websockets.connect(FRAME_SENDER_WS_URL) as ws:
                _frame_sender_ws = ws
                print("Successfully connected to frame sender")
                retry_count = 0  # Reset retry count on successful connection

                # Keep connection alive by listening for messages (server may send keepalives or close signals)
                try:
                    async for message in ws:
                        # Server doesn't send data on this channel, but this keeps connection alive
                        pass
                except websockets.ConnectionClosed:
                    print("Frame sender connection closed by server")
                    _frame_sender_ws = None

        except ConnectionRefusedError:
            retry_count += 1
            print(f"Frame sender connection refused (attempt {retry_count}/{max_retries}). Retrying in 3s...")
            await asyncio.sleep(3)
        except websockets.ConnectionClosed:
            print("Frame sender connection closed, reconnecting...")
            _frame_sender_ws = None
            await asyncio.sleep(1)
        except Exception as e:
            retry_count += 1
            print(f"Frame sender error (attempt {retry_count}/{max_retries}): {e}. Retrying in 3s...")
            await asyncio.sleep(3)

    print("Failed to connect frame sender after maximum retries")
    _frame_sender_ws = None

async def _send_frame_async(frame):
    """Async function to encode and send frame"""
    global _frame_sender_ws

    if _frame_sender_ws is None:
        print("Cannot send frame: No connection to server")
        return

    try:
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if not success:
            return  # Silently skip frame encoding failures

        base64_string = base64.b64encode(buffer.tobytes()).decode('utf-8')

        await _frame_sender_ws.send(base64_string)

    except websockets.ConnectionClosed:
        _frame_sender_ws = None
    except Exception:
        # Silently skip errors
        pass

def send_frame(frame):
    """Send the AI processed frame to the frontend."""
    global _loop

    if _loop is None:
        print("Event loop not initialized!")
        return

    try:
        # If server is slow, skip frame and move to the next one
        future = asyncio.run_coroutine_threadsafe(_send_frame_async(frame), _loop)
        future.result(timeout=0.008)  # 8ms timeout
    except asyncio.TimeoutError:
        # server is backlogged, next frame will be sent
        pass
    except Exception as e:
        # Silently skip errors
        pass

# CLEANUP
def shutdown():
    """Clean shutdown of all connections and event loop"""
    global _loop

    if _loop is not None:
        _loop.call_soon_threadsafe(_loop.stop)

    print(f"AiStreamClient shutdown complete. PORT {BACKEND_PORT}")