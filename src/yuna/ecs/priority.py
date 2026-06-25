"""Priority calculation for fair entity request processing."""

from typing import TYPE_CHECKING, Protocol

from yuna.types.identifiers import EntityID

if TYPE_CHECKING:
    from yuna.ecs.world import ECSWorld


class PriorityCalculator(Protocol):
    """Interface for calculating entity priority for request processing.

    Implementations define game-specific priority logic based on entity state.
    Systems pass calculator to world.sort_entities_by_priority() as needed.

    Design Philosophy:
    - Game-agnostic interface (belongs in CORE)
    - Implementation-specific logic (belongs in game code)
    - Deterministic results (same state = same priority)
    - Stateless (no side effects, pure calculation)
    - Flexible (different calculators for different scenarios)

    Usage:
        calculator = MyPriorityCalculator()
        sorted_ids = world.sort_entities_by_priority(
            entity_ids=request_ids,
            priority_calculator=calculator,
            tick=world.tick,
        )
    """

    def calculate_priority(self, entity_id: EntityID, world: ECSWorld) -> float:
        """Calculate priority value for entity.

        Higher values = higher priority = acts first.

        Args:
            entity_id: Entity to calculate priority for
            world: ECS world instance

        Returns:
            Priority value (typically 0.0-1.0, but any float valid)

        Note:
            This method must be pure - same inputs = same output.
            No side effects or state mutations allowed.
        """
        ...  # pragma: no cover


class EqualPriorityCalculator:
    """All entities get equal priority.

    Useful for scenarios where priority doesn't matter or
    pure random ordering (with tie-breaking) is desired.
    """

    def calculate_priority(self, entity_id: EntityID, world: ECSWorld) -> float:
        """Return equal priority for all entities.

        Args:
            entity_id: Entity to calculate priority for
            world: ECS world instance

        Returns:
            Fixed priority of 0.5
        """
        return 0.5
