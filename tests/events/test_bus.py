"""Tests for event bus."""

import time
from dataclasses import dataclass
from unittest.mock import MagicMock

from faker import Faker

from yuna.events.bus import EventBus
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


def test_event_bus_creation() -> None:
    """Test EventBus can be instantiated."""
    bus = EventBus()
    assert bus is not None


def test_emit_and_process() -> None:
    """Test emitting and processing events."""
    bus = EventBus()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    bus.subscribe(event_type="TestEvent", handler=handler)
    bus.emit(event=event)
    bus.process_events()
    handler.assert_called_once_with(event)


def test_emit_with_delay() -> None:
    """Test emitting events with frame delay."""
    bus = EventBus()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="delayed")
    bus.subscribe(event_type="TestEvent", handler=handler)
    bus.emit(event=event, delay_frames=1)
    bus.process_events()
    handler.assert_not_called()


def test_delayed_events_processed_after_end_tick() -> None:
    """Test delayed events processed after end_tick."""
    bus = EventBus()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="delayed")
    bus.subscribe(event_type="TestEvent", handler=handler)
    bus.emit(event=event, delay_frames=1)
    bus.end_tick()
    bus.process_events()
    handler.assert_called_once_with(event)


def test_emit_priority() -> None:
    """Test emitting events with specific priority."""
    bus = EventBus()
    processed_order = []

    def handler(event: Event) -> None:
        processed_order.append(event.message)  # type: ignore[attr-defined]

    bus.subscribe(event_type="TestEvent", handler=handler)
    event_low = TestEvent(timestamp=time.time(), tick=0, message="low")
    event_high = TestEvent(timestamp=time.time(), tick=0, message="high")
    bus.emit_priority(event=event_high, priority=200)
    bus.emit_priority(event=event_low, priority=100)
    bus.process_events()
    assert processed_order == ["low", "high"]


def test_subscribe_and_dispatch() -> None:
    """Test subscribing handler and dispatching events."""
    bus = EventBus()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    bus.subscribe(event_type="TestEvent", handler=handler)
    bus.emit(event=event)
    bus.process_events()
    handler.assert_called_once()


def test_subscribe_all() -> None:
    """Test subscribing wildcard handler to all events."""
    bus = EventBus()
    handler = MagicMock()
    bus.subscribe_all(handler=handler)
    event_1 = TestEvent(timestamp=time.time(), tick=0, message="test")
    event_2 = AnotherEvent(timestamp=time.time(), tick=0, value=42)
    bus.emit(event=event_1)
    bus.emit(event=event_2)
    bus.process_events()
    assert handler.call_count == 2


def test_unsubscribe() -> None:
    """Test unsubscribing handler from event type."""
    bus = EventBus()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    bus.subscribe(event_type="TestEvent", handler=handler)
    bus.unsubscribe(event_type="TestEvent", handler=handler)
    bus.emit(event=event)
    bus.process_events()
    handler.assert_not_called()


def test_unsubscribe_all() -> None:
    """Test unsubscribing wildcard handler."""
    bus = EventBus()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    bus.subscribe_all(handler=handler)
    bus.unsubscribe_all(handler=handler)
    bus.emit(event=event)
    bus.process_events()
    handler.assert_not_called()


def test_process_events_multiple_times() -> None:
    """Test processing events multiple times."""
    bus = EventBus()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    bus.subscribe(event_type="TestEvent", handler=handler)
    bus.emit(event=event)
    bus.process_events()
    bus.process_events()
    handler.assert_called_once()


def test_end_tick_swaps_buffers() -> None:
    """Test end_tick moves delayed events to current frame."""
    bus = EventBus()
    handler = MagicMock()
    event_current = TestEvent(timestamp=time.time(), tick=0, message="current")
    event_delayed = TestEvent(timestamp=time.time(), tick=0, message="delayed")
    bus.subscribe(event_type="TestEvent", handler=handler)
    bus.emit(event=event_current)
    bus.emit(event=event_delayed, delay_frames=1)
    bus.process_events()
    assert handler.call_count == 1
    bus.end_tick()
    bus.process_events()
    assert handler.call_count == 2


def test_priority_ordering_in_bus() -> None:
    """Test priority ordering maintained through bus."""
    bus = EventBus()
    processed_order = []

    def handler(event: Event) -> None:
        processed_order.append(event.message)  # type: ignore[attr-defined]

    bus.subscribe(event_type="TestEvent", handler=handler)
    event_1 = TestEvent(timestamp=time.time(), tick=0, message="first")
    event_2 = TestEvent(timestamp=time.time(), tick=0, message="second")
    event_3 = TestEvent(timestamp=time.time(), tick=0, message="third")
    bus.emit_priority(event=event_3, priority=300)
    bus.emit_priority(event=event_1, priority=100)
    bus.emit_priority(event=event_2, priority=200)
    bus.process_events()
    assert processed_order == ["first", "second", "third"]


