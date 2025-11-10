# main.py
import cv2
import os
import time
from SOT import ObjectTracker
from locate import locate

TARGET_CLS_ID = 0 # set the desired class (e.g., 0 for 'person')
MODEL_NAME = "yolo11n.pt" 
VIDEO_NAME = "video.mp4"

def process_frame(frame, tracker, uav_lat, uav_lon, uav_alt, bearing):
    """Runs one frame through tracker and locator, tracking a specific object."""
    detections = tracker.update(frame)
    target_det = None

    # 1. Selection Logic
    if tracker.target_id is None:
        for det in detections:
            # Pick the first object that matches the target class ID
            if det["cls"] == TARGET_CLS_ID:
                tracker.target_id = det["id"] # Store the persistent ID
                target_det = det
                break
    
    # 2. Tracking Logic (Run on subsequent frames)
    if tracker.target_id is not None:
        for det in detections:
            if det.get("id") == tracker.target_id:
                target_det = det
                break
    
    # 3. Processing and Drawing
    if target_det:
        det = target_det
        cx, cy = det["center"]
        
        # Draw Bounding Box and ID
        x, y, w, h = det["bbox"]
        x1, y1 = x, y
        x2, y2 = x + w, y + h
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw ID text
        cv2.putText(frame, f"ID: {det['id']}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        # Draw center point
        cv2.circle(frame, (int(cx), int(cy)), 5, (0, 0, 255), -1)

        lat_obj, lon_obj = locate(
            uav_latitude=uav_lat,
            uav_longitude=uav_lon,
            uav_altitude=uav_alt,
            bearing=bearing,
            obj_x_px=cx,
            obj_y_px=cy
        )
        
        print(f"Tracking ID {det['id']} @ ({lat_obj:.6f}, {lon_obj:.6f})") 
        
    else:
        # If the target object is lost
        if tracker.target_id is not None:
            print(f"Tracking lost for ID {tracker.target_id}...") 
            tracker.target_id = None


def run_video(input_path, tracker, uav_lat, uav_lon, uav_alt, bearing):
    cap = cv2.VideoCapture(input_path if isinstance(input_path, str) else 0)
    frame_count = 0
    total_time = 0.0
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print(f"\nVideo ended after {frame_count} frames.")
            break

        frame_count += 1
        start = time.time()

        process_frame(frame, tracker, uav_lat, uav_lon, uav_alt, bearing)

        end = time.time()
        total_time += end - start
        fps = 1.0 / (end - start + 1e-6)

        cv2.putText(frame, f"FPS: {fps:.2f}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow("Tracking Stream", frame)

    cap.release()
    cv2.destroyAllWindows()

    if frame_count > 0:
        avg_fps = frame_count / total_time
        print(f"\nAverage FPS: {avg_fps:.2f}")

def run_images(input_path, tracker, uav_lat, uav_lon, uav_alt, bearing):
    """Handle one or multiple images."""
    image_files = []
    if os.path.isdir(input_path):
        image_files = sorted([
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
    elif os.path.isfile(input_path):
        image_files = [input_path]
    else:
        raise FileNotFoundError(f"Invalid input path: {input_path}")

    for i, img_path in enumerate(image_files, start=1):
        frame = cv2.imread(img_path)
        if frame is None:
            print(f"Warning: Unable to read {img_path}")
            continue

        print(f"\nProcessing image {i}/{len(image_files)}: {os.path.basename(img_path)}")
        process_frame(frame, tracker, uav_lat, uav_lon, uav_alt, bearing)
        
        cv2.imshow("Detection Result", frame)

    cv2.destroyAllWindows()
    print("\nImage processing complete.")

if __name__ == "__main__":
    tracker = ObjectTracker(model_name=MODEL_NAME, show=True) 

    # UAV telemetry (example)
    uav_lat, uav_lon, uav_alt, bearing = 0.0, 0.0, 100.0, 0.0

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, VIDEO_NAME)

    print("Starting stream... Press 'ctrl + c' to quit.")
    if isinstance(input_path, int) or input_path.lower().endswith(('.mp4', '.avi', '.mov')):
        run_video(input_path, tracker, uav_lat, uav_lon, uav_alt, bearing)
    else:
        run_images(input_path, tracker, uav_lat, uav_lon, uav_alt, bearing)