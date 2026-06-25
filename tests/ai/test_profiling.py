"""Tests for AI profiling statistics."""

from faker import Faker

from yuna.ai.profiling import AIProfileStats

fake = Faker()


def test_ai_profile_stats_default_values() -> None:
    """Test AIProfileStats initializes with zeros."""
    stats = AIProfileStats()

    assert stats.behavior_tree_time_ms == 0.0
    assert stats.perception_time_ms == 0.0
    assert stats.pathfinding_time_ms == 0.0
    assert stats.steering_time_ms == 0.0
    assert stats.entities_updated == 0
    assert stats.entities_skipped == 0


def test_ai_profile_stats_custom_values() -> None:
    """Test AIProfileStats accepts custom values."""
    behavior_tree_time = fake.random.uniform(a=0.0, b=100.0)
    perception_time = fake.random.uniform(a=0.0, b=100.0)
    pathfinding_time = fake.random.uniform(a=0.0, b=100.0)
    steering_time = fake.random.uniform(a=0.0, b=100.0)
    entities_updated = fake.random_int(min=0, max=1000)
    entities_skipped = fake.random_int(min=0, max=1000)

    stats = AIProfileStats(
        behavior_tree_time_ms=behavior_tree_time,
        perception_time_ms=perception_time,
        pathfinding_time_ms=pathfinding_time,
        steering_time_ms=steering_time,
        entities_updated=entities_updated,
        entities_skipped=entities_skipped,
    )

    assert stats.behavior_tree_time_ms == behavior_tree_time
    assert stats.perception_time_ms == perception_time
    assert stats.pathfinding_time_ms == pathfinding_time
    assert stats.steering_time_ms == steering_time
    assert stats.entities_updated == entities_updated
    assert stats.entities_skipped == entities_skipped


def test_ai_profile_stats_reset() -> None:
    """Test reset clears all statistics."""
    stats = AIProfileStats(
        behavior_tree_time_ms=fake.random.uniform(a=1.0, b=100.0),
        perception_time_ms=fake.random.uniform(a=1.0, b=100.0),
        pathfinding_time_ms=fake.random.uniform(a=1.0, b=100.0),
        steering_time_ms=fake.random.uniform(a=1.0, b=100.0),
        entities_updated=fake.random_int(min=1, max=1000),
        entities_skipped=fake.random_int(min=1, max=1000),
    )

    stats.reset()

    assert stats.behavior_tree_time_ms == 0.0
    assert stats.perception_time_ms == 0.0
    assert stats.pathfinding_time_ms == 0.0
    assert stats.steering_time_ms == 0.0
    assert stats.entities_updated == 0
    assert stats.entities_skipped == 0


def test_ai_profile_stats_accumulate_timing() -> None:
    """Test accumulating timing values."""
    stats = AIProfileStats()

    stats.behavior_tree_time_ms += 5.0
    stats.perception_time_ms += 3.0
    stats.pathfinding_time_ms += 2.0
    stats.steering_time_ms += 1.0

    assert stats.behavior_tree_time_ms == 5.0
    assert stats.perception_time_ms == 3.0
    assert stats.pathfinding_time_ms == 2.0
    assert stats.steering_time_ms == 1.0


def test_ai_profile_stats_accumulate_counts() -> None:
    """Test accumulating count values."""
    stats = AIProfileStats()

    stats.entities_updated += 10
    stats.entities_skipped += 5

    assert stats.entities_updated == 10
    assert stats.entities_skipped == 5


def test_ai_profile_stats_multiple_accumulations() -> None:
    """Test multiple accumulations over several frames."""
    stats = AIProfileStats()

    for _ in range(5):
        stats.behavior_tree_time_ms += 2.0
        stats.entities_updated += 3

    assert stats.behavior_tree_time_ms == 10.0
    assert stats.entities_updated == 15


def test_ai_profile_stats_reset_and_reuse() -> None:
    """Test resetting and reusing stats object."""
    stats = AIProfileStats()

    stats.perception_time_ms = 10.0
    stats.entities_updated = 20
    stats.reset()

    stats.perception_time_ms = 5.0
    stats.entities_updated = 10

    assert stats.perception_time_ms == 5.0
    assert stats.entities_updated == 10


def test_ai_profile_stats_partial_data() -> None:
    """Test stats with only some fields populated."""
    stats = AIProfileStats(
        behavior_tree_time_ms=5.0,
        entities_updated=10,
    )

    assert stats.behavior_tree_time_ms == 5.0
    assert stats.perception_time_ms == 0.0
    assert stats.pathfinding_time_ms == 0.0
    assert stats.steering_time_ms == 0.0
    assert stats.entities_updated == 10
    assert stats.entities_skipped == 0


