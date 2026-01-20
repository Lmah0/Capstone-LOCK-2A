from AIEngine import TrackingEngine
from InterfaceHandler import Cv2UiHelperClass
from GeoLocate import locate
import os
import time
import AiStreamClient

# Global Vars
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'yolo11n-seg.pt')
VIDEO_PATH = os.path.join(BASE_DIR, 'video.mp4')

def handle_stop_tracking(): #TODO
    pass

def handle_reselect_object(): #TODO
    pass


def main():
    try:
        frame_count = 0

        # Init Video
        if not AiStreamClient.init(VIDEO_PATH):
            print("Failed to initialize video capture")
            return

        AiStreamClient.initialize()
        engine = TrackingEngine(MODEL_PATH)

        while True: 
            # Waiting for video stream to start
            frame = AiStreamClient.get_frame()
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


                    # TODO: Get telemetry (will need to update with the embedded information we get from the video stream data) 
                    current_alt = 10.0 
                    current_lat = 50
                    current_lon = 100
                    heading = 0

                     # --- Calculate Target Location ---
                    image_center_x = frame.shape[1] / 2
                    image_center_y = frame.shape[0] / 2

                    bbox_center_x = bbox[0] + bbox[2]/2
                    bbox_center_y = bbox[1] + bbox[3]/2

                    obj_x_px = bbox_center_x - image_center_x
                    obj_y_px = bbox_center_y - image_center_y

                    target_lat, target_lon = locate(current_lat, current_lon, current_alt, heading, obj_x_px, obj_y_px)
                    
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
                                
            AiStreamClient.push_frame(output_frame) # Always send frame to frontend
            time.sleep(0.01) # Small delay to prevent CPU overload
    
    except Exception as e:
        print(f"\nERROR: Unexpected exception: {e}")

    finally:
        AiStreamClient.shutdown()

if __name__ == "__main__":
    main()