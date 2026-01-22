import sys
import cv2
import os
import time
import numpy as np
import threading

# Keep your existing domain logic imports
from AIEngine import TrackingEngine
from InterfaceHandler import Cv2UiHelperClass
from GeoLocate import locate


# 1. Get the absolute path of the current script (test_ai.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Go up one level to 'backend'
#    (current_dir is '.../backend/ai_processor', so parent is '.../backend')
backend_dir = os.path.dirname(current_dir)

# 3. Construct the path to the videoStreaming folder
#    Target: '.../backend/gcs/videoStreaming'
video_stream_path = os.path.join(backend_dir, "gcs", "videoStreaming")

# 4. Add this path to system path so Python can find the file
sys.path.append(video_stream_path)

# 5. Now you can import it
from receiveVideoStream import yield_frames_with_timestamps

# Global Vars
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "yolo11n-seg.pt")

# Global State for Local Inputs
mouse_x, mouse_y = 0, 0
click_point = None  # Stores (x, y) when clicked


def mouse_callback(event, x, y, flags, param):
    """Handles local mouse interaction for the OpenCV window"""
    global mouse_x, mouse_y, click_point

    if event == cv2.EVENT_MOUSEMOVE:
        mouse_x, mouse_y = x, y
    elif event == cv2.EVENT_LBUTTONDOWN:
        click_point = (x, y)


class StreamThread:
    """
    Reads frames in a separate thread to prevent buffer overruns
    when the AI processing takes too long.
    """

    def __init__(self):
        self.latest_frame = None
        self.latest_ts = None
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        print("Stream Thread Started")
        try:
            # Continuously consume the generator
            for frame, timestamp in yield_frames_with_timestamps():
                if not self.running:
                    break

                # Update the latest frame safely
                with self.lock:
                    self.latest_frame = frame
                    self.latest_ts = timestamp
        except Exception as e:
            print(f"Stream Thread Error: {e}")
        finally:
            self.running = False

    def get_frame(self):
        """Returns the most recent frame and timestamp"""
        with self.lock:
            return self.latest_frame, self.latest_ts

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)


def main():
    global click_point, mouse_x, mouse_y  # Ensure we access global input state
    # 1. Setup AI Engine
    engine = TrackingEngine(MODEL_PATH)
    frame_count = 0

    # 2. Setup Window and Callbacks
    window_name = "AI Object Tracker"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)

    # 3. Start Video Stream Thread
    streamer = StreamThread()
    streamer.start()

    # Wait briefly for the stream to initialize
    print("Waiting for video stream...")
    time.sleep(2.0)

    print("--- Controls ---")
    print(" [Mouse Move] : Hover over objects")
    print(" [Left Click] : Select object to track")
    print(" [r]          : Reset / Stop Tracking")
    print(" [q]          : Quit")
    print("----------------")

    try:
        # 3. Main Loop: Iterate directly over the yield_frames_with_timestamps generator
        while True:

            frame, timestamp = streamer.get_frame()
            if frame is None:
                # Stream hasn't yielded a frame yet, or connection lost
                time.sleep(0.01)
                continue
            frame_count += 1
            output_frame = frame.copy()

            # Handle Keyboard Commands
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("r"):
                engine.is_tracking = False
                print("Tracking stopped by user.")

            # --- STATE 1: TRACKING MODE ---
            # --- STATE 1: TRACKING MODE ---
            if engine.is_tracking:
                # 1. Measure Tracking Speed
                t0 = time.time()
                success, bbox = engine.update(frame, frame_count)
                t1 = time.time()
                track_time = (t1 - t0) * 1000  # Convert to ms

                if success:
                    output_frame = Cv2UiHelperClass.draw_tracking_state(
                        output_frame,
                        bbox,
                        engine.tracked_class,
                        engine.status_message,
                    )

                    # 2. Measure Geolocation Speed
                    t2 = time.time()
                    draw_time = (t2 - t1) * 1000
                    # ... setup vars ...
                    current_alt = 10.0
                    current_lat = 50.0
                    current_lon = 100.0
                    heading = 0.0

                    image_center_x = frame.shape[1] / 2
                    image_center_y = frame.shape[0] / 2
                    bbox_center_x = bbox[0] + bbox[2] / 2
                    bbox_center_y = bbox[1] + bbox[3] / 2
                    obj_x_px = bbox_center_x - image_center_x
                    obj_y_px = bbox_center_y - image_center_y

                    target_lat, target_lon = locate(
                        current_lat,
                        current_lon,
                        current_alt,
                        heading,
                        obj_x_px,
                        obj_y_px,
                    )
                    t3 = time.time()
                    geo_time = (t3 - t2) * 1000

                    # Print diagnostics
                    print(
                        f"Tracking: {track_time:.1f}ms | Drawing: {draw_time:.1f} | Geo: {geo_time:.1f}ms"
                    )
                else:
                    print("Tracking Lost")

            # --- STATE 2: DETECTION MODE ---
            else:
                results = engine.detect_objects(frame)

                if results.masks is not None:
                    cursor_x, cursor_y = mouse_x, mouse_y
                    output_frame, hover_box, hover_index = (
                        Cv2UiHelperClass.draw_hover_effects(
                            frame,
                            results.masks.data,
                            results.boxes.xyxy.cpu().numpy(),
                            results.boxes.cls.cpu().numpy(),
                            cursor_x,
                            cursor_y,
                        )
                    )

                if click_point is not None:
                    click_x, click_y = click_point
                    click_point = None

                    if (
                        hover_box is not None
                        and abs(click_x - cursor_x) < 10
                        and abs(click_y - cursor_y) < 10
                    ):
                        # User clicked on the hovered object
                        class_id = int(results.boxes.cls[hover_index])
                        engine.start_tracking(frame, hover_box, class_id)
                        print(f"Started tracking object at ({click_x}, {click_y})")
                    else:
                        # Fallback: find which detection was clicked
                        boxes = results.boxes.xyxy.cpu().numpy()
                        classes = results.boxes.cls.cpu().numpy()

                        for i, box in enumerate(boxes):
                            x1, y1, x2, y2 = box.astype(int)

                            # Check if click is inside this bounding box
                            if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                                # Convert xyxy to xywh
                                bbox = (x1, y1, x2 - x1, y2 - y1)
                                class_id = int(classes[i])
                                engine.start_tracking(frame, bbox, class_id)
                                print(
                                    f"Started tracking object at ({click_x}, {click_y})"
                                )
                                break

            cv2.imshow(window_name, output_frame)

    except Exception as e:
        print(f"\nERROR: Unexpected exception: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up OpenCV windows
        # Note: The 'container' is automatically closed by the finally block in the generator
        cv2.destroyAllWindows()


if __name__ == "__main__":
    print("Starting AI Object Tracker...")
    main()
