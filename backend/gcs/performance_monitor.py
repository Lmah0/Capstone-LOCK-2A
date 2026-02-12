"""
Performance Monitor for GCS Video Processing Pipeline

Tracks timing for each component of the pipeline:
- Video Stream Receiving
- AI Processing (Detection/Tracking)
- Geolocation Calculations
- WebRTC Streaming
- Overall Frame Processing

Usage:
    from performance_monitor import perf_monitor

    with perf_monitor.measure("video_receive"):
        frame = video_receiver.read()

    perf_monitor.print_stats()
"""

import time
import numpy as np
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List
import threading


@dataclass
class ComponentStats:
    """Statistics for a single component"""
    name: str
    times: deque = field(default_factory=lambda: deque(maxlen=100))
    call_count: int = 0
    total_time: float = 0.0

    def add_measurement(self, duration_ms: float):
        """Add a timing measurement"""
        self.times.append(duration_ms)
        self.call_count += 1
        self.total_time += duration_ms

    @property
    def avg_ms(self) -> float:
        """Average time in milliseconds"""
        return np.mean(self.times) if len(self.times) > 0 else 0.0

    @property
    def min_ms(self) -> float:
        """Minimum time in milliseconds"""
        return np.min(self.times) if len(self.times) > 0 else 0.0

    @property
    def max_ms(self) -> float:
        """Maximum time in milliseconds"""
        return np.max(self.times) if len(self.times) > 0 else 0.0

    @property
    def std_ms(self) -> float:
        """Standard deviation in milliseconds"""
        return np.std(self.times) if len(self.times) > 0 else 0.0

    @property
    def p95_ms(self) -> float:
        """95th percentile in milliseconds"""
        return np.percentile(self.times, 95) if len(self.times) > 0 else 0.0

    @property
    def p99_ms(self) -> float:
        """99th percentile in milliseconds"""
        return np.percentile(self.times, 99) if len(self.times) > 0 else 0.0


