"""QuadTree spatial index for sparse, large worlds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from yuna.types.vector import Vector2

if TYPE_CHECKING:
    from yuna.types.identifiers import EntityID

ENTITY_HIT_RADIUS = 0.5


@dataclass
class Bounds:
    """Rectangular boundary for quadtree nodes."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def contains(self, position: Vector2) -> bool:
        """Check if position is within bounds."""
        return (
            self.min_x <= position.x <= self.max_x
            and self.min_y <= position.y <= self.max_y
        )

    def intersects_circle(self, center: Vector2, radius: float) -> bool:
        """Check if circle intersects bounds."""
        closest_x = max(self.min_x, min(center.x, self.max_x))
        closest_y = max(self.min_y, min(center.y, self.max_y))
        distance_x = center.x - closest_x
        distance_y = center.y - closest_y
        distance_squared = distance_x * distance_x + distance_y * distance_y
        return distance_squared <= radius * radius

    def intersects_bounds(self, other: Bounds) -> bool:
        """Check if another bounds intersects this one."""
        return not (
            other.max_x < self.min_x
            or other.min_x > self.max_x
            or other.max_y < self.min_y
            or other.min_y > self.max_y
        )


class QuadTreeNode:
    """Single node in quadtree structure."""

    def __init__(
        self,
        bounds: Bounds,
        max_objects: int,
        max_depth: int,
        depth: int = 0,
    ):
        self.bounds = bounds
        self.max_objects = max_objects
        self.max_depth = max_depth
        self.depth = depth
        self.entities: dict[EntityID, Vector2] = {}
        self.children: list[QuadTreeNode] | None = None

    def subdivide(self) -> None:
        """Split node into four children."""
        mid_x = (self.bounds.min_x + self.bounds.max_x) / 2
        mid_y = (self.bounds.min_y + self.bounds.max_y) / 2

        nw = QuadTreeNode(
            bounds=Bounds(
                min_x=self.bounds.min_x,
                min_y=mid_y,
                max_x=mid_x,
                max_y=self.bounds.max_y,
            ),
            max_objects=self.max_objects,
            max_depth=self.max_depth,
            depth=self.depth + 1,
        )
        ne = QuadTreeNode(
            bounds=Bounds(
                min_x=mid_x,
                min_y=mid_y,
                max_x=self.bounds.max_x,
                max_y=self.bounds.max_y,
            ),
            max_objects=self.max_objects,
            max_depth=self.max_depth,
            depth=self.depth + 1,
        )
        sw = QuadTreeNode(
            bounds=Bounds(
                min_x=self.bounds.min_x,
                min_y=self.bounds.min_y,
                max_x=mid_x,
                max_y=mid_y,
            ),
            max_objects=self.max_objects,
            max_depth=self.max_depth,
            depth=self.depth + 1,
        )
        se = QuadTreeNode(
            bounds=Bounds(
                min_x=mid_x,
                min_y=self.bounds.min_y,
                max_x=self.bounds.max_x,
                max_y=mid_y,
            ),
            max_objects=self.max_objects,
            max_depth=self.max_depth,
            depth=self.depth + 1,
        )

        self.children = [nw, ne, sw, se]

        entities_to_redistribute = list(self.entities.items())
        self.entities.clear()

        for entity_id, position in entities_to_redistribute:
            for child in self.children:
                if child.bounds.contains(position=position):
                    child.insert(entity_id=entity_id, position=position)
                    break

    def insert(self, entity_id: EntityID, position: Vector2) -> bool:
        """Insert entity into node.

        Returns:
            True if inserted successfully
        """
        if not self.bounds.contains(position=position):
            return False

        if self.children is None:
            self.entities[entity_id] = position

            if len(self.entities) > self.max_objects and self.depth < self.max_depth:
                self.subdivide()

            return True

        for child in self.children[:-1]:
            if child.insert(entity_id=entity_id, position=position):
                return True
        return self.children[-1].insert(entity_id=entity_id, position=position)

    def remove(self, entity_id: EntityID) -> bool:
        """Remove entity from node.

        Returns:
            True if removed successfully
        """
        if entity_id in self.entities:
            del self.entities[entity_id]
            return True

        if self.children is not None:
            for child in self.children:
                if child.remove(entity_id=entity_id):
                    return True

        return False

    def query_point(self, position: Vector2, result: set[EntityID]) -> None:
        """Query entities at position."""
        if not self.bounds.contains(position=position):
            return

        for entity_id, entity_position in self.entities.items():
            if entity_position.x == position.x and entity_position.y == position.y:
                result.add(entity_id)

        if self.children is not None:
            for child in self.children:
                child.query_point(position=position, result=result)

    def query_radius(
        self,
        position: Vector2,
        radius: float,
        result: set[EntityID],
    ) -> None:
        """Query entities within radius."""
        if not self.bounds.intersects_circle(center=position, radius=radius):
            return

        for entity_id, entity_position in self.entities.items():
            if entity_position.distance(other=position) <= radius:
                result.add(entity_id)

        if self.children is not None:
            for child in self.children:
                child.query_radius(position=position, radius=radius, result=result)

    def query_bounds(self, bounds: Bounds, result: set[EntityID]) -> None:
        """Query entities within bounds."""
        if not self.bounds.intersects_bounds(other=bounds):
            return

        for entity_id, entity_position in self.entities.items():
            if bounds.contains(position=entity_position):
                result.add(entity_id)

        if self.children is not None:
            for child in self.children:
                child.query_bounds(bounds=bounds, result=result)


