import sys
import os

# Add directory of this file to sys.path so files importing this can find TimestampReceiver
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import av
import cv2
import time
from datetime import datetime
from TimestampReceiver import TimestampReceiver
from benchmarking.benchmarkReceivingVideoStream import run_quality_metrics
import queue

STREAM_URL = "udp://192.168.1.66:5000"
TIMESTAMP_PORT = 5001

av.logging.set_level(av.logging.PANIC)


def setup_video_stream(url):
    """Opens the stream using PyAV with low-latency flags."""
    print(f"Connecting to video stream: {url}...")
    try:
        container = av.open(
            url,
            options={
                "rtbufsize": "100M",
                "fflags": "nobuffer",
                "flags": "low_delay",
                "probesize": "32",
                "fifo_size": "5000000",
            },
        )
        print("✓ Video stream successfully opened")
        return container
    except Exception as e:
        print(f"Failed to open stream: {e}")
        return None


def yield_frames_with_timestamps(stream_url=STREAM_URL, timestamp_port=TIMESTAMP_PORT):
    """
    Generator that yields frames with timestamps
    Returns: (frame_array, timestamp_info_dict)
    """
    container = None
    timestamp_receiver = None
    timestamp_thread = None
    try:
        container = setup_video_stream(stream_url)

        if not container:
            return
        video_stream = container.streams.video[0]
        video_stream.thread_type = "AUTO"  # Use multiple CPU cores for decoding
        print(f"✓ Video: {video_stream.width}x{video_stream.height}")
        # Start timestamp receiver
        timestamp_receiver = TimestampReceiver(timestamp_port)
        timestamp_thread = timestamp_receiver.start_receiving()

        stream_stabilized = False

        for packet in container.demux(video_stream):
            try:
                for frame in packet.decode():
                    if not stream_stabilized:
                        if frame.key_frame:
                            stream_stabilized = (
                                True  # We found a full picture! Start showing video.
                            )
                        else:
                            continue  # Throw away P-frames until we get a full picture.
                    receive_time = time.time()
                    img = frame.to_ndarray(format="bgr24")
                # 1. Convert to seconds: 21990000 / 90000 = 244.33 seconds
                    timestamp_in_seconds = float(frame.pts * frame.time_base)

                    # 2. Convert to Frame ID: 244.33 * 30 fps = 7330
                    current_frame_id = int(round(timestamp_in_seconds * 30))
                                        
                    # Get timestamp info for this frame based on frame ID from sender
                    timestamp_info = timestamp_receiver.get_timestamp(current_frame_id)
                    if timestamp_info:
                        timestamp_info["receive_time"] = receive_time

                        wall_clock = timestamp_info.get("wall_clock_time")

                        if wall_clock is not None:
                            timestamp_info["latency_ms"] = (
                                receive_time - wall_clock
                            ) * 1000
                        else:
                            timestamp_info["latency_ms"] = None

                    else:
                        timestamp_info = {
                            "frame_number": current_frame_id,
                            "receive_time": receive_time,
                            "wall_clock_time": None,
                            "latency_ms": None,
                        }
                    yield img, timestamp_info

            except av.error.InvalidDataError as e:
                print(f"Skipping corrupted packet: {e}")
                continue

    except Exception as e:
        print(f"Error during video streaming: {e}")
    finally:
        if container:
            container.close()
        if timestamp_receiver:
            timestamp_receiver.stop_receiving()
        if timestamp_thread:
            timestamp_thread.join(timeout=1.0)
        print("Stream resources released.")


def video_telemetry_sync_task(
    stream_url, timestamp_port, sync_manager, frame_queue, stop_event
):
    print(f"Starting sync task on {stream_url}...")
    while not stop_event.is_set():
        try:
            for frame, ts_info in yield_frames_with_timestamps(
                stream_url, timestamp_port
            ):
                if ts_info["wall_clock_time"] is None or frame is None:
                    continue

                success, buffer = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
                )
                if not success:
                    continue

                jpeg_bytes = buffer.tobytes()
                frame_num = ts_info["frame_number"]
                wall_clock = ts_info["wall_clock_time"]

                timestamped_frame = sync_manager.add_frame(
                    frame_num,
                    wall_clock,
                    jpeg_bytes,
                )

                if frame_num % 30 == 0:
                    diff = "N/A"
                    if timestamped_frame.telemetry:
                        diff = f"{timestamped_frame.telemetry.get('sync_time_diff_ms', 0):.2f}ms"
                        print(f"Frame {frame_num}: synced (diff: {diff})")
                    else:
                        print(f"Frame {frame_num}: no telemetry")

                try:
                    while not frame_queue.empty():
                        frame_queue.get_nowait()
                    frame_queue.put(jpeg_bytes, block=False)
                except queue.Full:
                    pass

        except KeyboardInterrupt:
            print("Sync task stopped by user.")
        except Exception as e:
            print(f"Sync task crashed: {e}")


