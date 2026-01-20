"""
AiStream - I/O layer for AI processor

Handles:
    1. Video Input: cv2 capture from file
    2. Video Output: WebRTC streaming via aiortc (H.264)
    3. Commands: WebSocket connection for frontend commands (clicks, mouse)
"""

import asyncio
import websockets
import cv2
import os
import threading
import time
import json
import numpy as np
import fractions
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
from dotenv import load_dotenv


load_dotenv(dotenv_path="../../.env")

# FastAPI app for WebRTC signaling
_app = FastAPI()
_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Class obj used to match the return JSON from frontend
# Offer/answer is the connection request - the video streaming begins when both sides agree
class RTCOffer(BaseModel):
    sdp: str #Text format that describes media session
    type: str # "offer" (from frontend) or "answer" (from backend)

# URLs
BACKEND_PORT = os.getenv('GCS_BACKEND_PORT')
WEBRTC_PORT = os.getenv('WEBRTC_PORT')
COMMAND_WS_URL = f"ws://backend-gcs:{BACKEND_PORT}/ws/ai-commands"

# Global state 
_main_loop = None
_main_thread = None

# Video Input (CV2)
_video_capture = None
_video_lock = threading.Lock()

# WebRTC Video
_peer_connections = set()
_output_frame = None
_output_frame_lock = threading.Lock()
_server = None

# Websocket AI Commands
_command_ws = None
_pending_click = None
_pending_command = None
_mouse_position = (0, 0)
_command_lock = threading.Lock()

# EVENT LOOP MANAGEMENT
def _start_event_loop():
    """Start the asyncio event loop in a background thread"""
    global _main_loop
    _main_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_main_loop)

    # Start both WebRTC server and command handler
    _main_loop.create_task(_start_webrtc_server())
    _main_loop.create_task(_receive_frontend_commands())

    _main_loop.run_forever()

def initialize():
    """Init. Establishes AI Command WebSocket connection and WebRTC server"""
    global _main_thread

    if _main_thread is not None:
        print("AiStreamClient already initialized")
        return

    print("Initializing AiStreamClient...")

    # Start event loop in background thread
    _main_thread = threading.Thread(target=_start_event_loop, daemon=True)
    _main_thread.start()

    # Wait for loop to start
    time.sleep(0.1)
    print("AiStreamClient initialized successfully")

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

# WebRTC Video Stream
class AIVideoStreamTrack(VideoStreamTrack):
    """Custom video track that streams AI-processed frames via WebRTC."""
    kind = "video"

    def __init__(self):
        super().__init__()
        self._start = None # Used internally by parent class of when streaming started

    async def recv(self):
        try:
            if self._start is None:
                self._start = time.time()

            # Pts = presentation timestamp which is the frame number
            pts, time_base = await self.next_timestamp()

            frame = _get_output_frame()

            if frame is None: # If no frame is avaliable send a black screen
                frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # Convert BGR (OpenCV format) to RGB (WebRTC format)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Wrap numpy array in a VideoFrame object for aiortc
            video_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
            
             # Attach timing info so client knows when to display this frame
            video_frame.pts = pts
            video_frame.time_base = time_base

            return video_frame

        except Exception as e:
            print(f"WebRTC recv ERROR: {e}")
            raise


def _get_output_frame():
    """Get the latest output frame"""
    global _output_frame
    with _output_frame_lock:
        if _output_frame is None:
            return None
        return _output_frame.copy()


def push_frame(frame: np.ndarray):
    """Push a processed frame to be streamed via WebRTC"""
    global _output_frame
    with _output_frame_lock:
        _output_frame = frame.copy()

@_app.post("/offer")
async def handle_offer(offer: RTCOffer):
    """Endpoint that handles WebRTC offer from frontend and return answer"""
    rtc_offer = RTCSessionDescription(sdp=offer.sdp, type=offer.type)

    pc = RTCPeerConnection()
    _peer_connections.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        state = pc.connectionState
        if state in ("connected", "failed", "closed"):
            print(f"WebRTC connection state: {state}")
        if state == "failed" or state == "closed":
            await pc.close()
            _peer_connections.discard(pc)

    video_track = AIVideoStreamTrack()
    pc.addTrack(video_track)

    # Process the offer from frontend and create an answer
    await pc.setRemoteDescription(rtc_offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # Frontend will use this to complete the connection
    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    }

async def _start_webrtc_server():
    """Start the WebRTC signaling server using uvicorn."""
    global _server

    config = uvicorn.Config(
        _app,
        host="0.0.0.0",
        port=int(WEBRTC_PORT),
        log_level="warning"
    )
    _server = uvicorn.Server(config)
    print(f"WebRTC server started on port {WEBRTC_PORT}")
    await _server.serve()


async def _stop_webrtc_server():
    """Stop the WebRTC signaling server."""
    global _server
    if _server:
        _server.should_exit = True

# Video Input (Mocked video stream)
def init(video_path: str = None) -> bool:
    """Initialize mocked video"""
    global _video_capture

    _video_capture = cv2.VideoCapture(video_path)

    if not _video_capture.isOpened():
        print(f"Error: Could not open video file at {video_path}")
        return False

    print(f"Video capture initialized: {video_path}")
    return True

def get_frame():
    """ Get the next frame from the video capture. Automatically loops when video ends."""
    global _video_capture

    if _video_capture is None:
        return None

    with _video_lock:
        ret, frame = _video_capture.read()

        if not ret: # Loop the video if we've reached the end
            _video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = _video_capture.read()
            if not ret:
                return None

        return frame.copy()

def _release_video():
    """Release the video capture resource."""
    global _video_capture
    if _video_capture is not None:
        _video_capture.release()
        _video_capture = None

# CLEANUP
def shutdown():
    """Clean shutdown of all connections and event loop"""
    global _main_loop

    _release_video()

    if _main_loop is not None:
        asyncio.run_coroutine_threadsafe(_stop_webrtc_server(), _main_loop)
        _main_loop.call_soon_threadsafe(_main_loop.stop)

    print("AiStreamClient shutdown complete")