"""Tests for collision mode enum."""

from yuna.spatial.collision import CollisionMode


def test_collision_mode_circle_value() -> None:
    """Test CollisionMode.CIRCLE has correct value."""
    assert CollisionMode.CIRCLE.value == "circle"


def test_collision_mode_grid_box_value() -> None:
    """Test CollisionMode.GRID_BOX has correct value."""
    assert CollisionMode.GRID_BOX.value == "grid_box"


def test_collision_mode_enum_members() -> None:
    """Test CollisionMode has expected members."""
    members = list(CollisionMode)
    assert CollisionMode.CIRCLE in members
    assert CollisionMode.GRID_BOX in members
    assert len(members) == 2


def test_collision_mode_comparison() -> None:
    """Test CollisionMode enum comparison."""
    assert CollisionMode.CIRCLE == CollisionMode.CIRCLE
    assert CollisionMode.GRID_BOX == CollisionMode.GRID_BOX
    assert CollisionMode.CIRCLE != CollisionMode.GRID_BOX
