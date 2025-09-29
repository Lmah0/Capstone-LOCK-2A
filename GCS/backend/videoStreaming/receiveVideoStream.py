import cv2
import time
import sys
from benchmarkVideoStream import StreamBenchmark

def setup_video_stream():
    stream_url = 'udp://192.168.1.123:5000'
    # stream_url = 'udp://@:5000'
    cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("Failed to open stream")
        exit()
    return cap

def display_video_stream(cap):
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imshow("Pi Stream", frame)
            
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cleanup_video_stream()

def benchmark_video_stream(cap, benchmark_time_seconds):
    benchmark = StreamBenchmark()
    start_time = time.time()
    while True:
        ret, frame = cap.read()
        if ret:
            break

    while time.time() - start_time <= benchmark_time_seconds:
        ret, frame = cap.read()
        benchmark.log_data(ret)
        if ret:
            cv2.imshow("Pi Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cleanup_video_stream()
    report = benchmark.report()
    print("\n--- Stream Performance ---")
    for k, v in report.items():
        print(f"{k}: {v}")

def cleanup_video_stream():
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    cap = setup_video_stream()
    if len(sys.argv) > 1 and sys.argv[1] == "bench":
        benchmark_video_stream(cap, 60)
    else:
        display_video_stream(cap)