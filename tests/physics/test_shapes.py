"""Tests for collision shapes."""

from yuna.physics.shapes import (
    BoxShape,
    CircleShape,
    CollisionLayer,
    PolygonShape,
)
from yuna.types.vector import Vector2


def test_collision_layer_flags() -> None:
    """Test collision layer flags."""
    assert CollisionLayer.LAYER_1 != CollisionLayer.LAYER_2
    assert CollisionLayer.ALL == (
        CollisionLayer.LAYER_1
        | CollisionLayer.LAYER_2
        | CollisionLayer.LAYER_3
        | CollisionLayer.LAYER_4
        | CollisionLayer.LAYER_5
        | CollisionLayer.LAYER_6
        | CollisionLayer.LAYER_7
        | CollisionLayer.LAYER_8
    )


def test_circle_shape_contains_point_inside() -> None:
    """Test circle contains point inside."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    position = Vector2(x=10.0, y=10.0)
    point = Vector2(x=12.0, y=12.0)

    assert shape.contains_point(point=point, position=position) is True


def test_circle_shape_contains_point_outside() -> None:
    """Test circle does not contain point outside."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    position = Vector2(x=10.0, y=10.0)
    point = Vector2(x=20.0, y=20.0)

    assert shape.contains_point(point=point, position=position) is False


def test_circle_shape_intersects_circle_overlapping() -> None:
    """Test circle intersects overlapping circle."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    position = Vector2(x=0.0, y=0.0)
    other_position = Vector2(x=8.0, y=0.0)

    assert (
        shape.intersects_circle(
            circle_position=other_position,
            circle_radius=5.0,
            position=position,
        )
        is True
    )


def test_circle_shape_intersects_circle_separate() -> None:
    """Test circle does not intersect separate circle."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    position = Vector2(x=0.0, y=0.0)
    other_position = Vector2(x=20.0, y=0.0)

    assert (
        shape.intersects_circle(
            circle_position=other_position,
            circle_radius=5.0,
            position=position,
        )
        is False
    )


