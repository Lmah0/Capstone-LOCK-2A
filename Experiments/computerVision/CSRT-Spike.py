import cv2
import sys

OUTPUT_FILE = "test_video.mp4" # Update this var to whatever your video file name is
 
if __name__ == '__main__' :
 
    tracker = cv2.legacy.TrackerCSRT_create()
    video = cv2.VideoCapture(OUTPUT_FILE)
 
    # Exit if video not opened.
    if not video.isOpened():
        print("Could not open video")
        sys.exit()
 
    # I skipped the initial 15 frames because the start of the video was a black screen for me
    if True: # make false is you dont want to skip ahead
        start_frame = 15       # The frame index to jump to initially 
        read_ahead = 20         # How many additional frames to skip ahead

        # Jump to the starting frame
        video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Read the starting frame
    ok, frame = video.read()
    if not ok:
        print(f"Cannot read video file")
        sys.exit()

    if True: # make false is you dont want to skip ahead
        # Optionally read more frames ahead (preview motion)
        for i in range(read_ahead):
            ok, frame = video.read()
            if not ok:
                print(f"Cannot read frame at {start_frame + i + 1}")
                break
        
    # Define an initial bounding box
    bbox = (287, 23, 86, 320)
 
    # Uncomment the line below to select a different bounding box
    bbox = cv2.selectROI(frame, False)
 
    # Initialize tracker with first frame and bounding box
    ok = tracker.init(frame, bbox)
 
    while True:
        # Read a new frame
        ok, frame = video.read()
        if not ok:
            break
         
        # Start timer
        timer = cv2.getTickCount()
 
        # Update tracker
        ok, bbox = tracker.update(frame)
 
        # Calculate Frames per second (FPS)
        fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer);
 
        # Draw bounding box
        if ok:
            # Tracking success
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)
        else :
            # Tracking failure
            cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
 
        # Display tracker type on frame
        cv2.putText(frame, "CSRT" + " Tracker", (100,20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50),2);
     
        # Display FPS on frame
        cv2.putText(frame, "FPS : " + str(int(fps)), (100,50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2);
 
        # Display result
        cv2.imshow("Tracking", frame)
 
        # Exit if ESC pressed
        k = cv2.waitKey(1) & 0xff
        if k == 27 : break