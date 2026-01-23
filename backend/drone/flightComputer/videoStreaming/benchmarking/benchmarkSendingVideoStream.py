import cmd
from fractions import Fraction
import subprocess
import time
import psutil
import datetime
import os
import re

def benchmark_ffmpeg(pipeline_tuple, duration=60):
    print("Benchmarking, Starting FFmpeg stream...")
    input_container, output_container, video_stream = pipeline_tuple
    input_stream = input_container.streams.video[0]
    print(f"Benchmarking Open Streams for {duration} seconds...")
    
    process = psutil.Process(os.getpid())
    start_time = time.time()
    cpu_usage, mem_usage = [], []
    fps_values, bitrate_values = [], []
    frame_count = 0
    total_bytes_encoded = 0
    speed_values = []
    frame_count = 0
    total_bytes_encoded = 0
    last_measure_time = start_time
    try:
        # Processing Loop
        for packet in input_container.demux(input_stream):
            
            # Check duration
            current_time = time.time()
            elapsed_total = current_time - start_time
            if elapsed_total > duration:
                break
            
            #Decode and timestamp frames
            for frame in packet.decode():
                frame.pts = frame_count
                frame.time_base = Fraction(1, 30)
                
                # Encode and Mux
                bytes_this_frame = 0
                for video_packet in video_stream.encode(frame):
                    output_container.mux(video_packet)
                    bytes_this_frame += video_packet.size
                
                total_bytes_encoded += bytes_this_frame
                frame_count += 1
                
                # Periodic Metrics (Every ~1 second)
                if current_time - last_measure_time >= 1.0:
                    # CPU & Memory
                    cpu = process.cpu_percent(interval=None)
                    mem = process.memory_info().rss / (1024 * 1024) # MB
                    
                    # FPS = total_frames / total_seconds
                    current_fps = frame_count / elapsed_total
                    # Bitrate (kbps) = total_bits / total_seconds / 1000
                    current_bitrate = (total_bytes_encoded * 8) / elapsed_total / 1000
                    # Speed = Current FPS / Target FPS (30)
                    current_speed = current_fps / 30.0
                    
                    # Store values
                    cpu_usage.append(cpu)
                    mem_usage.append(mem)
                    fps_values.append(current_fps)
                    bitrate_values.append(current_bitrate)
                    speed_values.append(current_speed)
                    
                    # Live Print 
                    print(f"\rFPS: {current_fps:.2f} | Bitrate: {current_bitrate:.0f}k | Size: {total_bytes_encoded/1024:.0f}KB | Speed: {current_speed:.2f}x", end="")
                    
                    last_measure_time = current_time

    except KeyboardInterrupt:
        print("\nBenchmark stopped manually.")
    except Exception as e:
        print(f"\nError during benchmark: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if output_container and video_stream:
            for packet in video_stream.encode():
                output_container.mux(packet)
            output_container.close()
        
        if input_container:
            input_container.close()

    # Generate Report
    avg = lambda vals: sum(vals) / len(vals) if vals else 0
    
    report = (
        f"\n\n=== PyAV Benchmark run at {datetime.datetime.now():%Y-%m-%d %H:%M:%S} ===\n"
        f"Duration: {duration}s\n"
        f"Average CPU usage: {avg(cpu_usage):.4f}%\n"
        f"Average Memory usage: {avg(mem_usage):.4f} MB\n"
        f"Total Size: {total_bytes_encoded / 1024:.4f} KB\n"
        f"Average FPS: {avg(fps_values):.4f}\n"
        f"Average Bitrate: {avg(bitrate_values):.4f} kbits/s\n"
        f"Average Speed: {avg(speed_values):.4f}x\n"
    )

    print(report)
    with open("benchmark_results_flight_computer.txt", "a") as f:
        f.write(report)
    
def benchmark_video_quality(duration=30):
    ffmpeg_record_video_command = [
        "ffmpeg",
        "-f",
        "v4l2",
        "-framerate",
        "60",
        "-video_size",
        "1280x720",
        "-i",
        "/dev/video0",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-tune",
        "zerolatency",
        "-x264-params",
        "aud=1:repeat-headers=1",
        "-f",
        "mpegts",
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