def test_circle_shape_with_offset() -> None:
    """Test circle shape with offset."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=10.0, y=0.0))
    position = Vector2(x=0.0, y=0.0)
    point = Vector2(x=10.0, y=0.0)

    assert shape.contains_point(point=point, position=position) is True


def test_box_shape_contains_point_inside() -> None:
    """Test box contains point inside."""
    shape = BoxShape(width=10.0, height=10.0, offset=Vector2(x=0.0, y=0.0))
    position = Vector2(x=10.0, y=10.0)
    point = Vector2(x=12.0, y=12.0)

    assert shape.contains_point(point=point, position=position) is True


def test_box_shape_contains_point_on_edge() -> None:
    """Test box contains point on edge."""
    shape = BoxShape(width=10.0, height=10.0, offset=Vector2(x=0.0, y=0.0))
    position = Vector2(x=10.0, y=10.0)
    point = Vector2(x=15.0, y=10.0)

    assert shape.contains_point(point=point, position=position) is True


def test_box_shape_contains_point_outside() -> None:
    """Test box does not contain point outside."""
    shape = BoxShape(width=10.0, height=10.0, offset=Vector2(x=0.0, y=0.0))
    position = Vector2(x=10.0, y=10.0)
    point = Vector2(x=20.0, y=20.0)

    assert shape.contains_point(point=point, position=position) is False


def test_box_shape_intersects_circle_overlapping() -> None:
    """Test box intersects overlapping circle."""
    shape = BoxShape(width=10.0, height=10.0, offset=Vector2(x=0.0, y=0.0))
    position = Vector2(x=0.0, y=0.0)
    circle_position = Vector2(x=8.0, y=0.0)

    assert (
        shape.intersects_circle(
            circle_position=circle_position,
            circle_radius=5.0,
            position=position,
        )
        is True
    )


def test_box_shape_intersects_circle_separate() -> None:
    """Test box does not intersect separate circle."""
    shape = BoxShape(width=10.0, height=10.0, offset=Vector2(x=0.0, y=0.0))
    position = Vector2(x=0.0, y=0.0)
    circle_position = Vector2(x=20.0, y=0.0)

    assert (
        shape.intersects_circle(
            circle_position=circle_position,
            circle_radius=5.0,
            position=position,
        )
        is False
    )


def test_polygon_shape_default_vertices() -> None:
    """Test polygon shape has default vertices."""
    shape = PolygonShape(offset=Vector2(x=0.0, y=0.0))

    assert len(shape.vertices) == 3


def test_polygon_shape_contains_point_inside() -> None:
    """Test polygon contains point inside."""
    shape = PolygonShape(
        vertices=[
            Vector2(x=-5.0, y=-5.0),
            Vector2(x=5.0, y=-5.0),
            Vector2(x=5.0, y=5.0),
            Vector2(x=-5.0, y=5.0),
        ],
        offset=Vector2(x=0.0, y=0.0),
    )
    position = Vector2(x=0.0, y=0.0)
    point = Vector2(x=2.0, y=2.0)

    assert shape.contains_point(point=point, position=position) is True


def test_polygon_shape_contains_point_outside() -> None:
    """Test polygon does not contain point outside."""
    shape = PolygonShape(
        vertices=[
            Vector2(x=-5.0, y=-5.0),
            Vector2(x=5.0, y=-5.0),
            Vector2(x=5.0, y=5.0),
            Vector2(x=-5.0, y=5.0),
        ],
        offset=Vector2(x=0.0, y=0.0),
    )
    position = Vector2(x=0.0, y=0.0)
    point = Vector2(x=10.0, y=10.0)

    assert shape.contains_point(point=point, position=position) is False


def test_polygon_shape_intersects_circle() -> None:
    """Test polygon intersects circle."""
    shape = PolygonShape(
        vertices=[
            Vector2(x=-5.0, y=-5.0),
            Vector2(x=5.0, y=-5.0),
            Vector2(x=5.0, y=5.0),
            Vector2(x=-5.0, y=5.0),
        ],
        offset=Vector2(x=0.0, y=0.0),
    )
    position = Vector2(x=0.0, y=0.0)
    circle_position = Vector2(x=8.0, y=0.0)

    assert (
        shape.intersects_circle(
            circle_position=circle_position,
            circle_radius=5.0,
            position=position,
        )
        is True
    )


def test_can_collide_with_same_layer() -> None:
    """Test shapes on same layer can collide."""
    shape1 = CircleShape(
        radius=5.0,
        offset=Vector2(x=0.0, y=0.0),
        layer=CollisionLayer.LAYER_1,
        mask=CollisionLayer.ALL,
    )
    shape2 = CircleShape(
        radius=5.0,
        offset=Vector2(x=0.0, y=0.0),
        layer=CollisionLayer.LAYER_1,
        mask=CollisionLayer.ALL,
    )

    assert shape1.can_collide_with(other=shape2) is True


def test_can_collide_with_different_layers_matching_mask() -> None:
    """Test shapes on different layers can collide with matching masks."""
    shape1 = CircleShape(
        radius=5.0,
        offset=Vector2(x=0.0, y=0.0),
        layer=CollisionLayer.LAYER_1,
        mask=CollisionLayer.LAYER_2,
    )
    shape2 = CircleShape(
        radius=5.0,
        offset=Vector2(x=0.0, y=0.0),
        layer=CollisionLayer.LAYER_2,
        mask=CollisionLayer.LAYER_1,
    )

    assert shape1.can_collide_with(other=shape2) is True


def test_cannot_collide_with_different_layers_no_mask() -> None:
    """Test shapes cannot collide with non-matching masks."""
    shape1 = CircleShape(
        radius=5.0,
        offset=Vector2(x=0.0, y=0.0),
        layer=CollisionLayer.LAYER_1,
        mask=CollisionLayer.LAYER_2,
    )
    shape2 = CircleShape(
        radius=5.0,
        offset=Vector2(x=0.0, y=0.0),
        layer=CollisionLayer.LAYER_3,
        mask=CollisionLayer.LAYER_4,
    )

    assert shape1.can_collide_with(other=shape2) is False


def test_polygon_shape_intersects_circle_center_inside() -> None:
    """Test polygon intersects circle when circle center is inside polygon."""
    shape = PolygonShape(
        vertices=[
            Vector2(x=-10.0, y=-10.0),
            Vector2(x=10.0, y=-10.0),
            Vector2(x=10.0, y=10.0),
            Vector2(x=-10.0, y=10.0),
        ],
        offset=Vector2(x=0.0, y=0.0),
    )
    position = Vector2(x=0.0, y=0.0)
    circle_position = Vector2(x=2.0, y=2.0)

    assert (
        shape.intersects_circle(
            circle_position=circle_position,
            circle_radius=1.0,
            position=position,
        )
        is True
    )


def test_polygon_shape_no_intersection() -> None:
    """Test polygon does not intersect circle when far away."""
    shape = PolygonShape(
        vertices=[
            Vector2(x=-5.0, y=-5.0),
            Vector2(x=5.0, y=-5.0),
            Vector2(x=5.0, y=5.0),
            Vector2(x=-5.0, y=5.0),
        ],
        offset=Vector2(x=0.0, y=0.0),
    )
    position = Vector2(x=0.0, y=0.0)
    circle_position = Vector2(x=100.0, y=100.0)

    assert (
        shape.intersects_circle(
            circle_position=circle_position,
            circle_radius=5.0,
            position=position,
        )
        is False
    )


def test_polygon_shape_with_degenerate_edge() -> None:
    """Test polygon with zero-length edge."""
    shape = PolygonShape(
        vertices=[
            Vector2(x=0.0, y=0.0),
            Vector2(x=0.0, y=0.0),
            Vector2(x=5.0, y=0.0),
            Vector2(x=5.0, y=5.0),
        ],
        offset=Vector2(x=0.0, y=0.0),
    )
    position = Vector2(x=0.0, y=0.0)
    circle_position = Vector2(x=10.0, y=10.0)

    result = shape.intersects_circle(
        circle_position=circle_position,
        circle_radius=2.0,
        position=position,
    )

    assert result is False
