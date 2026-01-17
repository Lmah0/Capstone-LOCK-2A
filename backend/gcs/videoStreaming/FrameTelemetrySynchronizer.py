import time
from collections import deque
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class TimestampedFrame:
    frame_number: int
    wall_clock_time: float
    jpeg_data: bytes
    telemetry: Optional[Dict] = None
    
@dataclass
class TelemetryData:
    timestamp: float
    data: Dict

class FrameTelemetrySynchronizer:
    """Synchronizes video frames with telemetry data based on wall-clock timestamps"""
    
    def __init__(self, max_history=300):  # Keep last 5 seconds at 60fps
        self.telemetry_buffer = deque(maxlen=max_history)
        self.frame_buffer = deque(maxlen=max_history)
        self.max_time_diff = 0.6  # Maximum 100ms difference for matching
    
    def add_telemetry(self, timestamp: float, data: Dict):
        """Add telemetry data with timestamp"""
        self.telemetry_buffer.append(TelemetryData(timestamp, data))
    
    def add_frame(self, frame_number: int, timestamp: float, jpeg_data: bytes) -> TimestampedFrame:
        """Add frame with timestamp and match with closest telemetry"""
        # Find closest telemetry data
        matched_telemetry = self._find_closest_telemetry(timestamp)
        
        frame = TimestampedFrame(
            frame_number=frame_number,
            wall_clock_time=timestamp,
            jpeg_data=jpeg_data,
            telemetry=matched_telemetry
        )
        
        self.frame_buffer.append(frame)
        return frame
    
    def _find_closest_telemetry(self, target_timestamp: float) -> Optional[Dict]:
        """Find telemetry data closest to target timestamp"""
        if not self.telemetry_buffer:
            return None
        
        closest = min(
            self.telemetry_buffer,
            key=lambda t: abs(t.timestamp - target_timestamp)
        )
        
        time_diff = abs(closest.timestamp - target_timestamp)
        
        # Only return if within acceptable time difference
        if time_diff <= self.max_time_diff:
            return {
                **closest.data,
                'sync_time_diff_ms': time_diff * 1000,
                'telemetry_timestamp': closest.timestamp,
                'frame_timestamp': target_timestamp
            }
        
        return None
    
    def get_frame_with_telemetry(self, frame_number: int) -> Optional[TimestampedFrame]:
        """Get a specific frame with its matched telemetry"""
        for frame in reversed(self.frame_buffer):
            if frame.frame_number == frame_number:
                return frame
        return None
