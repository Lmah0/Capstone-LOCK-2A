import cv2
import numpy as np
from ultralytics import YOLO
import os

# Tuning Parameters
REDETECT_INTERVAL = 10       # Run YOLO every N frames during tracking
IOU_THRESHOLD = 0.5          # Required overlap to accept realignment
CONFIDENCE_THRESHOLD = 0.1   # YOLO detection threshold
YOLO_NMS_THRESHOLD = 0.7     # NMS IOU threshold for YOLO
TRACKER_CONFIDENCE_THRESHOLD = 0.5  # Minimum tracker confidence to skip correction
MIN_DETECTION_IOU = 0.3      # Minimum IoU to consider a detection as a match
HISTORY_SIZE = 3             # Frames of consistency before realignment

class TrackingEngine:
    def __init__(self, model_path):
        if not os.path.exists(model_path):
            print(f"Warning: Model not found at {model_path}")
            print("YOLO will attempt to download the model...")
        else:
            print(f"Loading model from: {model_path}")

        self.model = YOLO(model_path)
        self.tracker = cv2.TrackerMIL_create()
        
        # State
        self.is_tracking = False
        self.tracked_bbox = None
        self.tracked_class = None
        self.detection_history = []
        self.status_message = ""

    def detect_objects(self, frame):
        """Run YOLO detection"""
        if frame is None or frame.size == 0:
            return None
        results = self.model.predict(frame, conf=CONFIDENCE_THRESHOLD, iou=YOLO_NMS_THRESHOLD, verbose=False)
        return results[0]

    def start_tracking(self, frame, bbox, class_id):
        """Initialize CSRT Tracker"""
        self.tracker.init(frame, bbox)
        self.tracked_bbox = bbox
        self.tracked_class = class_id
        self.is_tracking = True
        self.detection_history = []
        print(f"Engine: Started tracking Class {class_id}")

    def update(self, frame, frame_count):
        """Main update loop for tracking mode"""
        if not self.is_tracking:
            return False, None

        # 1. Update CSRT
        success, bbox = self.tracker.update(frame)
        self.status_message = ""

        if success:
            self.tracked_bbox = bbox
            
            # 2. Hybrid Check (Periodically re-run YOLO to correct drift)
            if frame_count % REDETECT_INTERVAL == 0:
                self._perform_drift_correction(frame, bbox)
            
            return True, self.tracked_bbox
        else:
            self.is_tracking = False
            return False, None

    def _perform_drift_correction(self, frame, tracked_bbox):
        """Internal logic to realign tracker if it drifts"""
        if frame is None or frame.size == 0:
            return
            
        tracker_conf = self.get_tracker_confidence(self.tracker, frame, tracked_bbox)
        
        # Only perform correction if tracker confidence is low
        if tracker_conf >= TRACKER_CONFIDENCE_THRESHOLD:
            # Tracker is confident, clear history and skip correction
            self.detection_history = []
            self.status_message = f"Tracker confident (conf: {tracker_conf:.2f})"
            return

        # Run YOLO
        results = self.detect_objects(frame)
        if results is None or results.boxes is None or len(results.boxes) == 0:
            self.detection_history.append(None)
            if len(self.detection_history) > HISTORY_SIZE:
                self.detection_history.pop(0)
            return

        boxes = results.boxes.xyxy.cpu().numpy()
        classes = results.boxes.cls.cpu().numpy()
        
        # Find best matching box
        best_box = None
        best_iou = 0

        for i, box in enumerate(boxes):
            if int(classes[i]) != self.tracked_class:
                continue
            
            # Convert xyxy -> xywh
            x1, y1, x2, y2 = box.astype(int)
            det_bbox = (x1, y1, x2 - x1, y2 - y1)
            
            iou = self.calculate_iou(self.tracked_bbox, det_bbox)
            if iou > best_iou and iou >= MIN_DETECTION_IOU:
                best_iou = iou
                best_box = det_bbox

        # Add to history (even if None)
        if best_box is not None:
            self.detection_history.append(best_box)
        else:
            self.detection_history.append(None)
        
        # Keep only recent history
        if len(self.detection_history) > HISTORY_SIZE:
            self.detection_history.pop(0)

        # Consensus Logic - check if we have enough consistent detections
        if len(self.detection_history) >= HISTORY_SIZE:
            # Count valid (non-None) detections
            valid_detections = [d for d in self.detection_history if d is not None]
            
            # Require at least HISTORY_SIZE - 1 valid detections (allow 1 miss)
            if len(valid_detections) >= HISTORY_SIZE - 1:
                # Calculate average box from valid detections
                avg_x = np.mean([d[0] for d in valid_detections])
                avg_y = np.mean([d[1] for d in valid_detections])
                avg_w = np.mean([d[2] for d in valid_detections])
                avg_h = np.mean([d[3] for d in valid_detections])
                smoothed_bbox = (int(avg_x), int(avg_y), int(avg_w), int(avg_h))

                final_iou = self.calculate_iou(self.tracked_bbox, smoothed_bbox)

                if final_iou > IOU_THRESHOLD:
                    # Re-initialize tracker at new position (reuse existing tracker instance)
                    self.tracker.init(frame, smoothed_bbox)
                    self.tracked_bbox = smoothed_bbox
                    self.detection_history = []
                    self.status_message = "REALIGNED (consensus)"
                    print(f"Realigned with consensus IoU: {final_iou:.2f}")
                elif final_iou > 0:
                    self.status_message = f"DRIFT DETECTED (IoU: {final_iou:.2f})"

    # --- Helper Methods ---
    @staticmethod
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

    @staticmethod
    def get_tracker_confidence(tracker, frame, bbox):
        """Estimate tracker confidence by checking response map"""
        try:
            # CSRT has a response map we can query
            response = tracker.getTrackingResponse(frame)
            if response is not None:
                # Get max value from response map as confidence estimate
                confidence = float(np.max(response))
                return confidence
            return TRACKER_CONFIDENCE_THRESHOLD  # Default to threshold if we can't get response
        except Exception as e:
            # Fallback if method doesn't exist or fails
            print(f"Warning: Could not get tracker confidence: {e}")
            return TRACKER_CONFIDENCE_THRESHOLD