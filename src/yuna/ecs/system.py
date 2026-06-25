"""Base system class for ECS processing.

Standard System Initialization Pattern
======================================

All CORE engine systems should follow this standard initialization pattern:

Args:
    event_bus: Optional event bus for emitting and subscribing to events
    command_invoker: Optional command invoker for executing validated commands
    priority: Execution priority (lower values run earlier, default varies by system)
    [system-specific params]: Additional parameters specific to the system

Systems should:
- Accept event_bus and command_invoker as optional parameters
- Store them as instance variables if provided (even if not immediately used)
- Define sensible default priority for their use case
- Use only what they need (dependencies can be None)

Example:
    class MySystem(System):
        def __init__(
            self,
            event_bus: EventBus | None = None,
            command_invoker: CommandInvoker[ECSWorld, Any] | None = None,
            priority: int = 100,
        ) -> None:
            self._event_bus = event_bus
            self._command_invoker = command_invoker
            self._priority = priority

        @property
        def priority(self) -> int:
            return self._priority

        def update(self, world: ECSWorld, delta_time: float) -> None:
            pass

This pattern ensures:
- Uniform initialization across all systems
- Game implementations can instantiate systems uniformly
- Systems remain flexible and optional
- Future extensibility without breaking changes
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yuna.ecs.world import ECSWorld


class System(ABC):
    """Abstract base class for all ECS systems.

    Responsibilities:
    - Process entities with specific component patterns
    - Define execution order via priority
    - Query world for entities to process
    - Implement game logic in update method

    Systems are executed in priority order (lower priority = earlier execution).
    Multiple systems with same priority execute in registration order.

    Usage:
        class MovementSystem(System):
            @property
            def priority(self) -> int:
                return 100

            def update(self, world: ECSWorld, delta_time: float) -> None:
                query = world.query(Position, Velocity)
                for entity_id, (pos, vel) in query.iterator():
                    # Update position based on velocity
                    pass

        class RenderSystem(System):
            @property
            def priority(self) -> int:
                return 1000

            @property
            def process_dirty_only(self) -> bool:
                return True

            def update(self, world: ECSWorld, delta_time: float) -> None:
                query = world.query(Position, Sprite).only_dirty()
                for entity_id, (pos, sprite) in query.iterator():
                    # Only render entities with changed position or sprite
                    pass
    """

    @property
    @abstractmethod
    def priority(self) -> int:
        """Execution priority for this system.

        Lower values execute earlier. Use this to control system
        execution order (e.g., input before movement before rendering).

        Returns:
            Priority value (typically 0-1000)
        """
        ...  # pragma: no cover

    @property
    def process_dirty_only(self) -> bool:
        """Whether this system only processes dirty entities.

        Systems that opt-in to dirty-only processing should use
        query.only_dirty() to filter entities. This is useful for
        systems like rendering that only need to update when components change.

        Returns:
            True if system processes only dirty entities, False otherwise
            (default: False)
        """
        return False

    @abstractmethod
    def update(self, world: ECSWorld, delta_time: float) -> None:
        """Process entities for this system.

        Args:
            world: ECS world containing entities and components
            delta_time: Time elapsed since last update in seconds
        """
        ...  # pragma: no cover
