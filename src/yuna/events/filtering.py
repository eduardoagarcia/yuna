"""Event filtering for selective event handling."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from yuna.events.event import Event
    from yuna.types.identifiers import EntityID


@runtime_checkable
class EventFilter(Protocol):
    """Protocol for event filters.

    Filters determine which events should be handled by a subscriber.
    """

    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria.

        Args:
            event: Event to check

        Returns:
            True if event matches filter
        """
        ...  # pragma: no cover


class EntityFilter:
    """Filter events by entity ID.

    Usage:
        filter = EntityFilter(entity_id=my_entity)
        if filter.matches(event):
            handle_event(event)
    """

    def __init__(self, entity_id: EntityID) -> None:
        """Initialize entity filter.

        Args:
            entity_id: Entity ID to filter by
        """
        self.entity_id = entity_id

    def matches(self, event: Event) -> bool:
        """Check if event is for specific entity.

        Args:
            event: Event to check

        Returns:
            True if event has entity_id field matching filter
        """
        return hasattr(event, "entity_id") and event.entity_id == self.entity_id


class TypeFilter:
    """Filter events by event type.

    Usage:
        filter = TypeFilter(event_types=["EntityCreated", "EntityDestroyed"])
        if filter.matches(event):
            handle_event(event)
    """

    def __init__(self, event_types: list[str] | set[str]) -> None:
        """Initialize type filter.

        Args:
            event_types: Event type names to match
        """
        self.event_types = set(event_types)

    def matches(self, event: Event) -> bool:
        """Check if event type matches filter.

        Args:
            event: Event to check

        Returns:
            True if event type in filter types
        """
        return event.event_type in self.event_types


class PredicateFilter:
    """Filter events with custom predicate function.

    Usage:
        filter = PredicateFilter(predicate=lambda e: e.value > 10)
        if filter.matches(event):
            handle_event(event)
    """

    def __init__(self, predicate: Callable[[Event], bool]) -> None:
        """Initialize predicate filter.

        Args:
            predicate: Function that returns True for matching events
        """
        self.predicate = predicate

    def matches(self, event: Event) -> bool:
        """Check if event matches predicate.

        Args:
            event: Event to check

        Returns:
            True if predicate returns True for event
        """
        return self.predicate(event)


class CompositeMode(Enum):
    """Mode for combining multiple filters."""

    AND = "and"
    OR = "or"


class CompositeFilter:
    """Combine multiple filters with AND/OR logic.

    Usage:
        filter = CompositeFilter(
            filters=[entity_filter, type_filter],
            mode=CompositeMode.AND,
        )
        if filter.matches(event):
            handle_event(event)
    """

    def __init__(
        self,
        filters: list[EventFilter],
        mode: CompositeMode = CompositeMode.AND,
    ) -> None:
        """Initialize composite filter.

        Args:
            filters: List of filters to combine
            mode: AND (all must match) or OR (any must match)
        """
        self.filters = filters
        self.mode = mode

    def matches(self, event: Event) -> bool:
        """Check if event matches composite filter.

        Args:
            event: Event to check

        Returns:
            True if event matches according to mode
        """
        if not self.filters:
            return True

        if self.mode == CompositeMode.AND:
            return all(f.matches(event) for f in self.filters)

        return any(f.matches(event) for f in self.filters)
