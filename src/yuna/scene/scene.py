"""Scene implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from yuna.ecs.world import ECSWorld
from yuna.events.bus import EventBus

if TYPE_CHECKING:
    from yuna.ecs.system import System


class Scene:
    """Container for game scene with world, systems, and event bus.

    Responsibilities:
    - Manage scene-specific ECS world
    - Manage scene-specific event bus
    - Manage scene-specific systems
    - Handle scene lifecycle (load/unload)
    - Update scene systems

    Usage:
        scene = Scene(name="MainMenu")
        scene.add_system(system=MenuSystem())
        scene.load()
        scene.update(delta_time=0.016)
        scene.unload()
    """

    _next_seed: ClassVar[int] = 1

    def __init__(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
        world_seed: int | None = None,
    ) -> None:
        """Initialize scene.

        Args:
            name: Scene identifier
            metadata: Optional scene metadata
            world_seed: Seed for entity generation (auto-increments if None)
        """
        self.name = name
        if world_seed is None:
            world_seed = Scene._next_seed
            Scene._next_seed += 1
        self.world = ECSWorld(seed=world_seed)
        self.event_bus = EventBus()
        self.systems: list[System] = []
        self.metadata = metadata or {}
        self.is_loaded = False

    def add_system(self, system: System) -> None:
        """Add system to scene.

        Args:
            system: System to add
        """
        self.systems.append(system)
        self.systems.sort(key=lambda s: s.priority)

    def load(self) -> None:
        """Load scene resources and prepare for execution."""
        if self.is_loaded:
            return
        self.is_loaded = True

    def unload(self) -> None:
        """Cleanup scene resources and release memory."""
        if not self.is_loaded:
            return
        self.is_loaded = False

    def update(self, delta_time: float) -> None:
        """Update scene systems and process events.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        if not self.is_loaded:
            return

        for system in self.systems:
            system.update(world=self.world, delta_time=delta_time)

        self.event_bus.process_events()
        self.event_bus.end_tick()
