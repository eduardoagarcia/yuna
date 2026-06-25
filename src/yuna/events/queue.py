"""Event queue with double buffering."""

from __future__ import annotations

from bisect import insort
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from yuna.resources.pools import get_global_pools

if TYPE_CHECKING:
    from yuna.events.event import Event


@dataclass(order=True)
class QueuedEvent:
    """Event wrapper with priority for queue ordering.

    Events are ordered by priority (lower = higher priority), then by
    sequence as a deterministic tiebreaker so equal-priority events
    dequeue in monotonic insertion order regardless of sort stability.
    """

    priority: int
    event: Event = field(compare=False)
    sequence: int


class EventQueue:
    """Double-buffered event queue for deferred processing.

    Responsibilities:
    - Queue events for current or future frames
    - Support priority-based ordering
    - Double buffering (current frame vs next frame)
    - Process events with handler function

    Usage:
        queue = EventQueue()
        queue.enqueue(event=my_event)
        queue.enqueue_priority(event=important_event, priority=0)
        queue.enqueue(event=delayed_event, delay_frames=1)
        queue.process(handler=lambda e: print(e))
        queue.swap_buffers()
    """

    def __init__(self) -> None:
        pools = get_global_pools()
        self._current_buffer: list[QueuedEvent] = pools.event_list.acquire()
        self._next_buffer: list[QueuedEvent] = pools.event_list.acquire()
        self._sequence = 0

    def enqueue(self, event: Event, delay_frames: int = 0) -> None:
        """Add event to queue with optional frame delay.

        Args:
            event: Event to queue
            delay_frames: Number of frames to delay (0 = current frame)
        """
        self.enqueue_priority(event=event, priority=100, delay_frames=delay_frames)

    def enqueue_priority(
        self,
        event: Event,
        priority: int,
        delay_frames: int = 0,
    ) -> None:
        """Add event to queue with specific priority.

        Args:
            event: Event to queue
            priority: Priority value (lower = higher priority)
            delay_frames: Number of frames to delay (0 = current frame)
        """
        queued = QueuedEvent(priority=priority, event=event, sequence=self._sequence)
        self._sequence += 1

        if delay_frames == 0:
            insort(a=self._current_buffer, x=queued)
        else:
            insort(a=self._next_buffer, x=queued)

    def process(self, handler: Callable[[Event], None]) -> None:
        """Process all events in current frame buffer.

        Events are processed in priority order (lower priority value first).
        Events with same priority are processed in insertion order.

        Args:
            handler: Function to call for each event
        """
        for queued in self._current_buffer:
            handler(queued.event)
        pools = get_global_pools()
        pools.event_list.release(obj=self._current_buffer)
        self._current_buffer = pools.event_list.acquire()

    def swap_buffers(self) -> None:
        """Move next frame events to current frame.

        Called at end of tick to advance delayed events.
        """
        pools = get_global_pools()
        pools.event_list.release(obj=self._current_buffer)
        self._current_buffer = self._next_buffer
        self._next_buffer = pools.event_list.acquire()

    def count_current(self) -> int:
        """Count events in current frame buffer.

        Returns:
            Number of events queued for current frame
        """
        return len(self._current_buffer)

    def count_next(self) -> int:
        """Count events in next frame buffer.

        Returns:
            Number of events queued for next frame
        """
        return len(self._next_buffer)
