"""Spatial grid for O(1) position-based entity lookups."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from yuna.profiling.monitor import get_performance_monitor
from yuna.spatial.collision import CollisionMode
from yuna.types.vector import Vector2

try:
    from engine_native import SpatialIndex as NativeSpatialIndex
except ImportError:  # pragma: no cover
    NativeSpatialIndex = None

if TYPE_CHECKING:
    from yuna.ecs.component import Component
    from yuna.ecs.world import ECSWorld
    from yuna.types.identifiers import EntityID

ENTITY_HIT_RADIUS = 0.5
CELL_HALF_EXTENT = 0.5
RAY_DIRECTION_EPSILON = 1e-10
RAY_INTERSECTION_EPSILON = 1e-10


class SpatialGrid:
    """Grid-based spatial index for fast entity position queries.

    Responsibilities:
    - Maintain spatial index of entities by position
    - Provide O(1) point queries
    - Provide efficient radius queries
    - Update entity positions

    Usage:
        grid = SpatialGrid(cell_size=10)
        grid.add(entity_id=entity, position=Vector2(x=5.0, y=5.0))
        entities = grid.get_at(position=Vector2(x=5.0, y=5.0))
    """

    def __init__(
        self,
        cell_size: int,
        profiling_enabled: bool = False,
        collision_mode: CollisionMode = CollisionMode.CIRCLE,
        native_raycast: bool = False,
    ):
        """Initialize spatial grid.

        Args:
            cell_size: Size of each grid cell for spatial hashing
            profiling_enabled: Whether to enable performance profiling
            collision_mode: Collision detection mode for raycast queries
            native_raycast: Route raycasts through the optional engine_native
                extension module. Requires an installed engine_native package
                providing SpatialIndex; when absent, the flag is inert and
                raycasts silently use the pure-Python path, which is the
                reference implementation and behaviorally identical.
        """
        self._cell_size = cell_size
        self._grid: dict[tuple[int, int], set[EntityID]] = {}
        self._entity_positions: dict[EntityID, Vector2] = {}
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None
        self._collision_mode = collision_mode
        self._world: ECSWorld | None = None
        self._tick = -1
        self._component_cache: dict[type, dict[EntityID, Vector2]] = {}
        self._static_component_cache: dict[type, set[Vector2]] = {}
        self._static_version = 0
        self._native_index = (
            NativeSpatialIndex(
                cell_size=float(cell_size),
                grid_box_mode=collision_mode == CollisionMode.GRID_BOX,
            )
            if native_raycast and NativeSpatialIndex is not None
            else None
        )

    def _get_cell(self, position: Vector2) -> tuple[int, int]:
        """Calculate grid cell coordinates for a position.

        Args:
            position: World position

        Returns:
            Grid cell coordinates (cell_x, cell_y)
        """
        return (
            math.floor(position.x / self._cell_size),
            math.floor(position.y / self._cell_size),
        )

    def add(self, entity_id: EntityID, position: Vector2) -> None:
        """Add entity to spatial grid at position.

        Args:
            entity_id: Entity to add
            position: Position of entity
        """
        if self._native_index is not None:
            self._native_index.add(entity_id=str(entity_id), x=position.x, y=position.y)
        cell = self._get_cell(position=position)
        if cell not in self._grid:
            self._grid[cell] = set()
        self._grid[cell].add(entity_id)
        self._entity_positions[entity_id] = position

    def remove(self, entity_id: EntityID) -> None:
        """Remove entity from spatial grid.

        Args:
            entity_id: Entity to remove
        """
        if self._native_index is not None:
            self._native_index.remove(entity_id=str(entity_id))
        if entity_id not in self._entity_positions:
            return
        position = self._entity_positions[entity_id]
        cell = self._get_cell(position=position)
        if cell in self._grid:
            self._grid[cell].discard(entity_id)
            if not self._grid[cell]:
                del self._grid[cell]
        del self._entity_positions[entity_id]

    def move(self, entity_id: EntityID, new_position: Vector2) -> None:
        """Update entity position in spatial grid.

        Args:
            entity_id: Entity to move
            new_position: New position
        """
        if self._native_index is not None:
            self._native_index.move_entity(
                entity_id=str(entity_id),
                new_x=new_position.x,
                new_y=new_position.y,
            )
        if entity_id in self._entity_positions:
            old_position = self._entity_positions[entity_id]
            if old_position == new_position:
                return
            old_cell = self._get_cell(position=old_position)
            new_cell = self._get_cell(position=new_position)
            if old_cell != new_cell:
                if old_cell in self._grid:
                    self._grid[old_cell].discard(entity_id)
                    if not self._grid[old_cell]:
                        del self._grid[old_cell]
                if new_cell not in self._grid:
                    self._grid[new_cell] = set()
                self._grid[new_cell].add(entity_id)
        else:
            cell = self._get_cell(position=new_position)
            if cell not in self._grid:
                self._grid[cell] = set()
            self._grid[cell].add(entity_id)
        self._entity_positions[entity_id] = new_position

    def get_at(self, position: Vector2) -> set[EntityID]:
        """Get all entities at a specific position (O(1) lookup).

        Args:
            position: Position to query

        Returns:
            Set of entity IDs at that position
        """
        cell = self._get_cell(position=position)
        return self._grid.get(cell, set()).copy()

    def _collect_cell_candidates(
        self,
        min_cell_x: int,
        max_cell_x: int,
        min_cell_y: int,
        max_cell_y: int,
    ) -> set[EntityID]:
        """Union the entity sets of occupied cells inside a cell bounding box.

        Picks the scan with fewer cells to visit: every cell in the bounding
        box, or only the occupied cells when the box is larger than the
        occupied set. Occupied cells are visited in sorted (x, y) order,
        matching the bounding-box scan's lexicographic order, so the
        candidate set is built by an identical insertion sequence and
        iterates identically in both branches.

        Args:
            min_cell_x: Minimum cell x coordinate, inclusive
            max_cell_x: Maximum cell x coordinate, inclusive
            min_cell_y: Minimum cell y coordinate, inclusive
            max_cell_y: Maximum cell y coordinate, inclusive

        Returns:
            Set of entity IDs registered in cells within the bounding box
        """
        candidates: set[EntityID] = set()
        if (max_cell_x - min_cell_x + 1) * (max_cell_y - min_cell_y + 1) > len(
            self._grid
        ):
            for cell in sorted(
                cell
                for cell in self._grid
                if min_cell_x <= cell[0] <= max_cell_x
                and min_cell_y <= cell[1] <= max_cell_y
            ):
                candidates.update(self._grid[cell])
            return candidates
        for cell_x in range(min_cell_x, max_cell_x + 1):
            for cell_y in range(min_cell_y, max_cell_y + 1):
                cell_entities = self._grid.get((cell_x, cell_y))
                if cell_entities:
                    candidates.update(cell_entities)
        return candidates

    def get_in_radius(
        self,
        position: Vector2,
        radius: float,
        predicate: Callable[[EntityID], bool] | None = None,
    ) -> set[EntityID]:
        """Get all entities within radius of position.

        Args:
            position: Center position
            radius: Search radius
            predicate: Optional predicate that returns True for entities to include

        Returns:
            Set of entity IDs within radius that pass the predicate
        """
        min_cell_x = math.floor((position.x - radius) / self._cell_size)
        max_cell_x = math.floor((position.x + radius) / self._cell_size)
        min_cell_y = math.floor((position.y - radius) / self._cell_size)
        max_cell_y = math.floor((position.y + radius) / self._cell_size)

        candidates = self._collect_cell_candidates(
            min_cell_x=min_cell_x,
            max_cell_x=max_cell_x,
            min_cell_y=min_cell_y,
            max_cell_y=max_cell_y,
        )

        result: set[EntityID] = set()
        for entity_id in candidates:
            entity_position = self._entity_positions[entity_id]
            if entity_position.distance(other=position) <= radius:
                if predicate is None or predicate(entity_id):
                    result.add(entity_id)

        return result

    def get_in_bounds(self, min_pos: Vector2, max_pos: Vector2) -> set[EntityID]:
        """Get all entities within rectangular bounds.

        Args:
            min_pos: Minimum corner of rectangle
            max_pos: Maximum corner of rectangle

        Returns:
            Set of entity IDs within bounds
        """
        min_cell_x = math.floor(min_pos.x / self._cell_size)
        max_cell_x = math.floor(max_pos.x / self._cell_size)
        min_cell_y = math.floor(min_pos.y / self._cell_size)
        max_cell_y = math.floor(max_pos.y / self._cell_size)

        candidates = self._collect_cell_candidates(
            min_cell_x=min_cell_x,
            max_cell_x=max_cell_x,
            min_cell_y=min_cell_y,
            max_cell_y=max_cell_y,
        )

        result: set[EntityID] = set()
        for entity_id in candidates:
            entity_position = self._entity_positions[entity_id]
            if (
                min_pos.x <= entity_position.x <= max_pos.x
                and min_pos.y <= entity_position.y <= max_pos.y
            ):
                result.add(entity_id)

        return result

    def raycast(
        self,
        origin: Vector2,
        direction: Vector2,
        max_distance: float,
    ) -> list[EntityID]:
        """Cast ray and return entities intersected in order.

        Args:
            origin: Ray start position
            direction: Ray direction (should be normalized)
            max_distance: Maximum ray distance

        Returns:
            List of entity IDs intersected, ordered by distance from origin
        """
        if self._native_index is not None and all(
            math.isfinite(component)
            for component in (
                origin.x,
                origin.y,
                direction.x,
                direction.y,
                max_distance,
                origin.x + direction.x * max_distance,
                origin.y + direction.y * max_distance,
            )
        ):
            return cast(
                "list[EntityID]",
                self._native_index.raycast(
                    origin_x=origin.x,
                    origin_y=origin.y,
                    dir_x=direction.x,
                    dir_y=direction.y,
                    max_distance=max_distance,
                ),
            )

        end_point = origin.add(other=direction.multiply(scalar=max_distance))
        min_x = min(origin.x, end_point.x)
        max_x = max(origin.x, end_point.x)
        min_y = min(origin.y, end_point.y)
        max_y = max(origin.y, end_point.y)

        candidates = self.get_in_bounds(
            min_pos=Vector2(x=min_x, y=min_y),
            max_pos=Vector2(x=max_x, y=max_y),
        )

        hits: list[tuple[float, EntityID]] = []
        for entity_id in candidates:
            entity_position = self._entity_positions[entity_id]

            if self._collision_mode == CollisionMode.CIRCLE:
                to_entity = entity_position.subtract(other=origin)
                projection_length = (
                    to_entity.x * direction.x + to_entity.y * direction.y
                )

                if 0 <= projection_length <= max_distance:
                    projection = direction.multiply(scalar=projection_length)
                    closest_point = origin.add(other=projection)
                    distance_to_ray = entity_position.distance(other=closest_point)

                    if distance_to_ray <= ENTITY_HIT_RADIUS:
                        hits.append((projection_length, entity_id))

            elif self._collision_mode == CollisionMode.GRID_BOX:
                intersection_distance = self._ray_box_intersection(
                    ray_origin=origin,
                    ray_dir_x=direction.x,
                    ray_dir_y=direction.y,
                    box_x=entity_position.x,
                    box_y=entity_position.y,
                    max_distance=max_distance,
                )

                if intersection_distance is not None:
                    hits.append((intersection_distance, entity_id))

        hits.sort(key=lambda x: (x[0], x[1]))
        return [entity_id for _, entity_id in hits]

    @staticmethod
    def _ray_box_intersection(
        ray_origin: Vector2,
        ray_dir_x: float,
        ray_dir_y: float,
        box_x: float,
        box_y: float,
        max_distance: float,
    ) -> float | None:
        """Calculate ray-AABB intersection for a 1×1 grid cell.

        Uses slab method for axis-aligned bounding box intersection. An entity
        at position (x, y) occupies the 1×1 box CENTERED on its position, from
        (x - 0.5, y - 0.5) to (x + 0.5, y + 0.5). Centering matches the CIRCLE
        collision mode (radius ENTITY_HIT_RADIUS around the position) so every
        raycast caller treats a position as the cell center rather than a
        corner; aiming at a target's position therefore
        sends the ray through the interior of its cell instead of grazing the
        shared corner of four cells.

        Args:
            ray_origin: Ray starting position
            ray_dir_x: Ray direction X component (should be normalized)
            ray_dir_y: Ray direction Y component (should be normalized)
            box_x: Grid cell X position (cell center)
            box_y: Grid cell Y position (cell center)
            max_distance: Maximum ray distance

        Returns:
            Distance to intersection point, or None if no intersection
        """
        box_min_x = box_x - CELL_HALF_EXTENT
        box_max_x = box_x + CELL_HALF_EXTENT
        box_min_y = box_y - CELL_HALF_EXTENT
        box_max_y = box_y + CELL_HALF_EXTENT

        if abs(ray_dir_x) < RAY_DIRECTION_EPSILON:
            t_min_x = float("-inf")
            t_max_x = float("inf")
        else:
            t1_x = (box_min_x - ray_origin.x) / ray_dir_x
            t2_x = (box_max_x - ray_origin.x) / ray_dir_x
            t_min_x = min(t1_x, t2_x)
            t_max_x = max(t1_x, t2_x)

        if abs(ray_dir_y) < RAY_DIRECTION_EPSILON:
            t_min_y = float("-inf")
            t_max_y = float("inf")
        else:
            t1_y = (box_min_y - ray_origin.y) / ray_dir_y
            t2_y = (box_max_y - ray_origin.y) / ray_dir_y
            t_min_y = min(t1_y, t2_y)
            t_max_y = max(t1_y, t2_y)

        t_near = max(t_min_x, t_min_y)
        t_far = min(t_max_x, t_max_y)

        if (
            t_near > t_far + RAY_INTERSECTION_EPSILON
            or t_far < 0
            or t_near > max_distance
        ):
            return None

        return max(t_near, 0.0)

    @staticmethod
    def ray_box_entry_point(
        ray_origin: Vector2,
        ray_direction: Vector2,
        box_position: Vector2,
        max_distance: float,
    ) -> Vector2 | None:
        """Calculate exact ray-AABB entry point on target grid cell.

        Args:
            ray_origin: Ray starting position
            ray_direction: Ray direction (should be normalized)
            box_position: Grid cell position of target
            max_distance: Maximum ray distance

        Returns:
            Vector2 intersection point, or None if no intersection
        """
        t_near = SpatialGrid._ray_box_intersection(
            ray_origin=ray_origin,
            ray_dir_x=ray_direction.x,
            ray_dir_y=ray_direction.y,
            box_x=box_position.x,
            box_y=box_position.y,
            max_distance=max_distance,
        )
        if t_near is None:
            return None
        return ray_origin.add(other=ray_direction.multiply(scalar=t_near))

    def get_in_radius_along_ray(
        self,
        origin: Vector2,
        direction: Vector2,
        max_distance: float,
        radius: float,
    ) -> list[EntityID]:
        """Get entities within radius of ray path, ordered by distance along ray.

        Returns entities that are within `radius` distance of any point along
        the ray from origin to origin + direction * max_distance. This is
        equivalent to a capsule/swept-sphere query.

        Args:
            origin: Ray start position
            direction: Ray direction (should be normalized)
            max_distance: Maximum ray distance
            radius: Radius around ray path to search

        Returns:
            List of entity IDs within radius of ray, ordered near-to-far along ray
        """
        end_point = origin.add(other=direction.multiply(scalar=max_distance))
        min_x = min(origin.x, end_point.x) - radius
        max_x = max(origin.x, end_point.x) + radius
        min_y = min(origin.y, end_point.y) - radius
        max_y = max(origin.y, end_point.y) + radius

        candidates = self.get_in_bounds(
            min_pos=Vector2(x=min_x, y=min_y),
            max_pos=Vector2(x=max_x, y=max_y),
        )

        hits: list[tuple[float, EntityID]] = []
        for entity_id in candidates:
            entity_position = self._entity_positions[entity_id]

            to_entity = entity_position.subtract(other=origin)
            projection_length = to_entity.x * direction.x + to_entity.y * direction.y

            if projection_length < 0:
                distance_to_ray = entity_position.distance(other=origin)
            elif projection_length > max_distance:
                distance_to_ray = entity_position.distance(other=end_point)
            else:
                projection = direction.multiply(scalar=projection_length)
                closest_point = origin.add(other=projection)
                distance_to_ray = entity_position.distance(other=closest_point)

            if distance_to_ray <= radius:
                hits.append((max(0.0, projection_length), entity_id))

        hits.sort(key=lambda x: (x[0], x[1]))
        return [entity_id for _, entity_id in hits]

    @staticmethod
    def get_grid_cells_along_ray(
        origin: Vector2,
        direction: Vector2,
        max_distance: float,
    ) -> list[Vector2]:
        """Get grid cell coordinates ray passes through using DDA algorithm.

        Uses Digital Differential Analyzer algorithm to efficiently traverse
        grid cells. Returns grid coordinates as integers (floor values).

        Args:
            origin: Ray start position
            direction: Ray direction (should be normalized)
            max_distance: Maximum ray distance to traverse

        Returns:
            List of Vector2 positions representing grid cell coordinates
        """
        cells: list[Vector2] = []

        current_cell_x = int(math.floor(origin.x))
        current_cell_y = int(math.floor(origin.y))

        step_x = 1 if direction.x >= 0 else -1
        step_y = 1 if direction.y >= 0 else -1

        if abs(direction.x) < RAY_DIRECTION_EPSILON:
            delta_t_x = float("inf")
            next_t_x = float("inf")
        else:
            delta_t_x = abs(1.0 / direction.x)
            if direction.x >= 0:
                next_t_x = (current_cell_x + 1 - origin.x) / direction.x
            else:
                next_t_x = (current_cell_x - origin.x) / direction.x

        if abs(direction.y) < RAY_DIRECTION_EPSILON:
            delta_t_y = float("inf")
            next_t_y = float("inf")
        else:
            delta_t_y = abs(1.0 / direction.y)
            if direction.y >= 0:
                next_t_y = (current_cell_y + 1 - origin.y) / direction.y
            else:
                next_t_y = (current_cell_y - origin.y) / direction.y

        cells.append(Vector2(x=float(current_cell_x), y=float(current_cell_y)))

        while True:
            if next_t_x < next_t_y:
                if next_t_x > max_distance + RAY_DIRECTION_EPSILON:
                    break
                current_cell_x += step_x
                next_t_x += delta_t_x
            else:
                if next_t_y > max_distance + RAY_DIRECTION_EPSILON:
                    break
                current_cell_y += step_y
                next_t_y += delta_t_y

            cells.append(Vector2(x=float(current_cell_x), y=float(current_cell_y)))

        return cells

    def get_nearest(self, position: Vector2, count: int) -> list[EntityID]:
        """Get k-nearest entities to position using progressive radius expansion.

        Uses progressive radius expansion for O(k log k) complexity instead of
        O(n log n). Starts with cell-size radius and expands until k entities found.

        Args:
            position: Query position
            count: Number of nearest entities to return

        Returns:
            List of entity IDs ordered by distance (closest first)
        """
        if self._monitor:
            with self._monitor.sample(category="spatial", name="get_nearest"):
                return self._execute_get_nearest(position=position, count=count)
        return self._execute_get_nearest(position=position, count=count)

    def _execute_get_nearest(self, position: Vector2, count: int) -> list[EntityID]:
        """Execute get_nearest query logic."""
        if count <= 0:
            return []

        total_entities = len(self._entity_positions)
        if total_entities == 0:
            return []

        if count >= total_entities:
            distances: list[tuple[float, EntityID]] = []
            for entity_id, entity_position in self._entity_positions.items():
                distance = entity_position.distance(other=position)
                distances.append((distance, entity_id))
            distances.sort(key=lambda x: (x[0], x[1]))
            return [entity_id for _, entity_id in distances]

        radius = float(self._cell_size)
        max_radius = 10000.0

        while radius <= max_radius:
            candidates = self.get_in_radius(position=position, radius=radius)

            if len(candidates) >= count:
                distances = []
                for entity_id in candidates:
                    entity_position = self._entity_positions[entity_id]
                    distance = entity_position.distance(other=position)
                    distances.append((distance, entity_id))

                distances.sort(key=lambda x: (x[0], x[1]))
                return [entity_id for _, entity_id in distances[:count]]

            radius *= 2

        distances = []
        for entity_id, entity_position in self._entity_positions.items():
            distance = entity_position.distance(other=position)
            distances.append((distance, entity_id))

        distances.sort(key=lambda x: (x[0], x[1]))
        return [entity_id for _, entity_id in distances[:count]]

    def set_world(self, world: ECSWorld) -> None:
        """Wire spatial grid to ECS world for component-based queries.

        Args:
            world: ECS world instance
        """
        self._world = world

    def get_positions_filtered(
        self,
        predicate: Callable[[EntityID], bool],
    ) -> dict[EntityID, Vector2]:
        """Get entity positions filtered by predicate function.

        Uses cached positions from spatial grid without ECS query.
        Predicate receives entity_id and returns True to include entity.

        Args:
            predicate: Function that returns True for entities to include

        Returns:
            Mapping of entity_id to position for entities matching predicate
        """
        return {
            entity_id: position
            for entity_id, position in self._entity_positions.items()
            if predicate(entity_id)
        }

    def get_positions_by_component(
        self,
        component_type: type[Component],
        exclude_entity: EntityID | None = None,
    ) -> dict[EntityID, Vector2]:
        """Get positions for all entities with specified component type.

        Caches results per tick to eliminate duplicate ECS queries.
        Updates cache only when tick changes for optimal performance.

        Args:
            component_type: Component type to filter by
            exclude_entity: Optional entity ID to exclude from results

        Returns:
            Mapping of entity_id to position for matching entities
        """
        if not self._world:
            return {}

        self._update_cache_if_needed()

        if component_type not in self._component_cache:
            self._component_cache[component_type] = self._query_component_positions(
                component_type=component_type,
            )

        results = self._component_cache[component_type].copy()

        if exclude_entity and exclude_entity in results:
            del results[exclude_entity]

        return results

    def _update_cache_if_needed(self) -> None:
        """Invalidate component cache if tick changed."""
        if self._world and self._tick != self._world.tick:
            self._component_cache.clear()
            self._tick = self._world.tick

    def _query_component_positions(
        self,
        component_type: type[Component],
    ) -> dict[EntityID, Vector2]:
        """Query ECS for entities with component and return cached positions.

        Uses spatial grid's cached positions instead of Position component.

        Args:
            component_type: Component type to query

        Returns:
            Mapping of entity_id to position for entities with component
        """
        if not self._world:
            return {}

        positions: dict[EntityID, Vector2] = {}
        query = self._world.query().with_components(component_type)

        for entity_id, _ in query.iterator():
            if entity_id in self._entity_positions:
                positions[entity_id] = self._entity_positions[entity_id]

        return positions

    @property
    def static_version(self) -> int:
        """Revision of the static position caches.

        Changes only when a static entity leaves the grid, so a caller holding
        its own derived cache compares one integer per read instead of
        rebuilding on a timer or re-deriving on every call.

        Returns:
            Current static cache revision
        """
        return self._static_version

    def invalidate_static_cache(self) -> None:
        """Drop cached static positions after a static entity is removed.

        Static entities are cached without expiry because they never move, but
        they can still be removed, and a cache that outlives the entity keeps
        reporting a position nothing occupies.

        Invalidation is driven by removal rather than by the clock so an
        ordinary tick pays nothing at all: the next reader re-queries once, and
        readers tracking static_version rebuild only then.
        """
        self._static_component_cache.clear()
        self._static_version += 1

    def get_static_positions_by_component(
        self,
        component_type: type[Component],
    ) -> set[Vector2]:
        """Get positions for static entities with specified component type.

        Static entities (e.g., walls) are queried once and cached. The cache
        assumes a fixed static population: removal invalidates it, but an entity
        added after the first read is not picked up. Use this for entities that
        never move during game.

        Args:
            component_type: Component type to filter by

        Returns:
            Set of positions for static entities with component
        """
        if component_type not in self._static_component_cache:
            self._static_component_cache[component_type] = (
                self._query_static_component_positions(component_type=component_type)
            )

        return self._static_component_cache[component_type].copy()

    def _query_static_component_positions(
        self,
        component_type: type[Component],
    ) -> set[Vector2]:
        """Query ECS for static entities with component and return positions.

        Args:
            component_type: Component type to query

        Returns:
            Set of positions for static entities with component
        """
        if not self._world:
            return set()

        positions: set[Vector2] = set()
        query = self._world.query().with_components(component_type)

        for entity_id, _ in query.iterator():
            if entity_id in self._entity_positions:
                positions.add(self._entity_positions[entity_id])

        return positions
