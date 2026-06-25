"""Tests for bounding shapes."""

import pytest
from faker import Faker

from yuna.types.bounds import Circle, Rectangle
from yuna.types.vector import Vector2

fake = Faker()


def test_rectangle_creation() -> None:
    """Test Rectangle can be created with dimensions."""
    x = fake.pyfloat()
    y = fake.pyfloat()
    width = fake.pyfloat(min_value=0)
    height = fake.pyfloat(min_value=0)
    rect = Rectangle(x=x, y=y, width=width, height=height)
    assert rect.x == x
    assert rect.y == y
    assert rect.width == width
    assert rect.height == height


def test_rectangle_is_immutable() -> None:
    """Test Rectangle is frozen and cannot be modified."""
    rect = Rectangle(
        x=fake.pyfloat(),
        y=fake.pyfloat(),
        width=fake.pyfloat(min_value=0),
        height=fake.pyfloat(min_value=0),
    )
    with pytest.raises(AttributeError):
        rect.x = fake.pyfloat()  # type: ignore[misc]


def test_rectangle_contains_point_inside() -> None:
    """Test Rectangle contains point inside bounds."""
    rect = Rectangle(x=0.0, y=0.0, width=100.0, height=100.0)
    point = Vector2(x=50.0, y=50.0)
    assert rect.contains_point(point=point) is True


def test_rectangle_contains_point_outside() -> None:
    """Test Rectangle does not contain point outside bounds."""
    rect = Rectangle(x=0.0, y=0.0, width=100.0, height=100.0)
    point = Vector2(x=150.0, y=150.0)
    assert rect.contains_point(point=point) is False


def test_rectangle_contains_point_on_edge() -> None:
    """Test Rectangle contains point exactly on edge."""
    rect = Rectangle(x=0.0, y=0.0, width=100.0, height=100.0)
    point = Vector2(x=100.0, y=100.0)
    assert rect.contains_point(point=point) is True


def test_rectangle_contains_point_at_origin() -> None:
    """Test Rectangle contains point at origin corner."""
    rect = Rectangle(x=0.0, y=0.0, width=100.0, height=100.0)
    point = Vector2(x=0.0, y=0.0)
    assert rect.contains_point(point=point) is True


def test_rectangle_contains_point_left_of_bounds() -> None:
    """Test Rectangle does not contain point to the left."""
    rect = Rectangle(x=10.0, y=10.0, width=50.0, height=50.0)
    point = Vector2(x=5.0, y=30.0)
    assert rect.contains_point(point=point) is False


def test_rectangle_contains_point_below_bounds() -> None:
    """Test Rectangle does not contain point below."""
    rect = Rectangle(x=10.0, y=10.0, width=50.0, height=50.0)
    point = Vector2(x=30.0, y=5.0)
    assert rect.contains_point(point=point) is False


def test_rectangle_intersects_overlapping() -> None:
    """Test Rectangle intersects with overlapping rectangle."""
    rect1 = Rectangle(x=0.0, y=0.0, width=100.0, height=100.0)
    rect2 = Rectangle(x=50.0, y=50.0, width=100.0, height=100.0)
    assert rect1.intersects(other=rect2) is True
    assert rect2.intersects(other=rect1) is True


def test_rectangle_intersects_separated() -> None:
    """Test Rectangle does not intersect with separated rectangle."""
    rect1 = Rectangle(x=0.0, y=0.0, width=50.0, height=50.0)
    rect2 = Rectangle(x=100.0, y=100.0, width=50.0, height=50.0)
    assert rect1.intersects(other=rect2) is False
    assert rect2.intersects(other=rect1) is False


def test_rectangle_intersects_touching_edge() -> None:
    """Test Rectangle intersects when edges touch."""
    rect1 = Rectangle(x=0.0, y=0.0, width=50.0, height=50.0)
    rect2 = Rectangle(x=50.0, y=0.0, width=50.0, height=50.0)
    assert rect1.intersects(other=rect2) is True


def test_rectangle_intersects_contained() -> None:
    """Test Rectangle intersects when one is inside the other."""
    rect1 = Rectangle(x=0.0, y=0.0, width=100.0, height=100.0)
    rect2 = Rectangle(x=25.0, y=25.0, width=50.0, height=50.0)
    assert rect1.intersects(other=rect2) is True
    assert rect2.intersects(other=rect1) is True


def test_rectangle_intersects_self() -> None:
    """Test Rectangle intersects with itself."""
    rect = Rectangle(
        x=fake.pyfloat(),
        y=fake.pyfloat(),
        width=fake.pyfloat(min_value=1),
        height=fake.pyfloat(min_value=1),
    )
    assert rect.intersects(other=rect) is True


def test_rectangle_with_zero_width() -> None:
    """Test Rectangle with zero width."""
    rect = Rectangle(x=10.0, y=10.0, width=0.0, height=50.0)
    point_inside = Vector2(x=10.0, y=30.0)
    point_outside = Vector2(x=11.0, y=30.0)
    assert rect.contains_point(point=point_inside) is True
    assert rect.contains_point(point=point_outside) is False


