import subprocess
import sys
import av
import time
import json
import socket
from datetime import datetime
from benchmarking.benchmarkSendingVideoStream import benchmark_ffmpeg
from benchmarking.benchmarkSendingVideoStream import benchmark_video_quality
from fractions import Fraction

VIDEO_INPUT_DEVICE = '/dev/video0'
OUTPUT_URL = 'udp://10.13.122.172:5000'
TIMESTAMP_URL = ('10.13.122.172', 5001)

# Original FFmpeg command for benchmarking
ffmpeg_command = [
    "ffmpeg",
    "-f", "v4l2",
    "-framerate", "60",
    "-video_size", "1280x720",
    "-i", VIDEO_INPUT_DEVICE,
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-tune", "zerolatency",
    "-x264-params", "aud=1:repeat-headers=1",
    "-f", "mpegts",
    OUTPUT_URL
]


class TimestampedVideoSender:
    """Send video with JSON timestamps on separate port"""
    
    def __init__(self, input_device, video_output_url, timestamp_output):
        self.input_device = input_device
        self.video_output_url = video_output_url
        self.timestamp_output = timestamp_output
        self.timestamp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def send_video(self):
        print(f"Starting timestamped video stream...")
        print(f"  Video stream:     {self.video_output_url}")
        print(f"  Timestamp stream: udp://{self.timestamp_output[0]}:{self.timestamp_output[1]}")
        
        # Open input camera
        input_container = av.open(self.input_device, format='v4l2', options={
            'framerate': '60',
            'video_size': '1280x720'
        })
        
        # Open output stream
        output_container = av.open(self.video_output_url, 'w', format='mpegts')
        
        input_stream = input_container.streams.video[0]
        
        # Configure video stream
        video_stream = output_container.add_stream('libx264', rate=60)
        video_stream.width = 1280
        video_stream.height = 720
        video_stream.pix_fmt = 'yuv420p'
        video_stream.options = {
            'preset': 'ultrafast',
            'tune': 'zerolatency',
            'x264-params': 'aud=1:repeat-headers=1'
        }
        
        frame_count = 0
        start_time = time.time()
        
        try:
            for packet in input_container.demux(input_stream):
                for frame in packet.decode():
                    # CRITICAL: Capture wall-clock timestamp immediately
                    capture_time = time.time()
                    
                    # Set video frame PTS
                    frame.pts = frame_count
                    frame.time_base = Fraction(1, 60)
                    
                    # Encode and mux video frame
                    for video_packet in video_stream.encode(frame):
                        output_container.mux(video_packet)
                    
                    # Send JSON timestamp packet
                    timestamp_data = {
                        'frame_number': frame_count,
                        'wall_clock_time': capture_time,
                        'datetime': datetime.fromtimestamp(capture_time).isoformat(),
                        'pts': frame_count,
                        'elapsed_seconds': capture_time - start_time
                    }
                    
                    message = json.dumps(timestamp_data).encode('utf-8')
                    self.timestamp_sock.sendto(message, self.timestamp_output)
                    
                    # Print status every second
                    if frame_count % 60 == 0:
                        dt = datetime.fromtimestamp(capture_time)
                        elapsed = capture_time - start_time
                        print(f"Frame {frame_count:5d} | "
                              f"Time: {dt.strftime('%H:%M:%S.%f')[:-3]} | "
                              f"Elapsed: {elapsed:.2f}s")
                    
                    frame_count += 1
                    
        except KeyboardInterrupt:
            print("\nStreaming stopped by user.")
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
        finally:
            for packet in video_stream.encode():
                output_container.mux(packet)
            
            output_container.close()
            input_container.close()
            self.timestamp_sock.close()
            print(f"Stream ended. Total frames sent: {frame_count}")


def send_video(cmd):
    """Original FFmpeg-based sender (for benchmarking)"""
    print("Starting FFmpeg stream...")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for line in process.stderr:
            print(line, end='')
    except KeyboardInterrupt:
        print("Streaming stopped.")
    finally:
        process.terminate()


def send_video_with_timestamps():
    """Send video with timestamps on separate port"""
    sender = TimestampedVideoSender(VIDEO_INPUT_DEVICE, OUTPUT_URL, TIMESTAMP_URL)
    sender.send_video()


if __name__ == "__main__":
    user_selection = input(
        "Select an option:\n"
        "1: Benchmark FFmpeg Performance\n"
        "2: Benchmark Stream Video Quality\n"
        "3: Send video with timestamps (2 ports)\n"
        "Press Enter to start live video streaming (FFmpeg)\n"
        "Enter your choice: "
    )
    
    if user_selection == '1':
        benchmark_ffmpeg(ffmpeg_command, duration=60)
    elif user_selection == '2':
        benchmark_video_quality(duration=30)
    elif user_selection == '3':
        send_video_with_timestamps()
    else:
        send_video(ffmpeg_command)