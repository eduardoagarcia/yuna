"""Tests for enhanced PerformanceMonitor."""

import json
import tempfile
import threading
import time
from collections import deque
from pathlib import Path
from unittest.mock import patch

import pytest
from faker import Faker

from yuna.profiling.monitor import (
    PerformanceMonitor,
    get_performance_monitor,
    reset_performance_monitor,
    set_performance_monitor,
)
from yuna.profiling.stats import CountStats, TimingStats

fake = Faker()


def test_monitor_initialization() -> None:
    """Test PerformanceMonitor initialization with default params."""
    monitor = PerformanceMonitor()

    assert monitor._enabled is True
    assert monitor._window_size == 1000


def test_monitor_initialization_disabled() -> None:
    """Test PerformanceMonitor initialization with disabled flag."""
    monitor = PerformanceMonitor(enabled=False)

    assert monitor._enabled is False


def test_monitor_initialization_custom_window_size() -> None:
    """Test PerformanceMonitor initialization with custom window size."""
    window_size = fake.random_int(min=100, max=5000)
    monitor = PerformanceMonitor(window_size=window_size)

    assert monitor._window_size == window_size


def test_context_manager_records_timing() -> None:
    """Test context manager records timing sample."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    with monitor.sample(category=category, name=name):
        time.sleep(0.01)

    stats = monitor.get_timing_stats(category=category, name=name)
    assert stats is not None
    assert stats.count == 1
    assert stats.avg_time > 0.0


def test_context_manager_disabled_has_zero_overhead() -> None:
    """Test context manager with disabled monitor does not record."""
    monitor = PerformanceMonitor(enabled=False)
    category = fake.word()
    name = fake.word()

    with monitor.sample(category=category, name=name):
        time.sleep(0.01)

    stats = monitor.get_timing_stats(category=category, name=name)
    assert stats is None


def test_context_manager_preserves_exceptions() -> None:
    """Test context manager still records timing on exception."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()
    error_message = fake.sentence()

    with pytest.raises(ValueError):
        with monitor.sample(category=category, name=name):
            time.sleep(0.01)
            raise ValueError(error_message)

    stats = monitor.get_timing_stats(category=category, name=name)  # type: ignore[unreachable]
    assert stats is not None
    assert stats.count == 1


def test_multiple_samples_same_metric() -> None:
    """Test multiple samples for same category/name."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    with monitor.sample(category=category, name=name):
        time.sleep(0.01)

    with monitor.sample(category=category, name=name):
        time.sleep(0.01)

    with monitor.sample(category=category, name=name):
        time.sleep(0.01)

    stats = monitor.get_timing_stats(category=category, name=name)
    assert stats is not None
    assert stats.count == 3
    assert stats.avg_time > 0.0


def test_timing_stats_percentiles() -> None:
    """Test timing stats include p95 and p99 percentiles."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    clock_values: list[float] = []
    elapsed = 0.0
    for i in range(100):
        clock_values.append(elapsed)
        elapsed += float(i + 1)
        clock_values.append(elapsed)

    with patch.object(time, "perf_counter", side_effect=clock_values):
        for _ in range(100):
            with monitor.sample(category=category, name=name):
                pass

    stats = monitor.get_timing_stats(category=category, name=name)
    assert stats is not None
    assert stats.count == 100
    assert stats.p95_time > stats.avg_time
    assert stats.p99_time > stats.p95_time
    assert stats.p99_time <= stats.max_time


def test_timing_stats_min_max_avg() -> None:
    """Test timing stats calculate min, max, avg correctly."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    with monitor.sample(category=category, name=name):
        time.sleep(0.01)

    with monitor.sample(category=category, name=name):
        time.sleep(0.02)

    with monitor.sample(category=category, name=name):
        time.sleep(0.015)

    stats = monitor.get_timing_stats(category=category, name=name)
    assert stats is not None
    assert stats.count == 3
    assert stats.min_time < stats.max_time
    assert stats.min_time <= stats.avg_time <= stats.max_time


def test_record_count() -> None:
    """Test record_count stores count samples."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()
    count_value = fake.random_int(min=1, max=100)

    monitor.record_count(category=category, name=name, count=count_value)

    stats = monitor.get_count_stats(category=category, name=name)
    assert stats is not None
    assert stats.count == 1
    assert stats.total_count == count_value
    assert stats.avg_count == count_value


def test_record_count_disabled() -> None:
    """Test record_count with disabled monitor does not record."""
    monitor = PerformanceMonitor(enabled=False)
    category = fake.word()
    name = fake.word()
    count_value = fake.random_int(min=1, max=100)

    monitor.record_count(category=category, name=name, count=count_value)

    stats = monitor.get_count_stats(category=category, name=name)
    assert stats is None


