from ultralytics import solutions
import cv2
import time  # Import the time module for performance measurement

# --- 1. SETUP AND INITIALIZATION ---

# Define the path to the video file
VIDEO_PATH = "people-detection.mp4" # IMPORTANT: Update this path to your actual video file location
MODEL_NAME = "yolo11n-seg.pt" # YOLOv11 Nano Segmentation model

# Initialize the video capture object
input_video = cv2.VideoCapture(VIDEO_PATH)

# Check if the video file was opened successfully
if not input_video.isOpened():
    # If the video cannot be opened, print an error and exit gracefully
    print(f"Error: Could not open video file at {VIDEO_PATH}. Please check the path.")
    exit()

# --- 2. VIDEO PROPERTIES SETUP (For informational purposes) ---

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

# --- 3. INSTANCE SEGMENTATION MODEL INITIALIZATION ---

# Initialize the InstanceSegmentation solution from Ultralytics
# show=True will ensure the results are displayed live
segmentation_model = solutions.InstanceSegmentation(
    show=True,  # Set to True to display the live output window during processing
    model=MODEL_NAME, # The pre-trained YOLO model for segmentation
)

# --- 4. VIDEO PROCESSING LOOP ---

print("Starting video processing...")
frame_count = 0
total_processing_time = 0.0

while input_video.isOpened():
    # Read the next frame from the video
    success, raw_frame = input_video.read()

    # Check if a frame was successfully read
    if not success:
        print(f"\nVideo processing complete after {frame_count} frames, or stream is empty.")
        break

    frame_count += 1
    
    # --- Performance Measurement Start ---
    start_time = time.time()

    # Run the instance segmentation model on the current frame
    # The 'show=True' setting in the model initialization handles the display
    segmentation_results = segmentation_model(raw_frame)

    # --- Performance Measurement End ---
    end_time = time.time()
    
    # Calculate processing time for this frame and derive FPS
    processing_time = end_time - start_time
    total_processing_time += processing_time
    processing_fps = 1.0 / (processing_time + 1e-6) # Use a small epsilon
    
    # Print real-time FPS to the console
    print(f"Frame: {frame_count:04d} | FPS: {processing_fps:.2f}", end='\r')

# --- 5. CLEANUP ---

print("\nReleasing resources and closing windows.")
# Release the input video capture object
input_video.release()

# Calculate and print final statistics
if frame_count > 0:
    average_fps = frame_count / total_processing_time
    print(f"Total Frames Processed: {frame_count}")
    print(f"Total Processing Time: {total_processing_time:.2f} seconds")
    print(f"Average Processing FPS: {average_fps:.2f}")

# Destroy all OpenCV display windows
cv2.destroyAllWindows()

print("Processing finished.")