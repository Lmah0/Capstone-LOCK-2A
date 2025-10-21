import cv2
import time
from benchmarking.benchmarkReceivingVideoStream import StreamBenchmark
from benchmarking.benchmarkReceivingVideoStream import run_quality_metrics

def setup_video_stream():
    stream_url = 'udp://192.168.1.123:5000' # Modify IP address and port based on flight computer
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

def benchmark_video_stream(cap, benchmark_time_seconds):
    benchmark = StreamBenchmark()
    start_time = time.time()
    while True:
        ret, frame = cap.read()
        if ret:
            break

    while time.time() - start_time <= benchmark_time_seconds:
        ret, frame = cap.read()
        benchmark.log_stream_data(ret)
        if ret:
            cv2.imshow("Pi Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    report = benchmark.report_stream_data()
    print("\n--- Stream Performance ---")
    print(report)

def return_video_stream(cap):
    while True:
        ret, frame = cap.read()
        if ret:
            yield frame

def cleanup_video_stream():
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    cap = setup_video_stream()
    user_selection = input(
        "Select 1: Display Stream, 2: Benchmark FFMPEG Stream\n"
        "3: Benchmark Video Quality\n Enter your choice: "
    )
    if user_selection == '1':
        display_video_stream(cap)
    elif user_selection == '2':
        benchmark_video_stream(cap, 55)
    elif user_selection == '3':
        reference_video = "reference.mp4"  # Path to the original reference video
        received_video = "received.mp4"    # Path to the received video for comparison
        run_quality_metrics(cap, reference_video, received_video, 30)
    cleanup_video_stream()