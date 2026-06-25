"""Factory for creating appropriate spatial index implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yuna.spatial.bvh import BoundingVolumeHierarchy
from yuna.spatial.grid import SpatialGrid
from yuna.spatial.quadtree import Bounds, QuadTree
from yuna.types.vector import Vector2

if TYPE_CHECKING:
    from yuna.spatial.queries import SpatialQuery

LOW_DENSITY_THRESHOLD = 0.01
LARGE_WORLD_AREA_THRESHOLD = 250000


class SpatialIndexFactory:
    """Factory for creating spatial index structures.

    Responsibilities:
    - Create appropriate spatial index for use case
    - Provide defaults for common scenarios
    - Auto-select best structure based on parameters

    Usage:
        factory = SpatialIndexFactory()
        index = factory.create_auto(
            entity_count=1000,
            world_size=Vector2(x=1000.0, y=1000.0),
        )
    """

    @staticmethod
    def create_grid(cell_size: int = 10) -> SpatialGrid:
        """Create grid-based spatial index.

        Best for:
        - Dense, evenly distributed entities
        - Small to medium worlds
        - O(1) point queries

        Args:
            cell_size: Size of each grid cell

        Returns:
            SpatialGrid instance
        """
        return SpatialGrid(cell_size=cell_size)

    @staticmethod
    def create_quadtree(
        bounds: Bounds,
        max_objects: int = 10,
        max_depth: int = 8,
    ) -> QuadTree:
        """Create quadtree-based spatial index.

        Best for:
        - Sparse, unevenly distributed entities
        - Large worlds
        - Dynamic entity counts

        Args:
            bounds: World bounds for the tree
            max_objects: Objects per node before split
            max_depth: Maximum tree depth

        Returns:
            QuadTree instance
        """
        return QuadTree(
            bounds=bounds,
            max_objects=max_objects,
            max_depth=max_depth,
        )

    @staticmethod
    def create_bvh() -> BoundingVolumeHierarchy:
        """Create BVH-based spatial index.

        Best for:
        - Raycast queries
        - Collision detection
        - Dynamic objects

        Returns:
            BoundingVolumeHierarchy instance
        """
        return BoundingVolumeHierarchy()

    @staticmethod
    def create_auto(
        entity_count: int,
        world_size: Vector2,
        min_pos: Vector2 | None = None,
    ) -> SpatialQuery:
        """Auto-select best spatial index based on parameters.

        Selection logic:
        - Small dense worlds (< 1000 entities, < 500x500): Grid
        - Large sparse worlds (> 1000 entities, > 500x500): QuadTree
        - Very large or very sparse: QuadTree

        Args:
            entity_count: Expected number of entities
            world_size: Size of the world
            min_pos: Minimum world position (default: origin)

        Returns:
            SpatialQuery implementation
        """
        if min_pos is None:
            min_pos = Vector2(x=0.0, y=0.0)

        world_area = world_size.x * world_size.y
        density = entity_count / world_area if world_area > 0 else 0

        if entity_count < 1000 and world_size.x < 500 and world_size.y < 500:
            cell_size = max(10, int(min(world_size.x, world_size.y) / 50))
            return SpatialGrid(cell_size=cell_size)

        if density < LOW_DENSITY_THRESHOLD or world_area > LARGE_WORLD_AREA_THRESHOLD:
            bounds = Bounds(
                min_x=min_pos.x,
                min_y=min_pos.y,
                max_x=min_pos.x + world_size.x,
                max_y=min_pos.y + world_size.y,
            )
            return QuadTree(bounds=bounds, max_objects=10, max_depth=8)

        cell_size = max(10, int(min(world_size.x, world_size.y) / 50))
        return SpatialGrid(cell_size=cell_size)
