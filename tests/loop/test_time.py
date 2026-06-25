"""Tests for time management implementation."""

from faker import Faker

from yuna.loop.time import TimeManager

fake = Faker()


def test_time_manager_creation() -> None:
    """Test TimeManager can be created with fixed delta."""
    fixed_delta = fake.pyfloat(min_value=0.001, max_value=1.0)
    time_manager = TimeManager(fixed_delta=fixed_delta)
    assert time_manager.fixed_delta == fixed_delta
    assert time_manager.accumulator == 0.0


def test_time_manager_with_common_timestep() -> None:
    """Test TimeManager with common 60 FPS timestep."""
    time_manager = TimeManager(fixed_delta=1 / 60)
    assert time_manager.fixed_delta == 1 / 60


def test_update_with_zero_elapsed() -> None:
    """Test update with zero elapsed time returns zero ticks."""
    time_manager = TimeManager(fixed_delta=0.016)
    ticks = time_manager.update(elapsed=0.0)
    assert ticks == 0
    assert time_manager.accumulator == 0.0


def test_update_with_less_than_fixed_delta() -> None:
    """Test update with time less than fixed delta accumulates."""
    time_manager = TimeManager(fixed_delta=0.016)
    ticks = time_manager.update(elapsed=0.01)
    assert ticks == 0
    assert time_manager.accumulator == 0.01


def test_update_with_exactly_fixed_delta() -> None:
    """Test update with exactly fixed delta executes one tick."""
    fixed_delta = 0.016
    time_manager = TimeManager(fixed_delta=fixed_delta)
    ticks = time_manager.update(elapsed=fixed_delta)
    assert ticks == 1
    assert time_manager.accumulator == 0.0


def test_update_with_multiple_fixed_deltas() -> None:
    """Test update with multiple fixed deltas executes multiple ticks."""
    fixed_delta = 0.016
    time_manager = TimeManager(fixed_delta=fixed_delta)
    ticks = time_manager.update(elapsed=fixed_delta * 3)
    assert ticks == 3
    assert time_manager.accumulator == 0.0


def test_update_with_partial_tick() -> None:
    """Test update with partial tick preserves remainder in accumulator."""
    fixed_delta = 0.016
    time_manager = TimeManager(fixed_delta=fixed_delta)
    ticks = time_manager.update(elapsed=fixed_delta * 2.5)
    assert ticks == 2
    assert time_manager.accumulator == fixed_delta * 0.5


def test_accumulator_carries_over_frames() -> None:
    """Test accumulator carries partial time across multiple updates."""
    fixed_delta = 0.016
    time_manager = TimeManager(fixed_delta=fixed_delta)
    time_manager.update(elapsed=0.01)
    assert time_manager.accumulator == 0.01
    ticks = time_manager.update(elapsed=0.01)
    assert ticks == 1
    assert time_manager.accumulator < 0.01


def test_reset_clears_accumulator() -> None:
    """Test reset clears accumulator to zero."""
    time_manager = TimeManager(fixed_delta=0.016)
    time_manager.update(elapsed=0.01)
    time_manager.reset()
    assert time_manager.accumulator == 0.0


def test_reset_does_not_affect_fixed_delta() -> None:
    """Test reset does not change fixed delta value."""
    fixed_delta = fake.pyfloat(min_value=0.001, max_value=1.0)
    time_manager = TimeManager(fixed_delta=fixed_delta)
    time_manager.reset()
    assert time_manager.fixed_delta == fixed_delta


def test_multiple_updates_maintain_consistency() -> None:
    """Test multiple updates maintain consistent tick counts."""
    fixed_delta = 0.01
    time_manager = TimeManager(fixed_delta=fixed_delta)
    total_ticks = 0
    for _ in range(10):
        ticks = time_manager.update(elapsed=0.025)
        total_ticks += ticks
    assert total_ticks == 25


