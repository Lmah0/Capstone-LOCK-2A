"""
GCS Backend AI Processor: WebSocket-based detection and tracking.
Uses TrackingEngine for code sharing but inlines hot path for performance.
"""

import os
import time
import cv2
import numpy as np

import AiStreamClient
from AIEngine import TrackingEngine, TrackingConfig
from GeoLocate import locate

# Global Vars
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'yolo11n.pt')

# Initialize engine (shares code with mouse_hover_refactored)
engine = TrackingEngine(MODEL_PATH)

# Direct references for hot path access (bypasses property overhead)
model = engine.model

# State tracking (module level for performance)
frame_count = 0
tracking = False
tracker = None
tracked_class = None
tracked_bbox = None
last_detection_results = None
last_tracker_bbox = None

print("AI Processor started, waiting for frames...")

try:
    AiStreamClient.initialize()
    
    while True: 
        # Waiting for video stream to start
        frame = AiStreamClient.get_current_frame()
        if frame is None:
            time.sleep(0.01)
            continue

        frame_count += 1
        output_frame = frame.copy()
        
        # Get interaction inputs from frontend
        cursor_pos = AiStreamClient.get_mouse_position()
        click_pos = AiStreamClient.get_pending_click()

        # Check for frontend commands
        command = AiStreamClient.get_pending_command()
        if command is not None:
            if command == "stop_tracking":
                tracking = False
                tracker = None
                tracked_class = None
                tracked_bbox = None
                print("Stopped tracking, resuming detection")
            elif command == "reselect_object":
                tracking = False
                tracker = None
                tracked_class = None
                tracked_bbox = None
                print("Ready to select new object")

        # --- DETECTION MODE ---
        if not tracking:
            # Skip frames to speed up initial detection phase
            should_detect = (frame_count % (TrackingConfig.DETECTION_FRAME_SKIP + 1)) == 0
            
            if should_detect:
                # Inline detection for performance
                results = model.predict(frame, conf=TrackingConfig.CONFIDENCE_THRESHOLD, 
                                       iou=TrackingConfig.MODEL_IOU, verbose=False)
                last_detection_results = results
            else:
                results = last_detection_results
            
            # Process bounding boxes
            if results is not None and results[0].boxes is not None and len(results[0].boxes) > 0:
                boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)
                classes = results[0].boxes.cls.cpu().numpy()
                
                hovered_index = None
                cursor_x, cursor_y = cursor_pos if cursor_pos else (0, 0)
                
                # Draw all detections
                for i, box in enumerate(boxes):
                    x1, y1, x2, y2 = box
                    
                    # Hover effect
                    if x1 <= cursor_x <= x2 and y1 <= cursor_y <= y2:
                        hovered_index = i
                        # Draw outline + fill for hovered box
                        cv2.rectangle(output_frame, (x1, y1), (x2, y2), (0, 200, 0), 2)
                        overlay = output_frame.copy()
                        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), -1)
                        output_frame = cv2.addWeighted(overlay, 0.3, output_frame, 0.7, 0)
                        cv2.putText(output_frame, f"Class {int(classes[i])}", (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        # Click = start tracking
                        if click_pos is not None:
                            tracker = cv2.TrackerCSRT.create()
                            tracker.init(frame, (x1, y1, x2 - x1, y2 - y1))
                            tracked_class = int(classes[i])
                            tracked_bbox = (x1, y1, x2 - x1, y2 - y1)
                            tracking = True
                            print(f"Started tracking object {i}, class {tracked_class}")
                            break
                    else:
                        # Draw regular box for non-hovered detections
                        cv2.rectangle(output_frame, (x1, y1), (x2, y2), (100, 100, 100), 1)
        
        # --- TRACKING MODE ---
        else:
            # Skip frames to speed up tracking phase
            should_track = (frame_count % (TrackingConfig.TRACKER_FRAME_SKIP + 1)) == 0
            
            if should_track:
                success, bbox = tracker.update(frame)
                last_tracker_bbox = (success, bbox)
            else:
                success, bbox = last_tracker_bbox if last_tracker_bbox else (False, None)
            
            if success and bbox is not None:
                x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                tracked_bbox = (x, y, w, h)
                
                # Draw gradient fill with transparency
                overlay = output_frame.copy()
                cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 255), -1)
                output_frame = cv2.addWeighted(overlay, 0.3, output_frame, 0.7, 0)
                
                # Draw outline
                cv2.rectangle(output_frame, (x, y), (x + w, y + h), (0, 200, 200), 2)
                cv2.putText(output_frame, f"Tracking class {tracked_class}", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                
                # Geolocation processing
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
            else:
                print("Lost tracking, resuming detection")
                tracking = False
                tracker = None
                tracked_class = None
                tracked_bbox = None

        # Send frame to frontend
        AiStreamClient.send_frame(output_frame)
        time.sleep(0.01)  # Small delay to prevent CPU overload

except Exception as e:
    print(f"\nERROR: Unexpected exception: {e}")
    import traceback
    traceback.print_exc()

finally:
    AiStreamClient.shutdown()