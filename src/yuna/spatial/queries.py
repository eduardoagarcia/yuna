"""Spatial query interface for efficient position-based lookups."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from yuna.types.identifiers import EntityID
    from yuna.types.vector import Vector2


@runtime_checkable
class SpatialQuery(Protocol):
    """Protocol defining spatial query operations.

    Responsibilities:
    - Define interface for spatial lookups
    - Support point queries
    - Support radius queries

    Usage:
        spatial: SpatialQuery = SpatialGrid(cell_size=10)
        entities = spatial.get_at(position=Vector2(x=5.0, y=5.0))
    """

    def get_at(self, position: Vector2) -> set[EntityID]:
        """Get all entities at a specific position.

        Args:
            position: The position to query

        Returns:
            Set of entity IDs at that position
        """

    def get_in_radius(self, position: Vector2, radius: float) -> set[EntityID]:
        """Get all entities within radius of position.

        Args:
            position: Center position
            radius: Search radius

        Returns:
            Set of entity IDs within radius
        """

    def get_in_bounds(self, min_pos: Vector2, max_pos: Vector2) -> set[EntityID]:
        """Get all entities within rectangular bounds.

        Args:
            min_pos: Minimum corner of rectangle
            max_pos: Maximum corner of rectangle

        Returns:
            Set of entity IDs within bounds
        """

    def raycast(
        self,
        origin: Vector2,
        direction: Vector2,
        max_distance: float,
    ) -> list[EntityID]:
        """Cast ray and return entities intersected in order.

        Args:
            origin: Ray start position
            direction: Ray direction (normalized)
            max_distance: Maximum ray distance

        Returns:
            List of entity IDs intersected, ordered by distance from origin
        """

    def get_nearest(self, position: Vector2, count: int) -> list[EntityID]:
        """Get k-nearest entities to position.

        Args:
            position: Query position
            count: Number of nearest entities to return

        Returns:
            List of entity IDs ordered by distance (closest first)
        """
