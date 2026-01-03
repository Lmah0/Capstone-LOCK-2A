'''
AI Helper File:
    - Handles all cv2 drawing (boxes, text, contours)
'''

import cv2
import numpy as np

class Cv2UiHelperClass:
    def __init__(self, window_name):
        self.cursor_x = 0
        self.cursor_y = 0
        self.clicked = False
        self.window_name = window_name
        
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, self.mouse_event)

    def get_mouse_position(self):
        return (self.cursor_x, self.cursor_y)
    
    def mouse_event(self, event, x, y, flags, param):
        self.cursor_x, self.cursor_y = x, y
        if event == cv2.EVENT_LBUTTONDOWN:
            self.clicked = True

    def consume_click(self):
        """Returns True if clicked, then resets flag"""
        if self.clicked:
            self.clicked = False
            return True
        return False

    # --- Helper Methods ---
    @staticmethod
    def draw_hover_effects(frame, masks, boxes, classes, cursor_x, cursor_y):
        """Draws outlines and fills when mouse hovers over a YOLO detection"""  
        annotated_frame = frame.copy()
        target_box = None
        target_index = None

        for i, mask in enumerate(masks):
            x1, y1, x2, y2 = boxes[i].astype(int)
            
            # Check Hover
            if x1 <= cursor_x <= x2 and y1 <= cursor_y <= y2:
                target_index = i
                target_box = (x1, y1, x2 - x1, y2 - y1)
                
                # Resize mask to frame size
                mask_img = (mask.cpu().numpy() * 255).astype(np.uint8)
                mask_resized = cv2.resize(mask_img, (frame.shape[1], frame.shape[0]))
                
                # 1. Draw Contours
                contours, _ = cv2.findContours(mask_resized, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    epsilon = 0.01 * cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, epsilon, True)
                    cv2.drawContours(annotated_frame, [approx], -1, (0, 200, 0), 2)

                # 2. Gradient Fill
                overlay = annotated_frame.copy()
                overlay[mask_resized > 0] = (0, 255, 0)
                annotated_frame = cv2.addWeighted(overlay, 0.4, annotated_frame, 0.6, 0)

        return annotated_frame, target_box, target_index

    @staticmethod
    def draw_tracking_state(frame, bbox, class_id, status_text=""):
        x, y, w, h = [int(v) for v in bbox]
        alpha = 0.4

        # Draw Gradient Box
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 255), -1)
        frame = cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0)

        # Outline & Text
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 200), 2)
        cv2.putText(frame, f"Tracking class {class_id}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # Status message with appropriate color
        # if status_text:
        #     # Determine color based on message content
        #     if "REALIGNED" in status_text:
        #         color = (0, 255, 0)  # Green for successful realignment
        #     elif "DRIFT DETECTED" in status_text:
        #         color = (0, 165, 255)  # Orange for drift warning
        #     elif "confident" in status_text:
        #         color = (50, 150, 50)  # Dark green for high confidence
        #     else:
        #         color = (0, 255, 0)  # Default green   
        #     cv2.putText(frame, status_text, (100, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
        return frame