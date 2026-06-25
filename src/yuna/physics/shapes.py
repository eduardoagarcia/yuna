"""Collision shapes for physics engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntFlag, auto

from yuna.types.vector import Vector2


class CollisionLayer(IntFlag):
    """Collision layers for filtering."""

    LAYER_1 = auto()
    LAYER_2 = auto()
    LAYER_3 = auto()
    LAYER_4 = auto()
    LAYER_5 = auto()
    LAYER_6 = auto()
    LAYER_7 = auto()
    LAYER_8 = auto()
    ALL = LAYER_1 | LAYER_2 | LAYER_3 | LAYER_4 | LAYER_5 | LAYER_6 | LAYER_7 | LAYER_8


@dataclass
class CollisionShape(ABC):
    """Base class for collision shapes.

    Attributes:
        offset: Local offset from body center
        layer: Collision layer this shape belongs to
        mask: Collision layers this shape can collide with
    """

    offset: Vector2
    layer: CollisionLayer = CollisionLayer.LAYER_1
    mask: CollisionLayer = CollisionLayer.ALL

    @abstractmethod
    def contains_point(self, point: Vector2, position: Vector2) -> bool:
        """Check if point is inside shape.

        Args:
            point: Point to check
            position: Shape center position

        Returns:
            True if point is inside shape
        """
        pass  # pragma: no cover

    @abstractmethod
    def intersects_circle(
        self,
        circle_position: Vector2,
        circle_radius: float,
        position: Vector2,
    ) -> bool:
        """Check if shape intersects circle.

        Args:
            circle_position: Circle center
            circle_radius: Circle radius
            position: Shape center position

        Returns:
            True if shapes intersect
        """
        pass  # pragma: no cover

    def can_collide_with(self, other: CollisionShape) -> bool:
        """Check if this shape can collide with another.

        Args:
            other: Other collision shape

        Returns:
            True if collision is possible based on layers/masks
        """
        return bool((self.layer & other.mask) and (other.layer & self.mask))


@dataclass
class CircleShape(CollisionShape):
    """Circular collision shape.

    Attributes:
        radius: Circle radius
        offset: Local offset from body center
        layer: Collision layer
        mask: Collision mask
    """

    radius: float = 1.0

    def contains_point(self, point: Vector2, position: Vector2) -> bool:
        """Check if point is inside circle."""
        center = Vector2(
            x=position.x + self.offset.x,
            y=position.y + self.offset.y,
        )
        return center.distance(other=point) <= self.radius

    def intersects_circle(
        self,
        circle_position: Vector2,
        circle_radius: float,
        position: Vector2,
    ) -> bool:
        """Check if circle intersects this circle."""
        center = Vector2(
            x=position.x + self.offset.x,
            y=position.y + self.offset.y,
        )
        distance = center.distance(other=circle_position)
        return distance <= (self.radius + circle_radius)


@dataclass
class BoxShape(CollisionShape):
    """Axis-aligned box collision shape.

    Attributes:
        width: Box width
        height: Box height
        offset: Local offset from body center
        layer: Collision layer
        mask: Collision mask
    """

    width: float = 1.0
    height: float = 1.0

    def contains_point(self, point: Vector2, position: Vector2) -> bool:
        """Check if point is inside box."""
        center = Vector2(
            x=position.x + self.offset.x,
            y=position.y + self.offset.y,
        )
        half_width = self.width / 2.0
        half_height = self.height / 2.0

        return (
            center.x - half_width <= point.x <= center.x + half_width
            and center.y - half_height <= point.y <= center.y + half_height
        )

    def intersects_circle(
        self,
        circle_position: Vector2,
        circle_radius: float,
        position: Vector2,
    ) -> bool:
        """Check if box intersects circle."""
        center = Vector2(
            x=position.x + self.offset.x,
            y=position.y + self.offset.y,
        )
        half_width = self.width / 2.0
        half_height = self.height / 2.0

        closest_x = max(
            center.x - half_width,
            min(circle_position.x, center.x + half_width),
        )
        closest_y = max(
            center.y - half_height,
            min(circle_position.y, center.y + half_height),
        )

        closest = Vector2(x=closest_x, y=closest_y)
        return closest.distance(other=circle_position) <= circle_radius


@dataclass
class PolygonShape(CollisionShape):
    """Convex polygon collision shape.

    Attributes:
        vertices: Polygon vertices in local space (relative to center)
        offset: Local offset from body center
        layer: Collision layer
        mask: Collision mask
    """

    vertices: list[Vector2] = field(
        default_factory=lambda: [
            Vector2(x=0.5, y=0.0),
            Vector2(x=-0.5, y=0.5),
            Vector2(x=-0.5, y=-0.5),
        ]
    )

    def contains_point(self, point: Vector2, position: Vector2) -> bool:
        """Check if point is inside polygon using ray casting."""
        center = Vector2(
            x=position.x + self.offset.x,
            y=position.y + self.offset.y,
        )

        world_vertices = [
            Vector2(x=v.x + center.x, y=v.y + center.y) for v in self.vertices
        ]

        inside = False
        n = len(world_vertices)

        for i in range(n):
            v1 = world_vertices[i]
            v2 = world_vertices[(i + 1) % n]

            if (v1.y > point.y) != (v2.y > point.y):
                slope = (point.y - v1.y) * (v2.x - v1.x) - (point.x - v1.x) * (
                    v2.y - v1.y
                )
                if (v2.y > v1.y and slope < 0) or (v2.y < v1.y and slope > 0):
                    inside = not inside

        return inside

    def intersects_circle(
        self,
        circle_position: Vector2,
        circle_radius: float,
        position: Vector2,
    ) -> bool:
        """Check if polygon intersects circle."""
        center = Vector2(
            x=position.x + self.offset.x,
            y=position.y + self.offset.y,
        )

        world_vertices = [
            Vector2(x=v.x + center.x, y=v.y + center.y) for v in self.vertices
        ]

        if self.contains_point(point=circle_position, position=position):
            return True

        n = len(world_vertices)
        for i in range(n):
            v1 = world_vertices[i]
            v2 = world_vertices[(i + 1) % n]

            edge = Vector2(x=v2.x - v1.x, y=v2.y - v1.y)
            to_circle = Vector2(x=circle_position.x - v1.x, y=circle_position.y - v1.y)

            edge_length_sq = edge.x * edge.x + edge.y * edge.y
            if edge_length_sq == 0:
                continue

            t = max(
                0.0,
                min(
                    1.0,
                    (to_circle.x * edge.x + to_circle.y * edge.y) / edge_length_sq,
                ),
            )

            closest = Vector2(x=v1.x + t * edge.x, y=v1.y + t * edge.y)

            if closest.distance(other=circle_position) <= circle_radius:
                return True

        return False
