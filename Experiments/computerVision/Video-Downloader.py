import subprocess
import sys
import os

# ------------------------------
# 1. Ensure Dependencies Exist
# ------------------------------
def ensure_package(package_name):
    """Ensures a pip package is installed."""
    try:
        __import__(package_name.split('[')[0])
    except ImportError:
        print(f"Installing {package_name} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

# Make sure yt-dlp and opencv-contrib-python are installed
ensure_package("yt-dlp")
ensure_package("opencv-contrib-python")

# ------------------------------
# 2. Download YouTube Video
# ------------------------------
YT_URL = "https://www.youtube.com/watch?v=XVO9CS8D4hQ"  # 👈 replace with any short video
OUTPUT_FILE = "test_video.mp4"

if not os.path.exists(OUTPUT_FILE):
    print("Downloading YouTube video...")
    subprocess.check_call([
        sys.executable, "-m", "yt_dlp",
        "-f", "mp4",
        "-o", OUTPUT_FILE,
        YT_URL
    ])
else:
    print("Video already downloaded ✅")