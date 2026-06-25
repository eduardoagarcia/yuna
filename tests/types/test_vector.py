"""Tests for 2D vector operations."""

import math

import pytest
from faker import Faker

from yuna.exceptions import ValidationError
from yuna.types.vector import Vector2

fake = Faker()


def test_vector2_creation() -> None:
    """Test Vector2 can be created with x and y coordinates."""
    x = fake.pyfloat()
    y = fake.pyfloat()
    vector = Vector2(x=x, y=y)
    assert vector.x == x
    assert vector.y == y


def test_vector2_is_immutable() -> None:
    """Test Vector2 is frozen and cannot be modified."""
    vector = Vector2(x=fake.pyfloat(), y=fake.pyfloat())
    with pytest.raises(AttributeError):
        vector.x = fake.pyfloat()  # type: ignore[misc]


def test_vector2_add() -> None:
    """Test adding two vectors."""
    v1_x = fake.pyfloat()
    v1_y = fake.pyfloat()
    v2_x = fake.pyfloat()
    v2_y = fake.pyfloat()
    v1 = Vector2(x=v1_x, y=v1_y)
    v2 = Vector2(x=v2_x, y=v2_y)
    result = v1.add(other=v2)
    assert result.x == v1_x + v2_x
    assert result.y == v1_y + v2_y


def test_vector2_subtract() -> None:
    """Test subtracting two vectors."""
    v1_x = fake.pyfloat()
    v1_y = fake.pyfloat()
    v2_x = fake.pyfloat()
    v2_y = fake.pyfloat()
    v1 = Vector2(x=v1_x, y=v1_y)
    v2 = Vector2(x=v2_x, y=v2_y)
    result = v1.subtract(other=v2)
    assert result.x == v1_x - v2_x
    assert result.y == v1_y - v2_y


def test_vector2_multiply() -> None:
    """Test multiplying vector by scalar."""
    x = fake.pyfloat()
    y = fake.pyfloat()
    scalar = fake.pyfloat()
    vector = Vector2(x=x, y=y)
    result = vector.multiply(scalar=scalar)
    assert result.x == x * scalar
    assert result.y == y * scalar


def test_vector2_magnitude() -> None:
    """Test calculating vector magnitude."""
    x = fake.pyfloat(min_value=0, max_value=100)
    y = fake.pyfloat(min_value=0, max_value=100)
    vector = Vector2(x=x, y=y)
    expected = math.sqrt(x * x + y * y)
    assert vector.magnitude() == pytest.approx(expected)


def test_vector2_magnitude_zero_vector() -> None:
    """Test magnitude of zero vector is zero."""
    vector = Vector2(x=0.0, y=0.0)
    assert vector.magnitude() == 0.0


def test_vector2_distance() -> None:
    """Test calculating distance between two vectors."""
    v1_x = fake.pyfloat(min_value=0, max_value=100)
    v1_y = fake.pyfloat(min_value=0, max_value=100)
    v2_x = fake.pyfloat(min_value=0, max_value=100)
    v2_y = fake.pyfloat(min_value=0, max_value=100)
    v1 = Vector2(x=v1_x, y=v1_y)
    v2 = Vector2(x=v2_x, y=v2_y)
    dx = v1_x - v2_x
    dy = v1_y - v2_y
    expected = math.sqrt(dx * dx + dy * dy)
    assert v1.distance(other=v2) == pytest.approx(expected)


def test_vector2_distance_same_point() -> None:
    """Test distance from vector to itself is zero."""
    x = fake.pyfloat()
    y = fake.pyfloat()
    vector = Vector2(x=x, y=y)
    assert vector.distance(other=vector) == 0.0


def test_vector2_normalize() -> None:
    """Test normalizing a vector creates unit vector."""
    x = fake.pyfloat(min_value=1, max_value=100)
    y = fake.pyfloat(min_value=1, max_value=100)
    vector = Vector2(x=x, y=y)
    normalized = vector.normalize()
    assert normalized.magnitude() == pytest.approx(1.0)


def test_vector2_normalize_preserves_direction() -> None:
    """Test normalized vector points in same direction."""
    x = fake.pyfloat(min_value=1, max_value=100)
    y = fake.pyfloat(min_value=1, max_value=100)
    vector = Vector2(x=x, y=y)
    normalized = vector.normalize()
    ratio = x / y if y != 0 else 0
    normalized_ratio = normalized.x / normalized.y if normalized.y != 0 else 0
    assert normalized_ratio == pytest.approx(ratio)


def test_vector2_normalize_zero_vector_raises_error() -> None:
    """Test normalizing zero vector raises ZeroDivisionError."""
    vector = Vector2(x=0.0, y=0.0)
    with pytest.raises(ValidationError, match="Cannot normalize zero vector"):
        vector.normalize()


def test_vector2_add_with_negative_values() -> None:
    """Test adding vectors with negative coordinates."""
    v1 = Vector2(x=-fake.pyfloat(min_value=0), y=-fake.pyfloat(min_value=0))
    v2 = Vector2(x=fake.pyfloat(), y=fake.pyfloat())
    result = v1.add(other=v2)
    assert result.x == v1.x + v2.x
    assert result.y == v1.y + v2.y


def test_vector2_multiply_by_zero() -> None:
    """Test multiplying vector by zero creates zero vector."""
    vector = Vector2(x=fake.pyfloat(), y=fake.pyfloat())
    result = vector.multiply(scalar=0.0)
    assert result.x == 0.0
    assert result.y == 0.0


def test_vector2_multiply_by_negative() -> None:
    """Test multiplying vector by negative scalar reverses direction."""
    x = fake.pyfloat(min_value=1, max_value=100)
    y = fake.pyfloat(min_value=1, max_value=100)
    scalar = -fake.pyfloat(min_value=1, max_value=10)
    vector = Vector2(x=x, y=y)
    result = vector.multiply(scalar=scalar)
    assert result.x == x * scalar
    assert result.y == y * scalar
    assert result.x < 0
    assert result.y < 0