def test_record_count_multiple_samples() -> None:
    """Test record_count with multiple samples."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    monitor.record_count(category=category, name=name, count=10)
    monitor.record_count(category=category, name=name, count=20)
    monitor.record_count(category=category, name=name, count=15)

    stats = monitor.get_count_stats(category=category, name=name)
    assert stats is not None
    assert stats.count == 3
    assert stats.total_count == 45
    assert stats.min_count == 10
    assert stats.max_count == 20
    assert stats.avg_count == 15.0


def test_rolling_window_enforces_max_size() -> None:
    """Test rolling window limits samples to window_size."""
    window_size = 10
    monitor = PerformanceMonitor(window_size=window_size)
    category = fake.word()
    name = fake.word()

    for _ in range(20):
        with monitor.sample(category=category, name=name):
            time.sleep(0.001)

    stats = monitor.get_timing_stats(category=category, name=name)
    assert stats is not None
    assert stats.count == window_size


def test_category_based_organization() -> None:
    """Test metrics organized by category."""
    monitor = PerformanceMonitor()
    category1 = fake.unique.word()
    category2 = fake.unique.word()
    name = fake.word()

    with monitor.sample(category=category1, name=name):
        time.sleep(0.01)

    with monitor.sample(category=category2, name=name):
        time.sleep(0.01)

    stats1 = monitor.get_timing_stats(category=category1, name=name)
    stats2 = monitor.get_timing_stats(category=category2, name=name)

    assert stats1 is not None
    assert stats2 is not None
    assert stats1.count == 1
    assert stats2.count == 1


def test_get_categories() -> None:
    """Test get_categories returns all categories."""
    monitor = PerformanceMonitor()
    category1 = fake.word()
    category2 = fake.word()
    category3 = fake.word()
    name = fake.word()

    with monitor.sample(category=category1, name=name):
        time.sleep(0.001)

    monitor.record_count(category=category2, name=name, count=10)

    with monitor.sample(category=category3, name=name):
        time.sleep(0.001)

    categories = monitor.get_categories()
    assert category1 in categories
    assert category2 in categories
    assert category3 in categories


def test_get_category_stats() -> None:
    """Test get_category_stats returns all metrics in category."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name1 = fake.unique.word()
    name2 = fake.unique.word()

    with monitor.sample(category=category, name=name1):
        time.sleep(0.001)

    monitor.record_count(category=category, name=name2, count=10)

    stats = monitor.get_category_stats(category=category)
    assert name1 in stats
    assert name2 in stats
    assert isinstance(stats[name1], TimingStats)
    assert isinstance(stats[name2], CountStats)


def test_get_category_stats_empty_category() -> None:
    """Test get_category_stats returns empty dict for unknown category."""
    monitor = PerformanceMonitor()
    category = fake.word()

    stats = monitor.get_category_stats(category=category)
    assert stats == {}


def test_get_timing_stats_returns_none_for_unknown_metric() -> None:
    """Test get_timing_stats returns None for unknown category/name."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    stats = monitor.get_timing_stats(category=category, name=name)
    assert stats is None


def test_get_timing_stats_returns_none_for_unknown_name_in_category() -> None:
    """Test get_timing_stats returns None for unknown name in existing category."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name1 = fake.unique.word()
    name2 = fake.unique.word()

    with monitor.sample(category=category, name=name1):
        time.sleep(0.001)

    stats = monitor.get_timing_stats(category=category, name=name2)
    assert stats is None


def test_get_count_stats_returns_none_for_unknown_metric() -> None:
    """Test get_count_stats returns None for unknown category/name."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    stats = monitor.get_count_stats(category=category, name=name)
    assert stats is None


def test_get_count_stats_returns_none_for_unknown_name_in_category() -> None:
    """Test get_count_stats returns None for unknown name in existing category."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name1 = fake.unique.word()
    name2 = fake.unique.word()

    monitor.record_count(category=category, name=name1, count=10)

    stats = monitor.get_count_stats(category=category, name=name2)
    assert stats is None


def test_reset_clears_all_data() -> None:
    """Test reset clears all timing and count samples."""
    monitor = PerformanceMonitor()
    category1 = fake.word()
    category2 = fake.word()
    name = fake.word()

    with monitor.sample(category=category1, name=name):
        time.sleep(0.001)

    monitor.record_count(category=category2, name=name, count=10)

    monitor.reset()

    assert len(monitor.get_categories()) == 0
    assert monitor.get_timing_stats(category=category1, name=name) is None
    assert monitor.get_count_stats(category=category2, name=name) is None


def test_reset_category_clears_category_data() -> None:
    """Test reset_category clears specific category."""
    monitor = PerformanceMonitor()
    category1 = fake.unique.word()
    category2 = fake.unique.word()
    name = fake.word()

    with monitor.sample(category=category1, name=name):
        time.sleep(0.001)

    with monitor.sample(category=category2, name=name):
        time.sleep(0.001)

    monitor.reset_category(category=category1)

    categories = monitor.get_categories()
    assert category1 not in categories
    assert category2 in categories


