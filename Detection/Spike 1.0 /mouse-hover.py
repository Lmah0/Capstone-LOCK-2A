import cv2
import numpy as np
from ultralytics import YOLO

VIDEO_PATH = "/Users/dominicgartner/Desktop/Capstone-LOCK-2A/Detection/Spike 1.0 /video.mp4"
SEG_MODEL_PATH = "/Users/dominicgartner/Desktop/Capstone-LOCK-2A/Detection/Spike 1.0 /yolo11n-seg.pt"

# Load model
model = YOLO(SEG_MODEL_PATH)
cap = cv2.VideoCapture(VIDEO_PATH)

cursor_x, cursor_y = 0, 0

def mouse_move(event, x, y, flags, param):
    global cursor_x, cursor_y
    cursor_x, cursor_y = x, y

cv2.namedWindow("Interactive Segmentation")
cv2.setMouseCallback("Interactive Segmentation", mouse_move)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model.predict(frame, conf=0.25, iou=0.7, verbose=False)
    annotated_frame = frame.copy()

    if results[0].masks is not None:
        masks = results[0].masks.data
        boxes = results[0].boxes.xyxy.cpu().numpy()

        for i, mask in enumerate(masks):
            mask_img = (mask.cpu().numpy() * 255).astype(np.uint8)
            mask_resized = cv2.resize(mask_img, (frame.shape[1], frame.shape[0]))  # Resize to frame

            x1, y1, x2, y2 = boxes[i].astype(int)

            if x1 <= cursor_x <= x2 and y1 <= cursor_y <= y2:
                color_mask = np.zeros_like(frame)
                color_mask[mask_resized > 0] = (0, 255, 0)
                annotated_frame = cv2.addWeighted(color_mask, 0.5, annotated_frame, 0.5, 0)


    cv2.imshow("Interactive Segmentation", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
