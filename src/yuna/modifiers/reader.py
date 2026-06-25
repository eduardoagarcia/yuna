"""Stat value reader for reading current component values."""

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from yuna.types.identifiers import EntityID


class StatValueReader(Protocol):
    """Protocol for reading current stat values from world components.

    Games implement this to define how to extract current component values
    before modifiers are applied. Mirrors StatApplicator for read/write symmetry.

    Design Philosophy:
    - Optional mechanism (defaults to 0.0 if not registered)
    - Per-stat flexibility (different stats, different components)
    - Read current values for baseline in modifier stacking
    - Type-safe (protocol-based interface)

    Usage:
        def read_health(entity_id: EntityID, stat: str, world: Any) -> float:
            telemetry = world.get_component(entity_id, TelemetryComponent)
            return telemetry.health if telemetry else 0.0

        config.register_value_reader(stat="health", reader=read_health)
    """

    def __call__(self, entity_id: EntityID, stat: str, world: Any) -> float:
        """Read current stat value from world component.

        Args:
            entity_id: Entity to read from
            stat: Stat name to read
            world: Game world for component access

        Returns:
            Current value of stat (before modifiers applied)
        """
        ...  # pragma: no cover
