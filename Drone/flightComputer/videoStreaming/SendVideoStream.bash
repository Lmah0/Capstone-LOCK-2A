ffmpeg -f v4l2 -framerate 60 -video_size 640x480 -i /dev/video0 \
-c:v libx264 -preset ultrafast -tune zerolatency -f mpegts udp://192.168.1.64:5000

# ffmpeg
# └── Command-line tool itself for streaming video/audio.

# -f v4l2
# └── Specifies the input format as Video4Linux2, which is used for capturing video from USB webcams.

# -framerate 60
# └── Sets the frame rate to 60 frames per second.

# -video_size 640x480 
# └── Sets size of video frames to 640x480 pixels.

# -i /dev/video0
# └── Specifies the input device, which is camera located at /dev/video0.

# -c:v libx264
# └── Specifies to use the H.264 encoder for encoding video.

# -preset ultrafast
# └── Specifices to use the ultrafast preset for the x264 encoder, prioritizing encoding speed.

# -tune zerolatency
# └── Minimizes latency by reducing buffering.

# -f mpegts
# └── Sets the output format to MPEG-TS.

# udp://192.168.1.98:5000
# └── Specifies the output destination as a UDP stream to the IP address.