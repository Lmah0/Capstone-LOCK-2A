"""
AI Processor: Object detection and tracking with direct video stream from Raspberry Pi.
Displays output in OpenCV window instead of WebSocket streaming.
"""

import os
import time
import cv2
import numpy as np
import sys
from collections import deque
import threading

from AIEngine import TrackingEngine, ProcessingState, process_detection_mode, process_tracking_mode
from GeoLocate import locate
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Go up one level to 'backend'
#    (current_dir is '.../backend/ai_processor', so parent is '.../backend')
backend_dir = os.path.dirname(current_dir)

# 3. Construct the path to the videoStreaming folder
#    Target: '.../backend/gcs/videoStreaming'
video_stream_path = os.path.join(backend_dir, "gcs", "videoStreaming")

# 4. Add this path to system path so Python can find the file
sys.path.append(video_stream_path)

from receiveVideoStream import yield_frames_with_timestamps

# Global Vars
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'yolo11n.pt')

# Initialize engine 
engine = TrackingEngine(MODEL_PATH)
model = engine.model

# Initialize processing state 
state = ProcessingState()

# Basic FPS tracking
STATS_WINDOW = 100
frame_times = deque(maxlen=STATS_WINDOW)
last_fps_print = time.time()


class StreamThread:
    """
    Reads frames in a separate thread to prevent buffer overruns
    when the AI processing takes too long.
    """

    def __init__(self):
        self.latest_frame = None
        self.latest_ts = None
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        print("Stream Thread Started")
        try:
            # Continuously consume the generator
            for frame, timestamp in yield_frames_with_timestamps():
                if not self.running:
                    break

                # Update the latest frame safely
                with self.lock:
                    self.latest_frame = frame
                    self.latest_ts = timestamp
        except Exception as e:
            print(f"Stream Thread Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
            print("Stream Thread Stopped")

    def get_frame(self):
        """Returns the most recent frame and timestamp"""
        with self.lock:
            return self.latest_frame, self.latest_ts

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)


class MouseInteraction:
    """Handle mouse events for object selection"""
    
    def __init__(self):
        self.cursor_pos = (0, 0)
        self.click_pos = None
        self.pending_click = None
        
    def mouse_callback(self, event, x, y, flags, param):
        """OpenCV mouse callback"""
        # Update cursor position
        self.cursor_pos = (x, y)
        
        # Handle clicks
        if event == cv2.EVENT_LBUTTONDOWN:
            self.pending_click = (x, y)
            print(f"Click registered at: ({x}, {y})")
    
    def get_cursor_position(self):
        return self.cursor_pos
    
    def get_pending_click(self):
        """Returns and clears pending click"""
        click = self.pending_click
        self.pending_click = None
        return click


def print_fps(frame_times, state):
    """Print FPS statistics with detailed profiling breakdown"""
    if len(frame_times) < 3:
        return
    
    avg_frame_time = np.mean(frame_times)
    fps = 1000.0 / avg_frame_time if avg_frame_time > 0 else 0
    mode = "TRACKING" if state.tracking else "DETECTION"
    
    print(f"\n[Frame {state.frame_count}] [{mode} MODE] FPS: {fps:.1f} (avg frame: {avg_frame_time:.2f}ms)")
    
    # Print detailed breakdown for DETECTION mode
    if not state.tracking:
        if state.detection_ran_this_frame:
            print(f"  Input Profiling:")
            print(f"    Frame: {state.profile_frame_shape} dtype={state.profile_frame_dtype}")
            print(f"  Detection Profiling:")
            print(f"    ├─ Model Inference:  {state.profile_inference_ms:.2f}ms")
            print(f"    │  ├─ Frame Prep:      {state.profile_frame_prep_ms:.2f}ms")
            print(f"    │  ├─ Model Predict:   {state.profile_model_predict_ms:.2f}ms")
            print(f"    │  └─ Results Proc:    {state.profile_results_process_ms:.2f}ms")
            print(f"    ├─ Extract Boxes:    {state.profile_boxes_ms:.2f}ms")
            print(f"    └─ Drawing/Overlay:  {state.profile_drawing_ms:.2f}ms")
            total_detection_time = state.profile_inference_ms + state.profile_boxes_ms + state.profile_drawing_ms
            print(f"    Total Detection:     {total_detection_time:.2f}ms")
        else:
            print(f"  (Using cached detection - no inference)")
    print()


