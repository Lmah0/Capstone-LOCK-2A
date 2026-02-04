# Drone side code
## videoStreaming
- `SendVideoStream.py` - Python file to send video over UDP to the GCS using GStreamer. Also provides the ability to benchmark video stream.

## Ports in Use
- `Port 5006` - Used to establish connection with flight controller to send commands, receive acks and monitor connection health
- `Port 5005` - Used to receive heartbeat information from MavProxy module
