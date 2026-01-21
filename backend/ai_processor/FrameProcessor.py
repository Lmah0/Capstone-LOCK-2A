"""
FrameProcessor: Core orchestration layer for detection/tracking state machine.
Abstracts away UI and I/O details, providing a clean interface for different frontends.
"""

import numpy as np
from AIEngine import TrackingEngine, TrackingConfig


class FrameProcessor:
    """
    High-level orchestration of detection/tracking workflow.
    State machine manages: detection_mode -> tracking_mode -> detection_mode
    """
    
    def __init__(self, model_path):
        """
        Args:
            model_path: Path to YOLO model
        """
        self.engine = TrackingEngine(model_path)
        
        # State tracking
        self.frame_count = 0
        self.last_detection_results = None
        self.last_tracker_result = None
        
        # Statistics
        self.stats = {
            'is_tracking': False,
            'tracked_class': None,
            'status_message': ''
        }
    
    def process_frame(self, frame, cursor_pos=None, click_pos=None):
        """
        Main processing loop. Returns annotated frame data and state info.
        
        Args:
            frame: Input video frame (numpy array)
            cursor_pos: (x, y) tuple for hover effects (detection mode only)
            click_pos: (x, y) tuple for object selection (detection mode only)
        
        Returns:
            dict with keys:
                - 'frame': Annotated frame
                - 'mode': 'detection' or 'tracking'
                - 'bbox': Current bbox if tracking, else None
                - 'detections': List of detection boxes if in detection mode
                - 'status': Status message
                - 'hovered_box': Box under cursor (detection mode)
                - 'hovered_index': Index of hovered detection
        """
        self.frame_count += 1
        cursor_pos = cursor_pos or (0, 0)
        
        result = {
            'frame': frame,
            'mode': 'detection' if not self.engine.is_tracking else 'tracking',
            'bbox': None,
            'detections': [],
            'status': self.engine.status_message,
            'hovered_box': None,
            'hovered_index': None,
            'clicked_bbox': None,
            'clicked_class': None,
        }
        
        # --- TRACKING MODE ---
        if self.engine.is_tracking:
            result.update(self._handle_tracking_mode(frame))
        # --- DETECTION MODE ---
        else:
            result.update(self._handle_detection_mode(frame, cursor_pos, click_pos))
        
        # Update stats
        self.stats['is_tracking'] = self.engine.is_tracking
        self.stats['tracked_class'] = self.engine.tracked_class
        self.stats['status_message'] = self.engine.status_message
        
        return result
    
    def _handle_detection_mode(self, frame, cursor_pos, click_pos):
        """Handle detection mode: run YOLO, check for clicks to start tracking"""
        result = {
            'detections': [],
            'hovered_box': None,
            'hovered_index': None,
            'clicked_bbox': None,
            'clicked_class': None,
        }
        
        # Skip frames to improve performance
        should_detect = (self.frame_count % (TrackingConfig.DETECTION_FRAME_SKIP + 1)) == 0
        
        if should_detect:
            self.last_detection_results = self.engine.detect_objects(frame)
        else:
            # Reuse last detection on skipped frames
            if self.last_detection_results is None:
                return result
        
        detection_results = self.last_detection_results
        if detection_results is None or detection_results.boxes is None:
            return result
        
        boxes = detection_results.boxes.xyxy.cpu().numpy().astype(np.int32)
        classes = detection_results.boxes.cls.cpu().numpy()
        
        cursor_x, cursor_y = cursor_pos
        
        # Check each detection for hover/click
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            det_dict = {
                'box': (x1, y1, x2 - x1, y2 - y1),
                'class': int(classes[i]),
                'index': i,
                'hovered': False
            }
            
            # Check if cursor is over this detection
            if x1 <= cursor_x <= x2 and y1 <= cursor_y <= y2:
                det_dict['hovered'] = True
                result['hovered_box'] = det_dict['box']
                result['hovered_index'] = i
                
                # Check for click
                if click_pos is not None:
                    click_x, click_y = click_pos
                    if abs(click_x - cursor_x) < 10 and abs(click_y - cursor_y) < 10:
                        # User clicked on hovered object
                        result['clicked_bbox'] = det_dict['box']
                        result['clicked_class'] = det_dict['class']
                        self.engine.start_tracking(frame, det_dict['box'], det_dict['class'])
                        return result
            
            result['detections'].append(det_dict)
        
        # Fallback: click without hovering
        if click_pos is not None and result['clicked_bbox'] is None:
            click_x, click_y = click_pos
            for det_dict in result['detections']:
                x1, y1, w, h = det_dict['box']
                x2, y2 = x1 + w, y1 + h
                if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                    result['clicked_bbox'] = det_dict['box']
                    result['clicked_class'] = det_dict['class']
                    self.engine.start_tracking(frame, det_dict['box'], det_dict['class'])
                    break
        
        return result
    
    def _handle_tracking_mode(self, frame):
        """Handle tracking mode: update tracker, optionally perform drift correction"""
        result = {'bbox': None}
        
        # Skip frames if configured
        should_track = (self.frame_count % (TrackingConfig.TRACKER_FRAME_SKIP + 1)) == 0
        
        if should_track:
            success, bbox = self.engine.update(frame, self.frame_count)
            self.last_tracker_result = (success, bbox)
        else:
            # Reuse last tracker result on skipped frames
            success, bbox = self.last_tracker_result if self.last_tracker_result else (False, None)
        
        if success and bbox is not None:
            result['bbox'] = bbox
            result['status'] = self.engine.status_message
        else:
            # Lost tracking, return to detection mode
            self.engine.is_tracking = False
            result['status'] = "Lost tracking, resuming detection"
        
        return result
    
    def stop_tracking(self):
        """Manually stop tracking and return to detection mode"""
        self.engine.is_tracking = False
        self.engine.tracked_bbox = None
        self.engine.tracked_class = None
        self.engine.detection_history = []
        print("Stopped tracking, resuming detection")
    
    def reset(self):
        """Reset processor state"""
        self.frame_count = 0
        self.detection_frame_skip_counter = 0
        self.tracker_frame_skip_counter = 0
        self.last_detection_results = None
        self.last_tracker_result = None
        self.stop_tracking()
