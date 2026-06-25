"""Event consumption support for stopping propagation."""

from __future__ import annotations

from typing import Any
from weakref import WeakSet


class ConsumableEvent:
    """Mixin for events that can be consumed to stop propagation.

    Since Event base class is frozen, consumption state is tracked
    externally using object identity.

    Usage:
        @dataclass(frozen=True)
        class MyEvent(Event, ConsumableEvent):
            value: int

        event = MyEvent(timestamp=0.0, tick=0, value=42)
        event.consume()
        assert event.is_consumed is True
    """

    _consumed_events: WeakSet[Any] = WeakSet()

    @property
    def is_consumed(self) -> bool:
        """Check if event has been consumed.

        Returns:
            True if event is consumed
        """
        return self in ConsumableEvent._consumed_events

    def consume(self) -> None:
        """Mark event as consumed to stop further propagation."""
        ConsumableEvent._consumed_events.add(self)
