import cmd
import subprocess
import time
import psutil
import datetime
import os
import re

def benchmark_ffmpeg(cmd, duration=60):
    print("Benchmarking, Starting FFmpeg stream...")
    start_time = time.time()

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    p = psutil.Process(process.pid)
    cpu_usage, mem_usage, fps_values, size_values, bit_rate_values, drop_values, speed_values = [], [], [], [], [], [], []

    pattern = re.compile(
        r"fps=\s*([\d\.]+)\s+q=.*?size=\s*([\d\w]+B)\s+time=.*?"
        r"bitrate=\s*([\d\.]+)kbits/s.*?drop=\s*(\d+).*?speed=\s*([\d\.]+)x"
    )

    try:
        while time.time() - start_time < duration:
            # collect system metrics
            cpu_usage.append(p.cpu_percent(interval=1))
            mem_usage.append(p.memory_info().rss / (1024 * 1024))

            line = process.stderr.readline()
            if not line:
                continue

            print(line, end='')
            match = pattern.search(line)
            if match:
                fps, size, bitrate, drop, speed = match.groups()
                fps_values.append(float(fps))
                size_values.append(float(re.sub(r'[^\d\.]', '', size)))
                bit_rate_values.append(float(bitrate))
                drop_values.append(int(drop))
                speed_values.append(float(speed))

    except KeyboardInterrupt:
        print("Benchmark stopped manually.")
    finally:
        process.terminate()

    avg = lambda vals: sum(vals) / len(vals) if vals else 0
    report = (
        f"\n=== Benchmark run at {datetime.datetime.now():%Y-%m-%d %H:%M:%S} ===\n"
        f"Duration: {duration}s\n"
        f"Average CPU usage: {avg(cpu_usage):.4f}%\n"
        f"Average Memory usage: {avg(mem_usage):.4f} MB\n"
        f"Average Size (ffmpeg): {avg(size_values):.4f} KB\n"
        f"Average FPS (ffmpeg): {avg(fps_values):.4f}\n"
        f"Average Bitrate (ffmpeg): {avg(bit_rate_values):.4f} kbits/s\n"
        f"Average Dropped Frames (ffmpeg): {avg(drop_values):.4f}\n"
        f"Average Speed (ffmpeg): {avg(speed_values):.4f}x\n"
    )

    print(report)
    with open("benchmark_results_flight_computer.txt", "a") as f:
        f.write(report)
    
def benchmark_video_quality(duration=30):
    ffmpeg_record_video_command = [
        "ffmpeg",
        "-f", "v4l2",
        "-framerate", "60",
        "-video_size", "1280x720",
        "-i", "/dev/video0",
        "-c:v", "libx264",
        "-t", f"{duration}",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "reference.mp4"
    ]
    ffmpeg_send_recorded_video_command = [
        "ffmpeg",
        "-re",
        "-i", "reference.mp4",
        "-c:v", "copy",
        "-f", "mpegts",
        "udp://192.168.1.91:5000"
    ]
    print("Recording reference video...")
    subprocess.run(ffmpeg_record_video_command, check=True)
    if not os.path.exists("reference.mp4") or os.path.getsize("reference.mp4") == 0:
        raise RuntimeError("Recording failed — reference.mp4 not found or empty")
    print("Sending recorded video for benchmarking...")
    subprocess.run(ffmpeg_send_recorded_video_command, check=True)
