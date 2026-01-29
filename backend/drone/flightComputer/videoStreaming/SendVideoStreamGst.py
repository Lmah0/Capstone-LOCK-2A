from datetime import datetime
import os
import random
import sys
import time
import struct

import psutil
import gi
import json

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

# --- Global Metrics State (Used by GStreamer callbacks) ---
metrics = {"packet_count": 0, "total_bytes": 0, "start_time": 0}

# --- Configuration ---
VIDEO_INPUT_DEVICE = "/dev/video0"
GCS_IP = "192.168.1.82"
GCS_PORT = 5000
FPS = 60


def build_pipeline_string():
    """
    Constructs the GStreamer pipeline string.
    Maps your previous PyAV/x264 settings to GStreamer elements.
    """
    return (
        # ---Define Video Output ---
        f"mpegtsmux name=mux alignment=7 ! "  # MPEG-TS with KLV alignment
        f"udpsink host={GCS_IP} port={GCS_PORT} sync=false "  # Send to GCS IP using UDP
        # --- Define Video Source ---
        f"v4l2src device={VIDEO_INPUT_DEVICE} ! "  # Get video from dev/video0
        f"video/x-raw,width=1280,height=720,framerate={FPS}/1 ! "  # Set resolution & framerate
        "videoconvert ! "  # Ensure format compatibility with encoder
        # --- Define Encoder ---
        "x264enc "  # Use H.264 Encoder
        "tune=zerolatency "  # Disables buffering for low latency
        "speed-preset=ultrafast "  # Prioritize speed over compression and quality
        "bitrate=3000 "  # Set target bandwidth to 3000 kbps
        "key-int-max=30 "  # Send keyframe every 60 frames
        "aud=true ! "  # Insert "Access Unit Delimiters" (helps the player find frame boundaries).
        "mux. "
        # Define KLV Metadata Stream --
        "appsrc name=klv_src format=time is-live=true do-timestamp=true "  # Create empty input pipe to write binary data to
        'caps="meta/x-klv, parsed=true, sparse=true" ! mux.'  # Define metadata format as KLV for muxer
    )


def start_video_streaming(telemetry_callback=None):
    print(f"Starting GStreamer broadcast to {GCS_IP}:{GCS_PORT}...")

    # Init GStreamer
    Gst.init(None)
    pipeline_str = build_pipeline_string()
    pipeline = Gst.parse_launch(pipeline_str)

    # Get the handle to inject KLV data
    klv_src = pipeline.get_by_name("klv_src")
    if not klv_src:
        print("Error: Could not find 'klv_src' in pipeline")
        sys.exit(1)

    # Start GStreamer Pipeline and start sending video
    pipeline.set_state(Gst.State.PLAYING)

    frame_count = 0
    start_time = time.time()

    frame_target_duration = 1.0 / FPS

    try:
        while True:
            loop_start = time.time()

            # --- KLV Packet ---
            capture_time = time.time()
            elapsed = capture_time - start_time

            telemetry_data = {}
            if telemetry_callback:
                try:
                    telemetry_data = telemetry_callback()
                except Exception as e:
                    print(f"Callback error: {e}")

            klv_data = {
                "frame_number": frame_count,
                "timestamp": capture_time,
            }
            klv_data.update(telemetry_data)

            # Encode JSON
            data_bytes = json.dumps(klv_data).encode("utf-8")

            # Wrap data in GStreamer Buffer
            gst_buffer = Gst.Buffer.new_allocate(None, len(data_bytes), None)
            gst_buffer.fill(0, data_bytes)

            # Synchronization (Critical!)
            # Set the PTS (Presentation Time Stamp) allows the receiver to align  packets with the video frames
            current_pipeline_time = Gst.util_get_timestamp() - pipeline.get_base_time()
            gst_buffer.pts = current_pipeline_time
            gst_buffer.duration = Gst.util_uint64_scale_int(1, Gst.SECOND, FPS)

            # Push buffer with metadata to Pipeline
            retval = klv_src.emit("push-buffer", gst_buffer)
            if retval != Gst.FlowReturn.OK:
                print(f"Error pushing data: {retval}")
                break

            # Logging (Every 60 frames / 1 second)
            if frame_count % 60 == 0:
                print(f"Frame {frame_count} | Elapsed: {elapsed:.2f}s | Streaming OK")

            frame_count += 1

            # Precise loop timing to maintain ~60Hz
            processing_time = time.time() - loop_start
            sleep_time = max(0, frame_target_duration - processing_time)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nStreaming stopped by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Shutting down pipeline...")
        pipeline.set_state(Gst.State.NULL)


