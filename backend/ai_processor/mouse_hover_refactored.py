"""
Interactive object detection and tracking with cv2 window interface.
Uses TrackingEngine for code sharing but inlines hot path for performance.
"""

import cv2
import numpy as np
import os
import time
import argparse
from collections import deque

from AIEngine import TrackingEngine, TrackingConfig, ProcessingState, process_detection_mode, process_tracking_mode

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Interactive object detection and tracking')
parser.add_argument('--stats', action='store_true', default=False, help='Enable statistics collection and reporting')
args = parser.parse_args()
COLLECT_STATS = args.stats

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Use relative paths from the script directory
VIDEO_PATH = os.path.join(script_dir, "../gcs/video.mp4")
MODEL_PATH = os.path.join(script_dir, "models", "yolo11n.pt")

# Initialize engine (reuses code with GCS backend)
engine = TrackingEngine(MODEL_PATH)

# Direct references to engine attributes for hot path access (bypasses property overhead)
model = engine.model

# Initialize processing state
state = ProcessingState()

cap = cv2.VideoCapture(VIDEO_PATH)

cursor_x, cursor_y = 0, 0
click_flag = False

# Performance statistics (track last 100 frames)
STATS_WINDOW = 100
frame_times = deque(maxlen=STATS_WINDOW)

def mouse_event(event, x, y, flags, param):
    global cursor_x, cursor_y, click_flag
    cursor_x, cursor_y = x, y
    if event == cv2.EVENT_LBUTTONDOWN:
        click_flag = True

cv2.namedWindow("Interactive Segmentation")
cv2.setMouseCallback("Interactive Segmentation", mouse_event)

def print_performance_stats():
    """Print simple performance statistics"""
    if not COLLECT_STATS:
        return
    
    if len(frame_times) < 3:
        return
    
    avg_frame_time = np.mean(frame_times)
    fps = 1000.0 / avg_frame_time if avg_frame_time > 0 else 0
    
    print("\n" + "="*60)
    print(f"Performance Statistics (last {len(frame_times)} frames)")
    print(f"FPS: {fps:.2f}")
    print("="*60 + "\n")

while cap.isOpened():
    if COLLECT_STATS:
        frame_start_time = time.time()
    ret, frame = cap.read()
    if not ret:
        break

    state.increment_frame()
    annotated_frame = None

    if not state.tracking:
        # --- DETECTION MODE ---
        output_frame, _, mode_changed = process_detection_mode(
            frame, model, state, (cursor_x, cursor_y), (cursor_x, cursor_y) if click_flag else None
        )
        annotated_frame = output_frame
        if mode_changed:
            click_flag = False
    else:
        # --- TRACKING MODE ---
        output_frame, tracking_succeeded, mode_changed = process_tracking_mode(frame, state)
        annotated_frame = output_frame
        if mode_changed:
            # Switched back to detection mode
            pass
    
    # Display frame
    if annotated_frame is None:
        cv2.imshow("Interactive Segmentation", frame)
    else:
        cv2.imshow("Interactive Segmentation", annotated_frame)
    
    # Record frame time and print stats every 100 frames
    if COLLECT_STATS:
        frame_time = (time.time() - frame_start_time) * 1000
        frame_times.append(frame_time)
    
    if COLLECT_STATS and state.frame_count % 100 == 0:
        print(f"[Frame {state.frame_count}] ", end="")
        print_performance_stats()
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Print final statistics
if COLLECT_STATS:
    print("\n" + "="*60)
    print("Final Performance Statistics")
    print_performance_stats()
