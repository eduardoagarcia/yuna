"""Base event class for engine events."""

from abc import ABC
from dataclasses import dataclass


@dataclass(frozen=True)
class Event(ABC):
    """Base class for all engine events.

    Responsibilities:
    - Immutable event data
    - Timestamp tracking
    - Tick tracking
    - Event type identification

    All events must be frozen dataclasses extending this base class.
    Events are immutable to prevent modification during processing.

    Usage:
        @dataclass(frozen=True)
        class EntityCreatedEvent(Event):
            entity_id: EntityID

        event = EntityCreatedEvent(
            timestamp=time.time(),
            tick=100,
            entity_id=EntityID("abc123"),
        )
    """

    timestamp: float
    tick: int

    @property
    def event_type(self) -> str:
        """Get event type from class name.

        Returns:
            Class name as event type identifier
        """
        return self.__class__.__name__
