"""Bounding Volume Hierarchy for efficient collision detection and raycasting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from yuna.types.vector import Vector2

if TYPE_CHECKING:
    from yuna.types.identifiers import EntityID

ENTITY_HIT_RADIUS = 0.5


@dataclass
class AABB:
    """Axis-Aligned Bounding Box."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @staticmethod
    def from_point(position: Vector2, padding: float = 0.5) -> AABB:
        """Create AABB from point with padding."""
        return AABB(
            min_x=position.x - padding,
            min_y=position.y - padding,
            max_x=position.x + padding,
            max_y=position.y + padding,
        )

    @staticmethod
    def merge(a: AABB, b: AABB) -> AABB:
        """Merge two AABBs into one that contains both."""
        return AABB(
            min_x=min(a.min_x, b.min_x),
            min_y=min(a.min_y, b.min_y),
            max_x=max(a.max_x, b.max_x),
            max_y=max(a.max_y, b.max_y),
        )

    def contains_point(self, position: Vector2) -> bool:
        """Check if point is within AABB."""
        return (
            self.min_x <= position.x <= self.max_x
            and self.min_y <= position.y <= self.max_y
        )

    def intersects_circle(self, center: Vector2, radius: float) -> bool:
        """Check if circle intersects AABB."""
        closest_x = max(self.min_x, min(center.x, self.max_x))
        closest_y = max(self.min_y, min(center.y, self.max_y))
        distance_x = center.x - closest_x
        distance_y = center.y - closest_y
        distance_squared = distance_x * distance_x + distance_y * distance_y
        return distance_squared <= radius * radius

    def intersects_aabb(self, other: AABB) -> bool:
        """Check if another AABB intersects this one."""
        return not (
            other.max_x < self.min_x
            or other.min_x > self.max_x
            or other.max_y < self.min_y
            or other.min_y > self.max_y
        )

    def surface_area(self) -> float:
        """Calculate surface area (perimeter in 2D)."""
        width = self.max_x - self.min_x
        height = self.max_y - self.min_y
        return 2 * (width + height)


class BVHNode:
    """Single node in BVH tree."""

    def __init__(self, aabb: AABB):
        self.aabb = aabb
        self.entity_id: EntityID | None = None
        self.left: BVHNode | None = None
        self.right: BVHNode | None = None

    def is_leaf(self) -> bool:
        """Check if node is a leaf."""
        return self.entity_id is not None


