import cv2
import numpy as np
from ultralytics import YOLO

VIDEO_PATH = "/Users/dominicgartner/Desktop/Capstone-LOCK-2A/Detection/Spike 1.0 /video.mp4"
SEG_MODEL_PATH = "/Users/dominicgartner/Desktop/Capstone-LOCK-2A/Detection/Spike 1.0 /yolo11n-seg.pt"

# Load YOLO segmentation model
model = YOLO(SEG_MODEL_PATH)
cap = cv2.VideoCapture(VIDEO_PATH)

cursor_x, cursor_y = 0, 0
click_flag = False

# Tracking variables
tracking = False
tracker = None
tracked_class = None
tracked_bbox = None  # Keep current bbox

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

    annotated_frame = frame.copy()

    if not tracking:
        # --- RUN DETECTION ---
        results = model.predict(frame, conf=0.25, iou=0.7, verbose=False)
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
        else:
            print("Lost tracking, resuming detection")
            tracking = False
            tracker = None
            tracked_class = None
            tracked_bbox = None

    cv2.imshow("Interactive Segmentation", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()