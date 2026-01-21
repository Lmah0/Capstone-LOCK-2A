import cv2
import numpy as np
from ultralytics import YOLO
import os

class TrackingConfig:
    """Centralized configuration for all tracking and detection parameters"""
    
    # --- Tracking Mode ---
    TRACKING_MODE = "tracking_only"  # "tracking_only" or "drift_detection"
    
    # --- Frame Skipping ---
    DETECTION_FRAME_SKIP = 2  # Skip N frames during detection phase (0=every frame, 1=every 2nd, 2=every 3rd)
    TRACKER_FRAME_SKIP = 1    # Skip N frames during tracking phase (0=every frame, 1=every 2nd)
    
    # --- Detection Parameters ---
    CONFIDENCE_THRESHOLD = 0.1    # YOLO detection confidence threshold
    MODEL_IOU = 0.5               # NMS IOU threshold for YOLO
    
    # --- Tracking Parameters ---
    REDETECT_INTERVAL = 10        # Re-run YOLO every N frames (only in drift_detection mode)
    IOU_THRESHOLD = 0.5           # Required overlap to accept realignment
    DETECTION_HISTORY_SIZE = 3    # Frames of consistency before realignment
    TRACKER_CONFIDENCE_THRESHOLD = 0.5  # Minimum tracker confidence to skip correction
    MIN_DETECTION_IOU = 0.3       # Minimum IoU to consider a detection as a match

class TrackingEngine:
    def __init__(self, model_path):
        if not os.path.exists(model_path):
            print(f"Warning: Model not found at {model_path}")
            print("YOLO will attempt to download the model...")
        else:
            print(f"Loading model from: {model_path}")

        # Public attributes for high-performance direct access (hot path)
        self.model = YOLO(model_path)
        self.tracker = None  # Created on-demand in start_tracking()
        
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
        results = self.model.predict(frame, conf=TrackingConfig.CONFIDENCE_THRESHOLD, 
                                   iou=TrackingConfig.MODEL_IOU, verbose=False)
        return results[0]

    def start_tracking(self, frame, bbox, class_id):
        """Initialize CSRT Tracker"""
        # Create new tracker for each tracking session (can't reuse after failure)
        self.tracker = cv2.TrackerCSRT.create()
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
            if TrackingConfig.TRACKING_MODE == "drift_detection" and frame_count % TrackingConfig.REDETECT_INTERVAL == 0:
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
        if tracker_conf >= TrackingConfig.TRACKER_CONFIDENCE_THRESHOLD:
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
            if iou > best_iou and iou >= TrackingConfig.MIN_DETECTION_IOU:
                best_iou = iou
                best_box = det_bbox

        # Add to history (even if None)
        if best_box is not None:
            self.detection_history.append(best_box)
        else:
            self.detection_history.append(None)
        
        # Keep only recent history
        if len(self.detection_history) > TrackingConfig.DETECTION_HISTORY_SIZE:
            self.detection_history.pop(0)

        # Consensus Logic - check if we have enough consistent detections
        if len(self.detection_history) >= TrackingConfig.DETECTION_HISTORY_SIZE:
            # Count valid (non-None) detections
            valid_detections = [d for d in self.detection_history if d is not None]
            
            # Require at least DETECTION_HISTORY_SIZE - 1 valid detections (allow 1 miss)
            if len(valid_detections) >= TrackingConfig.DETECTION_HISTORY_SIZE - 1:
                # Calculate average box from valid detections
                avg_x = np.mean([d[0] for d in valid_detections])
                avg_y = np.mean([d[1] for d in valid_detections])
                avg_w = np.mean([d[2] for d in valid_detections])
                avg_h = np.mean([d[3] for d in valid_detections])
                smoothed_bbox = (int(avg_x), int(avg_y), int(avg_w), int(avg_h))

                final_iou = self.calculate_iou(self.tracked_bbox, smoothed_bbox)

                if final_iou > TrackingConfig.IOU_THRESHOLD:
                    # Re-initialize tracker at new position (create new tracker instance)
                    self.tracker = cv2.legacy.TrackerCSRT_create()
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
            return TrackingConfig.TRACKER_CONFIDENCE_THRESHOLD  # Default to threshold if we can't get response
        except Exception as e:
            # Fallback if method doesn't exist or fails
            return TrackingConfig.TRACKER_CONFIDENCE_THRESHOLD


# ============================================================================
# SHARED RENDERING AND INTERACTION LOGIC
# ============================================================================

