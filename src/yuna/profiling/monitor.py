"""Production-grade performance monitoring system."""

from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass

from yuna.profiling.stats import CountStats, TimingStats


@dataclass
class TimingSample:
    """Single timing measurement."""

    timestamp: float
    duration: float


@dataclass
class CountSample:
    """Single count measurement."""

    timestamp: float
    count: int


class PerformanceMonitor:
    """Production-grade performance profiling monitor.

    Responsibilities:
    - Track timing and count metrics by category
    - Store rolling window of samples (prevents memory growth)
    - Calculate advanced statistics (min/max/avg/p95/p99)
    - Export metrics to JSON
    - Generate formatted console reports
    - Thread-safe collection
    - Zero overhead when disabled

    Usage:
        monitor = PerformanceMonitor(enabled=True, window_size=1000)

        # Timing metrics
        with monitor.sample(category="systems", name="physics"):
            # ... physics code ...
            pass

        # Count metrics
        monitor.record_count(category="entities", name="spawned", count=10)

        # Get statistics
        stats = monitor.get_timing_stats(category="systems", name="physics")
        print(f"Physics p95: {stats.p95_time:.4f}s")

        # Generate report
        monitor.print_report()

        # Export to JSON
        monitor.export_json(path="metrics.json")
    """

    def __init__(self, enabled: bool = True, window_size: int = 1000):
        """Initialize performance monitor.

        Args:
            enabled: Whether monitoring is active (zero overhead when False)
            window_size: Maximum samples to retain per metric
        """
        self._enabled = enabled
        self._window_size = window_size
        self._timing_samples: dict[str, dict[str, deque[TimingSample]]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=window_size))
        )
        self._count_samples: dict[str, dict[str, deque[CountSample]]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=window_size))
        )
        self._lock = threading.Lock()

    @contextmanager
    def sample(self, category: str, name: str) -> Iterator[None]:
        """Context manager for timing code blocks.

        Args:
            category: Metric category for organization
            name: Metric name

        Yields:
            None

        Usage:
            with monitor.sample(category="systems", name="physics"):
                # ... code to profile ...
                pass
        """
        if not self._enabled:
            yield
            return

        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            with self._lock:
                self._timing_samples[category][name].append(
                    TimingSample(timestamp=time.time(), duration=duration)
                )

    def record_count(self, category: str, name: str, count: int) -> None:
        """Record count metric.

        Args:
            category: Metric category
            name: Metric name
            count: Count value
        """
        if not self._enabled:
            return

        with self._lock:
            self._count_samples[category][name].append(
                CountSample(timestamp=time.time(), count=count)
            )

    def get_timing_stats(self, category: str, name: str) -> TimingStats | None:
        """Calculate timing statistics for specific metric.

        Args:
            category: Metric category
            name: Metric name

        Returns:
            Timing statistics, None if metric not found
        """
        with self._lock:
            if category not in self._timing_samples:
                return None
            if name not in self._timing_samples[category]:
                return None

            samples = list(self._timing_samples[category][name])

        if not samples:
            return None

        return self._calculate_timing_stats(samples=samples)

    def get_count_stats(self, category: str, name: str) -> CountStats | None:
        """Calculate count statistics for specific metric.

        Args:
            category: Metric category
            name: Metric name

        Returns:
            Count statistics, None if metric not found
        """
        with self._lock:
            if category not in self._count_samples:
                return None
            if name not in self._count_samples[category]:
                return None

            samples = list(self._count_samples[category][name])

        if not samples:
            return None

        return self._calculate_count_stats(samples=samples)

    def get_categories(self) -> set[str]:
        """Get all metric categories.

        Returns:
            Set of category names
        """
        with self._lock:
            return set(self._timing_samples.keys()) | set(self._count_samples.keys())

    def get_category_stats(self, category: str) -> dict[str, TimingStats | CountStats]:
        """Get all statistics for a category.

        Args:
            category: Metric category

        Returns:
            Dictionary of metric name -> stats
        """
        result: dict[str, TimingStats | CountStats] = {}

        with self._lock:
            if category in self._timing_samples:
                for name, samples in self._timing_samples[category].items():
                    sample_list = list(samples)
                    if sample_list:
                        result[name] = self._calculate_timing_stats(samples=sample_list)

            if category in self._count_samples:
                for name, count_sample_list in self._count_samples[category].items():
                    count_samples = list(count_sample_list)
                    if count_samples:
                        result[name] = self._calculate_count_stats(
                            samples=count_samples
                        )

        return result

    def print_report(self) -> None:
        """Print formatted console report of all metrics."""
        categories = self.get_categories()

        if not categories:
            print("No metrics collected")
            return

        print("=" * 80)
        print("PERFORMANCE REPORT")
        print("=" * 80)

        for category in sorted(categories):
            stats = self.get_category_stats(category=category)
            if not stats:
                continue

            print(f"\n{category.upper()}:")
            print("-" * 80)

            for name, stat in sorted(stats.items()):
                if isinstance(stat, TimingStats):
                    print(
                        f"  {name:30} "
                        f"count={stat.count:6} "
                        f"avg={stat.avg_time * 1000:7.3f}ms "
                        f"p95={stat.p95_time * 1000:7.3f}ms "
                        f"p99={stat.p99_time * 1000:7.3f}ms"
                    )
                elif isinstance(stat, CountStats):
                    print(
                        f"  {name:30} "
                        f"samples={stat.count:6} "
                        f"total={stat.total_count:8} "
                        f"avg={stat.avg_count:7.1f}"
                    )

        print("=" * 80)

    def export_json(self, path: str) -> None:
        """Export metrics to JSON file.

        Args:
            path: Output file path
        """
        categories = self.get_categories()
        data: dict[str, dict[str, dict]] = {}

        for category in categories:
            stats = self.get_category_stats(category=category)
            data[category] = {name: asdict(stat) for name, stat in stats.items()}

        with open(path, mode="w", encoding="utf-8") as file:
            json.dump(obj=data, fp=file, indent=2)

    def reset(self) -> None:
        """Clear all statistics."""
        with self._lock:
            self._timing_samples.clear()
            self._count_samples.clear()

    def reset_category(self, category: str) -> None:
        """Clear statistics for specific category.

        Args:
            category: Category to clear
        """
        with self._lock:
            self._timing_samples.pop(category, None)
            self._count_samples.pop(category, None)

    @staticmethod
    def _calculate_timing_stats(samples: list[TimingSample]) -> TimingStats:
        """Calculate aggregate timing statistics."""
        durations = sorted([sample.duration for sample in samples])
        count = len(durations)

        return TimingStats(
            count=count,
            min_time=durations[0],
            max_time=durations[-1],
            avg_time=sum(durations) / count,
            p95_time=PerformanceMonitor._percentile(values=durations, percentile=0.95),
            p99_time=PerformanceMonitor._percentile(values=durations, percentile=0.99),
        )

    @staticmethod
    def _calculate_count_stats(samples: list[CountSample]) -> CountStats:
        """Calculate aggregate count statistics."""
        counts = [sample.count for sample in samples]
        total = sum(counts)
        count = len(counts)

        return CountStats(
            count=count,
            min_count=min(counts),
            max_count=max(counts),
            avg_count=total / count,
            total_count=total,
        )

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        """Calculate percentile from sorted values.

        Args:
            values: Sorted list of values
            percentile: Percentile to calculate (0.0-1.0)

        Returns:
            Value at the specified percentile
        """
        if not values:
            return 0.0

        index = int(len(values) * percentile)
        if index >= len(values):
            index = len(values) - 1

        return values[index]


_global_monitor: PerformanceMonitor | None = None
_monitor_lock = threading.Lock()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor singleton.

    Returns:
        Global PerformanceMonitor instance
    """
    global _global_monitor
    if _global_monitor is None:
        with _monitor_lock:
            if _global_monitor is None:
                _global_monitor = PerformanceMonitor()
    return _global_monitor


def set_performance_monitor(monitor: PerformanceMonitor) -> None:
    """Install a configured monitor as the global singleton.

    Games install a per-run monitor here so disabled runs pay no sampling
    overhead at the unconditional call sites.

    Args:
        monitor: Monitor instance to install globally
    """
    global _global_monitor
    with _monitor_lock:
        _global_monitor = monitor


def reset_performance_monitor() -> None:
    """Reset global performance monitor (primarily for testing)."""
    global _global_monitor
    with _monitor_lock:
        _global_monitor = None
