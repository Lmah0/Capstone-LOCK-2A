import cv2
import numpy as np
import time
from ultralytics import YOLO
import os

class TrackingConfig:
    """Centralized configuration for all tracking and detection parameters"""
    
    # --- Frame Skipping ---
    DETECTION_FRAME_SKIP = 2  # Skip N frames during detection phase (0=every frame, 1=every 2nd, 2=every 3rd)
    TRACKER_FRAME_SKIP = 1    # Skip N frames during tracking phase (0=every frame, 1=every 2nd)
    
    # --- Detection Parameters ---
    CONFIDENCE_THRESHOLD = 0.1    # YOLO detection confidence threshold
    MODEL_IOU = 0.5               # NMS IOU threshold for YOLO

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

        # Update CSRT tracker
        success, bbox = self.tracker.update(frame)

        if success:
            self.tracked_bbox = bbox
            return True, self.tracked_bbox
        else:
            self.is_tracking = False
            return False, None






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
        
        # Fine-grained profiling timings (in ms)
        self.profile_inference_ms = 0.0      # YOLO model inference time
        self.profile_boxes_ms = 0.0          # Box extraction and processing time
        self.profile_drawing_ms = 0.0        # Drawing/visualization time
        self.detection_ran_this_frame = False  # Track if detection actually ran this frame
        
        # Detailed inference breakdown
        self.profile_frame_prep_ms = 0.0     # Frame preparation before model
        self.profile_model_predict_ms = 0.0  # Actual model.predict() call
        self.profile_results_process_ms = 0.0  # Processing results after model
        
        # Input profiling
        self.profile_frame_shape = None
        self.profile_frame_dtype = None
        self.profile_frame_device = "unknown"
        self.profile_model_device = "unknown"
    
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
    output_frame = None
    mode_changed = False
    
    # Determine if we should run detection this frame
    should_detect = (state.frame_count % (TrackingConfig.DETECTION_FRAME_SKIP + 1)) == 0
    
    # Reset timings for this frame
    state.profile_inference_ms = 0.0
    state.profile_boxes_ms = 0.0
    state.profile_drawing_ms = 0.0
    state.detection_ran_this_frame = False
    
    if should_detect:
        state.detection_ran_this_frame = True
        
        # Profile frame inputs
        state.profile_frame_shape = frame.shape
        state.profile_frame_dtype = str(frame.dtype)
        if hasattr(frame, 'device'):
            state.profile_frame_device = str(frame.device)
        else:
            state.profile_frame_device = "CPU (numpy)"
        
        # Profile model device
        try:
            if hasattr(model, 'device'):
                state.profile_model_device = str(model.device)
            else:
                # Check the underlying model's device
                for param in model.model.parameters():
                    state.profile_model_device = str(param.device)
                    break
        except:
            state.profile_model_device = "unknown"
        
        # Time frame prep
        t_frame_prep = time.time()
        # (frame is already loaded, just a timestamp marker)
        state.profile_frame_prep_ms = (time.time() - t_frame_prep) * 1000
        
        # Time the actual model inference
        t_model_start = time.time()
        results = model.predict(frame, conf=TrackingConfig.CONFIDENCE_THRESHOLD,
                               iou=TrackingConfig.MODEL_IOU, verbose=False)
        state.profile_model_predict_ms = (time.time() - t_model_start) * 1000
        
        # Time result processing
        t_results_start = time.time()
        state.last_detection_results = results
        state.profile_results_process_ms = (time.time() - t_results_start) * 1000
        
        state.profile_inference_ms = state.profile_frame_prep_ms + state.profile_model_predict_ms + state.profile_results_process_ms
    else:
        results = state.last_detection_results
    
    # Process bounding boxes
    if results is not None and results[0].boxes is not None and len(results[0].boxes) > 0:
        t_boxes_start = time.time()
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)
        classes = results[0].boxes.cls.cpu().numpy()
        state.profile_boxes_ms = (time.time() - t_boxes_start) * 1000
        
        cursor_x, cursor_y = cursor_pos if cursor_pos else (0, 0)
        
        # Draw all detections
        t_drawing_start = time.time()
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
        state.profile_drawing_ms = (time.time() - t_drawing_start) * 1000
    
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