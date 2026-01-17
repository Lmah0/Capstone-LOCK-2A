import av
import cv2
import time
from datetime import datetime
import TimestampReceiver
import traceback
import queue

STREAM_URL = 'udp://10.13.20.180:5000'
TIMESTAMP_PORT = 5001


# class TimestampReceiver:
#     """Receive JSON timestamps from separate UDP port"""
    
#     def __init__(self, port):
#         self.frame_timestamps = {}
#         self.frame_number = 0
#         self.port = port
#         self.running = False
#         self.sock = None
    
#     def start_receiving(self):
#         """Start background thread to receive timestamps"""
#         self.running = True
#         self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         self.sock.bind(('0.0.0.0', self.port))
#         self.sock.settimeout(1.0)
        
#         thread = threading.Thread(target=self._receive_loop, daemon=True)
#         thread.start()
#         print(f"✓ Listening for timestamps on port {self.port}")
#         return thread
    
#     def _receive_loop(self):
#         """Background loop to receive timestamp packets"""
#         while self.running:
#             try:
#                 data, addr = self.sock.recvfrom(4096)
#                 timestamp_info = json.loads(data.decode('utf-8'))
                
#                 frame_num = timestamp_info['frame_number']
#                 self.frame_number = frame_num
#                 self.frame_timestamps[frame_num] = timestamp_info
                    
#             except socket.timeout:
#                 continue
#             except json.JSONDecodeError as e:
#                 print(f"Invalid JSON: {e}")
#             except Exception as e:
#                 if self.running:
#                     print(f"Timestamp receive error: {e}")
    
#     def stop_receiving(self):
#         """Stop receiving timestamps"""
#         self.running = False
#         if self.sock:
#             self.sock.close()
    
#     def get_timestamp(self, frame_number):
#         """Get timestamp for a specific frame number"""
#         return self.frame_timestamps.get(frame_number, None)


def setup_video_stream(url):
    """Opens the stream using PyAV with low-latency flags."""
    print(f"Connecting to video stream: {url}...")
    try:
        container = av.open(
            url, 
            options={
                'rtbufsize': '100M',
                'fflags': 'nobuffer', 
                'flags': 'low_delay',
                'timeout': '10000000'
            }
        )
        print("✓ Video stream successfully opened")
        return container
    except Exception as e:
        print(f"Failed to open stream: {e}")
        return None


def return_video_stream():
    """
    Generator that yields frames with timestamps
    Returns: (frame_array, timestamp_info_dict)
    """
    container = setup_video_stream(STREAM_URL)
    
    if not container:
        return
    
    # Start timestamp receiver
    timestamp_receiver = TimestampReceiver(TIMESTAMP_PORT)
    timestamp_thread = timestamp_receiver.start_receiving()
    
    video_stream = None
    
    for stream in container.streams:
        if stream.type == 'video':
            video_stream = stream
            print(f"✓ Video: {stream.width}x{stream.height} @ {stream.average_rate} fps")
            break
    
    if not video_stream:
        print("Error: No video stream found!")
        container.close()
        timestamp_receiver.stop_receiving()
        return
    
    try:
        for packet in container.demux(video_stream):
            try:
                for frame in packet.decode():
                    receive_time = time.time()
                    img = frame.to_ndarray(format='bgr24')
                    
                    # Get timestamp info for this frame
                    timestamp_info = timestamp_receiver.get_timestamp(timestamp_receiver.frame_number)
                    
                    if timestamp_info:
                        timestamp_info['receive_time'] = receive_time
                        timestamp_info['latency_ms'] = (receive_time - timestamp_info['wall_clock_time']) * 1000
                    else:
                        timestamp_info = {
                            'frame_number': timestamp_receiver.frame_number,
                            'receive_time': receive_time,
                            'wall_clock_time': None,
                            'latency_ms': None
                        }
                    print("TIMESTAMP INFO FOR FRAME", timestamp_info["frame_number"])
                    yield img, timestamp_info
                    
            except av.error.InvalidDataError as e:
                print(f"Skipping corrupted packet: {e}")
                continue
                
    except Exception as e:
        print(f"Error during video streaming: {e}")
    finally:
        container.close()
        timestamp_receiver.stop_receiving()
        timestamp_thread.join(timeout=2)

