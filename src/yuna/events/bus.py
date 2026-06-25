"""Event bus combining queue and dispatcher."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from yuna.events.dispatcher import EventDispatcher
from yuna.events.queue import EventQueue

if TYPE_CHECKING:
    from yuna.events.event import Event
    from yuna.events.filtering import EventFilter


class EventBus:
    """Unified event bus combining queue and dispatcher.

    Responsibilities:
    - Queue events for deferred processing
    - Subscribe handlers to event types
    - Process and dispatch events in priority order
    - Manage frame-based event buffering

    Usage:
        bus = EventBus()

        def on_entity_created(event: Event) -> None:
            print(f"Created: {event}")

        bus.subscribe(event_type="EntityCreatedEvent", handler=on_entity_created)
        bus.emit(event=entity_created_event)
        bus.process_events()
        bus.end_tick()
    """

    def __init__(self) -> None:
        self._queue = EventQueue()
        self._dispatcher = EventDispatcher()

    def emit(self, event: Event, delay_frames: int = 0) -> None:
        """Emit event with optional frame delay.

        Args:
            event: Event to emit
            delay_frames: Number of frames to delay (0 = current frame)
        """
        self._queue.enqueue(event=event, delay_frames=delay_frames)

    def emit_priority(
        self,
        event: Event,
        priority: int,
        delay_frames: int = 0,
    ) -> None:
        """Emit event with specific priority.

        Args:
            event: Event to emit
            priority: Priority value (lower = higher priority)
            delay_frames: Number of frames to delay (0 = current frame)
        """
        self._queue.enqueue_priority(
            event=event,
            priority=priority,
            delay_frames=delay_frames,
        )

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None],
        priority: int = 0,
        event_filter: EventFilter | None = None,
        consume: bool = False,
    ) -> None:
        """Subscribe handler to specific event type.

        Args:
            event_type: Type of event to listen for
            handler: Function to call when event is dispatched
            priority: Handler priority (higher runs first, default 0)
            event_filter: Optional filter to apply before handling
            consume: Whether to consume event after handling
        """
        self._dispatcher.subscribe(
            event_type=event_type,
            handler=handler,
            priority=priority,
            event_filter=event_filter,
            consume=consume,
        )

    def subscribe_all(
        self,
        handler: Callable[[Event], None],
        priority: int = 0,
        event_filter: EventFilter | None = None,
        consume: bool = False,
    ) -> None:
        """Subscribe handler to all event types (wildcard).

        Args:
            handler: Function to call for any event
            priority: Handler priority (higher runs first, default 0)
            event_filter: Optional filter to apply before handling
            consume: Whether to consume event after handling
        """
        self._dispatcher.subscribe_all(
            handler=handler,
            priority=priority,
            event_filter=event_filter,
            consume=consume,
        )

    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None],
    ) -> None:
        """Unsubscribe handler from specific event type.

        Args:
            event_type: Type of event to stop listening for
            handler: Handler to remove
        """
        self._dispatcher.unsubscribe(event_type=event_type, handler=handler)

    def unsubscribe_all(self, handler: Callable[[Event], None]) -> None:
        """Unsubscribe wildcard handler from all events.

        Args:
            handler: Wildcard handler to remove
        """
        self._dispatcher.unsubscribe_all(handler=handler)

    def process_events(self) -> None:
        """Process all events in current frame.

        Events are processed in priority order and dispatched to handlers.
        """
        self._queue.process(handler=self._dispatcher.dispatch)

    def end_tick(self) -> None:
        """End current tick and move delayed events to current frame.

        Called at end of game tick to advance frame-based event delays.
        """
        self._queue.swap_buffers()
