"""Tests for event queue."""

import time
from dataclasses import dataclass
from unittest.mock import MagicMock

from faker import Faker

from yuna.events.event import Event
from yuna.events.queue import EventQueue, QueuedEvent

fake = Faker()


@dataclass(frozen=True)
class TestEvent(Event):
    """Test event implementation."""

    message: str


@dataclass(frozen=True)
class AnotherEvent(Event):
    """Another test event implementation."""

    value: int


def test_event_queue_creation() -> None:
    """Test EventQueue can be instantiated."""
    queue = EventQueue()
    assert queue is not None


def test_enqueue_event() -> None:
    """Test enqueuing an event to current frame."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    queue.enqueue(event=event)
    assert queue.count_current() == 1


def test_process_events_with_handler() -> None:
    """Test processing events calls handler."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    queue.enqueue(event=event)
    handler = MagicMock()
    queue.process(handler=handler)
    handler.assert_called_once_with(event)


def test_process_clears_current_buffer() -> None:
    """Test processing events clears current frame buffer."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    queue.enqueue(event=event)
    queue.process(handler=lambda e: None)
    assert queue.count_current() == 0


def test_enqueue_with_delay_frames() -> None:
    """Test enqueuing event with delay goes to next frame."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="delayed")
    queue.enqueue(event=event, delay_frames=1)
    assert queue.count_current() == 0
    assert queue.count_next() == 1


def test_swap_buffers_moves_next_to_current() -> None:
    """Test buffer swap moves next frame to current frame."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="delayed")
    queue.enqueue(event=event, delay_frames=1)
    queue.swap_buffers()
    assert queue.count_current() == 1
    assert queue.count_next() == 0


def test_swap_buffers_clears_next_buffer() -> None:
    """Test buffer swap creates new empty next buffer."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="delayed")
    queue.enqueue(event=event, delay_frames=1)
    queue.swap_buffers()
    assert queue.count_next() == 0


def test_enqueue_priority() -> None:
    """Test enqueuing event with specific priority."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="priority")
    queue.enqueue_priority(event=event, priority=50)
    assert queue.count_current() == 1


def test_priority_ordering_lower_first() -> None:
    """Test events processed in priority order (lower first)."""
    queue = EventQueue()
    event_low = TestEvent(timestamp=time.time(), tick=0, message="low")
    event_high = TestEvent(timestamp=time.time(), tick=0, message="high")
    event_medium = TestEvent(timestamp=time.time(), tick=0, message="medium")
    queue.enqueue_priority(event=event_high, priority=300)
    queue.enqueue_priority(event=event_low, priority=100)
    queue.enqueue_priority(event=event_medium, priority=200)
    processed_order: list[str] = []
    queue.process(handler=lambda e: processed_order.append(e.message))  # type: ignore[attr-defined]
    assert processed_order == ["low", "medium", "high"]


def test_same_priority_maintains_insertion_order() -> None:
    """Test events with same priority maintain insertion order."""
    queue = EventQueue()
    event_1 = TestEvent(timestamp=time.time(), tick=0, message="first")
    event_2 = TestEvent(timestamp=time.time(), tick=0, message="second")
    event_3 = TestEvent(timestamp=time.time(), tick=0, message="third")
    queue.enqueue_priority(event=event_1, priority=100)
    queue.enqueue_priority(event=event_2, priority=100)
    queue.enqueue_priority(event=event_3, priority=100)
    processed_order: list[str] = []
    queue.process(handler=lambda e: processed_order.append(e.message))  # type: ignore[attr-defined]
    assert processed_order == ["first", "second", "third"]


def test_same_priority_sequence_tiebreaker_orders_queued_events() -> None:
    """Test sequence tiebreaker orders equal-priority QueuedEvents."""
    earlier = QueuedEvent(
        priority=100,
        event=TestEvent(timestamp=time.time(), tick=0, message="earlier"),
        sequence=1,
    )
    later = QueuedEvent(
        priority=100,
        event=TestEvent(timestamp=time.time(), tick=0, message="later"),
        sequence=2,
    )
    assert earlier < later
    assert sorted([later, earlier]) == [earlier, later]


def test_sequence_assigned_monotonically_across_enqueues() -> None:
    """Test enqueue assigns monotonically increasing sequence values."""
    queue = EventQueue()
    for index in range(5):
        message = fake.word() + str(index)
        queue.enqueue(event=TestEvent(timestamp=time.time(), tick=0, message=message))
    sequences = [queued.sequence for queued in queue._current_buffer]
    assert sequences == sorted(sequences)
    assert len(set(sequences)) == len(sequences)


def test_enqueue_default_priority() -> None:
    """Test enqueue uses default priority of 100."""
    queue = EventQueue()
    event_default = TestEvent(timestamp=time.time(), tick=0, message="default")
    event_lower = TestEvent(timestamp=time.time(), tick=0, message="lower")
    event_higher = TestEvent(timestamp=time.time(), tick=0, message="higher")
    queue.enqueue(event=event_default)
    queue.enqueue_priority(event=event_lower, priority=50)
    queue.enqueue_priority(event=event_higher, priority=150)
    processed_order: list[str] = []
    queue.process(handler=lambda e: processed_order.append(e.message))  # type: ignore[attr-defined]
    assert processed_order == ["lower", "default", "higher"]


def test_multiple_events_different_types() -> None:
    """Test queue handles multiple event types."""
    queue = EventQueue()
    event_1 = TestEvent(timestamp=time.time(), tick=0, message="test")
    event_2 = AnotherEvent(timestamp=time.time(), tick=0, value=42)
    queue.enqueue(event=event_1)
    queue.enqueue(event=event_2)
    assert queue.count_current() == 2


def test_process_with_no_events() -> None:
    """Test processing empty queue completes without error."""
    queue = EventQueue()
    handler = MagicMock()
    queue.process(handler=handler)
    handler.assert_not_called()


def test_swap_buffers_with_empty_queue() -> None:
    """Test swapping buffers with no events."""
    queue = EventQueue()
    queue.swap_buffers()
    assert queue.count_current() == 0
    assert queue.count_next() == 0


def test_multiple_swaps() -> None:
    """Test multiple buffer swaps in sequence."""
    queue = EventQueue()
    event_1 = TestEvent(timestamp=time.time(), tick=0, message="first")
    event_2 = TestEvent(timestamp=time.time(), tick=0, message="second")
    queue.enqueue(event=event_1, delay_frames=1)
    queue.swap_buffers()
    queue.enqueue(event=event_2, delay_frames=1)
    queue.swap_buffers()
    assert queue.count_current() == 1


def test_delayed_events_not_processed_before_swap() -> None:
    """Test delayed events not processed until after swap."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="delayed")
    queue.enqueue(event=event, delay_frames=1)
    handler = MagicMock()
    queue.process(handler=handler)
    handler.assert_not_called()


