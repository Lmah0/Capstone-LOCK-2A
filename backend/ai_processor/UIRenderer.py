"""
UIRenderer: Centralized visualization utilities for drawing boxes, text, and overlays.
Decoupled from business logic, can be used by any frontend (cv2, web, etc.)
"""

import cv2
import numpy as np


class UIRenderer:
    """Handles all visualization/drawing operations"""
    
    @staticmethod
    def draw_detection_boxes(frame, detections, hovered_index=None, alpha=0.3):
        """
        Draw detection boxes with hover effects.
        Only draws boxes for hovered detections.
        
        Args:
            frame: Input frame
            detections: List of detection dicts with 'box', 'class', 'hovered' keys
            hovered_index: Index of hovered detection (for highlighting)
            alpha: Transparency for filled overlay
        
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        for i, det in enumerate(detections):
            # Only draw boxes for hovered detections
            if not det['hovered']:
                continue
            
            x, y, w, h = det['box']
            x2, y2 = x + w, y + h
            
            # Hovered: bright green fill + outline
            color = (0, 255, 0)
            cv2.rectangle(annotated, (x, y), (x2, y2), color, 2)
            
            # Gradient fill
            overlay = annotated.copy()
            cv2.rectangle(overlay, (x, y), (x2, y2), color, -1)
            annotated = cv2.addWeighted(overlay, alpha, annotated, 1 - alpha, 0)
            
            # Class label
            cv2.putText(annotated, f"Class {det['class']}", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return annotated
    
    @staticmethod
    def draw_tracking_box(frame, bbox, class_id, status_message="", alpha=0.3):
        """
        Draw tracking box with status info.
        
        Args:
            frame: Input frame
            bbox: Bounding box as (x, y, w, h)
            class_id: Class identifier
            status_message: Optional status text
            alpha: Transparency for filled overlay
        
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        
        color = (0, 255, 255)  # Cyan
        
        # Draw filled box with transparency
        overlay = annotated.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
        annotated = cv2.addWeighted(overlay, alpha, annotated, 1 - alpha, 0)
        
        # Draw outline
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
        
        # Label with class
        cv2.putText(annotated, f"Tracking Class {class_id}", (x, y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Status message
        if status_message:
            cv2.putText(annotated, status_message, (x + 10, y + h + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 200), 2)
        
        return annotated
    
    @staticmethod
    def draw_status_bar(frame, text, position=(10, 30), font_scale=0.7, 
                       color=(255, 255, 255), thickness=2):
        """
        Draw status text on frame.
        
        Args:
            frame: Input frame
            text: Text to display
            position: (x, y) position
            font_scale: Font size
            color: BGR color tuple
            thickness: Text thickness
        
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        cv2.putText(annotated, text, position,
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
        return annotated
    
    @staticmethod
    def draw_performance_stats(frame, stats_dict, position=None):
        """
        Draw performance statistics on frame.
        
        Args:
            frame: Input frame
            stats_dict: Dict with 'fps', 'mode', 'tracked_class' keys
            position: (x, y) position for bottom-left corner (default: top-left)
        
        Returns:
            Annotated frame
        """
        if position is None:
            position = (10, 30)
        
        annotated = frame.copy()
        y = position[1]
        
        fps = stats_dict.get('fps', 0)
        mode = stats_dict.get('mode', 'N/A')
        
        text = f"FPS: {fps:.1f} | Mode: {mode}"
        cv2.putText(annotated, text, (position[0], y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 1)
        
        return annotated


class Cv2Window:
    """Wrapper for cv2 window with mouse event handling"""
    
    def __init__(self, window_name="Interactive Segmentation"):
        self.window_name = window_name
        self.cursor_x = 0
        self.cursor_y = 0
        self.click_pos = None
        
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, self._mouse_callback)
    
    def _mouse_callback(self, event, x, y, flags, param):
        """Internal callback for mouse events"""
        self.cursor_x = x
        self.cursor_y = y
        if event == cv2.EVENT_LBUTTONDOWN:
            self.click_pos = (x, y)
    
    def get_cursor_pos(self):
        """Returns current cursor position"""
        return (self.cursor_x, self.cursor_y)
    
    def get_and_clear_click(self):
        """Returns click position if clicked, then clears flag"""
        if self.click_pos is not None:
            pos = self.click_pos
            self.click_pos = None
            return pos
        return None
    
    def display(self, frame):
        """Display frame in window"""
        cv2.imshow(self.window_name, frame)
    
    def wait_key(self, delay=1):
        """Wait for key press. Returns True if 'q' pressed"""
        key = cv2.waitKey(delay) & 0xFF
        return key == ord('q')
    
    def close(self):
        """Close window"""
        cv2.destroyAllWindows()