class BoundingVolumeHierarchy:
    """Bounding Volume Hierarchy for efficient spatial queries.

    Responsibilities:
    - Build BVH tree from entities
    - Provide efficient raycasts
    - Support range queries
    - Handle dynamic updates

    Best for:
    - Raycast queries
    - Collision detection
    - Dynamic objects with complex shapes

    Usage:
        bvh = BoundingVolumeHierarchy()
        bvh.add(entity_id=entity, position=Vector2(x=5.0, y=5.0))
        hits = bvh.raycast(
            origin=Vector2(x=0.0, y=0.0),
            direction=Vector2(x=1.0, y=0.0),
            max_distance=100.0,
        )
    """

    def __init__(self) -> None:
        """Initialize empty BVH."""
        self._root: BVHNode | None = None
        self._entity_nodes: dict[EntityID, BVHNode] = {}
        self._entity_positions: dict[EntityID, Vector2] = {}
        self._needs_rebuild = False

    def _build_tree(self, entities: list[tuple[EntityID, AABB]]) -> BVHNode | None:
        """Recursively build BVH tree.

        Args:
            entities: List of (entity_id, aabb) tuples

        Returns:
            Root node of subtree
        """
        if len(entities) == 1:
            entity_id, aabb = entities[0]
            node = BVHNode(aabb=aabb)
            node.entity_id = entity_id
            self._entity_nodes[entity_id] = node
            return node

        combined_aabb = entities[0][1]
        for _, aabb in entities[1:]:
            combined_aabb = AABB.merge(a=combined_aabb, b=aabb)

        width = combined_aabb.max_x - combined_aabb.min_x
        height = combined_aabb.max_y - combined_aabb.min_y

        if width > height:
            entities.sort(key=lambda x: ((x[1].min_x + x[1].max_x) / 2, x[0]))
        else:
            entities.sort(key=lambda x: ((x[1].min_y + x[1].max_y) / 2, x[0]))

        mid = len(entities) // 2
        left_entities = entities[:mid]
        right_entities = entities[mid:]

        node = BVHNode(aabb=combined_aabb)
        node.left = self._build_tree(entities=left_entities)
        node.right = self._build_tree(entities=right_entities)

        return node

    def _rebuild_if_needed(self) -> None:
        """Rebuild tree if marked as needing rebuild."""
        if self._needs_rebuild and self._entity_positions:
            entities = [
                (entity_id, AABB.from_point(position=position))
                for entity_id, position in self._entity_positions.items()
            ]
            self._entity_nodes.clear()
            self._root = self._build_tree(entities=entities)
            self._needs_rebuild = False

    def add(self, entity_id: EntityID, position: Vector2) -> None:
        """Add entity to BVH at position.

        Args:
            entity_id: Entity to add
            position: Position of entity
        """
        self._entity_positions[entity_id] = position
        self._needs_rebuild = True

    def remove(self, entity_id: EntityID) -> None:
        """Remove entity from BVH.

        Args:
            entity_id: Entity to remove
        """
        if entity_id in self._entity_positions:
            del self._entity_positions[entity_id]
            if entity_id in self._entity_nodes:
                del self._entity_nodes[entity_id]
            self._needs_rebuild = True

    def move(self, entity_id: EntityID, new_position: Vector2) -> None:
        """Update entity position in BVH.

        Args:
            entity_id: Entity to move
            new_position: New position
        """
        self._entity_positions[entity_id] = new_position
        self._needs_rebuild = True

    def _query_point(self, node: BVHNode | None, position: Vector2) -> set[EntityID]:
        """Recursively query point in tree."""
        if node is None:
            return set()

        if not node.aabb.contains_point(position=position):
            return set()

        if node.is_leaf():
            entity_id = cast("EntityID", node.entity_id)
            entity_position = self._entity_positions[entity_id]
            if entity_position.x == position.x and entity_position.y == position.y:
                return {entity_id}
            return set()

        result: set[EntityID] = set()
        result.update(self._query_point(node=node.left, position=position))
        result.update(self._query_point(node=node.right, position=position))
        return result

    def get_at(self, position: Vector2) -> set[EntityID]:
        """Get all entities at a specific position.

        Args:
            position: Position to query

        Returns:
            Set of entity IDs at that position
        """
        self._rebuild_if_needed()
        return self._query_point(node=self._root, position=position)

    def _query_radius(
        self,
        node: BVHNode | None,
        position: Vector2,
        radius: float,
    ) -> set[EntityID]:
        """Recursively query radius in tree."""
        if node is None:
            return set()

        if not node.aabb.intersects_circle(center=position, radius=radius):
            return set()

        if node.is_leaf():
            entity_id = cast("EntityID", node.entity_id)
            entity_position = self._entity_positions[entity_id]
            if entity_position.distance(other=position) <= radius:
                return {entity_id}
            return set()

        result: set[EntityID] = set()
        result.update(
            self._query_radius(node=node.left, position=position, radius=radius)
        )
        result.update(
            self._query_radius(node=node.right, position=position, radius=radius)
        )
        return result

    def get_in_radius(self, position: Vector2, radius: float) -> set[EntityID]:
        """Get all entities within radius of position.

        Args:
            position: Center position
            radius: Search radius

        Returns:
            Set of entity IDs within radius
        """
        self._rebuild_if_needed()
        return self._query_radius(node=self._root, position=position, radius=radius)

    def _query_aabb(self, node: BVHNode | None, aabb: AABB) -> set[EntityID]:
        """Recursively query AABB in tree."""
        if node is None:
            return set()

        if not node.aabb.intersects_aabb(other=aabb):
            return set()

        if node.is_leaf():
            entity_id = cast("EntityID", node.entity_id)
            entity_position = self._entity_positions[entity_id]
            if aabb.contains_point(position=entity_position):
                return {entity_id}
            return set()

        result: set[EntityID] = set()
        result.update(self._query_aabb(node=node.left, aabb=aabb))
        result.update(self._query_aabb(node=node.right, aabb=aabb))
        return result

    def get_in_bounds(self, min_pos: Vector2, max_pos: Vector2) -> set[EntityID]:
        """Get all entities within rectangular bounds.

        Args:
            min_pos: Minimum corner of rectangle
            max_pos: Maximum corner of rectangle

        Returns:
            Set of entity IDs within bounds
        """
        self._rebuild_if_needed()
        aabb = AABB(
            min_x=min_pos.x,
            min_y=min_pos.y,
            max_x=max_pos.x,
            max_y=max_pos.y,
        )
        return self._query_aabb(node=self._root, aabb=aabb)

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
        self._rebuild_if_needed()

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
        """Get k-nearest entities to position.

        Args:
            position: Query position
            count: Number of nearest entities to return

        Returns:
            List of entity IDs ordered by distance (closest first)
        """
        self._rebuild_if_needed()

        distances: list[tuple[float, EntityID]] = []
        for entity_id, entity_position in self._entity_positions.items():
            distance = entity_position.distance(other=position)
            distances.append((distance, entity_id))

        distances.sort(key=lambda x: (x[0], x[1]))
        return [entity_id for _, entity_id in distances[:count]]
