from collections import deque
import socket
import threading
import json


class TimestampReceiver:
    """Receive JSON timestamps from separate UDP port"""

    def __init__(self, port):
        self.timestamp_queue = deque(maxlen=500)       
        self.port = port
        self.running = False
        self.sock = None
        self._lock = threading.Lock()

    def start_receiving(self):
        """Start background thread to receive timestamps"""
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", self.port))
        self.sock.settimeout(1.0)

        thread = threading.Thread(target=self._receive_loop, daemon=True)
        thread.start()
        print(f"✓ Listening for frame timestamps on port {self.port}")
        return thread

    def _receive_loop(self):
        """Background loop to receive timestamp packets"""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                timestamp_info = json.loads(data.decode("utf-8"))
                with self._lock:
                    self.timestamp_queue.append(timestamp_info)

            except socket.timeout:
                continue
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}")
            except Exception as e:
                if self.running:
                    print(f"Timestamp receive error: {e}")

    def stop_receiving(self):
        """Stop receiving timestamps"""
        self.running = False
        if self.sock:
            self.sock.close()

    def get_timestamp(self, target_frame_number):
        """
        Searches queue for a specific frame number.
        Discards any packets OLDER than the target (flush stale data).
        """
        with self._lock:
            while len(self.timestamp_queue) > 0:
                # Peek at the oldest item
                oldest_item = self.timestamp_queue[0]
                oldest_num = oldest_item['frame_number']

                if oldest_num == target_frame_number:
                    # MATCH FOUND! Remove and return.
                    return self.timestamp_queue.popleft()
                
                elif oldest_num < target_frame_number:
                    # This packet is too old (stale). Trash it and keep looking.
                    self.timestamp_queue.popleft()
                    continue
                
                else:
                    # oldest_num > target_frame_number
                    # The queue only has NEWER data. The packet we want is missing 
                    # (dropped or never arrived).
                    return None
            
            # Queue is empty
            return None
