from ultralytics import YOLO # type: ignore
import cv2
import time

# --- 1. SETUP AND INITIALIZATION ---

# Define the path to the video file
VIDEO_PATH = "people-detection.mp4" 

# 🚨 CRITICAL CHANGE 🚨
# Replace this with the path to your custom model weights file (e.g., 'runs/detect/train/weights/best.pt')
CUSTOM_MODEL_PATH = "path/to/your/roboflow/best.pt" 

# Initialize the video capture object
input_video = cv2.VideoCapture(VIDEO_PATH)

if not input_video.isOpened():
    print(f"Error: Could not open video file at {VIDEO_PATH}. Please check the path.")
    exit()

# --- 2. VIDEO PROPERTIES SETUP ---

# Retrieve necessary properties from the input video
frame_width, frame_height, frame_fps = (
    int(input_video.get(prop)) for prop in (
        cv2.CAP_PROP_FRAME_WIDTH,
        cv2.CAP_PROP_FRAME_HEIGHT,
        cv2.CAP_PROP_FPS
    )
)

print(f"Input Video Resolution: {frame_width}x{frame_height} at {frame_fps:.2f} FPS (Source)")
print("Processing will display live output but will NOT save an output video file.")

# --- 3. CUSTOM YOLO MODEL INITIALIZATION ---

# Load the custom YOLO detection model using the base YOLO class
model = YOLO(CUSTOM_MODEL_PATH)

# --- 4. VIDEO PROCESSING LOOP ---

print("Starting video processing...")
frame_count = 0
total_processing_time = 0.0

while input_video.isOpened():
    success, raw_frame = input_video.read()

    if not success:
        print(f"\nVideo processing complete after {frame_count} frames, or stream is empty.")
        break

    frame_count += 1
    
    start_time = time.time()

    # Perform prediction using the standard model call (Predict Mode)
    # The results object contains bounding box coordinates, class, and confidence
    results = model.predict(
        source=raw_frame, 
        conf=0.25,      # Optional: Set a confidence threshold
        iou=0.7,        # Optional: Set an IoU threshold
        verbose=False   # Keep terminal clean from per-frame logs
    )

    end_time = time.time()
    
    processing_time = end_time - start_time
    total_processing_time += processing_time
    processing_fps = 1.0 / (processing_time + 1e-6)
    
    print(f"Frame: {frame_count:04d} | FPS: {processing_fps:.2f}", end='\r')

    # The plot() method draws the bounding boxes and labels onto the frame
    # results[0] is the result object for the current frame
    annotated_frame = results[0].plot() 

    # Display the annotated frame
    cv2.imshow("YOLO Custom Detection Output", annotated_frame)
    
    # Exit loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- 5. CLEANUP ---

print("\nReleasing resources and closing windows.")
input_video.release()

# Calculate and print final statistics
if frame_count > 0:
    average_fps = frame_count / total_processing_time
    print(f"Total Frames Processed: {frame_count}")
    print(f"Average Processing FPS: {average_fps:.2f}")

cv2.destroyAllWindows()

print("Processing finished.")