def test_export_json() -> None:
    """Test export_json writes metrics to JSON file."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name1 = fake.unique.word()
    name2 = fake.unique.word()

    with monitor.sample(category=category, name=name1):
        time.sleep(0.001)

    monitor.record_count(category=category, name=name2, count=10)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "metrics.json"
        monitor.export_json(path=str(path))

        assert path.exists()

        with open(path, encoding="utf-8") as file:
            data = json.load(fp=file)

        assert category in data
        assert name1 in data[category]
        assert name2 in data[category]
        assert data[category][name1]["count"] == 1
        assert data[category][name2]["count"] == 1
        assert data[category][name2]["total_count"] == 10


def test_print_report_no_metrics() -> None:
    """Test print_report with no metrics."""
    monitor = PerformanceMonitor()
    monitor.print_report()


def test_print_report_with_metrics(capsys) -> None:
    """Test print_report outputs formatted report."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    with monitor.sample(category=category, name=name):
        time.sleep(0.001)

    monitor.print_report()

    captured = capsys.readouterr()
    assert "PERFORMANCE REPORT" in captured.out
    assert category.upper() in captured.out


def test_thread_safety_timing() -> None:
    """Test thread-safe timing sample recording."""
    monitor = PerformanceMonitor()
    category = fake.word()
    num_threads = 10
    samples_per_thread = 5

    def worker(thread_id: int) -> None:
        name = f"thread_{thread_id}"
        for _ in range(samples_per_thread):
            with monitor.sample(category=category, name=name):
                time.sleep(0.001)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for i in range(num_threads):
        name = f"thread_{i}"
        stats = monitor.get_timing_stats(category=category, name=name)
        assert stats is not None
        assert stats.count == samples_per_thread


def test_thread_safety_count() -> None:
    """Test thread-safe count sample recording."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()
    num_threads = 10

    def worker() -> None:
        for _ in range(5):
            monitor.record_count(category=category, name=name, count=1)

    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    stats = monitor.get_count_stats(category=category, name=name)
    assert stats is not None
    assert stats.count == 50


def test_global_singleton_get_performance_monitor() -> None:
    """Test get_performance_monitor returns singleton."""
    reset_performance_monitor()

    monitor1 = get_performance_monitor()
    monitor2 = get_performance_monitor()

    assert monitor1 is monitor2


def test_reset_performance_monitor() -> None:
    """Test reset_performance_monitor clears singleton."""
    monitor1 = get_performance_monitor()
    reset_performance_monitor()
    monitor2 = get_performance_monitor()

    assert monitor1 is not monitor2


def test_percentile_calculation_boundary_cases() -> None:
    """Test percentile calculation with boundary values."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    for i in range(10):
        with monitor.sample(category=category, name=name):
            time.sleep(0.001 * (i + 1))

    stats = monitor.get_timing_stats(category=category, name=name)
    assert stats is not None
    assert stats.p95_time > 0.0
    assert stats.p99_time > 0.0
    assert stats.p99_time >= stats.p95_time


def test_get_category_stats_skips_empty_stats() -> None:
    """Test get_category_stats skips categories with no stats."""
    monitor = PerformanceMonitor()
    category = fake.word()

    stats = monitor.get_category_stats(category=category)
    assert stats == {}


def test_print_report_with_count_stats(capsys) -> None:
    """Test print_report outputs count stats correctly."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    monitor.record_count(category=category, name=name, count=10)
    monitor.print_report()

    captured = capsys.readouterr()
    assert category.upper() in captured.out
    assert name in captured.out
    assert "total=" in captured.out
    assert "10" in captured.out


def test_percentile_with_empty_list() -> None:
    """Test _percentile handles empty list gracefully."""
    monitor = PerformanceMonitor()
    result = monitor._percentile(values=[], percentile=0.95)
    assert result == 0.0


def test_percentile_with_index_out_of_bounds() -> None:
    """Test _percentile handles index >= len edge case."""
    monitor = PerformanceMonitor()
    values = [1.0]
    result = monitor._percentile(values=values, percentile=1.0)
    assert result == 1.0


def test_get_timing_stats_with_empty_samples() -> None:
    """Test get_timing_stats returns None for empty sample deque."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    monitor._timing_samples[category][name] = deque(maxlen=1000)

    stats = monitor.get_timing_stats(category=category, name=name)
    assert stats is None


def test_get_count_stats_with_empty_samples() -> None:
    """Test get_count_stats returns None for empty sample deque."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    monitor._count_samples[category][name] = deque(maxlen=1000)

    stats = monitor.get_count_stats(category=category, name=name)
    assert stats is None


def test_print_report_skips_category_with_empty_stats(capsys) -> None:
    """Test print_report continues when category has no valid stats."""
    monitor = PerformanceMonitor()
    category = fake.word()
    name = fake.word()

    monitor._timing_samples[category][name] = deque(maxlen=1000)

    monitor.print_report()

    captured = capsys.readouterr()
    assert "PERFORMANCE REPORT" in captured.out


def test_set_performance_monitor_installs_global_singleton() -> None:
    """set_performance_monitor replaces the global monitor instance."""
    installed_monitor = PerformanceMonitor(enabled=False)

    set_performance_monitor(monitor=installed_monitor)

    assert get_performance_monitor() is installed_monitor
    assert get_performance_monitor()._enabled is False

    reset_performance_monitor()