class QuadTree:
    """QuadTree spatial index for efficient 2D spatial queries.

    Responsibilities:
    - Partition 2D space recursively into quadrants
    - Provide efficient queries for sparse, large worlds
    - Support point, radius, and range queries
    - Automatically subdivide nodes when capacity exceeded

    Better than grid for:
    - Sparse, large worlds with uneven entity distribution
    - Dynamic entity counts
    - Large radius queries

    Usage:
        tree = QuadTree(
            bounds=Bounds(min_x=0, min_y=0, max_x=1000, max_y=1000),
            max_objects=10,
            max_depth=8,
        )
        tree.add(entity_id=entity, position=Vector2(x=5.0, y=5.0))
        entities = tree.get_at(position=Vector2(x=5.0, y=5.0))
    """

    def __init__(
        self,
        bounds: Bounds,
        max_objects: int = 10,
        max_depth: int = 8,
    ):
        """Initialize quadtree.

        Args:
            bounds: World bounds for the tree
            max_objects: Objects per node before split
            max_depth: Maximum tree depth
        """
        self._root = QuadTreeNode(
            bounds=bounds,
            max_objects=max_objects,
            max_depth=max_depth,
        )
        self._entity_positions: dict[EntityID, Vector2] = {}

    def add(self, entity_id: EntityID, position: Vector2) -> None:
        """Add entity to quadtree at position.

        Args:
            entity_id: Entity to add
            position: Position of entity
        """
        self._root.insert(entity_id=entity_id, position=position)
        self._entity_positions[entity_id] = position

    def remove(self, entity_id: EntityID) -> None:
        """Remove entity from quadtree.

        Args:
            entity_id: Entity to remove
        """
        if entity_id in self._entity_positions:
            self._root.remove(entity_id=entity_id)
            del self._entity_positions[entity_id]

    def move(self, entity_id: EntityID, new_position: Vector2) -> None:
        """Update entity position in quadtree.

        Args:
            entity_id: Entity to move
            new_position: New position
        """
        if entity_id in self._entity_positions:
            self._root.remove(entity_id=entity_id)
        self._root.insert(entity_id=entity_id, position=new_position)
        self._entity_positions[entity_id] = new_position

    def get_at(self, position: Vector2) -> set[EntityID]:
        """Get all entities at a specific position.

        Args:
            position: Position to query

        Returns:
            Set of entity IDs at that position
        """
        result: set[EntityID] = set()
        self._root.query_point(position=position, result=result)
        return result

    def get_in_radius(self, position: Vector2, radius: float) -> set[EntityID]:
        """Get all entities within radius of position.

        Args:
            position: Center position
            radius: Search radius

        Returns:
            Set of entity IDs within radius
        """
        result: set[EntityID] = set()
        self._root.query_radius(position=position, radius=radius, result=result)
        return result

    def get_in_bounds(self, min_pos: Vector2, max_pos: Vector2) -> set[EntityID]:
        """Get all entities within rectangular bounds.

        Args:
            min_pos: Minimum corner of rectangle
            max_pos: Maximum corner of rectangle

        Returns:
            Set of entity IDs within bounds
        """
        bounds = Bounds(
            min_x=min_pos.x,
            min_y=min_pos.y,
            max_x=max_pos.x,
            max_y=max_pos.y,
        )
        result: set[EntityID] = set()
        self._root.query_bounds(bounds=bounds, result=result)
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
            to_entity = entity_position.subtract(other=origin)
            projection_length = to_entity.x * direction.x + to_entity.y * direction.y

            if 0 <= projection_length <= max_distance:
                projection = direction.multiply(scalar=projection_length)
                closest_point = origin.add(other=projection)
                distance_to_ray = entity_position.distance(other=closest_point)

                if distance_to_ray < ENTITY_HIT_RADIUS:
                    hits.append((projection_length, entity_id))

        hits.sort(key=lambda x: (x[0], x[1]))
        return [entity_id for _, entity_id in hits]

    def get_nearest(self, position: Vector2, count: int) -> list[EntityID]:
        """Get k-nearest entities to position using progressive radius expansion.

        Uses progressive radius expansion for O(k log k) complexity instead of
        O(n log n). Starts with small radius and expands until k entities found.

        Args:
            position: Query position
            count: Number of nearest entities to return

        Returns:
            List of entity IDs ordered by distance (closest first)
        """
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

        radius = 10.0
        max_radius = 10000.0
        candidates: set[EntityID] = set()

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
