"""2D vector operations for spatial calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass

from yuna.exceptions import ValidationError

VECTOR_ZERO_EPSILON = 1e-10


@dataclass(frozen=True)
class Vector2:
    """Immutable 2D vector with mathematical operations.

    Responsibilities:
    - Store 2D position or direction
    - Provide vector math operations (add, subtract, multiply)
    - Calculate distance and magnitude
    - Normalize vectors

    Usage:
        pos = Vector2(x=10.0, y=20.0)
        dir = Vector2(x=1.0, y=0.0)
        new_pos = pos.add(other=dir.multiply(scalar=5.0))
    """

    x: float
    y: float

    def add(self, other: Vector2) -> Vector2:
        """Add two vectors component-wise.

        Args:
            other: Vector to add

        Returns:
            New vector with summed components
        """
        return Vector2(x=self.x + other.x, y=self.y + other.y)

    def subtract(self, other: Vector2) -> Vector2:
        """Subtract another vector from this one.

        Args:
            other: Vector to subtract

        Returns:
            New vector with subtracted components
        """
        return Vector2(x=self.x - other.x, y=self.y - other.y)

    def multiply(self, scalar: float) -> Vector2:
        """Multiply vector by scalar.

        Args:
            scalar: Multiplier value

        Returns:
            New vector with scaled components
        """
        return Vector2(x=self.x * scalar, y=self.y * scalar)

    def magnitude(self) -> float:
        """Calculate vector length.

        Returns:
            Magnitude of the vector
        """
        return math.sqrt(self.x * self.x + self.y * self.y)

    def distance(self, other: Vector2) -> float:
        """Calculate Euclidean distance to another vector.

        Args:
            other: Target vector

        Returns:
            Distance between the two vectors
        """
        return self.subtract(other=other).magnitude()

    def normalize(self) -> Vector2:
        """Create unit vector pointing in same direction.

        Returns:
            Normalized vector with magnitude 1.0

        Raises:
            ValidationError: If vector has zero magnitude
        """
        mag = self.magnitude()
        if mag < VECTOR_ZERO_EPSILON:
            raise ValidationError(
                reason="Cannot normalize zero vector",
                value=f"Vector2(x={self.x}, y={self.y})",
            )
        return Vector2(x=self.x / mag, y=self.y / mag)
