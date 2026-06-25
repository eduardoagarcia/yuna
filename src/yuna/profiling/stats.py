"""Performance profiling statistics."""

from dataclasses import dataclass


@dataclass
class TimingStats:
    """Aggregate timing statistics with percentiles.

    Tracks comprehensive timing statistics for performance analysis.

    Attributes:
        count: Number of samples recorded
        min_time: Minimum sample duration (seconds)
        max_time: Maximum sample duration (seconds)
        avg_time: Average sample duration (seconds)
        p95_time: 95th percentile duration (seconds)
        p99_time: 99th percentile duration (seconds)

    Usage:
        stats = TimingStats(
            count=100,
            min_time=0.001,
            max_time=0.010,
            avg_time=0.005,
            p95_time=0.008,
            p99_time=0.009,
        )
        print(f"p95: {stats.p95_time:.4f}s")
    """

    count: int
    min_time: float
    max_time: float
    avg_time: float
    p95_time: float
    p99_time: float


@dataclass
class CountStats:
    """Aggregate count statistics.

    Tracks statistics for count-based metrics.

    Attributes:
        count: Number of samples recorded
        min_count: Minimum count value
        max_count: Maximum count value
        avg_count: Average count value
        total_count: Sum of all counts

    Usage:
        stats = CountStats(
            count=50,
            min_count=1,
            max_count=100,
            avg_count=30.5,
            total_count=1525,
        )
        print(f"Total: {stats.total_count}")
    """

    count: int
    min_count: int
    max_count: int
    avg_count: float
    total_count: int