def test_delayed_events_processed_after_swap() -> None:
    """Test delayed events processed after buffer swap."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="delayed")
    queue.enqueue(event=event, delay_frames=1)
    queue.swap_buffers()
    handler = MagicMock()
    queue.process(handler=handler)
    handler.assert_called_once_with(event)


def test_count_current_returns_zero_initially() -> None:
    """Test count_current returns zero for new queue."""
    queue = EventQueue()
    assert queue.count_current() == 0


def test_count_next_returns_zero_initially() -> None:
    """Test count_next returns zero for new queue."""
    queue = EventQueue()
    assert queue.count_next() == 0


def test_enqueue_priority_with_delay() -> None:
    """Test priority events can be delayed."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="priority delayed")
    queue.enqueue_priority(event=event, priority=50, delay_frames=1)
    assert queue.count_current() == 0
    assert queue.count_next() == 1


def test_priority_ordering_in_next_buffer() -> None:
    """Test priority ordering maintained in next buffer after swap."""
    queue = EventQueue()
    event_low = TestEvent(timestamp=time.time(), tick=0, message="low")
    event_high = TestEvent(timestamp=time.time(), tick=0, message="high")
    queue.enqueue_priority(event=event_high, priority=200, delay_frames=1)
    queue.enqueue_priority(event=event_low, priority=100, delay_frames=1)
    queue.swap_buffers()
    processed_order: list[str] = []
    queue.process(handler=lambda e: processed_order.append(e.message))  # type: ignore[attr-defined]
    assert processed_order == ["low", "high"]


def test_mixed_current_and_delayed_events() -> None:
    """Test queue handles mix of current and delayed events."""
    queue = EventQueue()
    event_current = TestEvent(timestamp=time.time(), tick=0, message="current")
    event_delayed = TestEvent(timestamp=time.time(), tick=0, message="delayed")
    queue.enqueue(event=event_current)
    queue.enqueue(event=event_delayed, delay_frames=1)
    assert queue.count_current() == 1
    assert queue.count_next() == 1


def test_process_multiple_times() -> None:
    """Test processing queue multiple times."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    queue.enqueue(event=event)
    queue.process(handler=lambda e: None)
    queue.process(handler=lambda e: None)
    assert queue.count_current() == 0


def test_large_number_of_events() -> None:
    """Test queue handles large number of events."""
    queue = EventQueue()
    for i in range(1000):
        event = TestEvent(timestamp=time.time(), tick=0, message=f"event_{i}")
        queue.enqueue(event=event)
    assert queue.count_current() == 1000
    queue.process(handler=lambda e: None)
    assert queue.count_current() == 0


def test_negative_priority() -> None:
    """Test events can have negative priority."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="negative")
    queue.enqueue_priority(event=event, priority=-100)
    assert queue.count_current() == 1


def test_zero_priority() -> None:
    """Test events can have zero priority."""
    queue = EventQueue()
    event = TestEvent(timestamp=time.time(), tick=0, message="zero")
    queue.enqueue_priority(event=event, priority=0)
    assert queue.count_current() == 1


def test_insort_matches_append_then_sort_for_random_interleavings() -> None:
    """Buffer state after every enqueue equals the legacy append+sort result."""
    queue = EventQueue()
    reference: list[tuple[int, int]] = []

    for index in range(200):
        priority = fake.random_int(min=-5, max=5)
        queue.enqueue_priority(
            event=TestEvent(timestamp=time.time(), tick=0, message=f"event_{index}"),
            priority=priority,
        )
        reference.append((priority, index))
        reference.sort()

        assert [
            (queued.priority, queued.sequence) for queued in queue._current_buffer
        ] == reference


def test_mid_process_enqueue_inserts_into_live_buffer() -> None:
    """Same-frame events emitted during process() keep their sorted position."""
    queue = EventQueue()
    processed: list[str] = []

    def handler(event: Event) -> None:
        message = event.message  # type: ignore[attr-defined]
        processed.append(message)
        if message == "first":
            queue.enqueue_priority(
                event=TestEvent(timestamp=time.time(), tick=0, message="emitted"),
                priority=15,
            )

    queue.enqueue_priority(
        event=TestEvent(timestamp=time.time(), tick=0, message="first"),
        priority=10,
    )
    queue.enqueue_priority(
        event=TestEvent(timestamp=time.time(), tick=0, message="second"),
        priority=20,
    )

    queue.process(handler=handler)

    assert processed == ["first", "emitted", "second"]