def test_ai_profile_stats_zero_timing() -> None:
    """Test stats with zero timing values."""
    stats = AIProfileStats(
        behavior_tree_time_ms=0.0,
        perception_time_ms=0.0,
        pathfinding_time_ms=0.0,
        steering_time_ms=0.0,
    )

    assert stats.behavior_tree_time_ms == 0.0
    assert stats.perception_time_ms == 0.0
    assert stats.pathfinding_time_ms == 0.0
    assert stats.steering_time_ms == 0.0


def test_ai_profile_stats_large_values() -> None:
    """Test stats with large values."""
    stats = AIProfileStats(
        behavior_tree_time_ms=1000.0,
        perception_time_ms=2000.0,
        pathfinding_time_ms=3000.0,
        steering_time_ms=4000.0,
        entities_updated=100000,
        entities_skipped=50000,
    )

    assert stats.behavior_tree_time_ms == 1000.0
    assert stats.perception_time_ms == 2000.0
    assert stats.pathfinding_time_ms == 3000.0
    assert stats.steering_time_ms == 4000.0
    assert stats.entities_updated == 100000
    assert stats.entities_skipped == 50000


def test_ai_profile_stats_small_timing_values() -> None:
    """Test stats with small microsecond-level timing values."""
    stats = AIProfileStats(
        behavior_tree_time_ms=0.001,
        perception_time_ms=0.002,
        pathfinding_time_ms=0.003,
        steering_time_ms=0.004,
    )

    assert stats.behavior_tree_time_ms == 0.001
    assert stats.perception_time_ms == 0.002
    assert stats.pathfinding_time_ms == 0.003
    assert stats.steering_time_ms == 0.004


def test_ai_profile_stats_total_time_calculation() -> None:
    """Test calculating total AI time from all subsystems."""
    stats = AIProfileStats(
        behavior_tree_time_ms=5.0,
        perception_time_ms=3.0,
        pathfinding_time_ms=2.0,
        steering_time_ms=1.0,
    )

    total_time = (
        stats.behavior_tree_time_ms
        + stats.perception_time_ms
        + stats.pathfinding_time_ms
        + stats.steering_time_ms
    )

    assert total_time == 11.0


def test_ai_profile_stats_total_entities_calculation() -> None:
    """Test calculating total entities from updated and skipped."""
    stats = AIProfileStats(
        entities_updated=75,
        entities_skipped=25,
    )

    total_entities = stats.entities_updated + stats.entities_skipped

    assert total_entities == 100


def test_ai_profile_stats_update_ratio() -> None:
    """Test calculating update ratio."""
    stats = AIProfileStats(
        entities_updated=80,
        entities_skipped=20,
    )

    total = stats.entities_updated + stats.entities_skipped
    update_ratio = stats.entities_updated / total if total > 0 else 0.0

    assert update_ratio == 0.8


def test_ai_profile_stats_average_time_per_entity() -> None:
    """Test calculating average time per updated entity."""
    stats = AIProfileStats(
        behavior_tree_time_ms=100.0,
        entities_updated=10,
    )

    avg_time = (
        stats.behavior_tree_time_ms / stats.entities_updated
        if stats.entities_updated > 0
        else 0.0
    )

    assert avg_time == 10.0


def test_ai_profile_stats_reset_preserves_type() -> None:
    """Test reset maintains correct types."""
    stats = AIProfileStats(
        behavior_tree_time_ms=5.0,
        entities_updated=10,
    )

    stats.reset()

    assert isinstance(stats.behavior_tree_time_ms, float)
    assert isinstance(stats.perception_time_ms, float)
    assert isinstance(stats.pathfinding_time_ms, float)
    assert isinstance(stats.steering_time_ms, float)
    assert isinstance(stats.entities_updated, int)
    assert isinstance(stats.entities_skipped, int)


def test_ai_profile_stats_multiple_resets() -> None:
    """Test multiple consecutive resets."""
    stats = AIProfileStats(
        behavior_tree_time_ms=10.0,
        entities_updated=20,
    )

    stats.reset()
    stats.reset()
    stats.reset()

    assert stats.behavior_tree_time_ms == 0.0
    assert stats.entities_updated == 0


def test_ai_profile_stats_fractional_timing() -> None:
    """Test stats with fractional timing values."""
    stats = AIProfileStats(
        behavior_tree_time_ms=1.5,
        perception_time_ms=2.7,
        pathfinding_time_ms=3.9,
        steering_time_ms=4.1,
    )

    assert stats.behavior_tree_time_ms == 1.5
    assert stats.perception_time_ms == 2.7
    assert stats.pathfinding_time_ms == 3.9
    assert stats.steering_time_ms == 4.1
