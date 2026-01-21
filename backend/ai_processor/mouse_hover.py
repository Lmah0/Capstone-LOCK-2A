import cv2
import numpy as np
import os
import time
from collections import deque
import argparse

from AIEngine import TrackingConfig

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Interactive object detection and tracking')
parser.add_argument('--stats', action='store_true', default=False, help='Enable statistics collection and reporting')
args = parser.parse_args()
COLLECT_STATS = args.stats

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Use relative paths from the script directory
VIDEO_PATH = os.path.join(script_dir, "../gcs/video.mp4")
# VIDEO_PATH = '/Users/lionelhasan/Downloads/Trimmed Angle.mp4'
MODEL_PATH = os.path.join(script_dir, "models", "yolo11n.pt")

# Load YOLO detection model (bounding box only)
from ultralytics import YOLO
model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(VIDEO_PATH)

cursor_x, cursor_y = 0, 0
click_flag = False

# Tracking variables
tracking = False
tracker = None
tracked_class = None
tracked_bbox = None
frame_count = 0
detection_history = []  # Store recent detections for consistency checking
last_detection_results = None  # Cache detection results for skipped frames
last_tracker_bbox = None  # Cache tracker position for skipped frames

# Performance statistics (track last 100 frames)
STATS_WINDOW = 100
frame_times = deque(maxlen=STATS_WINDOW)
detection_times = deque(maxlen=STATS_WINDOW)
tracker_times = deque(maxlen=STATS_WINDOW)
redetection_times = deque(maxlen=STATS_WINDOW)
frame_start_time = 0

def calculate_iou(box1, box2):
    """Calculate Intersection over Union between two boxes"""
    # box format: (x, y, w, h)
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    # Convert to (x1, y1, x2, y2)
    box1_x2, box1_y2 = x1 + w1, y1 + h1
    box2_x2, box2_y2 = x2 + w2, y2 + h2

    # Intersection area
    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(box1_x2, box2_x2)
    yi2 = min(box1_y2, box2_y2)
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)

    # Union area
    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area

    return inter_area / union_area if union_area > 0 else 0

def get_tracker_confidence(tracker, frame, bbox):
    """Estimate tracker confidence by checking response map"""
    try:
        # CSRT has a response map we can query
        response = tracker.getTrackingResponse(frame)
        if response is not None:
            # Get max value from response map as confidence estimate
            confidence = float(np.max(response))
            return confidence
        return 0.5  # Default to medium confidence if we can't get response
    except:
        return 0.5  # Fallback if method doesn't exist

def mouse_event(event, x, y, flags, param):
    global cursor_x, cursor_y, click_flag
    cursor_x, cursor_y = x, y
    if event == cv2.EVENT_LBUTTONDOWN:
        click_flag = True

cv2.namedWindow("Interactive Segmentation")
cv2.setMouseCallback("Interactive Segmentation", mouse_event)

def draw_gradient_box(frame, bbox, color=(0, 255, 255)):
    """Draw a smooth filled gradient inside a bbox"""
    x, y, w, h = bbox
    overlay = frame.copy()
    alpha = 0.4
    cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
    return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

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
    print(f"Tracking Mode: {TrackingConfig.TRACKING_MODE}")
    print(f"Currently Tracking: {tracking}")
    print(f"FPS: {fps:.2f}")
    print("="*60 + "\n")

def get_current_fps():
    """Get current FPS from frame times"""
    if len(frame_times) < 3:
        return 0
    avg_frame_time = np.mean(frame_times)
    return 1000.0 / avg_frame_time if avg_frame_time > 0 else 0

