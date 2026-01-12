import subprocess
import sys
from benchmarking.benchmarkSendingVideoStream import benchmark_ffmpeg
from benchmarking.benchmarkSendingVideoStream import benchmark_video_quality

VIDEO_INPUT_DEVICE = '/dev/video0'
OUTPUT_URL = 'udp://10.13.121.44:5000'

ffmpeg_command = [
    "ffmpeg",   # Command-line tool for streaming video/audio.
    "-f", "v4l2", # Specifies the input format.
    "-framerate", "60", # Sets the frame rate.
    "-video_size", "1280x720", # Sets size of video frames.
    "-i", VIDEO_INPUT_DEVICE, # Specifies the input device.
    "-c:v", "libx264", # Specifies encoder to use.
    "-preset", "ultrafast", # Specifies whether to prioritize speed or compression efficiency.
    "-tune", "zerolatency", # Specifies tuning of encoder.
    "-f", "mpegts", # Sets the output format to MPEG-TS.
    OUTPUT_URL # Specifies the output destination as a UDP stream to the IP address. Modify based on GCS.
]

def send_video(cmd):
    print("Starting FFmpeg stream...")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for line in process.stderr:
            print(line, end='')
    except KeyboardInterrupt:
        print("Streaming stopped.")
    finally:
        process.terminate()

if __name__ == "__main__":
    user_selection = input(
        "Select an option:\n"
        "1: Benchmark FFmpeg Performance\n"
        "2: Benchmark Stream Video Quality\n"
        "Press Enter to start live video streaming\n"
        "Enter your choice: "
    )    
    if user_selection == '1':
        benchmark_ffmpeg(ffmpeg_command, duration=60)
    elif user_selection == '2':
        benchmark_video_quality(duration=30)
    else:
        send_video(ffmpeg_command)