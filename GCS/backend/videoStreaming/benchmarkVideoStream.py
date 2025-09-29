# benchmark.py
import time
import psutil


class StreamBenchmark:
    def __init__(self):
        self.frame_times = []
        self.dropped_frames = 0
        self.cpu_usages = []
        self.ram_usages = []

    def log_data(self, success: bool):
        now = time.time()
        self.cpu_usages.append(psutil.cpu_percent(interval=None))
        self.ram_usages.append(psutil.virtual_memory().percent)
        if success:
            self.frame_times.append(now)
        else:
            self.dropped_frames += 1

    def report(self):
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

        report = {
            "elapsed_time": elapsed,
            "frames_received": num_frames,
            "dropped_frames": self.dropped_frames,
            "fps": fps,
            "frame_interval_avg": avg_interval,
            "frame_interval_min": min_interval,
            "frame_interval_max": max_interval,
            "mean_cpu_usage": (
                sum(self.cpu_usages) / len(self.cpu_usages)
                if len(self.cpu_usages) > 0
                else 0
            ),
            "mean_ram_usage": (
                sum(self.ram_usages) / len(self.ram_usages)
                if len(self.ram_usages) > 0
                else 0
            ),
        }
        with open("benchmark_results_gcs.txt", "a") as f:
            f.write(report)
        return report
