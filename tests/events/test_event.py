"""Tests for event base class."""

import time
from dataclasses import FrozenInstanceError, dataclass

import pytest
from faker import Faker

from yuna.events.event import Event

fake = Faker()


@dataclass(frozen=True)
class TestEvent(Event):
    """Test event implementation."""

    message: str


@dataclass(frozen=True)
class AnotherEvent(Event):
    """Another test event implementation."""

    value: int


@dataclass(frozen=True)
class ComplexEvent(Event):
    """Complex event with multiple fields."""

    entity_id: str
    action: str
    data: dict[str, int]


def test_concrete_event_can_be_created() -> None:
    """Test concrete event extending Event can be created."""
    timestamp = time.time()
    tick = 100
    event = TestEvent(timestamp=timestamp, tick=tick, message="test")
    assert event is not None
    assert isinstance(event, Event)


def test_event_has_timestamp() -> None:
    """Test event has timestamp field."""
    timestamp = time.time()
    event = TestEvent(timestamp=timestamp, tick=0, message="test")
    assert event.timestamp == timestamp


def test_event_has_tick() -> None:
    """Test event has tick field."""
    tick = 42
    event = TestEvent(timestamp=time.time(), tick=tick, message="test")
    assert event.tick == tick


def test_event_type_property_returns_class_name() -> None:
    """Test event_type property returns class name."""
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    assert event.event_type == "TestEvent"


def test_different_event_types_have_different_names() -> None:
    """Test different event classes have different event_type values."""
    event_1 = TestEvent(timestamp=time.time(), tick=0, message="test")
    event_2 = AnotherEvent(timestamp=time.time(), tick=0, value=42)
    assert event_1.event_type != event_2.event_type
    assert event_1.event_type == "TestEvent"
    assert event_2.event_type == "AnotherEvent"


def test_event_is_immutable() -> None:
    """Test event cannot be modified after creation."""
    event = TestEvent(timestamp=time.time(), tick=0, message="original")
    with pytest.raises(FrozenInstanceError):
        event.message = "modified"  # type: ignore[misc]


def test_event_timestamp_is_immutable() -> None:
    """Test event timestamp cannot be modified."""
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    with pytest.raises(FrozenInstanceError):
        event.timestamp = time.time()  # type: ignore[misc]


def test_event_tick_is_immutable() -> None:
    """Test event tick cannot be modified."""
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    with pytest.raises(FrozenInstanceError):
        event.tick = 100  # type: ignore[misc]


def test_event_with_zero_tick() -> None:
    """Test event can have zero tick value."""
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    assert event.tick == 0


def test_event_with_large_tick() -> None:
    """Test event can have large tick value."""
    tick = 999999
    event = TestEvent(timestamp=time.time(), tick=tick, message="test")
    assert event.tick == tick


def test_event_with_negative_tick() -> None:
    """Test event can have negative tick value."""
    tick = -100
    event = TestEvent(timestamp=time.time(), tick=tick, message="test")
    assert event.tick == tick


def test_event_with_zero_timestamp() -> None:
    """Test event can have zero timestamp."""
    event = TestEvent(timestamp=0.0, tick=0, message="test")
    assert event.timestamp == 0.0


def test_multiple_events_can_be_created() -> None:
    """Test multiple event instances can be created."""
    event_1 = TestEvent(timestamp=time.time(), tick=0, message="first")
    event_2 = TestEvent(timestamp=time.time(), tick=1, message="second")
    event_3 = AnotherEvent(timestamp=time.time(), tick=2, value=42)
    assert event_1 is not event_2
    assert event_2 is not event_3


def test_complex_event_with_multiple_fields() -> None:
    """Test event with multiple custom fields."""
    entity_id = fake.uuid4()
    event = ComplexEvent(
        timestamp=time.time(),
        tick=100,
        entity_id=entity_id,
        action="move",
        data={"x": 10, "y": 20},
    )
    assert event.entity_id == entity_id
    assert event.action == "move"
    assert event.data == {"x": 10, "y": 20}


def test_event_equality() -> None:
    """Test events with same values are equal."""
    timestamp = time.time()
    tick = 42
    message = "test"
    event_1 = TestEvent(timestamp=timestamp, tick=tick, message=message)
    event_2 = TestEvent(timestamp=timestamp, tick=tick, message=message)
    assert event_1 == event_2


def test_event_inequality() -> None:
    """Test events with different values are not equal."""
    timestamp = time.time()
    event_1 = TestEvent(timestamp=timestamp, tick=0, message="first")
    event_2 = TestEvent(timestamp=timestamp, tick=0, message="second")
    assert event_1 != event_2


def test_event_hashing() -> None:
    """Test frozen events can be hashed."""
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    event_set = {event}
    assert event in event_set


def test_event_can_be_used_as_dict_key() -> None:
    """Test frozen event can be used as dictionary key."""
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    event_dict = {event: "value"}
    assert event_dict[event] == "value"


def test_event_type_is_consistent() -> None:
    """Test event_type property returns same value for same class."""
    event_1 = TestEvent(timestamp=time.time(), tick=0, message="first")
    event_2 = TestEvent(timestamp=time.time(), tick=1, message="second")
    assert event_1.event_type == event_2.event_type


def test_event_with_float_timestamp() -> None:
    """Test event stores float timestamp with precision."""
    timestamp = 1234567890.123456
    event = TestEvent(timestamp=timestamp, tick=0, message="test")
    assert event.timestamp == timestamp
