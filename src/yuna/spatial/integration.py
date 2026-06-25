"""Spatial system integration with ECS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from yuna.ecs.component import Component
from yuna.ecs.markers import StaticComponent
from yuna.ecs.system import System
from yuna.spatial.collision import CollisionMode
from yuna.spatial.grid import SpatialGrid
from yuna.types.vector import Vector2

if TYPE_CHECKING:
    from yuna.ecs.world import ECSWorld
    from yuna.types.identifiers import EntityID


@dataclass(frozen=True)
class Position(Component):
    """Position component for spatial tracking.

    Attributes:
        position: 2D position vector
    """

    position: Vector2


class SpatialSystem(System):
    """System that maintains spatial grid synchronized with entity positions.

    Responsibilities:
    - Update spatial grid with current entity positions each tick
    - Synchronize grid with Position components (pull-based)
    - Provide spatial query interface
    - Handle static vs dynamic entity optimizations

    Design:
    - Runs at priority 75 to sync grid with current entity positions
    - Priority 75 leaves ample headroom (1-74) for pre-spatial systems
    - Pull-based updates: queries Position components directly
    - StaticComponent entities are added once, never updated
    - Dynamic entities are synchronized every tick

    Usage:
        spatial_system = SpatialSystem(cell_size=10)
        world.register_system(system=spatial_system)

        entities = world.spatial.get_at(position=Vector2(x=5.0, y=5.0))
        nearby = world.spatial.get_in_radius(
            position=Vector2(x=10.0, y=10.0),
            radius=5.0,
        )
    """

    def __init__(
        self,
        cell_size: int = 10,
        collision_mode: CollisionMode = CollisionMode.CIRCLE,
    ):
        """Initialize spatial system.

        Args:
            cell_size: Size of spatial grid cells
            collision_mode: Collision detection mode for spatial queries
        """
        self._grid = SpatialGrid(cell_size=cell_size, collision_mode=collision_mode)
        self._initialized = False
        self._static_entities: set[EntityID] = set()

    @property
    def priority(self) -> int:
        """Spatial system syncs grid with current entity positions.

        Priority 75 leaves headroom (1-74) for systems that update positions
        before spatial synchronization.

        Returns:
            Priority value (75)
        """
        return 75

    def update(self, world: ECSWorld, delta_time: float) -> None:
        """Update spatial system with current entity positions.

        On first update:
        - Wires grid to world.spatial
        - Adds all entities with Position components

        On subsequent updates:
        - Synchronizes dynamic entity positions with components
        - Static entities are never updated (performance optimization)

        Args:
            world: ECS world
            delta_time: Time delta (unused)
        """
        if not self._initialized:
            world._spatial_grid = self._grid
            self._initialize_grid(world=world)
            self._initialized = True
        else:
            self._sync_dynamic_entities(world=world)

    def _initialize_grid(self, world: ECSWorld) -> None:
        """Initialize grid with all entities that have Position components.

        Args:
            world: ECS world
        """
        self._grid.set_world(world=world)
        query = world.query().with_components(Position)

        for entity_id, (position_component,) in query.iterator():
            position = cast(Position, position_component)
            self._grid.add(entity_id=entity_id, position=position.position)

            if world.has_component(
                entity_id=entity_id,
                component_type=StaticComponent,
            ):
                self._static_entities.add(entity_id)

    def _sync_dynamic_entities(self, world: ECSWorld) -> None:
        """Synchronize dynamic entity positions with current component state.

        Only updates entities without StaticComponent for performance.
        Automatically handles entity creation/destruction via grid move/remove.

        Args:
            world: ECS world
        """
        current_entities: set[EntityID] = set()
        query = world.query().with_components(Position)

        for entity_id, (position_component,) in query.iterator():
            current_entities.add(entity_id)

            if entity_id in self._static_entities:
                continue

            position = cast(Position, position_component)
            self._grid.move(entity_id=entity_id, new_position=position.position)

        grid_entities = set(self._grid._entity_positions.keys())
        for entity_id in sorted(grid_entities):
            if entity_id not in current_entities:
                self._grid.remove(entity_id=entity_id)
                self._static_entities.discard(entity_id)

    def get_at(self, position: Vector2) -> set[EntityID]:
        """Get all entities at specific position.

        Args:
            position: Position to query

        Returns:
            Set of entity IDs at that position
        """
        return self._grid.get_at(position=position)

    def get_in_radius(self, position: Vector2, radius: float) -> set[EntityID]:
        """Get all entities within radius of position.

        Args:
            position: Center position
            radius: Search radius

        Returns:
            Set of entity IDs within radius
        """
        return self._grid.get_in_radius(position=position, radius=radius)