def add_info_overlay(frame, timestamp_info, state):
    """Add information overlay to frame"""
    overlay = frame.copy()
    
    # Semi-transparent background
    cv2.rectangle(overlay, (10, 10), (400, 150), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
    
    # Frame info
    mode = "TRACKING" if state.tracking else "DETECTION"
    cv2.putText(frame, f"Mode: {mode}", (20, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f"Frame: {state.frame_count}", (20, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Timestamp info
    if timestamp_info:
        if timestamp_info.get('wall_clock_time'):
            from datetime import datetime
            dt = datetime.fromtimestamp(timestamp_info['wall_clock_time'])
            cv2.putText(frame, f"Time: {dt.strftime('%H:%M:%S.%f')[:-3]}", 
                       (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            if timestamp_info.get('latency_ms'):
                latency_color = (0, 255, 0) if timestamp_info['latency_ms'] < 100 else (0, 165, 255)
                cv2.putText(frame, f"Latency: {timestamp_info['latency_ms']:.1f}ms", 
                           (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, latency_color, 1)
    
    # Controls
    cv2.putText(frame, "Controls: [Click] Select | [R] Reset | [Q] Quit", 
                (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    return frame


def main():
    print("AI Processor started, waiting for frames from Raspberry Pi...")
    print("--- Controls ---")
    print(" [Click]      : Select object to track")
    print(" [R]          : Reset tracking / reselect object")
    print(" [Q] or [ESC] : Quit")
    print()
    
    # Initialize video stream thread
    stream_thread = StreamThread()
    stream_thread.start()
    
    # Wait for first frame
    print("Waiting for video stream...")
    while stream_thread.get_frame()[0] is None:
        time.sleep(0.1)
    print("✓ Video stream connected\n")
    
    # Create window and mouse interaction
    window_name = "AI Processor - Raspberry Pi Stream"
    cv2.namedWindow(window_name)
    mouse_handler = MouseInteraction()
    cv2.setMouseCallback(window_name, mouse_handler.mouse_callback)
    
    last_fps_print = time.time()
    
    try:
        while True:
            frame_start_time = time.time()
            
            # Get latest frame and timestamp
            frame, timestamp_info = stream_thread.get_frame()
            
            if frame is None:
                time.sleep(0.01)
                continue
            
            state.increment_frame()
            
            # Get interaction inputs
            cursor_pos = mouse_handler.get_cursor_position()
            click_pos = mouse_handler.get_pending_click()
            cursor_x, cursor_y = cursor_pos
            
            # Check for keyboard commands
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # Q or ESC
                print("Quit requested")
                break
            elif key == ord('r'):  # R to reset
                state.reset_tracking()
                print("Tracking reset - ready to select new object")
            
            # --- DETECTION MODE or TRACKING MODE ---
            if not state.tracking:
                # --- DETECTION MODE ---
                output_frame, _, mode_changed = process_detection_mode(
                    frame, model, state, (cursor_x, cursor_y), click_pos
                )
            else:
                # --- TRACKING MODE ---
                output_frame, tracking_succeeded, mode_changed = process_tracking_mode(frame, state)
                
                # Geolocation processing - only run every N frames
                if tracking_succeeded and state.frame_count % 5 == 0:
                    x, y, w, h = state.tracked_bbox
                    
                    # TODO: Get telemetry from timestamp_info or flight computer
                    # For now, use placeholder values
                    current_alt = 10.0 
                    current_lat = 50
                    current_lon = 100
                    heading = 0
                    
                    # Calculate target location
                    image_center_x = frame.shape[1] / 2
                    image_center_y = frame.shape[0] / 2
                    
                    bbox_center_x = x + w/2
                    bbox_center_y = y + h/2
                    
                    obj_x_px = bbox_center_x - image_center_x
                    obj_y_px = bbox_center_y - image_center_y
                    
                    target_lat, target_lon = locate(
                        current_lat, current_lon, current_alt, heading, obj_x_px, obj_y_px
                    )
                    print(f"Target at relative lat/lon: {target_lat:.6f}, {target_lon:.6f}")
            
            # Add info overlay
            display_frame = output_frame if output_frame is not None else frame
            display_frame = add_info_overlay(display_frame, timestamp_info, state)
            
            # Show frame
            cv2.imshow(window_name, display_frame)
            
            # Track FPS
            frame_time = (time.time() - frame_start_time) * 1000
            frame_times.append(frame_time)
            
            # Print FPS every 2 seconds
            if time.time() - last_fps_print > 2.0:
                print_fps(frame_times, state)
                last_fps_print = time.time()
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nERROR: Unexpected exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nCleaning up...")
        stream_thread.stop()
        cv2.destroyAllWindows()
        print("Shutdown complete")


if __name__ == "__main__":
    main()