class ProcessingState:
    """Manages state for detection/tracking processing"""
    def __init__(self):
        self.tracking = False
        self.tracker = None
        self.tracked_class = None
        self.tracked_bbox = None
        self.frame_count = 0
        self.last_detection_results = None
        self.last_tracker_bbox = None
        self._last_infer_ms = 0  # Track inference time
    
    def reset_tracking(self):
        """Reset tracking state"""
        self.tracking = False
        self.tracker = None
        self.tracked_class = None
        self.tracked_bbox = None
        self.last_tracker_bbox = None
    
    def start_tracking(self, frame, bbox, class_id):
        """Initialize tracking from a detection"""
        self.tracker = cv2.TrackerCSRT.create()
        self.tracker.init(frame, bbox)
        self.tracked_class = class_id
        self.tracked_bbox = bbox
        self.tracking = True
        print(f"Started tracking object, class {class_id}")
    
    def increment_frame(self):
        """Increment frame counter"""
        self.frame_count += 1


def process_detection_mode(frame, model, state, cursor_pos, click_pos):
    """
    Process frame in detection mode.
    
    Args:
        frame: Input frame
        model: YOLO model instance
        state: ProcessingState object
        cursor_pos: Tuple (x, y) of cursor position or None
        click_pos: Tuple (x, y) of click position or None
    
    Returns:
        Tuple (output_frame, detection_results, mode_changed)
        - output_frame: Annotated frame or None if unchanged
        - detection_results: Latest detection results
        - mode_changed: True if mode switched to tracking
    """
    import time
    output_frame = None
    mode_changed = False
    
    # Determine if we should run detection this frame
    should_detect = (state.frame_count % (TrackingConfig.DETECTION_FRAME_SKIP + 1)) == 0
    
    if should_detect:
        t_infer_start = time.time()
        results = model.predict(frame, conf=TrackingConfig.CONFIDENCE_THRESHOLD,
                               iou=TrackingConfig.MODEL_IOU, verbose=False)
        t_infer_end = time.time()
        state._last_infer_ms = (t_infer_end - t_infer_start) * 1000
        state.last_detection_results = results
    else:
        state._last_infer_ms = 0
        results = state.last_detection_results
    
    # Process bounding boxes
    if results is not None and results[0].boxes is not None and len(results[0].boxes) > 0:
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)
        classes = results[0].boxes.cls.cpu().numpy()
        
        cursor_x, cursor_y = cursor_pos if cursor_pos else (0, 0)
        
        # Draw all detections
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            
            # Hover effect
            if x1 <= cursor_x <= x2 and y1 <= cursor_y <= y2:
                if output_frame is None:
                    output_frame = frame.copy()
                
                # Draw outline + fill for hovered box
                cv2.rectangle(output_frame, (x1, y1), (x2, y2), (0, 200, 0), 2)
                overlay = output_frame.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), -1)
                output_frame = cv2.addWeighted(overlay, 0.3, output_frame, 0.7, 0)
                cv2.putText(output_frame, f"Class {int(classes[i])}", (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Click = start tracking
                if click_pos is not None:
                    state.start_tracking(frame, (x1, y1, x2 - x1, y2 - y1), int(classes[i]))
                    mode_changed = True
                    break
    
    return output_frame, results, mode_changed


def process_tracking_mode(frame, state):
    """
    Process frame in tracking mode.
    
    Args:
        frame: Input frame
        state: ProcessingState object
    
    Returns:
        Tuple (output_frame, tracking_succeeded, mode_changed)
        - output_frame: Annotated frame or None if tracking lost
        - tracking_succeeded: True if tracking succeeded
        - mode_changed: True if mode switched back to detection
    """
    output_frame = None
    mode_changed = False
    
    # Determine if we should update tracker this frame
    should_track = (state.frame_count % (TrackingConfig.TRACKER_FRAME_SKIP + 1)) == 0
    
    if should_track:
        success, bbox = state.tracker.update(frame)
        state.last_tracker_bbox = (success, bbox)
    else:
        success, bbox = state.last_tracker_bbox if state.last_tracker_bbox else (False, None)
    
    if success and bbox is not None:
        x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        state.tracked_bbox = (x, y, w, h)
        
        output_frame = frame.copy()
        
        # Draw gradient fill with transparency
        overlay = output_frame.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 255), -1)
        output_frame = cv2.addWeighted(overlay, 0.3, output_frame, 0.7, 0)
        
        # Draw outline
        cv2.rectangle(output_frame, (x, y), (x + w, y + h), (0, 200, 200), 2)
        cv2.putText(output_frame, f"Tracking class {state.tracked_class}", (x, y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        return output_frame, True, False
    else:
        print("Lost tracking, resuming detection")
        state.reset_tracking()
        return None, False, True