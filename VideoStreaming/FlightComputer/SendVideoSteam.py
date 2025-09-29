import subprocess
import time
import sys
import psutil
import datetime


ffmpeg_command = [
    "ffmpeg",   # ffmpeg - Command-line tool itself for streaming video/audio.
    "-f", "v4l2", # -f v4l2 - Specifies the input format as Video4Linux2, which is used for capturing video from USB webcams.
    "-framerate", "60", # -framerate 60 - Sets the frame rate to 60 frames per second.
    "-video_size", "640x480", # -video_size 640x480 - Sets size of video frames to 640x480 pixels.
    "-i", "/dev/video0", # -i /dev/video0 - Specifies the input device, which is camera located at /dev/video0.
    "-c:v", "libx264", # -c:v libx264 - Specifies to use the H.264 encoder for encoding video.
    "-preset", "ultrafast", # -preset ultrafast - Specifices to use the ultrafast preset for the x264 encoder, prioritizing encoding speed.
    "-tune", "zerolatency", # -tune zerolatency - Minimizes latency by reducing buffering.
    "-f", "mpegts", # -f mpegts - Sets the output format to MPEG-TS.
    "udp://192.168.1.98:5000" # - Specifies the output destination as a UDP stream to the IP address.
]

def benchmark_ffmpeg(cmd, duration=10):
    print("Starting FFmpeg stream...")
    start_time = time.time()

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    p = psutil.Process(process.pid)
    cpu_usage, mem_usage, fps_values, size_values, bit_rate_values, speed_values = [], [], [], [], [], []

    try:
        while time.time() - start_time < duration:
            # CPU/memory usage
            cpu_usage.append(p.cpu_percent(interval=1))
            mem_usage.append(p.memory_info().rss / (1024 * 1024))

            pattern = re.compile(
                r"fps=\s*([\d\.]+)\s+q=.*?size=\s*(\d+)(\wB)\s+time=.*?bitrate=\s*([\d\.]+kbits/s)\s+speed=\s*([\d\.]+)x"
            )

            for line in process.stderr:
                        print(line, end='')
                        line = line.strip()
                        match = pattern.search(line)
                        if match:
                            fps, size, bitrate, speed = match.groups()
                            fps_values.append(fps)
                            size_values.append(size)
                            bit_rate_values.append(bitrate)
                            speed_values.append(speed)
                            


    except KeyboardInterrupt:
        print("Benchmark stopped.")
    finally:
        process.terminate()

    avg_cpu = sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
    avg_mem = sum(mem_usage) / len(mem_usage) if mem_usage else 0
    avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0
    avg_size = sum(size_values) / len(size_values) if size_values else 0
    avg_bitrate = sum(bit_rate_values) / len(bit_rate_values) if bit_rate_values else 0
    avg_speed = sum(speed_values) / len(speed_values) if speed_values else 0

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = (
        f"\n=== Benchmark run at {timestamp} ===\n"
        f"Duration: {duration}s\n"
        f"Average CPU usage: {avg_cpu:.2f}%\n"
        f"Average Memory usage: {avg_mem:.2f} MB\n"
        f"Average FPS (ffmpeg): {avg_fps:.2f}\n"
        f"Average Size (ffmpeg): {avg_size:.2f} B\n"
        f"Average Bitrate (ffmpeg): {avg_bitrate:.2f} kbits/s\n"
        f"Average Speed (ffmpeg): {avg_speed:.2f}x\n"
    )

    print(report)

    with open("benchmark_results_flight_computer.txt", "a") as f:
        f.write(report)

def send_video():
    pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "bench":
        benchmark_ffmpeg(ffmpeg_command, duration=60)
    else:
        send_video()


















import subprocess
import time
import psutil
import re
import cv2

# FFmpeg command with timestamp overlay for latency measurement
ffmpeg_command = [
    "ffmpeg",
    "-f", "v4l2",
    "-framerate", "60",
    "-video_size", "640x480",
    "-i", "/dev/video0",
    "-vf", "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
           "text='%{pts\\:hms}':fontsize=24:fontcolor=white:x=10:y=10",
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-tune", "zerolatency",
    "-f", "mpegts",
    "udp://192.168.1.98:5000"
]

def benchmark_ffmpeg(cmd, duration=10):
    """
    Run ffmpeg, measure CPU/memory usage, and parse FPS from logs.
    """
    print("Starting FFmpeg stream...")
    start_time = time.time()

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    p = psutil.Process(process.pid)
    cpu_usage, mem_usage, fps_values = [], [], []

    try:
        while time.time() - start_time < duration:
            # CPU/memory usage
            cpu_usage.append(p.cpu_percent(interval=1))
            mem_usage.append(p.memory_info().rss / (1024 * 1024))

            # Parse FFmpeg stderr for FPS
            line = process.stderr.readline()
            if "fps=" in line:
                match = re.search(r"fps=\s*([\d\.]+)", line)
                if match:
                    fps_values.append(float(match.group(1)))

    except psutil.NoSuchProcess:
        print("FFmpeg exited early.")

    process.terminate()
    process.wait()

    avg_cpu = sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
    avg_mem = sum(mem_usage) / len(mem_usage) if mem_usage else 0
    avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0

    print(f"\nBenchmark results (duration: {duration}s):")
    print(f"Average CPU usage: {avg_cpu:.2f}%")
    print(f"Average Memory usage: {avg_mem:.2f} MB")
    print(f"Average FPS (reported by ffmpeg): {avg_fps:.2f}")

def measure_latency(stream_url="udp://192.168.1.98:5000"):
    """
    Capture frames from the UDP stream and estimate latency.
    """
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print("❌ Could not open stream for latency test")
        return

    print("Measuring latency... Press Ctrl+C to stop")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Get current time and assume overlay is timestamp
        recv_time = time.time()

        # (Optional) OCR could read the FFmpeg drawtext timestamp, but
        # for demo, we'll just mark when frame was received.
        # A true latency test needs both sender + receiver timestamps.

        print(f"Frame received at {recv_time:.3f} (latency test needs overlay parsing)")
        time.sleep(0.5)  # Print every 0.5s

    cap.release()

if __name__ == "__main__":
    benchmark_ffmpeg(ffmpeg_command, duration=10)

    # Uncomment to test latency (requires OpenCV + OCR for timestamps)
    # measure_latency()
