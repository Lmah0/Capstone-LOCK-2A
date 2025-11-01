import cv2
import numpy as np
from ultralytics import YOLO
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Use relative paths from the script directory
VIDEO_PATH = os.path.join(script_dir, "video.mp4")
# VIDEO_PATH = '/Users/lionelhasan/Downloads/Trimmed Angle.mp4'
SEG_MODEL_PATH = os.path.join(script_dir, "yolo11n-seg.pt")


# Tracking parameters
REDETECT_INTERVAL = 10  # Re-run detector every 10 frames
IOU_THRESHOLD = 0.5     # Higher threshold - more conservative realignment
DETECTION_HISTORY_SIZE = 3  # Require consistency across N frames
CONFIDENCE_THRESHOLD = 0.1  # Lower detection confidence to catch more objects

# Load YOLO segmentation model
model = YOLO(SEG_MODEL_PATH)
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

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    annotated_frame = frame.copy()

    if not tracking:
        # --- RUN DETECTION ---
        results = model.predict(frame, conf=CONFIDENCE_THRESHOLD, iou=0.7, verbose=False)
        current_boxes = []

        if results[0].masks is not None:
            masks = results[0].masks.data
            boxes = results[0].boxes.xyxy.cpu().numpy()
            classes = results[0].boxes.cls.cpu().numpy()

            for i, mask in enumerate(masks):
                mask_img = (mask.cpu().numpy() * 255).astype(np.uint8)
                mask_resized = cv2.resize(mask_img, (frame.shape[1], frame.shape[0]))
                x1, y1, x2, y2 = boxes[i].astype(int)
                current_boxes.append((x1, y1, x2, y2, classes[i]))

                # Hover effect: outline + smooth gradient
                if x1 <= cursor_x <= x2 and y1 <= cursor_y <= y2:
                    # Smooth outline
                    contours, _ = cv2.findContours(mask_resized, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    for cnt in contours:
                        epsilon = 0.01 * cv2.arcLength(cnt, True)
                        approx = cv2.approxPolyDP(cnt, epsilon, True)
                        cv2.drawContours(annotated_frame, [approx], -1, (0, 200, 0), 2)

                    # Gradient fill
                    overlay = annotated_frame.copy()
                    overlay[mask_resized > 0] = (0, 255, 0)
                    annotated_frame = cv2.addWeighted(overlay, 0.4, annotated_frame, 0.6, 0)

                    # Click = start tracking
                    if click_flag:
                        tracker = cv2.legacy.TrackerCSRT_create()
                        tracker.init(frame, (x1, y1, x2 - x1, y2 - y1))
                        tracked_class = int(classes[i])
                        tracked_bbox = (x1, y1, x2 - x1, y2 - y1)
                        tracking = True
                        detection_history = []  # Reset history
                        click_flag = False
                        print(f"Started tracking object {i}, class {tracked_class}")
                        break
    else:
        # --- TRACKING MODE ---
        success, bbox = tracker.update(frame)
        if success:
            x, y, w, h = [int(v) for v in bbox]
            tracked_bbox = (x, y, w, h)

            annotated_frame = draw_gradient_box(annotated_frame, tracked_bbox, color=(0, 255, 255))

            # Draw outline
            cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (0, 200, 200), 2)
            cv2.putText(annotated_frame, f"Tracking class {tracked_class}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            print(f"tracking {tracked_class}")

            # --- PERIODIC RE-DETECTION (Hybrid Approach) ---
            if frame_count % REDETECT_INTERVAL == 0:
                # Get tracker confidence
                tracker_confidence = get_tracker_confidence(tracker, frame, tracked_bbox)
                
                results = model.predict(frame, conf=CONFIDENCE_THRESHOLD, iou=0.7, verbose=False)
                
                if results[0].boxes is not None and len(results[0].boxes) > 0:
                    boxes = results[0].boxes.xyxy.cpu().numpy()
                    classes = results[0].boxes.cls.cpu().numpy()
                    
                    best_iou = 0
                    best_box = None
                    
                    # Find detection that best matches tracked box
                    for i, det_box in enumerate(boxes):
                        if int(classes[i]) != tracked_class:
                            continue
                        
                        x1, y1, x2, y2 = det_box.astype(int)
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
                        if len(detection_history) > DETECTION_HISTORY_SIZE:
                            detection_history.pop(0)
                        
                        # Check if we have consistent detections
                        if len(detection_history) >= DETECTION_HISTORY_SIZE:
                            # Count how many non-None detections we have
                            valid_detections = [d for d in detection_history if d is not None]
                            
                            if len(valid_detections) >= DETECTION_HISTORY_SIZE - 1:
                                # Average the recent detections for stability
                                avg_x = np.mean([d[0] for d in valid_detections])
                                avg_y = np.mean([d[1] for d in valid_detections])
                                avg_w = np.mean([d[2] for d in valid_detections])
                                avg_h = np.mean([d[3] for d in valid_detections])
                                smoothed_bbox = (int(avg_x), int(avg_y), int(avg_w), int(avg_h))
                                
                                # Check IoU with current tracker position
                                final_iou = calculate_iou(tracked_bbox, smoothed_bbox)
                                
                                if final_iou > IOU_THRESHOLD:
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

    cv2.imshow("Interactive Segmentation", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()