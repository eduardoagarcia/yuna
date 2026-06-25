"""Tests for TimingStats and CountStats."""

from faker import Faker

from yuna.profiling.stats import CountStats, TimingStats

fake = Faker()


def test_timing_stats_initialization() -> None:
    """Test TimingStats initialization with all fields."""
    count = fake.random_int(min=1, max=100)
    min_time = fake.pyfloat(min_value=0.0, max_value=1.0)
    max_time = fake.pyfloat(min_value=1.0, max_value=10.0)
    avg_time = fake.pyfloat(min_value=0.0, max_value=5.0)
    p95_time = fake.pyfloat(min_value=0.0, max_value=8.0)
    p99_time = fake.pyfloat(min_value=0.0, max_value=10.0)

    stats = TimingStats(
        count=count,
        min_time=min_time,
        max_time=max_time,
        avg_time=avg_time,
        p95_time=p95_time,
        p99_time=p99_time,
    )

    assert stats.count == count
    assert stats.min_time == min_time
    assert stats.max_time == max_time
    assert stats.avg_time == avg_time
    assert stats.p95_time == p95_time
    assert stats.p99_time == p99_time


def test_timing_stats_equality() -> None:
    """Test TimingStats equality comparison."""
    count = fake.random_int(min=1, max=100)
    min_time = fake.pyfloat(min_value=0.0, max_value=1.0)
    max_time = fake.pyfloat(min_value=1.0, max_value=10.0)
    avg_time = fake.pyfloat(min_value=0.0, max_value=5.0)
    p95_time = fake.pyfloat(min_value=0.0, max_value=8.0)
    p99_time = fake.pyfloat(min_value=0.0, max_value=10.0)

    stats1 = TimingStats(
        count=count,
        min_time=min_time,
        max_time=max_time,
        avg_time=avg_time,
        p95_time=p95_time,
        p99_time=p99_time,
    )

    stats2 = TimingStats(
        count=count,
        min_time=min_time,
        max_time=max_time,
        avg_time=avg_time,
        p95_time=p95_time,
        p99_time=p99_time,
    )

    assert stats1 == stats2


def test_count_stats_initialization() -> None:
    """Test CountStats initialization with all fields."""
    count = fake.random_int(min=1, max=100)
    min_count = fake.random_int(min=1, max=10)
    max_count = fake.random_int(min=10, max=100)
    avg_count = fake.pyfloat(min_value=1.0, max_value=50.0)
    total_count = fake.random_int(min=100, max=1000)

    stats = CountStats(
        count=count,
        min_count=min_count,
        max_count=max_count,
        avg_count=avg_count,
        total_count=total_count,
    )

    assert stats.count == count
    assert stats.min_count == min_count
    assert stats.max_count == max_count
    assert stats.avg_count == avg_count
    assert stats.total_count == total_count


def test_count_stats_equality() -> None:
    """Test CountStats equality comparison."""
    count = fake.random_int(min=1, max=100)
    min_count = fake.random_int(min=1, max=10)
    max_count = fake.random_int(min=10, max=100)
    avg_count = fake.pyfloat(min_value=1.0, max_value=50.0)
    total_count = fake.random_int(min=100, max=1000)

    stats1 = CountStats(
        count=count,
        min_count=min_count,
        max_count=max_count,
        avg_count=avg_count,
        total_count=total_count,
    )

    stats2 = CountStats(
        count=count,
        min_count=min_count,
        max_count=max_count,
        avg_count=avg_count,
        total_count=total_count,
    )

    assert stats1 == stats2
