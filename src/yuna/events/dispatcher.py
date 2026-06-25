"""Event dispatcher for type-safe event subscriptions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from yuna.events.consumption import ConsumableEvent

if TYPE_CHECKING:
    from yuna.events.event import Event
    from yuna.events.filtering import EventFilter


@dataclass
class HandlerRegistration:
    """Handler registration with metadata."""

    handler: Callable[[Event], None]
    priority: int = 0
    event_filter: EventFilter | None = None
    consume: bool = False


class EventDispatcher:
    """Type-safe event dispatcher with subscriptions.

    Responsibilities:
    - Register handlers for specific event types
    - Register wildcard handlers for all events
    - Unregister handlers
    - Dispatch events to subscribed handlers

    Usage:
        dispatcher = EventDispatcher()

        def on_entity_created(event: Event) -> None:
            print(f"Entity created: {event}")

        dispatcher.subscribe(
            event_type="EntityCreatedEvent",
            handler=on_entity_created,
        )
        dispatcher.dispatch(event=entity_created_event)
    """

    def __init__(self) -> None:
        self._subscriptions: dict[str, list[HandlerRegistration]] = {}
        self._wildcard_handlers: list[HandlerRegistration] = []

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
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []

        for registration in self._subscriptions[event_type]:
            if registration.handler == handler:
                return

        registration = HandlerRegistration(
            handler=handler,
            priority=priority,
            event_filter=event_filter,
            consume=consume,
        )
        self._subscriptions[event_type].append(registration)
        self._subscriptions[event_type].sort(key=lambda r: -r.priority)

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
        for registration in self._wildcard_handlers:
            if registration.handler == handler:
                return

        registration = HandlerRegistration(
            handler=handler,
            priority=priority,
            event_filter=event_filter,
            consume=consume,
        )
        self._wildcard_handlers.append(registration)
        self._wildcard_handlers.sort(key=lambda r: -r.priority)

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
        if event_type in self._subscriptions:
            self._subscriptions[event_type] = [
                r for r in self._subscriptions[event_type] if r.handler != handler
            ]
            if not self._subscriptions[event_type]:
                del self._subscriptions[event_type]

    def unsubscribe_all(self, handler: Callable[[Event], None]) -> None:
        """Unsubscribe wildcard handler from all events.

        Args:
            handler: Wildcard handler to remove
        """
        self._wildcard_handlers = [
            r for r in self._wildcard_handlers if r.handler != handler
        ]

    def dispatch(self, event: Event) -> None:
        """Dispatch event to all subscribed handlers.

        Calls type-specific handlers first (by priority), then wildcard handlers.
        Stops dispatching if event is consumed.

        Args:
            event: Event to dispatch
        """

        event_type = event.event_type

        if event_type in self._subscriptions:
            for registration in self._subscriptions[event_type]:
                if isinstance(event, ConsumableEvent) and event.is_consumed:
                    return

                if registration.event_filter and not registration.event_filter.matches(
                    event
                ):
                    continue

                registration.handler(event)

                if registration.consume and isinstance(event, ConsumableEvent):
                    event.consume()

        for registration in self._wildcard_handlers:
            if isinstance(event, ConsumableEvent) and event.is_consumed:
                return

            if registration.event_filter and not registration.event_filter.matches(
                event
            ):
                continue

            registration.handler(event)

            if registration.consume and isinstance(event, ConsumableEvent):
                event.consume()

    def count_subscriptions(self, event_type: str) -> int:
        """Count handlers subscribed to specific event type.

        Args:
            event_type: Type of event to count

        Returns:
            Number of handlers subscribed to event type
        """
        if event_type not in self._subscriptions:
            return 0
        return len(self._subscriptions[event_type])

    def count_wildcard_subscriptions(self) -> int:
        """Count wildcard handlers subscribed to all events.

        Returns:
            Number of wildcard handlers
        """
        return len(self._wildcard_handlers)
