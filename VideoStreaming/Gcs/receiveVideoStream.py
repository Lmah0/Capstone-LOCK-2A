import cv2

def setup_video_stream():
    stream_url = 'udp://192.168.1.123:5000'

    cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("Failed to open stream")
        exit()
    return cap

def display_video_stream(cap):
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        cv2.imshow("Pi Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cleanup_video_stream()

def video_stream_frame():
    ret, frame = cap.read()
    if ret:
        return frame

def cleanup_video_stream():
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    cap = setup_video_stream()
    display_video_stream(cap)