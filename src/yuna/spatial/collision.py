"""Spatial collision detection modes and utilities."""

from enum import Enum


class CollisionMode(Enum):
    """Collision detection mode for spatial queries.

    Attributes:
        CIRCLE: Treat entities as circles with 0.5 radius (continuous space)
        GRID_BOX: Treat entities as 1×1 grid cells (discrete grid games)
    """

    CIRCLE = "circle"
    GRID_BOX = "grid_box"
