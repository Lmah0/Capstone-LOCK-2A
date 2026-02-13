import subprocess
import os
import av
import cv2
import time
import json
import threading
from datetime import datetime

# --- CONFIGURATION ---
GCS_VIDEO_PORT = os.getenv("GCS_VIDEO_PORT", 5000)
STREAM_URL = "udp://0.0.0.0:" +  str(GCS_VIDEO_PORT) + "?overrun_nonfatal=1&fifo_size=10000"
DISPLAY_WITH_OVERLAY = True
# Reduce log noise
av.logging.set_level(av.logging.PANIC)


class VideoStreamReceiver:
    def __init__(self, stream_url=STREAM_URL):
        self.stream_url = stream_url
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

        # Shared Variables
        self.latest_frame = None
        self.latest_telemetry = {
            "frame_number": -1,
            "error": "Waiting for stream...",
            "latency_ms": None,
        }
        
        # Recording
        self.recording = False
        self.video_writer = None
        self.record_filename = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self.update_loop, daemon=True)
        self.thread.start()
        print(f"Background thread started for {self.stream_url}")

    def stop(self):
        self.running = False
        if self.thread:
            print("Stopping background thread...")
            self.thread.join()
        self.stop_recording()

    def start_recording(self, filename="recorded.mp4", fps=60, resolution=(1280, 720)):
        """Start recording frames to a video file."""
        if self.recording:
            print("Already recording!")
            return
        
        self.record_filename = filename
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(filename, fourcc, fps, resolution)
        self.recording = True
        print(f"Started recording to {filename}")
    
    def stop_recording(self):
        """Stop recording and release the video writer."""
        if self.recording and self.video_writer:
            self.recording = False
            self.video_writer.release()
            print(f"Recording saved to {self.record_filename}")
            self.video_writer = None
            self.record_filename = None

    def update_loop(self):
        """Background loop: Reads packets continuously."""
        print(f"Connecting to {self.stream_url}...")
        container = None

        while self.running:
            try:
                # Re-open connection if lost
                if container is None:
                    container = av.open(
                        self.stream_url,
                        options={
                            "fflags": "nobuffer+discardcorrupt",
                            "flags": "low_delay",
                            "flush_packets": "1",
                            "probesize": "32",
                            "analyzeduration": "0",
                            "reorder_queue_size": "0",
                            "max_delay": "0",
                            "timeout": "2000000",
                            "rw_timeout": "2000000"
                        },
                    )
                    container.streams.video[0].thread_type = "AUTO"
                    print("Stream Connected.")

                # Demux Packets
                for packet in container.demux():
                    if not self.running:
                        break

                    # Handle Telemetry (Metadata)
                    if packet.stream.type == "data":
                        try:
                            payload = bytes(packet)
                            text = payload.decode("utf-8", errors="ignore")
                            meta = json.loads(text)

                            # Calculate Latency immediately upon arrival
                            meta["receive_time"] = time.time()
                            if meta.get("video_timestamp"):
                                meta["latency_ms"] = (
                                    meta["receive_time"] - meta["video_timestamp"]
                                ) * 1000

                            with self.lock:
                                self.latest_telemetry = meta

                        except Exception:
                            pass

                    # Handle Video
                    elif packet.stream.type == "video":
                        try:
                            for frame in packet.decode():
                                img = frame.to_ndarray(format="bgr24")
    
                                with self.lock:
                                    self.latest_frame = img
                                
                                # Write to file if recording
                                if self.recording and self.video_writer:
                                    self.video_writer.write(img)
                                    
                        except (av.FFmpegError, OSError, ValueError) as e:
                            print(f"Video Decode Error: {e}. Continuing...")
                            continue
    
            except (av.FFmpegError, OSError) as e:
                if container:
                    container.close()
                    container = None
                time.sleep(2)
            except Exception as e:
                print(f"Unexpected Error: {e}")
                break

        if container:
            container.close()
        print("Stream closed.")

    def read(self):
        """Returns the absolute NEWEST frame and telemetry."""
        with self.lock:
            if self.latest_frame is None:
                return None, self.latest_telemetry
            return self.latest_frame, self.latest_telemetry