def test_rectangle_with_zero_height() -> None:
    """Test Rectangle with zero height."""
    rect = Rectangle(x=10.0, y=10.0, width=50.0, height=0.0)
    point_inside = Vector2(x=30.0, y=10.0)
    point_outside = Vector2(x=30.0, y=11.0)
    assert rect.contains_point(point=point_inside) is True
    assert rect.contains_point(point=point_outside) is False


def test_circle_creation() -> None:
    """Test Circle can be created with center and radius."""
    x = fake.pyfloat()
    y = fake.pyfloat()
    radius = fake.pyfloat(min_value=0)
    center = Vector2(x=x, y=y)
    circle = Circle(center=center, radius=radius)
    assert circle.center == center
    assert circle.radius == radius


def test_circle_is_immutable() -> None:
    """Test Circle is frozen and cannot be modified."""
    circle = Circle(
        center=Vector2(x=fake.pyfloat(), y=fake.pyfloat()),
        radius=fake.pyfloat(min_value=0),
    )
    with pytest.raises(AttributeError):
        circle.radius = fake.pyfloat()  # type: ignore[misc]


def test_circle_contains_point_inside() -> None:
    """Test Circle contains point inside bounds."""
    circle = Circle(center=Vector2(x=0.0, y=0.0), radius=50.0)
    point = Vector2(x=25.0, y=25.0)
    assert circle.contains_point(point=point) is True


def test_circle_contains_point_outside() -> None:
    """Test Circle does not contain point outside bounds."""
    circle = Circle(center=Vector2(x=0.0, y=0.0), radius=50.0)
    point = Vector2(x=100.0, y=100.0)
    assert circle.contains_point(point=point) is False


def test_circle_contains_point_on_edge() -> None:
    """Test Circle contains point exactly on edge."""
    circle = Circle(center=Vector2(x=0.0, y=0.0), radius=50.0)
    point = Vector2(x=50.0, y=0.0)
    assert circle.contains_point(point=point) is True


def test_circle_contains_point_at_center() -> None:
    """Test Circle contains point at center."""
    center = Vector2(x=fake.pyfloat(), y=fake.pyfloat())
    circle = Circle(center=center, radius=fake.pyfloat(min_value=1))
    assert circle.contains_point(point=center) is True


def test_circle_intersects_overlapping() -> None:
    """Test Circle intersects with overlapping circle."""
    circle1 = Circle(center=Vector2(x=0.0, y=0.0), radius=50.0)
    circle2 = Circle(center=Vector2(x=50.0, y=0.0), radius=50.0)
    assert circle1.intersects(other=circle2) is True
    assert circle2.intersects(other=circle1) is True


def test_circle_intersects_separated() -> None:
    """Test Circle does not intersect with separated circle."""
    circle1 = Circle(center=Vector2(x=0.0, y=0.0), radius=25.0)
    circle2 = Circle(center=Vector2(x=100.0, y=100.0), radius=25.0)
    assert circle1.intersects(other=circle2) is False
    assert circle2.intersects(other=circle1) is False


def test_circle_intersects_touching() -> None:
    """Test Circle intersects when edges touch."""
    circle1 = Circle(center=Vector2(x=0.0, y=0.0), radius=50.0)
    circle2 = Circle(center=Vector2(x=100.0, y=0.0), radius=50.0)
    assert circle1.intersects(other=circle2) is True


def test_circle_intersects_contained() -> None:
    """Test Circle intersects when one is inside the other."""
    circle1 = Circle(center=Vector2(x=0.0, y=0.0), radius=100.0)
    circle2 = Circle(center=Vector2(x=0.0, y=0.0), radius=25.0)
    assert circle1.intersects(other=circle2) is True
    assert circle2.intersects(other=circle1) is True


def test_circle_intersects_self() -> None:
    """Test Circle intersects with itself."""
    circle = Circle(
        center=Vector2(x=fake.pyfloat(), y=fake.pyfloat()),
        radius=fake.pyfloat(min_value=1),
    )
    assert circle.intersects(other=circle) is True


def test_circle_with_zero_radius() -> None:
    """Test Circle with zero radius contains only center point."""
    center = Vector2(x=10.0, y=10.0)
    circle = Circle(center=center, radius=0.0)
    assert circle.contains_point(point=center) is True
    assert circle.contains_point(point=Vector2(x=11.0, y=10.0)) is False


def test_circle_with_negative_coordinates() -> None:
    """Test Circle with negative center coordinates."""
    circle = Circle(center=Vector2(x=-50.0, y=-50.0), radius=25.0)
    point_inside = Vector2(x=-40.0, y=-40.0)
    point_outside = Vector2(x=0.0, y=0.0)
    assert circle.contains_point(point=point_inside) is True
    assert circle.contains_point(point=point_outside) is False
