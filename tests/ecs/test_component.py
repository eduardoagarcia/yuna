"""Tests for component protocol."""

from dataclasses import dataclass

from yuna.ecs.component import Component


@dataclass
class Position(Component):
    """Test component for position data."""

    x: float
    y: float


@dataclass
class Health(Component):
    """Test component for health data."""

    current: int
    maximum: int


def test_component_protocol_with_dataclass() -> None:
    """Test Component protocol works with dataclass."""
    position = Position(x=10.0, y=20.0)
    assert isinstance(position, Position)
    assert position.x == 10.0
    assert position.y == 20.0


def test_multiple_component_types() -> None:
    """Test creating multiple different component types."""
    position = Position(x=5.0, y=15.0)
    health = Health(current=80, maximum=100)
    assert isinstance(position, Position)
    assert isinstance(health, Health)
    assert position.x == 5.0
    assert health.current == 80


def test_component_immutability_with_frozen_dataclass() -> None:
    """Test components can be immutable if frozen."""

    @dataclass(frozen=True)
    class ImmutablePosition(Component):
        x: float
        y: float

    pos = ImmutablePosition(x=1.0, y=2.0)
    assert pos.x == 1.0
    assert pos.y == 2.0