def test_update_with_large_elapsed_time() -> None:
    """Test update with very large elapsed time."""
    fixed_delta = 0.016
    time_manager = TimeManager(fixed_delta=fixed_delta)
    ticks = time_manager.update(elapsed=1.0)
    assert ticks == 62
    assert time_manager.accumulator < fixed_delta


def test_update_with_very_small_fixed_delta() -> None:
    """Test update with very small fixed delta."""
    fixed_delta = 0.001
    time_manager = TimeManager(fixed_delta=fixed_delta)
    ticks = time_manager.update(elapsed=0.016)
    assert ticks >= 15
    assert time_manager.accumulator < fixed_delta


def test_accumulator_never_exceeds_fixed_delta() -> None:
    """Test accumulator never exceeds fixed delta after update."""
    fixed_delta = fake.pyfloat(min_value=0.001, max_value=0.1)
    time_manager = TimeManager(fixed_delta=fixed_delta)
    for _ in range(100):
        elapsed = fake.pyfloat(min_value=0.0, max_value=0.5)
        time_manager.update(elapsed=elapsed)
        assert time_manager.accumulator < fixed_delta


def test_fixed_delta_property() -> None:
    """Test fixed_delta property returns correct value."""
    fixed_delta = fake.pyfloat(min_value=0.001, max_value=1.0)
    time_manager = TimeManager(fixed_delta=fixed_delta)
    assert time_manager.fixed_delta == fixed_delta


def test_accumulator_property() -> None:
    """Test accumulator property returns current accumulator value."""
    time_manager = TimeManager(fixed_delta=0.016)
    assert time_manager.accumulator == 0.0
    time_manager.update(elapsed=0.01)
    assert time_manager.accumulator == 0.01


def test_update_with_negative_elapsed_time() -> None:
    """Test update with negative elapsed time."""
    time_manager = TimeManager(fixed_delta=0.016)
    time_manager._accumulator = 0.032
    ticks = time_manager.update(elapsed=-0.016)
    assert ticks == 1
    assert time_manager.accumulator == 0.0


def test_consecutive_updates_with_varying_elapsed() -> None:
    """Test consecutive updates with varying elapsed times."""
    fixed_delta = 0.016
    time_manager = TimeManager(fixed_delta=fixed_delta)
    ticks1 = time_manager.update(elapsed=0.01)
    ticks2 = time_manager.update(elapsed=0.02)
    assert ticks1 == 0
    assert ticks2 == 1
    ticks3 = time_manager.update(elapsed=0.005)
    assert ticks3 in (0, 1)


def test_reset_after_multiple_updates() -> None:
    """Test reset works correctly after multiple updates."""
    time_manager = TimeManager(fixed_delta=0.016)
    for _ in range(5):
        time_manager.update(elapsed=0.01)
    time_manager.reset()
    assert time_manager.accumulator == 0.0
    ticks = time_manager.update(elapsed=0.01)
    assert ticks == 0


def test_time_manager_determinism() -> None:
    """Test time manager produces deterministic results."""
    fixed_delta = 0.016
    time_manager1 = TimeManager(fixed_delta=fixed_delta)
    time_manager2 = TimeManager(fixed_delta=fixed_delta)
    elapsed_times = [0.01, 0.02, 0.015, 0.03, 0.005]
    ticks1 = [time_manager1.update(elapsed=e) for e in elapsed_times]
    ticks2 = [time_manager2.update(elapsed=e) for e in elapsed_times]
    assert ticks1 == ticks2


def test_fractional_ticks_accumulate_correctly() -> None:
    """Test fractional ticks accumulate correctly over time."""
    fixed_delta = 1 / 60
    time_manager = TimeManager(fixed_delta=fixed_delta)
    total_ticks = 0
    for _ in range(60):
        ticks = time_manager.update(elapsed=1 / 60)
        total_ticks += ticks
    assert total_ticks == 60
    assert time_manager.accumulator < fixed_delta