while cap.isOpened():
    if COLLECT_STATS:
        frame_start_time = time.time()
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    annotated_frame = None  # Only create copy if needed for drawing

    if not tracking:
        # --- RUN DETECTION (Bounding Box Only) ---
        # Skip frames to speed up initial detection phase
        should_run_detection = (frame_count % (TrackingConfig.DETECTION_FRAME_SKIP + 1)) == 0
        
        if should_run_detection:
            if COLLECT_STATS:
                detection_start = time.time()
            results = model.predict(frame, conf=TrackingConfig.CONFIDENCE_THRESHOLD, iou=TrackingConfig.MODEL_IOU, verbose=False)
            if COLLECT_STATS:
                detection_time = (time.time() - detection_start) * 1000  # Convert to ms
                detection_times.append(detection_time)
            last_detection_results = results
        else:
            # Reuse last detection results on skipped frames (don't record time)
            results = last_detection_results
        
        current_boxes = []

        # Process bounding boxes
        if results is not None and results[0].boxes is not None and len(results[0].boxes) > 0:
            boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)
            classes = results[0].boxes.cls.cpu().numpy()

            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box
                current_boxes.append((x1, y1, x2, y2, classes[i]))

                # Hover effect: outline + gradient fill
                if x1 <= cursor_x <= x2 and y1 <= cursor_y <= y2:
                    if annotated_frame is None:
                        annotated_frame = frame.copy()
                    # Draw bounding box outline
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 200, 0), 2)
                    
                    # Gradient fill inside bounding box with transparency
                    overlay = annotated_frame.copy()
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), -1)
                    annotated_frame = cv2.addWeighted(overlay, 0.3, annotated_frame, 0.7, 0)

                    # Click = start tracking
                    if click_flag:
                        tracker = cv2.TrackerCSRT.create()
                        tracker.init(frame, (x1, y1, x2 - x1, y2 - y1))
                        tracked_class = int(classes[i])
                        tracked_bbox = (x1, y1, x2 - x1, y2 - y1)
                        tracking = True
                        detection_history = []  # Reset history
                        detection_times.clear()  # Clear detection times from selection phase
                        click_flag = False
                        print(f"Started tracking object {i}, class {tracked_class}")
                        break
    else:
        # --- TRACKING MODE ---
        # Skip frames to speed up tracking phase
        should_run_tracker = (frame_count % (TrackingConfig.TRACKER_FRAME_SKIP + 1)) == 0
        
        if should_run_tracker:
            if COLLECT_STATS:
                tracker_start = time.time()
            success, bbox = tracker.update(frame)
            if COLLECT_STATS:
                tracker_time = (time.time() - tracker_start) * 1000  # Convert to ms
                tracker_times.append(tracker_time)
            last_tracker_bbox = (success, bbox)
        else:
            # Reuse last tracker result on skipped frames
            success, bbox = last_tracker_bbox if last_tracker_bbox else (False, None)
        
        if success and bbox is not None:
            if annotated_frame is None:
                annotated_frame = frame.copy()
            
            x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            tracked_bbox = (x, y, w, h)

            # Draw gradient fill with transparency
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 255), -1)
            annotated_frame = cv2.addWeighted(overlay, 0.3, annotated_frame, 0.7, 0)
            
            # Draw outline
            cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (0, 200, 200), 2)
            cv2.putText(annotated_frame, f"Tracking class {tracked_class}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            # --- PERIODIC RE-DETECTION (Hybrid Approach) - Only in drift_detection mode ---
            if TrackingConfig.TRACKING_MODE == "drift_detection" and frame_count % TrackingConfig.REDETECT_INTERVAL == 0:
                # Get tracker confidence
                if COLLECT_STATS:
                    redetect_start = time.time()
                tracker_confidence = get_tracker_confidence(tracker, frame, tracked_bbox)

                results = model.predict(frame, conf=TrackingConfig.CONFIDENCE_THRESHOLD, iou=TrackingConfig.MODEL_IOU, verbose=False)
                if COLLECT_STATS:
                    redetect_time = (time.time() - redetect_start) * 1000  # Convert to ms
                    redetection_times.append(redetect_time)

                if results[0].boxes is not None and len(results[0].boxes) > 0:
                    boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)
                    classes = results[0].boxes.cls.cpu().numpy()

                    best_iou = 0
                    best_box = None

                    # Find detection that best matches tracked box
                    for i, det_box in enumerate(boxes):
                        if int(classes[i]) != tracked_class:
                            continue

                        x1, y1, x2, y2 = det_box
                        det_bbox = (x1, y1, x2 - x1, y2 - y1)

                        iou = calculate_iou(tracked_bbox, det_bbox)
                        if iou > best_iou:
                            best_iou = iou
                            best_box = det_bbox

                    # Only consider realigning if tracker confidence is low
                    if tracker_confidence < 0.5:
                        # Store this detection for history
                        if best_box is not None:
                            detection_history.append(best_box)
                        else:
                            detection_history.append(None)

                        # Keep only recent history
                        if len(detection_history) > TrackingConfig.DETECTION_HISTORY_SIZE:
                            detection_history.pop(0)

                        # Check if we have consistent detections
                        if len(detection_history) >= TrackingConfig.DETECTION_HISTORY_SIZE:
                            # Count how many non-None detections we have
                            valid_detections = [d for d in detection_history if d is not None]

                            if len(valid_detections) >= TrackingConfig.DETECTION_HISTORY_SIZE - 1:
                                # Average the recent detections for stability
                                avg_x = np.mean([d[0] for d in valid_detections])
                                avg_y = np.mean([d[1] for d in valid_detections])
                                avg_w = np.mean([d[2] for d in valid_detections])
                                avg_h = np.mean([d[3] for d in valid_detections])
                                smoothed_bbox = (int(avg_x), int(avg_y), int(avg_w), int(avg_h))

                                # Check IoU with current tracker position
                                final_iou = calculate_iou(tracked_bbox, smoothed_bbox)

                                if final_iou > TrackingConfig.IOU_THRESHOLD:
                                    tracker = cv2.legacy.TrackerCSRT_create()
                                    tracker.init(frame, smoothed_bbox)
                                    tracked_bbox = smoothed_bbox
                                    cv2.putText(annotated_frame, "REALIGNED (consensus)", (100, 110),
                                               cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                                    print(f"Realigned with consensus IoU: {final_iou:.2f}")
                                    detection_history = []  # Reset history after realignment
                                elif final_iou > 0:
                                    cv2.putText(annotated_frame, f"DRIFT DETECTED (IoU: {final_iou:.2f})",
                                               (100, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 165, 255), 2)
                    else:
                        # Tracker confidence is high, clear history to avoid interference
                        detection_history = []
                        cv2.putText(annotated_frame, f"Tracker confident (conf: {tracker_confidence:.2f})",
                                   (100, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 150, 50), 2)
        else:
            print("Lost tracking, resuming detection")
            tracking = False
            tracker = None
            tracked_class = None
            tracked_bbox = None
            detection_history = []
            detection_times.clear()  # Clear old detection times when resuming detection

    # Display frame (only show if we created annotated_frame, else show original)
    if annotated_frame is None:
        cv2.imshow("Interactive Segmentation", frame)
    else:
        cv2.imshow("Interactive Segmentation", annotated_frame)
    
    # Record frame time and print stats every 100 frames
    if COLLECT_STATS:
        frame_time = (time.time() - frame_start_time) * 1000  # Convert to ms
        frame_times.append(frame_time)
    
    if COLLECT_STATS and frame_count % 100 == 0:
        print(f"[Frame {frame_count}] ", end="")
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