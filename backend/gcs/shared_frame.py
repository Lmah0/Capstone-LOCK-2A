import numpy as np
from multiprocessing import shared_memory
import threading
import json
import os
import time

FRAME_DTYPE = np.uint8
SHM_NAME = "gcs_video_frame"

_lock = threading.Lock()
_shm = None
_array = None


def create_shared_frame(frame_shape=(1080, 1920, 3)):
    global _shm, _array
    # Remove old shared memory if it exists
    try:
        old_shm = shared_memory.SharedMemory(name=SHM_NAME)
        old_shm.close()
        old_shm.unlink()
    except FileNotFoundError:
        pass  # Already removed, ignore
    except Exception as e:
        print(f"Warning: could not remove old shared memory: {e}")
    
    # Create new shared memory
    size = int(np.prod(frame_shape))
    _shm = shared_memory.SharedMemory(name=SHM_NAME, create=True, size=size)
    _array = np.ndarray(frame_shape, dtype=FRAME_DTYPE, buffer=_shm.buf)
    _array[:] = 0
    print(f"Shared memory created: {SHM_NAME}, size: {size} bytes, shape: {frame_shape}")



def attach_shared_frame():
    """Attach to shared memory, reading shape from metadata"""
    global _shm, _array
    frame_shape = (1080, 1920, 3)
    
    # Attach to existing shared memory
    _shm = shared_memory.SharedMemory(name=SHM_NAME)
    _array = np.ndarray(frame_shape, dtype=FRAME_DTYPE, buffer=_shm.buf)
    
    print(f"Attached to shared memory: {SHM_NAME}, shape: {frame_shape}")


def write_frame(frame: np.ndarray):
    """Write frame to shared memory"""
    global _array
    
    if _array is None:
        return False
    
    with _lock:
        try:
            # Ensure frame matches expected shape
            if frame.shape != _array.shape:
                import cv2
                frame = cv2.resize(frame, (_array.shape[1], _array.shape[0]))
            
            # Ensure 3 channels
            if len(frame.shape) == 2:
                import cv2
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            
            _array[:] = frame
            return True
        except Exception as e:
            print(f"Error writing frame: {e}")
            return False


def read_frame():
    """Read frame from shared memory"""
    global _array
    
    if _array is None:
        return None
    
    with _lock:
        try:
            return _array.copy()
        except Exception as e:
            print(f"Error reading frame: {e}")
            return None


def cleanup():
    """Clean up shared memory"""
    global _shm
    if _shm:
        try:
            _shm.close()
        except Exception as e:
            print(f"Error closing shared memory: {e}")
        
        try:
            _shm.unlink()
        except FileNotFoundError:
            # Already unlinked, safe to ignore
            pass
        except Exception as e:
            print(f"Error unlinking shared memory: {e}")
        finally:
            _shm = None
