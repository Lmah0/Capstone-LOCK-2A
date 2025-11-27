import cv2
from AIEngine import TrackingEngine
from InterfaceHandler import Cv2UiHelperClass
from GeoLocate import locate
import sys
import os
import asyncio
import threading
import time

# Tell python to look into parent directory for the AiStream file
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)
from GCS.backend import AiStream

# Global Vars
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_PATH = os.path.join(BASE_DIR, "Spike_1.0", "video.mp4")
MODEL_PATH = os.path.join(BASE_DIR, "Spike_1.0", "yolo11n-seg.pt")
WINDOW_NAME = "Interactive Segmentation"

_loop = None # async event loop controller, manages the websocket sending
_loop_thread = None # OS thread process controller, prevents the cv2 loop from being blocked by the websocket I/O

def start_event_loop():
    """Start the asyncio event loop in a background thread"""
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_forever() 

def initialize_async_client():
    """Initialize the async client in the background thread"""
    global _loop, _loop_thread
    
    if _loop_thread is None:
        # Start event loop in a background thread
        _loop_thread = threading.Thread(target=start_event_loop, daemon=True)
        _loop_thread.start()
        
        # Wait a moment for the loop to start
        time.sleep(0.1)
        
        # Connect to server
        future = asyncio.run_coroutine_threadsafe(
            AiStream.connect_to_server(), 
            _loop
        )
        try:
            future.result(timeout=10) 
            print("Async client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize async client: {e}")

def run_async_send_frame(frame):
    """Background thread that sends the cv2 frame to gcs server"""
    global _loop
    
    if _loop is None:
        print("Event loop not initialized!")
        return
        
    try:
        future = asyncio.run_coroutine_threadsafe(
            AiStream.send_frame_to_server(frame), 
            _loop
        )
        future.result(timeout=0.1)
    except asyncio.TimeoutError:
        print("Frame send timeout - server may be slow")
    except Exception as e:
        print(f"Error sending frame: {e}")

def main():
    initialize_async_client()
    
    cap = cv2.VideoCapture(VIDEO_PATH)
    input_manager = Cv2UiHelperClass(WINDOW_NAME)
    engine = TrackingEngine(MODEL_PATH)
    
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: 
            break
        
        frame_count += 1
        output_frame = frame.copy()

        # --- STATE 1: TRACKING MODE ---
        if engine.is_tracking:
            success, bbox = engine.update(frame, frame_count)
            if success:
                output_frame = Cv2UiHelperClass.draw_tracking_state(
                    output_frame, 
                    bbox, 
                    engine.tracked_class, 
                    engine.status_message
                )

                # --- Calculate Target Location ---
                cx = bbox[0] + bbox[2]/2
                cy = bbox[1] + bbox[3]/2
                
                # Get telemetry (Example values)
                current_alt = 10.0 # meters
                current_lat = 50
                current_lon = 100
                heading = 0 # East
                
                target_lat, target_lon = locate(
                    current_lat, current_lon, current_alt, heading, cx, cy
                )
                
                print(f"Target Found at relative latitude, longitude: {target_lat}, {target_lon}")
                run_async_send_frame(output_frame)
            else:
                print("Tracking Lost")

        # --- STATE 2: DETECTION MODE ---
        else:
            results = engine.detect_objects(frame)
            
            if results.masks is not None:
                (cursor_x, cursor_y) = input_manager.get_mouse_position()

                # Draw hover effects
                output_frame, hover_box, hover_index = Cv2UiHelperClass.draw_hover_effects(
                    frame, 
                    results.masks.data, 
                    results.boxes.xyxy.cpu().numpy(),
                    results.boxes.cls.cpu().numpy(),
                    cursor_x,
                    cursor_y,
                )

                # Check for Click to Start Tracking
                if input_manager.consume_click() and hover_box is not None:
                    class_id = int(results.boxes.cls[hover_index])
                    engine.start_tracking(frame, hover_box, class_id)
        
        # Display
        cv2.imshow("Interactive Segmentation", output_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    
    # Cleanup
    if _loop is not None:
        _loop.call_soon_threadsafe(_loop.stop)

if __name__ == "__main__":
    main()