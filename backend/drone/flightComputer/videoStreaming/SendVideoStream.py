import subprocess
import sys
import av
import time
import os
import json
import socket
from datetime import datetime
# from .benchmarking.benchmarkSendingVideoStream import benchmark_ffmpeg
# from .benchmarking.benchmarkSendingVideoStream import benchmark_video_quality
from fractions import Fraction
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../../../.env")

VIDEO_INPUT_DEVICE = "/dev/video0"
GCS_VIDEO_IP = "udp://" + os.getenv(
        "GCS_IP", "192.168.") + ":5000"
GCS_TIMESTAMP_IP = (os.getenv(
        "GCS_IP", "192.168."), 5001)
TIMESTAMP_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def setup_video_pipeline():
    """Helper: Handles all the complex PyAV / FFmpeg configuration"""
    # Open input camera
    input_container = av.open(
        VIDEO_INPUT_DEVICE,
        format="v4l2",
        options={
            "framerate": "30",
            "video_size": "1280x720",
            "input_format": "h264",
        },
    )

    # Open output stream
    output_container = av.open(GCS_VIDEO_IP, "w", format="mpegts")
    
    # Configure output stream
    video_stream = output_container.add_stream("libx264", rate=30)
    video_stream.width = 1280
    video_stream.height = 720
    video_stream.pix_fmt = "yuv420p"
    video_stream.options = {
        "preset": "ultrafast",
        "tune": "zerolatency",
        "maxrate": "3M",
        "bufsize": "6M",
        "g": "30",
        "x264-params": "aud=1:repeat-headers=1:slice-max-size=1200",
    }
    
    return input_container, output_container, video_stream

def send_timestamp_packet(frame_count, capture_time, start_time):
    """Helper: Handles purely the JSON packaging and UDP sending"""
    timestamp_data = {
        "frame_number": frame_count,
        "wall_clock_time": capture_time,
        "datetime": datetime.fromtimestamp(capture_time).isoformat(),
        "pts": frame_count,
        "elapsed_seconds": capture_time - start_time,
    }

    try:
        message = json.dumps(timestamp_data).encode("utf-8")
        TIMESTAMP_SOCKET.sendto(message, GCS_TIMESTAMP_IP)
    except Exception as e:
        print(f"Timestamp send error: {e}")

def start_video_streaming(timestamps_enabled=True):
    """The Main Conductor: Orchestrates the loop"""
    print(f"Starting video streaming to {GCS_VIDEO_IP} with timestamps: {timestamps_enabled}")
    
    # Setup video pipeline
    input_container, output_container, video_stream = setup_video_pipeline()
    input_stream = input_container.streams.video[0]

    frame_count = 0
    start_time = time.time()

    try:
        # Send and timestamp packets
        for packet in input_container.demux(input_stream):
            for frame in packet.decode():
                capture_time = time.time() 
                
                # Send Video
                frame.pts = frame_count
                frame.time_base = Fraction(1, 30)
                for video_packet in video_stream.encode(frame):
                    output_container.mux(video_packet)

                # Send Timestamp (Delegated to helper)
                if timestamps_enabled:
                    send_timestamp_packet(frame_count, capture_time, start_time)

                # Logging
                if frame_count % 30 == 0:
                    elapsed = capture_time - start_time
                    print(f"Frame {frame_count} | Elapsed: {elapsed:.2f}s")

                frame_count += 1

    except KeyboardInterrupt:
        print("\nStreaming stopped by user.")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup Phase
        if output_container:
            for packet in video_stream.encode():
                output_container.mux(packet)
            output_container.close()
        
        if input_container:
            input_container.close()
            
        TIMESTAMP_SOCKET.close()



if __name__ == "__main__":
    user_selection = input(
        "Select an option:\n"
        "1: Benchmark FFmpeg Performance\n"
        "2: Benchmark Stream Video Quality\n"
        "3: Stream Video Only\n"
        "Press Enter to send video with timestamps (2 ports)\n"
        "Enter your choice: "
    )

    if user_selection == "1":
        # benchmark_ffmpeg(setup_video_pipeline(), duration=60)
        pass
    elif user_selection == "2":
        # benchmark_video_quality(duration=30)
        pass
    elif user_selection == "3":
        start_video_streaming(timestamps_enabled=False)
    else:
        start_video_streaming(timestamps_enabled=True)
