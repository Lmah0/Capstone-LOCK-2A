from datetime import datetime
import time
import psutil
import cv2
import subprocess

class StreamBenchmark:
    def __init__(self):
        self.frame_times = []
        self.dropped_frames = 0
        self.cpu_usages = []
        self.ram_usages = []

    def log_stream_data(self, success: bool):
        now = time.time()
        self.cpu_usages.append(psutil.cpu_percent(interval=None))
        self.ram_usages.append(psutil.virtual_memory().percent)
        if success:
            self.frame_times.append(now)
        else:
            self.dropped_frames += 1

    def report_stream_data(self):
        elapsed = (
            self.frame_times[-1] - self.frame_times[0]
            if len(self.frame_times) > 1
            else 0
        )
        num_frames = len(self.frame_times)
        fps = num_frames / elapsed if elapsed > 0 else 0

        intervals = [t2 - t1 for t1, t2 in zip(self.frame_times, self.frame_times[1:])]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        min_interval = min(intervals) if intervals else 0
        max_interval = max(intervals) if intervals else 0

        report = (
            f"\n=== Benchmark run at {datetime.now():%Y-%m-%d %H:%M:%S} ===\n"
            f"elapsed_time: {elapsed}\n"
            f"frames_received: {num_frames:.4f}\n"
            f"dropped_frames: {self.dropped_frames:.4f}\n"
            f"fps: {fps:.4f}\n"
            f"frame_interval_avg: {avg_interval:.4f}\n"
            f"frame_interval_min: {min_interval:.4f}\n"
            f"frame_interval_max: {max_interval:.4f}\n"
            f"mean_cpu_usage: {(sum(self.cpu_usages) / len(self.cpu_usages) if len(self.cpu_usages) > 0 else 0):.4f}\n"
            f"mean_ram_usage: {(sum(self.ram_usages) / len(self.ram_usages) if len(self.ram_usages) > 0 else 0):.4f}\n"
        )

        with open("benchmark_results_gcs.txt", "a") as f:
            f.write(report)
        return report

def receive_and_save_video(cap, output_file, duration):
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 60  

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 'mp4v' works well for MP4
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

    start_time = time.time()
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        out.write(frame)  # save frame to MP4
        cv2.imshow("Pi Stream", frame)  # optional live display

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if time.time() - start_time >= duration:
            break

    out.release()
    cv2.destroyAllWindows()
    print(f"Video saved as {output_file}")

def run_quality_metrics(cap, reference_video, received_video, duration=25):
    print("Receiving and saving video for quality assessment...")
    receive_and_save_video(cap, received_video, duration)
    commands = {
        "psnr": f'ffmpeg -i "{reference_video}" -i "{received_video}" -lavfi "[0:v][1:v]psnr=stats_file=psnr.log" -f null NUL',
        "ssim": f'ffmpeg -i "{reference_video}" -i "{received_video}" -lavfi "[0:v][1:v]ssim=stats_file=ssim.log" -f null NUL',
        "vmaf": f"ffmpeg -i {reference_video} -i {received_video} -lavfi libvmaf='log_path=vmaf.json:log_fmt=json' -f null -"
    }
    for name, cmd in commands.items():
        print(f"\n--- Running {name.upper()} ---")
        subprocess.run(cmd, shell=True)