def video_receiver_sync_task(stream_url, timestamp_port, sync_manager, frame_queue):
    """
    Background task to receive video with timestamps and sync with telemetry.
    
    Args:
        stream_url (str): The UDP URL for the video stream.
        timestamp_port (int): The UDP port for the timestamp stream.
        sync_manager (FrameTelemetrySynchronizer): The object handling data alignment.
        frame_queue (queue.Queue): The output queue for MJPEG streaming/AI.
    """
    print(f"Starting video receiver on {stream_url} with sync port {timestamp_port}...")
    
    # Initialize timestamp receiver
    timestamp_receiver = TimestampReceiver(timestamp_port)
    timestamp_thread = timestamp_receiver.start_receiving()
    
    # Open video stream
    container = None
    try:
        container = av.open(stream_url, options={
            'rtbufsize': '100M',
            'fflags': 'nobuffer',
            'flags': 'low_delay',
            'timeout': '10000000'
        })
        print("✓ Video stream opened successfully")
    except Exception as e:
        print(f"Failed to open video stream: {e}")
        timestamp_receiver.stop_receiving()
        return
    
    # Get video stream
    video_stream = next((s for s in container.streams if s.type == 'video'), None)
    
    if not video_stream:
        print("Error: No video stream found!")
        container.close()
        timestamp_receiver.stop_receiving()
        return

    print(f"✓ Video: {video_stream.width}x{video_stream.height} @ {video_stream.average_rate} fps")
    
    try:
        for packet in container.demux(video_stream):
            try:
                for frame in packet.decode():
                    receive_time = time.time()
                    
                    # Get timestamp info for this frame
                    # Note: You might need to adjust this depending on if you implemented 
                    # the Queue approach or the Dictionary approach in TimestampReceiver
                    timestamp_info = timestamp_receiver.get_timestamp(timestamp_receiver.frame_number)
                    
                    if timestamp_info:
                        wall_clock_time = timestamp_info.get('wall_clock_time')
                        timestamp_info['receive_time'] = receive_time
                        timestamp_info['latency_ms'] = (receive_time - wall_clock_time) * 1000
                        
                        # Convert frame to JPEG
                        img = frame.to_ndarray(format='bgr24')
                        success, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        
                        if success:
                            jpeg_bytes = buffer.tobytes()
                            
                            # Add to synchronizer with telemetry matching
                            timestamped_frame = sync_manager.add_frame(
                                timestamp_receiver.frame_number,
                                wall_clock_time,
                                jpeg_bytes
                            )
                            
                            # Log sync status occasionally
                            if timestamp_receiver.frame_number % 60 == 0:
                                if timestamped_frame.telemetry:
                                    sync_diff = timestamped_frame.telemetry.get('sync_time_diff_ms', 'N/A')
                                    print(f"Frame {timestamp_receiver.frame_number}: synced (diff: {sync_diff:.2f}ms)")
                                else:
                                    print(f"Frame {timestamp_receiver.frame_number}: no matching telemetry")
                            
                            # Put frame in queue for AI processor and MJPEG streaming
                            try:
                                # Clear old frames if queue is full to prevent lag
                                while not frame_queue.empty():
                                    frame_queue.get_nowait()
                                frame_queue.put(jpeg_bytes, block=False)
                            except queue.Full:
                                pass
                    
                    frame_count += 1
                    
            except av.error.InvalidDataError as e:
                # Common in UDP streams, just skip
                continue
                
    except KeyboardInterrupt:
        print("Video receiver stopped")
    except Exception as e:
        print(f"Error in video receiver: {e}")
        traceback.print_exc()
    finally:
        if container:
            container.close()
        timestamp_receiver.stop_receiving()
        timestamp_thread.join(timeout=2)
        print("Video receiver task ended")

def display_video_stream():
    """Display video stream with timestamp overlay"""
    print("Starting video display with timestamps...")
    print("Press 'q' to quit\n")
    
    for frame, timestamp_info in return_video_stream():
        frame_display = frame.copy()
        frame_num = timestamp_info['frame_number']
        
        # Draw background
        cv2.rectangle(frame_display, (10, 10), (500, 120), (0, 0, 0), -1)
        cv2.rectangle(frame_display, (10, 10), (500, 120), (0, 255, 0), 2)
        
        # Frame number
        cv2.putText(frame_display, f"Frame: {frame_num}", 
                   (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Timestamps
        if timestamp_info['wall_clock_time']:
            capture_dt = datetime.fromtimestamp(timestamp_info['wall_clock_time'])
            cv2.putText(frame_display, f"Captured: {capture_dt.strftime('%H:%M:%S.%f')[:-3]}", 
                       (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            latency_color = (0, 255, 0) if timestamp_info['latency_ms'] < 100 else (0, 165, 255)
            cv2.putText(frame_display, f"Latency: {timestamp_info['latency_ms']:.2f}ms", 
                       (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, latency_color, 2)
        else:
            cv2.putText(frame_display, "No timestamp data", 
                       (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        receive_dt = datetime.fromtimestamp(timestamp_info['receive_time'])
        cv2.putText(frame_display, f"Received: {receive_dt.strftime('%H:%M:%S.%f')[:-3]}", 
                   (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow("Video Stream with Timestamps", frame_display)
        
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    cv2.destroyAllWindows()


def benchmark_video_stream(duration=60):
    """Benchmark video stream with timestamp analysis"""
    from benchmarking.benchmarkReceivingVideoStream import StreamBenchmark
    
    benchmark = StreamBenchmark()
    stream = return_video_stream()
    
    print(f"Starting benchmark for {duration}s...\n")
    
    start_time = time.time()
    latencies = []
    frames_with_timestamps = 0
    total_frames = 0
    
    try:
        for frame, timestamp_info in stream:
            benchmark.log_stream_data(success=True)
            total_frames += 1
            
            if timestamp_info['latency_ms'] is not None:
                latencies.append(timestamp_info['latency_ms'])
                frames_with_timestamps += 1
                
                if total_frames % 60 == 0:
                    avg_latency = sum(latencies) / len(latencies)
                    elapsed = time.time() - start_time
                    print(f"Frame {total_frames:5d} | Elapsed: {elapsed:6.2f}s | "
                          f"Latency: {timestamp_info['latency_ms']:6.2f}ms | "
                          f"Avg: {avg_latency:6.2f}ms")
            
            frame_display = frame.copy()
            if timestamp_info['latency_ms']:
                text = f"Frame {total_frames} | Latency: {timestamp_info['latency_ms']:.1f}ms"
                cv2.putText(frame_display, text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Benchmarking Stream", frame_display)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
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
    print("\n" + "="*70)
    print("TIMESTAMP STATISTICS")
    print("="*70)
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
        jitter = variance ** 0.5
        print(f"  Jitter:     {jitter:.2f}ms")
    
    print("="*70)
    
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
        from benchmarking.benchmarkReceivingVideoStream import run_quality_metrics
        run_quality_metrics(reference_video, received_video)
    else:
        print("Invalid selection")