def display_video_stream():
    """Function to display the incoming video stream with telemetry overlay."""
    receiver = VideoStreamReceiver()
    receiver.start()

    # Wait for connection
    time.sleep(1)
    print("Starting Display...")
    print("Press 'r' to start/stop recording")
    print("Press 'q' to quit")

    try:
        while True:
            # Get latest data (non-blocking)
            frame, ts_info = receiver.read()

            if frame is None:
                time.sleep(0.01)
                continue

            display_frame = frame.copy()

            # --- Extract Data ---
            frame_num = ts_info.get("frame_number", "N/A")
            wall_time = ts_info.get("video_timestamp")
            latency = ts_info.get("latency_ms")
            receive_time = ts_info.get("receive_time")

            if DISPLAY_WITH_OVERLAY:
                # Draw Info Box 
                box_height = 180 if receiver.recording else 150
                cv2.rectangle(display_frame, (0, 0), (450, box_height), (0, 0, 0), -1)
                cv2.rectangle(display_frame, (0, 0), (450, box_height), (0, 255, 0), 2)
                
                # Display Text
                cv2.putText(
                    display_frame,
                    f"Frame: {frame_num}",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                if wall_time:
                    dt = datetime.fromtimestamp(wall_time)
                    time_str = dt.strftime("%H:%M:%S.%f")[:-3]
                    cv2.putText(
                        display_frame,
                        f"Drone Time: {time_str}",
                        (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )

                if receive_time:
                    dt = datetime.fromtimestamp(receive_time)
                    time_str = dt.strftime("%H:%M:%S.%f")[:-3]
                    cv2.putText(
                        display_frame,
                        f"GCS Time: {time_str}",
                        (20, 105),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )

                if latency is not None:
                    color = (0, 255, 0) if latency < 150 else (0, 0, 255)
                    cv2.putText(
                        display_frame,
                        f"Latency: {latency:.1f} ms",
                        (20, 140),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        2,
                    )
                
                # Recording indicator
                if receiver.recording:
                    cv2.putText(
                        display_frame,
                        "REC",
                        (20, 170),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                    )
                    cv2.circle(display_frame, (100, 162), 8, (0, 0, 255), -1)

            cv2.imshow("GCS Stream (Threaded)", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("r"):
                if receiver.recording:
                    receiver.stop_recording()
                else:
                    # Get frame dimensions for video writer
                    h, w = frame.shape[:2]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"recording_{timestamp}.mp4"
                    receiver.start_recording(filename=filename, fps=60, resolution=(w, h))
                    
    finally:
        receiver.stop()
        cv2.destroyAllWindows()


def benchmark_video_stream(duration=30):
    """Function to bench mark the incoming video stream latency."""
    print(f"Benchmarking for {duration} seconds...")
    receiver = VideoStreamReceiver()
    receiver.start()

    start_time = time.time()
    latencies = []
    frames_counted = 0

    try:
        while (time.time() - start_time) < duration:
            frame, info = receiver.read()
            if frame is None:
                continue

            lat = info.get("latency_ms")
            if lat:
                latencies.append(lat)

            frames_counted += 1
            if frames_counted % 30 == 0:
                # Artificial sleep to simulate AI load
                time.sleep(0.03)
                current_avg = sum(latencies[-30:]) / 30 if latencies else 0
                print(f"Sampled {frames_counted} | Current Avg: {current_avg:.1f}ms")
            else:
                time.sleep(0.01)

    finally:
        receiver.stop()

    print("\n" + "=" * 40)
    print(f"Total Samples: {len(latencies)}")
    if latencies:
        print(f"Avg Latency: {sum(latencies)/len(latencies):.2f} ms")
        print(f"Min Latency: {min(latencies):.2f} ms")
        print(f"Max Latency: {max(latencies):.2f} ms")
    print("=" * 40)


def record_incoming_stream(filename="received.mp4", duration=35):
    """Saves the stream using FFmpeg subprocess for quality analysis later."""
    print(f"Recording to '{filename}' for {duration}s using FFmpeg...")

    cmd = [
        "ffmpeg",
        "-y",
        "-t",
        str(duration),
        "-i",
        "udp://0.0.0.0:" + str(GCS_VIDEO_PORT) + "?overrun_nonfatal=1&fifo_size=50000000",
        "-c",
        "copy",
        filename,
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ Saved to {filename}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e}")
    except FileNotFoundError:
        print("Error: FFmpeg is not installed or not in PATH.")


def run_quality_metrics_wrapper(ref="reference.mp4", recv="received.mp4"):
    """Measures PSNR and SSIM between reference and received videos."""
    null_out = "NUL" if os.name == "nt" else "/dev/null"

    # Ensure received file exists
    if not os.path.exists(recv):
        print(f"Error: {recv} not found. Run option 4 first.")
        return

    commands = {
        "psnr": f'ffmpeg -i "{ref}" -i "{recv}" -lavfi "psnr" -f null {null_out}',
        "ssim": f'ffmpeg -i "{ref}" -i "{recv}" -lavfi "ssim" -f null {null_out}',
    }

    for name, cmd in commands.items():
        print(f"\n--- Running {name.upper()} ---")
        subprocess.run(cmd, shell=True)


if __name__ == "__main__":
    while True:
        print("\n--- GCS Video Tool ---")
        print("1: Display Stream (Threaded Low Latency)")
        print("2: Benchmark Latency")
        print("3: Run Quality Metrics (requires reference.mp4)")
        print("4: Record Incoming Stream (for quality check)")
        print("q: Quit")

        choice = input("Enter choice: ")

        if choice == "1":
            display_video_stream()
        elif choice == "2":
            benchmark_video_stream()
        elif choice == "3":
            run_quality_metrics_wrapper()
        elif choice == "4":
            record_incoming_stream()
        elif choice.lower() == "q":
            break
        else:
            print("Invalid Selection")