def monitor_probe(pad, info, user_data):
    """
    Callback function that runs for EVERY packet leaving the device.
    We use this to count actual bytes sent to the network.
    """
    global metrics
    buffer = info.get_buffer()
    if buffer:
        # Update counters
        metrics["total_bytes"] += buffer.get_size()
        metrics["packet_count"] += 1

    return Gst.PadProbeReturn.OK


def benchmark_gstreamer(duration=60):
    """
    Runs the GStreamer pipeline and measures performance.
    """
    print(f"\n=== Starting GStreamer Benchmark for {duration} seconds ===\n")

    # Setup GStreamer
    Gst.init(None)
    pipeline_str = build_pipeline_string()
    pipeline = Gst.parse_launch(pipeline_str)

    # Attach Probe to measure data flow (The Speedometer)
    monitor = pipeline.get_by_name("monitor")
    sink_pad = monitor.get_static_pad("src")
    sink_pad.add_probe(Gst.PadProbeType.BUFFER, monitor_probe, None)

    # Setup Metadata Source
    klv_src = pipeline.get_by_name("klv_src")

    # Start Pipeline
    pipeline.set_state(Gst.State.PLAYING)

    # Initialize Metrics
    process = psutil.Process(os.getpid())
    metrics["start_time"] = time.time()
    metrics["packet_count"] = 0
    metrics["total_bytes"] = 0

    cpu_usage = []
    mem_usage = []
    bitrate_values = []

    last_measure_time = metrics["start_time"]
    last_bytes = 0

    # Calculate exact sleep time to simulate 60Hz metadata injection
    frame_target_duration = 1.0 / FPS

    try:
        while True:
            loop_start = time.time()
            elapsed_total = loop_start - metrics["start_time"]

            # --- Stop Condition ---
            if elapsed_total > duration:
                break

            # --- Inject Dummy Metadata (Required to keep pipeline healthy) ---
            # Even though this is a benchmark, we must feed the 'appsrc' or it might stall
            data = json.dumps({"ts": loop_start}).encode("utf-8")
            buf = Gst.Buffer.new_allocate(None, len(data), None)
            buf.fill(0, data)
            # Use pipeline time for PTS
            buf.pts = Gst.util_get_timestamp() - pipeline.get_base_time()
            buf.duration = Gst.util_uint64_scale_int(1, Gst.SECOND, FPS)
            klv_src.emit("push-buffer", buf)

            # --- Measure System Stats (Every 1 second) ---
            if loop_start - last_measure_time >= 1.0:
                # CPU & Mem
                cpu = process.cpu_percent(interval=None)
                mem = process.memory_info().rss / (1024 * 1024)  # MB

                # Bitrate Calculation (Bytes since last check * 8 / time_diff)
                bytes_diff = metrics["total_bytes"] - last_bytes
                time_diff = loop_start - last_measure_time
                current_bitrate_kbps = (bytes_diff * 8) / time_diff / 1000

                # Store
                cpu_usage.append(cpu)
                mem_usage.append(mem)
                bitrate_values.append(current_bitrate_kbps)

                # Print Live Stats
                print(
                    f"\rTime: {elapsed_total:.0f}s | CPU: {cpu:.1f}% | Mem: {mem:.1f}MB | Bitrate: {current_bitrate_kbps:.0f} kbps",
                    end="",
                )

                # Reset tick counters
                last_measure_time = loop_start
                last_bytes = metrics["total_bytes"]

            # --- Precision Timing ---
            processing_time = time.time() - loop_start
            sleep_time = max(0, frame_target_duration - processing_time)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nBenchmark stopped manually.")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        pipeline.set_state(Gst.State.NULL)

    # --- Generate Report ---
    avg = lambda v: sum(v) / len(v) if v else 0

    report = (
        f"\n\n=== GStreamer Benchmark Report ===\n"
        f"Date: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"Duration: {duration}s\n"
        f"Avg CPU Usage: {avg(cpu_usage):.2f}%\n"
        f"Avg Memory Usage: {avg(mem_usage):.2f} MB\n"
        f"Avg Bitrate: {avg(bitrate_values):.0f} kbps\n"
        f"Total Data Sent: {metrics['total_bytes']/1024/1024:.2f} MB\n"
    )

    print(report)
    with open("benchmark_results_gstreamer.txt", "a") as f:
        f.write(report)


