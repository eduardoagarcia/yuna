"""Blackboard pattern for AI agent memory and state storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from yuna.ai.events import BlackboardValueChanged

if TYPE_CHECKING:
    from yuna.events.bus import EventBus
    from yuna.types.identifiers import EntityID


@dataclass
class BlackboardKey:
    """Schema definition for blackboard key with type validation.

    Responsibilities:
    - Define expected type for key
    - Provide default value
    - Document key purpose

    Usage:
        target_key = BlackboardKey(
            name="target",
            value_type=EntityID,
            description="Current combat target"
        )
        blackboard.register_key(key=target_key)
    """

    name: str
    value_type: type
    default_value: Any = None
    description: str = ""


@dataclass
class Blackboard:
    """Shared memory for AI agent with type-safe key-value storage.

    Responsibilities:
    - Store AI state and memory
    - Validate types against schema
    - Emit events on value changes
    - Provide type-safe data access

    Game-agnostic key-value store. Games define their own keys based on
    what their AI needs to track (targets, positions, states, waypoints).

    Usage:
        blackboard = Blackboard()

        blackboard.register_key(
            key=BlackboardKey(
                name="target",
                value_type=EntityID,
            )
        )

        blackboard.set_value(
            key="target",
            value=EntityID("enemy-123"),
            entity_id=agent_id,
            event_bus=bus,
        )

        target = blackboard.get_value(key="target")
    """

    data: dict[str, Any] = field(default_factory=dict)
    schema: dict[str, BlackboardKey] = field(default_factory=dict)
    emit_events: bool = True

    def register_key(self, key: BlackboardKey) -> None:
        """Register key in schema for type validation.

        Args:
            key: Key definition with type and defaults
        """
        self.schema[key.name] = key
        if key.default_value is not None:
            self.data.setdefault(key.name, key.default_value)

    def set_value(
        self,
        key: str,
        value: Any,
        entity_id: EntityID | None = None,
        event_bus: EventBus | None = None,
        tick: int = 0,
    ) -> None:
        """Set blackboard value with optional type validation and event emission.

        Args:
            key: Key name
            value: Value to set
            entity_id: Entity owning this blackboard (for events)
            event_bus: Event bus for emitting change events
            tick: Current game tick, stamped on the emitted change event

        Raises:
            TypeError: If value doesn't match schema type
        """
        if key in self.schema:
            expected_type = self.schema[key].value_type
            if not isinstance(value, expected_type):
                raise TypeError(
                    f"Key '{key}' expects {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

        old_value = self.data.get(key)
        self.data[key] = value

        if self.emit_events and event_bus is not None and entity_id is not None:
            event_bus.emit(
                event=BlackboardValueChanged.create(
                    tick=tick,
                    entity_id=entity_id,
                    key=key,
                    old_value=old_value,
                    new_value=value,
                )
            )

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get blackboard value or default.

        Args:
            key: Key name
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        return self.data.get(key, default)

    def has_key(self, key: str) -> bool:
        """Check if key exists in blackboard.

        Args:
            key: Key name

        Returns:
            True if key exists
        """
        return key in self.data

    def clear_key(self, key: str) -> None:
        """Remove key from blackboard.

        Args:
            key: Key name
        """
        if key in self.data:
            del self.data[key]

    def clear_all(self) -> None:
        """Clear all data from blackboard."""
        self.data.clear()
