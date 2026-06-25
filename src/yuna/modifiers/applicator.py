"""Stat applicator for writing modifier results to components."""

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from yuna.types.identifiers import EntityID


class StatApplicator(Protocol):
    """Protocol for applying stat modifications to world components.

    Games implement this to define how final modifier values
    get written back to components. Keeps CORE generic while
    allowing game-specific component updates.

    Design Philosophy:
    - Optional mechanism (games can use final_values dict instead)
    - Per-stat flexibility (different stats, different logic)
    - Clean separation (modification vs application)
    - Type-safe (protocol-based interface)

    Usage:
        def apply_health(entity_id: EntityID, stat: str, value: float, world: Any):
            telemetry = world.get_component(entity_id, TelemetryComponent)
            telemetry.health = value
            world.add_component(entity_id, telemetry)

        config.register_applicator(stat="health", applicator=apply_health)
    """

    def __call__(
        self, entity_id: EntityID, stat: str, value: float, world: Any
    ) -> None:
        """Apply final stat value to world component.

        Args:
            entity_id: Entity to modify
            stat: Stat name being applied
            value: Final computed value after all modifiers
            world: Game world for component access
        """
        ...  # pragma: no cover