# --- Functions for benchmarking video quality ---
def generate_reference_video(duration=30, filename="reference.mp4"):
    """
    Records a high-quality raw video from the camera to use as Ground Truth.
    """
    print(f"Recording {duration}s reference video to '{filename}'...")

    # High bitrate (10Mbps) to ensure the reference is clean
    pipeline_str = (
        f"v4l2src device={VIDEO_INPUT_DEVICE} num-buffers={duration*FPS} ! "
        f"video/x-raw,width=1280,height=720,framerate={FPS}/1 ! "
        "videoconvert ! "
        "x264enc speed-preset=superfast bitrate=10000 ! "  # High Quality
        "mp4mux ! "
        f"filesink location={filename}"
    )

    pipeline = Gst.parse_launch(pipeline_str)
    pipeline.set_state(Gst.State.PLAYING)

    # Wait for completion
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(
        Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS | Gst.MessageType.ERROR
    )

    pipeline.set_state(Gst.State.NULL)
    print("✓ Reference recording complete.")


def stream_reference_file(filename="reference.mp4"):
    """
    Reads the reference file and streams it to the Laptop
    using the EXACT same compression settings as your real flight code.
    """
    print(f"Streaming '{filename}' to {GCS_IP}:{GCS_PORT} for analysis...")

    # 1. Read File -> 2. Decode -> 3. Re-Encode (Flight Settings) -> 4. Send
    pipeline_str = (
        f"filesrc location={filename} ! "
        "qtdemux ! h264parse ! avdec_h264 ! "  # Decode reference
        "videoconvert ! "
        # --- FLIGHT SETTINGS (Must match start_video_streaming) ---
        "x264enc tune=zerolatency speed-preset=ultrafast bitrate=3000 key-int-max=60 aud=true ! "
        "mpegtsmux alignment=7 ! "
        f"udpsink host={GCS_IP} port={GCS_PORT} sync=true"  # sync=true important for file playback!
    )

    pipeline = Gst.parse_launch(pipeline_str)
    pipeline.set_state(Gst.State.PLAYING)

    # Wait for file to finish
    bus = pipeline.get_bus()
    bus.timed_pop_filtered(
        Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS | Gst.MessageType.ERROR
    )

    pipeline.set_state(Gst.State.NULL)
    print("✓ Streaming complete.")


def get_mock_telemetry():
    """Simulates a drone flying in a circle."""
    return {
        "timestamp": datetime.datetime.now().timestamp(),
        "latitude": random.uniform(40.7123, 60.7133),
        "longitude": random.uniform(-74.0065, -60.0055),
        "altitude": random.uniform(145.0, 155.0),
        "speed": random.uniform(20.0, 30.0),
        "heading": random.randint(0, 360),
        "roll": random.uniform(-5.0, 5.0),
        "pitch": random.uniform(-5.0, 5.0),
        "yaw": random.uniform(-5.0, 5.0),
        "battery_remaining": random.uniform(30.0, 100.0),
        "battery_voltage": random.uniform(10.1, 80.6),
    }


if __name__ == "__main__":
    user_input = input(
        "Enter '1' to run benchmark or anything else to start streaming: "
    )

    if user_input == "1":
        benchmark_gstreamer()
    else:
        start_video_streaming(telemetry_callback=get_mock_telemetry)
