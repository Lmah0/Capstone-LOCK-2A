"""
GCS Backend AI Processor: WebSocket-based detection and tracking.
Uses TrackingEngine for code sharing - EXACT SAME approach as mouse_hover_refactored.py
"""

import os
import time
import numpy as np
from collections import deque

import AiStreamClient
from AIEngine import TrackingEngine, ProcessingState, process_detection_mode, process_tracking_mode
from GeoLocate import locate

# Global Vars
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'yolo11n.pt')
VIDEO_PATH = os.path.join(BASE_DIR, 'video.mp4')

# Initialize engine 
engine = TrackingEngine(MODEL_PATH)

# Direct references to engine attributes for hot path access (bypasses property overhead)
model = engine.model

# Initialize processing state 
state = ProcessingState()

# Basic FPS tracking (minimal overhead)
STATS_WINDOW = 100
frame_times = deque(maxlen=STATS_WINDOW)
last_fps_print = time.time()

def print_fps():
    """Print FPS statistics with detailed profiling breakdown for DETECTION mode"""
    if len(frame_times) < 3:
        return
    
    avg_frame_time = np.mean(frame_times)
    fps = 1000.0 / avg_frame_time if avg_frame_time > 0 else 0
    mode = "TRACKING" if state.tracking else "DETECTION"
    
    avg_get = np.mean(get_frame_times) if len(get_frame_times) > 0 else 0
    avg_send = np.mean(send_frame_times) if len(send_frame_times) > 0 else 0
    
    print(f"\n[Frame {state.frame_count}] [{mode} MODE] FPS: {fps:.1f} (avg frame: {avg_frame_time:.2f}ms)")
    
    # WebSocket timing
    print(f"  WebSocket I/O:")
    print(f"    ├─ Get Frame:  {avg_get:.2f}ms")
    print(f"    └─ Send Frame: {avg_send:.2f}ms")
    
    # Print detailed breakdown for DETECTION mode
    if not state.tracking:
        if state.detection_ran_this_frame:
            print(f"  Input Profiling:")
            print(f"    Frame: {state.profile_frame_shape} dtype={state.profile_frame_dtype} device={state.profile_frame_device}")
            print(f"    Model Device: {state.profile_model_device}")
            print(f"  Detection Profiling (detection ran this frame):")
            print(f"    ├─ Model Inference:  {state.profile_inference_ms:.2f}ms")
            print(f"    │  ├─ Frame Prep:      {state.profile_frame_prep_ms:.2f}ms")
            print(f"    │  ├─ Model Predict:   {state.profile_model_predict_ms:.2f}ms (BOTTLENECK CHECK)")
            print(f"    │  └─ Results Proc:    {state.profile_results_process_ms:.2f}ms")
            print(f"    ├─ Extract Boxes:    {state.profile_boxes_ms:.2f}ms")
            print(f"    └─ Drawing/Overlay:  {state.profile_drawing_ms:.2f}ms")
            total_detection_time = state.profile_inference_ms + state.profile_boxes_ms + state.profile_drawing_ms
            print(f"    Total Detection:     {total_detection_time:.2f}ms")
        else:
            print(f"  (Using cached detection from previous frame - no inference run)")
    print()

print("AI Processor started, waiting for frames...")

try:
    AiStreamClient.initialize_video(VIDEO_PATH) # Start Playing Mocked Video
    AiStreamClient.initialize() # 
    
    # Track WebSocket timing
    get_frame_times = deque(maxlen=100)
    send_frame_times = deque(maxlen=100)
    
    while True: 
        frame_start_time = time.time()
        
        # Get frame
        t_get_start = time.time()
        frame = AiStreamClient.get_video_frame()
        t_get_ms = (time.time() - t_get_start) * 1000
        get_frame_times.append(t_get_ms)
        
        if frame is None:
            time.sleep(0.01)
            continue

        state.increment_frame()
        
        # Get interaction inputs from frontend
        cursor_pos = AiStreamClient.get_mouse_position()
        click_pos = AiStreamClient.get_pending_click()
        
        cursor_x, cursor_y = cursor_pos if cursor_pos else (0, 0)
        
        # Check for frontend commands
        command = AiStreamClient.get_pending_command()
        if command is not None:
            if command == "stop_tracking":
                state.reset_tracking()
                print("Stopped tracking, resuming detection")
            elif command == "reselect_object":
                state.reset_tracking()
                print("Ready to select new object")

        # --- DETECTION MODE or TRACKING MODE ---
        if not state.tracking:
            # --- DETECTION MODE ---
            output_frame, _, mode_changed = process_detection_mode(
                frame, model, state, (cursor_x, cursor_y), click_pos
            )
        else:
            # --- TRACKING MODE ---
            output_frame, tracking_succeeded, mode_changed = process_tracking_mode(frame, state)
            
            # Geolocation processing - only run every N frames to reduce computational load
            if tracking_succeeded and state.frame_count % 5 == 0:
                x, y, w, h = state.tracked_bbox
                
                # TODO: Get telemetry from frame metadata or flight computer
                current_alt = 10.0 
                current_lat = 50
                current_lon = 100
                heading = 0
                
                # --- Calculate Target Location ---
                image_center_x = frame.shape[1] / 2
                image_center_y = frame.shape[0] / 2
                
                bbox_center_x = x + w/2
                bbox_center_y = y + h/2
                
                obj_x_px = bbox_center_x - image_center_x
                obj_y_px = bbox_center_y - image_center_y
                
                target_lat, target_lon = locate(current_lat, current_lon, current_alt, heading, obj_x_px, obj_y_px)
                print(f"Target Found at relative latitude, longitude: {target_lat}, {target_lon}")
        
        # Send frame to frontend
        display_frame = output_frame if output_frame is not None else frame
        t_send_start = time.time()
        AiStreamClient.push_frame(display_frame)
        t_send_ms = (time.time() - t_send_start) * 1000
        send_frame_times.append(t_send_ms)
        
        # Track FPS
        frame_time = (time.time() - frame_start_time) * 1000
        frame_times.append(frame_time)
        
        # Print FPS every 2 seconds
        if time.time() - last_fps_print > 2.0:
            print_fps()
            last_fps_print = time.time()

except Exception as e:
    print(f"\nERROR: Unexpected exception: {e}")
    import traceback
    traceback.print_exc()

finally:
    AiStreamClient.shutdown()