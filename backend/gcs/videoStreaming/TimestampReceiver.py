import socket
import threading
import json

class TimestampReceiver:
    """Receive JSON timestamps from separate UDP port"""
    
    def __init__(self, port):
        self.frame_timestamps = {}
        self.frame_number = 0
        self.port = port
        self.running = False
        self.sock = None
    
    def start_receiving(self):
        """Start background thread to receive timestamps"""
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', self.port))
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
                timestamp_info = json.loads(data.decode('utf-8'))
                
                frame_num = timestamp_info['frame_number']
                self.frame_timestamps[frame_num] = timestamp_info
                    
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
    
    def get_timestamp(self, frame_number):
        """Get timestamp for a specific frame number"""
        return self.frame_timestamps.get(frame_number, None)