class PerformanceMonitor:
    """
    Thread-safe performance monitoring for the video processing pipeline.

    Tracks timing for different components and provides detailed statistics.
    """

    def __init__(self, window_size: int = 100):
        self.components: Dict[str, ComponentStats] = defaultdict(
            lambda: ComponentStats(name="")
        )
        self.window_size = window_size
        self.enabled = True
        self.lock = threading.Lock()

        # Frame-level timing
        self.frame_times = deque(maxlen=window_size)
        self.frame_count = 0
        self.last_print_time = time.time()

        # Component hierarchy for visualization
        self.hierarchy = {
            "total_frame": [
                "video_receive",
                "ai_processing",
                "webrtc_write",
                "rate_limiting"
            ],
            "video_receive": [
                "video_decode",
                "video_metadata_parse"
            ],
            "ai_processing": [
                "ai_detection",
                "ai_tracking",
                "ai_geolocation",
                "ai_frame_copy"
            ],
            "ai_detection": [
                "yolo_inference",
                "yolo_boxes_extract",
                "yolo_drawing"
            ],
            "webrtc_write": [
                "webrtc_lock",
                "webrtc_frame_copy"
            ]
        }

    @contextmanager
    def measure(self, component_name: str):
        """
        Context manager to measure timing for a component.

        Usage:
            with perf_monitor.measure("video_receive"):
                frame = video_receiver.read()
        """
        if not self.enabled:
            yield
            return

        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            with self.lock:
                if component_name not in self.components:
                    self.components[component_name] = ComponentStats(name=component_name)
                self.components[component_name].add_measurement(duration_ms)

    def record(self, component_name: str, duration_ms: float):
        """
        Manually record a timing measurement.

        Args:
            component_name: Name of the component
            duration_ms: Duration in milliseconds
        """
        if not self.enabled:
            return

        with self.lock:
            if component_name not in self.components:
                self.components[component_name] = ComponentStats(name=component_name)
            self.components[component_name].add_measurement(duration_ms)

    def record_frame(self, duration_ms: float):
        """Record total frame processing time"""
        with self.lock:
            self.frame_times.append(duration_ms)
            self.frame_count += 1

    def get_fps(self) -> float:
        """Get current FPS"""
        with self.lock:
            if len(self.frame_times) == 0:
                return 0.0
            avg_frame_time = np.mean(self.frame_times)
            return 1000.0 / avg_frame_time if avg_frame_time > 0 else 0.0

    def get_stats(self, component_name: str) -> ComponentStats:
        """Get statistics for a specific component"""
        with self.lock:
            return self.components.get(component_name)

    def get_bottleneck(self) -> tuple:
        """
        Identify the biggest bottleneck in the pipeline.

        Returns:
            Tuple of (component_name, avg_time_ms, percentage_of_frame)
        """
        with self.lock:
            if len(self.frame_times) == 0:
                return ("N/A", 0.0, 0.0)

            avg_frame_time = np.mean(self.frame_times)
            if avg_frame_time == 0:
                return ("N/A", 0.0, 0.0)

            # Find component with highest average time
            max_component = None
            max_time = 0.0

            for name, stats in self.components.items():
                if stats.avg_ms > max_time:
                    max_time = stats.avg_ms
                    max_component = name

            if max_component:
                percentage = (max_time / avg_frame_time) * 100
                return (max_component, max_time, percentage)

            return ("N/A", 0.0, 0.0)

    def print_stats(self, detailed: bool = True):
        """
        Print comprehensive performance statistics.

        Args:
            detailed: If True, print detailed breakdown for each component
        """
        with self.lock:
            if self.frame_count == 0:
                print("\n[Performance Monitor] No data collected yet.")
                return

            # Calculate overall metrics
            avg_frame_time = np.mean(self.frame_times) if len(self.frame_times) > 0 else 0
            fps = 1000.0 / avg_frame_time if avg_frame_time > 0 else 0

            print("\n" + "="*80)
            print(f"PERFORMANCE MONITOR - Frame {self.frame_count}")
            print("="*80)
            print(f"Overall FPS: {fps:.1f} | Avg Frame Time: {avg_frame_time:.2f}ms")
            print(f"Target: 60 FPS (16.67ms per frame)")

            if avg_frame_time > 16.67:
                overhead = avg_frame_time - 16.67
                print(f"⚠️  BEHIND TARGET by {overhead:.2f}ms ({overhead/16.67*100:.1f}%)")
            else:
                headroom = 16.67 - avg_frame_time
                print(f"✅ ON TARGET with {headroom:.2f}ms headroom")

            # Identify bottleneck
            bottleneck_name, bottleneck_time, bottleneck_pct = self.get_bottleneck()
            print(f"\n🔍 BOTTLENECK: {bottleneck_name} ({bottleneck_time:.2f}ms, {bottleneck_pct:.1f}% of frame)")

            if detailed:
                self._print_detailed_breakdown(avg_frame_time)

            print("="*80 + "\n")

    def _print_detailed_breakdown(self, avg_frame_time: float):
        """Print detailed timing breakdown organized by hierarchy"""
        print("\n" + "-"*80)
        print("DETAILED TIMING BREAKDOWN")
        print("-"*80)

        # Print top-level components
        self._print_component_tree("", avg_frame_time, 0)

    def _print_component_tree(self, parent: str, total_time: float, indent: int):
        """Recursively print component tree"""
        components_to_show = []

        if parent == "":
            # Root level - show main components
            components_to_show = self.hierarchy.get("total_frame", [])
        else:
            # Show children of this component
            components_to_show = self.hierarchy.get(parent, [])

        for comp_name in components_to_show:
            stats = self.components.get(comp_name)
            if stats and len(stats.times) > 0:
                pct = (stats.avg_ms / total_time * 100) if total_time > 0 else 0

                # Visual indicator
                if pct > 50:
                    indicator = "🔴"  # Major bottleneck
                elif pct > 25:
                    indicator = "🟡"  # Significant time
                else:
                    indicator = "🟢"  # Minor component

                indent_str = "  " * indent
                tree_char = "├─" if indent > 0 else ""

                print(f"{indent_str}{tree_char} {indicator} {comp_name:30s} "
                      f"{stats.avg_ms:7.2f}ms ({pct:5.1f}%) "
                      f"[min:{stats.min_ms:6.2f} max:{stats.max_ms:6.2f} "
                      f"p95:{stats.p95_ms:6.2f}]")

                # Print children
                self._print_component_tree(comp_name, total_time, indent + 1)

        # Also show any components not in hierarchy
        if parent == "":
            for comp_name, stats in self.components.items():
                if comp_name not in self.hierarchy.get("total_frame", []) and \
                   comp_name not in [c for children in self.hierarchy.values() for c in children]:
                    if len(stats.times) > 0:
                        pct = (stats.avg_ms / total_time * 100) if total_time > 0 else 0
                        print(f"  ⚪ {comp_name:30s} {stats.avg_ms:7.2f}ms ({pct:5.1f}%)")

    def print_summary(self):
        """Print a quick one-line summary"""
        fps = self.get_fps()
        bottleneck_name, bottleneck_time, _ = self.get_bottleneck()
        print(f"[PERF] FPS:{fps:.1f} | Bottleneck:{bottleneck_name}({bottleneck_time:.1f}ms)")

    def reset(self):
        """Reset all statistics"""
        with self.lock:
            self.components.clear()
            self.frame_times.clear()
            self.frame_count = 0
            self.last_print_time = time.time()

    def enable(self):
        """Enable performance monitoring"""
        self.enabled = True

    def disable(self):
        """Disable performance monitoring (zero overhead)"""
        self.enabled = False

    def export_csv(self, filename: str = "performance_log.csv"):
        """Export statistics to CSV file"""
        import csv

        with self.lock:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Component', 'Avg(ms)', 'Min(ms)', 'Max(ms)',
                               'Std(ms)', 'P95(ms)', 'P99(ms)', 'Call Count'])

                for name, stats in sorted(self.components.items()):
                    if len(stats.times) > 0:
                        writer.writerow([
                            name,
                            f"{stats.avg_ms:.2f}",
                            f"{stats.min_ms:.2f}",
                            f"{stats.max_ms:.2f}",
                            f"{stats.std_ms:.2f}",
                            f"{stats.p95_ms:.2f}",
                            f"{stats.p99_ms:.2f}",
                            stats.call_count
                        ])

        print(f"Performance stats exported to {filename}")


# Global singleton instance
perf_monitor = PerformanceMonitor()


# Convenience decorators
def measure_performance(component_name: str):
    """
    Decorator to measure function performance.

    Usage:
        @measure_performance("my_function")
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with perf_monitor.measure(component_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
