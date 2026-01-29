from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
import uvicorn
from contextlib import asynccontextmanager
import traceback
import asyncio
import numpy as np
import time
import os
import cv2
from shared_frame import attach_shared_frame, read_frame

# Class obj used to match the return JSON from frontend
# Offer/answer is the connection request - the video streaming begins when both sides agree
class RTCOffer(BaseModel):
    sdp: str #Text format that describes media session
    type: str # "offer" (from frontend) or "answer" (from backend)

_peer_connections = set()
_shared_memory_attached = False

def try_attach_shared_memory():
    """Try to attach to shared memory on first frame request"""
    global _shared_memory_attached
    if _shared_memory_attached:
        return True
    
    try:
        attach_shared_frame()
        _shared_memory_attached = True
        print("[WebRTC] Successfully attached to shared memory")
        return True
    except Exception as e:
        return False

    
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("[WebRTC] Shutting down peer connections...")
    await asyncio.gather(
        *[pc.close() for pc in list(_peer_connections)],
        return_exceptions=True
    )
    _peer_connections.clear()


_app = FastAPI(lifespan=lifespan)
_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebRTC Video Stream
class AIVideoStreamTrack(VideoStreamTrack):
    """
        - Custom video track that streams AI-processed frames via WebRTC.
        - Architecture: latest-frame (overwrite) buffer
        - Frames may be dropped & delivery of every frame is not guaranteed but this is low latency
    """
    def __init__(self):
        super().__init__()
        self._start = None # Used internally by parent class of when streaming started
        self.port = int(os.getenv("WEBRTC_PORT", 8767))

    async def recv(self):
        """Give WebRTC the next frame to send."""
        try:
            if self._start is None:
                self._start = time.time()

            # Pts = presentation timestamp which is the frame number
            pts, time_base = await self.next_timestamp()

            # Try to attach on first frame
            if not try_attach_shared_memory():
                frame = None
            else:
                frame = read_frame()

            if frame is None:  # If no frame available send a black screen
                frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # Convert BGR (OpenCV format) to RGB (WebRTC format)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Wrap numpy array in a VideoFrame object for aiortc
            video_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
            
            # Attach timing info so parent client (VideoStreamTrack) knows when to display this frame
            video_frame.pts = pts
            video_frame.time_base = time_base

            return video_frame

        except Exception as e:
            print(f"WebRTC recv ERROR: {e}")
            traceback.print_exc()
            raise

async def start_webrtc_server():
    """Start the WebRTC server as a background task"""
    try:
        port = int(os.getenv("WEBRTC_PORT", 8767))
        config = uvicorn.Config(
            _app,
            host="0.0.0.0",
            port=port,
            log_level="warning"
        )
        server = uvicorn.Server(config)
        print(f"WebRTC server starting on port {port}")
        await server.serve()
    except asyncio.CancelledError:
        print("WebRTC server shutting down...")
        raise
    except Exception as e:
        print(f"WebRTC server error: {e}")
        raise

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


if __name__ == "__main__":
    asyncio.run(start_webrtc_server())