def test_emit_priority_with_delay() -> None:
    """Test emitting priority events with delay."""
    bus = EventBus()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="priority delayed")
    bus.subscribe(event_type="TestEvent", handler=handler)
    bus.emit_priority(event=event, priority=50, delay_frames=1)
    bus.process_events()
    handler.assert_not_called()
    bus.end_tick()
    bus.process_events()
    handler.assert_called_once()


def test_multiple_handlers_same_event() -> None:
    """Test multiple handlers receive same event."""
    bus = EventBus()
    handler_1 = MagicMock()
    handler_2 = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    bus.subscribe(event_type="TestEvent", handler=handler_1)
    bus.subscribe(event_type="TestEvent", handler=handler_2)
    bus.emit(event=event)
    bus.process_events()
    handler_1.assert_called_once_with(event)
    handler_2.assert_called_once_with(event)


def test_type_specific_and_wildcard_handlers() -> None:
    """Test both type-specific and wildcard handlers called."""
    bus = EventBus()
    specific_handler = MagicMock()
    wildcard_handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    bus.subscribe(event_type="TestEvent", handler=specific_handler)
    bus.subscribe_all(handler=wildcard_handler)
    bus.emit(event=event)
    bus.process_events()
    specific_handler.assert_called_once_with(event)
    wildcard_handler.assert_called_once_with(event)


def test_emit_without_subscribers() -> None:
    """Test emitting event with no subscribers."""
    bus = EventBus()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    bus.emit(event=event)
    bus.process_events()


def test_process_without_events() -> None:
    """Test processing with no events queued."""
    bus = EventBus()
    handler = MagicMock()
    bus.subscribe(event_type="TestEvent", handler=handler)
    bus.process_events()
    handler.assert_not_called()


def test_end_tick_with_no_events() -> None:
    """Test ending tick with no events."""
    bus = EventBus()
    bus.end_tick()


def test_multiple_end_ticks() -> None:
    """Test calling end_tick multiple times clears events."""
    bus = EventBus()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    bus.subscribe(event_type="TestEvent", handler=handler)
    bus.emit(event=event, delay_frames=1)
    bus.end_tick()
    bus.process_events()
    assert handler.call_count == 1
    bus.end_tick()
    bus.process_events()
    assert handler.call_count == 1


def test_complex_scenario() -> None:
    """Test complex scenario with multiple event types and handlers."""
    bus = EventBus()
    test_handler = MagicMock()
    another_handler = MagicMock()
    wildcard_handler = MagicMock()
    bus.subscribe(event_type="TestEvent", handler=test_handler)
    bus.subscribe(event_type="AnotherEvent", handler=another_handler)
    bus.subscribe_all(handler=wildcard_handler)
    test_event = TestEvent(timestamp=time.time(), tick=0, message="test")
    another_event = AnotherEvent(timestamp=time.time(), tick=0, value=42)
    bus.emit_priority(event=test_event, priority=100)
    bus.emit_priority(event=another_event, priority=200)
    bus.process_events()
    test_handler.assert_called_once_with(test_event)
    another_handler.assert_called_once_with(another_event)
    assert wildcard_handler.call_count == 2


def test_events_cleared_after_processing() -> None:
    """Test events are cleared after processing."""
    bus = EventBus()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    bus.subscribe(event_type="TestEvent", handler=handler)
    bus.emit(event=event)
    bus.process_events()
    bus.process_events()
    handler.assert_called_once()


def test_delayed_events_with_priority_ordering() -> None:
    """Test delayed events maintain priority after end_tick."""
    bus = EventBus()
    processed_order = []

    def handler(event: Event) -> None:
        processed_order.append(event.message)  # type: ignore[attr-defined]

    bus.subscribe(event_type="TestEvent", handler=handler)
    event_low = TestEvent(timestamp=time.time(), tick=0, message="low")
    event_high = TestEvent(timestamp=time.time(), tick=0, message="high")
    bus.emit_priority(event=event_high, priority=200, delay_frames=1)
    bus.emit_priority(event=event_low, priority=100, delay_frames=1)
    bus.end_tick()
    bus.process_events()
    assert processed_order == ["low", "high"]
