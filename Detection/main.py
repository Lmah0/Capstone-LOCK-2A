from AIEngine import TrackingEngine
from InterfaceHandler import Cv2UiHelperClass
from GeoLocate import locate
import sys
import os
import time

# Tell python to look into parent directory for the AiStream file
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)
from GCS.backend import AiStreamClient

# Global Vars
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "Spike_1.0", "yolo11n-seg.pt")

def handle_stop_tracking(): #TODO
    pass

def handle_reselect_object(): #TODO
    pass


def main():
    try:
        frame_count = 0
        AiStreamClient.initialize()
        engine = TrackingEngine(MODEL_PATH)

        while True: 
            # Waiting for video stream to start
            frame = AiStreamClient.get_current_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            frame_count += 1
            output_frame = frame.copy()

            # Check for pending commands from frontend
            command = AiStreamClient.get_pending_command()
            if command is not None:
                if command == "stop_tracking":
                    handle_stop_tracking()
                elif command == "reselect_object":
                    handle_reselect_object()

            # --- STATE 1: TRACKING MODE ---
            if engine.is_tracking:
                success, bbox = engine.update(frame, frame_count)
                if success:
                    output_frame = Cv2UiHelperClass.draw_tracking_state(
                        output_frame,
                        bbox,
                        engine.tracked_class,
                        engine.status_message
                    )

                    # --- Calculate Target Location ---
                    cx = bbox[0] + bbox[2]/2
                    cy = bbox[1] + bbox[3]/2

                    # TODO: Get telemetry (will need to update with the embedded information we get from the video stream data) 
                    current_alt = 10.0 
                    current_lat = 50
                    current_lon = 100
                    heading = 0

                    target_lat, target_lon = locate(
                        current_lat, current_lon, current_alt, heading, cx, cy
                    )
                    
                    # TODO: Update to send cmds to drone
                    print(f"Target Found at relative latitude, longitude: {target_lat}, {target_lon}")
                else:
                    print("Tracking Lost")

            # --- STATE 2: DETECTION MODE ---
            else:
                results = engine.detect_objects(frame)

                if results.masks is not None:
                    cursor_x, cursor_y = AiStreamClient.get_mouse_position()

                    output_frame, hover_box, hover_index = Cv2UiHelperClass.draw_hover_effects(
                        frame,
                        results.masks.data,
                        results.boxes.xyxy.cpu().numpy(),
                        results.boxes.cls.cpu().numpy(),
                        cursor_x,
                        cursor_y,
                    )

                    # Check for frontend click to start tracking
                    click = AiStreamClient.get_pending_click()
                    if click is not None:
                        click_x, click_y = click

                        # Use the hover_box if click matches current hover position
                        if hover_box is not None and abs(click_x - cursor_x) < 10 and abs(click_y - cursor_y) < 10:
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
                                    print(f"Started tracking object at ({click_x}, {click_y})")
                                    break

            AiStreamClient.send_frame(output_frame) # Always send frame to frontend
            time.sleep(0.01) # Small delay to prevent CPU overload
    
    except Exception as e:
        print(f"\nERROR: Unexpected exception: {e}")

    finally:
        AiStreamClient.shutdown()

if __name__ == "__main__":
    main()