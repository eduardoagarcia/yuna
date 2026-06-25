"""Tests for PlaybackControls."""

import pytest
from faker import Faker

from yuna.exceptions import ValidationError
from yuna.replay.controls import PlaybackControls

fake = Faker()


def test_playback_controls_defaults() -> None:
    """Test PlaybackControls with default values."""
    controls = PlaybackControls()

    assert controls.speed == 1.0
    assert controls.loop is False
    assert controls.start_tick == 0
    assert controls.end_tick is None


def test_playback_controls_custom_values() -> None:
    """Test PlaybackControls with custom values."""
    speed = fake.pyfloat(min_value=0.1, max_value=10.0)
    loop = fake.boolean()
    start_tick = fake.random_int(min=0, max=100)
    end_tick = fake.random_int(min=start_tick, max=200)

    controls = PlaybackControls(
        speed=speed,
        loop=loop,
        start_tick=start_tick,
        end_tick=end_tick,
    )

    assert controls.speed == speed
    assert controls.loop == loop
    assert controls.start_tick == start_tick
    assert controls.end_tick == end_tick


def test_playback_controls_speed_validation() -> None:
    """Test that speed must be positive."""
    with pytest.raises(ValidationError, match="Playback speed must be positive"):
        PlaybackControls(speed=0.0)

    with pytest.raises(ValidationError, match="Playback speed must be positive"):
        PlaybackControls(speed=-1.0)


def test_playback_controls_start_tick_validation() -> None:
    """Test that start tick must be non-negative."""
    with pytest.raises(ValidationError, match="Start tick must be non-negative"):
        PlaybackControls(start_tick=-1)


def test_playback_controls_end_tick_validation() -> None:
    """Test that end tick must be >= start tick."""
    with pytest.raises(
        ValidationError, match="End tick must be greater than or equal to start tick"
    ):
        PlaybackControls(start_tick=10, end_tick=5)


def test_playback_controls_valid_tick_range() -> None:
    """Test valid tick range."""
    controls = PlaybackControls(start_tick=10, end_tick=10)
    assert controls.start_tick == 10
    assert controls.end_tick == 10

    controls = PlaybackControls(start_tick=10, end_tick=20)
    assert controls.start_tick == 10
    assert controls.end_tick == 20


def test_playback_controls_none_end_tick() -> None:
    """Test that end_tick can be None."""
    controls = PlaybackControls(start_tick=10, end_tick=None)
    assert controls.start_tick == 10
    assert controls.end_tick is None


def test_playback_controls_slow_speed() -> None:
    """Test playback with slow speed."""
    controls = PlaybackControls(speed=0.5)
    assert controls.speed == 0.5


def test_playback_controls_fast_speed() -> None:
    """Test playback with fast speed."""
    controls = PlaybackControls(speed=2.0)
    assert controls.speed == 2.0


def test_playback_controls_loop_enabled() -> None:
    """Test playback with loop enabled."""
    controls = PlaybackControls(loop=True)
    assert controls.loop is True


def test_playback_controls_loop_disabled() -> None:
    """Test playback with loop disabled."""
    controls = PlaybackControls(loop=False)
    assert controls.loop is False


def test_playback_controls_immutable_after_creation() -> None:
    """Test that controls can be modified after creation."""
    controls = PlaybackControls(speed=1.0)
    controls.speed = 2.0
    assert controls.speed == 2.0
