"""WebRTC functionality for streaming AI-processed video frames."""
from fastapi import APIRouter
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
from pydantic import BaseModel
import cv2
import time
import numpy as np
import threading
from fractions import Fraction
import asyncio

# Frame buffer for video streaming
_frame_lock = threading.Lock()
_current_frame = None

# WebRTC peer connections
_peer_connections = set()


class AIVideoStreamTrack(VideoStreamTrack):
    """
    Custom video track that streams AI-processed frames via WebRTC.
    Optimized for Low Latency using Wall Clock timestamps.
    """
    def __init__(self):
        super().__init__()
        self._start = None
        self._timestamp = 0

    async def recv(self):
        """Give WebRTC the next frame to send."""
        if self._start is None:
            self._start = time.time()

        # 90000 is the standard clock rate for video (90kHz)
        timestamp = time.time() - self._start
        pts = int(timestamp * 90000)
        
        # Read frame from buffer
        global _current_frame, _frame_lock
        with _frame_lock:
            frame = _current_frame
            
        if frame is None:
            # Send a black frame if buffer is empty
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add a small sleep to prevent spinning CPU if no frames exist
            await asyncio.sleep(0.01)

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create VideoFrame
        video_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        
        video_frame.pts = pts
        video_frame.time_base = Fraction(1, 90000)

        return video_frame


class RTCOffer(BaseModel):
    """WebRTC offer from client."""
    sdp: str
    type: str


# Create WebRTC router
webrtc_router = APIRouter(prefix="", tags=["webrtc"])

@webrtc_router.post("/offer")
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

    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    }


def write_frame(frame):
    """Write a frame to the shared buffer for WebRTC streaming."""
    global _current_frame, _frame_lock
    with _frame_lock:
        _current_frame = frame


def get_peer_connections():
    """Get the set of active peer connections for cleanup."""
    return _peer_connections