"""Bounding shapes for spatial collision and containment checks."""

from __future__ import annotations

from dataclasses import dataclass

from yuna.types.vector import Vector2


@dataclass(frozen=True)
class Rectangle:
    """Axis-aligned rectangular bounding box.

    Responsibilities:
    - Define rectangular area in 2D space
    - Check point containment
    - Check intersection with other rectangles

    Usage:
        bounds = Rectangle(x=0.0, y=0.0, width=100.0, height=50.0)
        is_inside = bounds.contains_point(point=Vector2(x=25.0, y=25.0))
        overlaps = bounds.intersects(other=other_rect)
    """

    x: float
    y: float
    width: float
    height: float

    def contains_point(self, point: Vector2) -> bool:
        """Check if point is inside rectangle.

        Args:
            point: Point to test

        Returns:
            True if point is within bounds (inclusive)
        """
        return (
            self.x <= point.x <= self.x + self.width
            and self.y <= point.y <= self.y + self.height
        )

    def intersects(self, other: Rectangle) -> bool:
        """Check if this rectangle overlaps another.

        Args:
            other: Rectangle to test against

        Returns:
            True if rectangles overlap
        """
        return not (
            self.x + self.width < other.x
            or other.x + other.width < self.x
            or self.y + self.height < other.y
            or other.y + other.height < self.y
        )


@dataclass(frozen=True)
class Circle:
    """Circular bounding shape.

    Responsibilities:
    - Define circular area in 2D space
    - Check point containment
    - Check intersection with other circles

    Usage:
        bounds = Circle(center=Vector2(x=50.0, y=50.0), radius=25.0)
        is_inside = bounds.contains_point(point=Vector2(x=60.0, y=55.0))
        overlaps = bounds.intersects(other=other_circle)
    """

    center: Vector2
    radius: float

    def contains_point(self, point: Vector2) -> bool:
        """Check if point is inside circle.

        Args:
            point: Point to test

        Returns:
            True if point is within radius (inclusive)
        """
        return self.center.distance(other=point) <= self.radius

    def intersects(self, other: Circle) -> bool:
        """Check if this circle overlaps another.

        Args:
            other: Circle to test against

        Returns:
            True if circles overlap
        """
        return self.center.distance(other=other.center) <= self.radius + other.radius