def display_video_stream():
    """Display video stream with timestamp overlay"""
    print("Starting video display with timestamps...")
    print("Press 'q' to quit\n")

    for frame, timestamp_info in yield_frames_with_timestamps():
        frame_display = frame.copy()
        frame_num = timestamp_info["frame_number"]

        # Draw background
        cv2.rectangle(frame_display, (10, 10), (500, 120), (0, 0, 0), -1)
        cv2.rectangle(frame_display, (10, 10), (500, 120), (0, 255, 0), 2)

        # Frame number
        cv2.putText(
            frame_display,
            f"Frame: {frame_num}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

        # Timestamps
        if timestamp_info["wall_clock_time"]:
            capture_dt = datetime.fromtimestamp(timestamp_info["wall_clock_time"])
            cv2.putText(
                frame_display,
                f"Captured: {capture_dt.strftime('%H:%M:%S.%f')[:-3]}",
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

            latency_color = (
                (0, 255, 0) if timestamp_info["latency_ms"] < 100 else (0, 165, 255)
            )
            cv2.putText(
                frame_display,
                f"Latency: {timestamp_info['latency_ms']:.2f}ms",
                (20, 85),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                latency_color,
                2,
            )
        else:
            cv2.putText(
                frame_display,
                "No timestamp data",
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )

        receive_dt = datetime.fromtimestamp(timestamp_info["receive_time"])
        cv2.putText(
            frame_display,
            f"Received: {receive_dt.strftime('%H:%M:%S.%f')[:-3]}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Video Stream with Timestamps", frame_display)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()


def benchmark_video_stream(duration=60):
    """Benchmark video stream with timestamp analysis"""
    from benchmarking.benchmarkReceivingVideoStream import StreamBenchmark

    benchmark = StreamBenchmark()
    stream = yield_frames_with_timestamps()

    print(f"Starting benchmark for {duration}s...\n")

    start_time = time.time()
    latencies = []
    frames_with_timestamps = 0
    total_frames = 0

    try:
        for frame, timestamp_info in stream:
            benchmark.log_stream_data(success=True)
            total_frames += 1

            if timestamp_info["latency_ms"] is not None:
                latencies.append(timestamp_info["latency_ms"])
                frames_with_timestamps += 1

                if total_frames % 60 == 0:
                    avg_latency = sum(latencies) / len(latencies)
                    elapsed = time.time() - start_time
                    print(
                        f"Frame {total_frames:5d} | Elapsed: {elapsed:6.2f}s | "
                        f"Latency: {timestamp_info['latency_ms']:6.2f}ms | "
                        f"Avg: {avg_latency:6.2f}ms"
                    )

            frame_display = frame.copy()
            if timestamp_info["latency_ms"]:
                text = f"Frame {total_frames} | Latency: {timestamp_info['latency_ms']:.1f}ms"
                cv2.putText(
                    frame_display,
                    text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

            cv2.imshow("Benchmarking Stream", frame_display)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Benchmark stopped by user.")
                break

            if time.time() - start_time >= duration:
                print(f"Benchmark completed after {duration}s.")
                break

    except Exception as e:
        print(f"Benchmark interrupted: {e}")
        benchmark.log_stream_data(success=False)
    finally:
        cv2.destroyAllWindows()

    # Print statistics
    print("\n" + "=" * 70)
    print("TIMESTAMP STATISTICS")
    print("=" * 70)
    print(f"Total frames received:           {total_frames}")
    print(f"Frames with timestamps:          {frames_with_timestamps}")

    if total_frames > 0:
        match_rate = (frames_with_timestamps / total_frames) * 100
        print(f"Timestamp match rate:            {match_rate:.1f}%")

    if latencies:
        print(f"\nLATENCY ANALYSIS:")
        print(f"  Average:    {sum(latencies)/len(latencies):.2f}ms")
        print(f"  Minimum:    {min(latencies):.2f}ms")
        print(f"  Maximum:    {max(latencies):.2f}ms")

        avg = sum(latencies) / len(latencies)
        variance = sum((x - avg) ** 2 for x in latencies) / len(latencies)
        jitter = variance**0.5
        print(f"  Jitter:     {jitter:.2f}ms")

    print("=" * 70)

    return benchmark.report_stream_data()


if __name__ == "__main__":
    user_selection = input(
        "Select an option:\n"
        "1: Display Stream with Timestamps\n"
        "2: Benchmark Performance with Latency Analysis\n"
        "3: Benchmark Video Quality\n"
        "Enter your choice: "
    )

    if user_selection == "1":
        display_video_stream()
    elif user_selection == "2":
        print(benchmark_video_stream(30))
    elif user_selection == "3":
        reference_video = "reference.mp4"
        received_video = "received.mp4"

        run_quality_metrics(reference_video, received_video)
    else:
        print("Invalid selection")
