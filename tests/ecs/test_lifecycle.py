"""Tests for component lifecycle hooks."""

from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.lifecycle import ComponentLifecycle
from yuna.exceptions import ValidationError
from yuna.types.identifiers import EntityID

fake = Faker()


@dataclass
class Position(Component):
    """Test position component."""

    x: float
    y: float


@dataclass
class Velocity(Component):
    """Test velocity component."""

    dx: float
    dy: float


def test_lifecycle_initialization() -> None:
    """Test lifecycle initializes with empty callbacks."""
    lifecycle = ComponentLifecycle()

    assert not lifecycle.has_added_callbacks(component_type=Position)
    assert not lifecycle.has_removed_callbacks(component_type=Position)
    assert lifecycle.get_added_callback_count(component_type=Position) == 0
    assert lifecycle.get_removed_callback_count(component_type=Position) == 0


def test_register_added_callback() -> None:
    """Test registering callback for component add."""
    lifecycle = ComponentLifecycle()
    callback = Mock()

    lifecycle.register_added_callback(component_type=Position, callback=callback)

    assert lifecycle.has_added_callbacks(component_type=Position)
    assert lifecycle.get_added_callback_count(component_type=Position) == 1


def test_register_removed_callback() -> None:
    """Test registering callback for component remove."""
    lifecycle = ComponentLifecycle()
    callback = Mock()

    lifecycle.register_removed_callback(component_type=Position, callback=callback)

    assert lifecycle.has_removed_callbacks(component_type=Position)
    assert lifecycle.get_removed_callback_count(component_type=Position) == 1


def test_on_component_added_invokes_callback() -> None:
    """Test callback invoked when component added."""
    lifecycle = ComponentLifecycle()
    callback = Mock()
    entity_id = EntityID(fake.uuid4())
    component = Position(x=fake.pyfloat(), y=fake.pyfloat())

    lifecycle.register_added_callback(component_type=Position, callback=callback)
    lifecycle.on_component_added(
        entity_id=entity_id,
        component_type=Position,
        component=component,
    )

    callback.assert_called_once_with(entity_id, Position, component)


def test_on_component_removed_invokes_callback() -> None:
    """Test callback invoked when component removed."""
    lifecycle = ComponentLifecycle()
    callback = Mock()
    entity_id = EntityID(fake.uuid4())
    component = Position(x=fake.pyfloat(), y=fake.pyfloat())

    lifecycle.register_removed_callback(component_type=Position, callback=callback)
    lifecycle.on_component_removed(
        entity_id=entity_id,
        component_type=Position,
        component=component,
    )

    callback.assert_called_once_with(entity_id, Position, component)


def test_multiple_callbacks_per_type() -> None:
    """Test multiple callbacks registered for same component type."""
    lifecycle = ComponentLifecycle()
    callback1 = Mock()
    callback2 = Mock()
    callback3 = Mock()
    entity_id = EntityID(fake.uuid4())
    component = Position(x=fake.pyfloat(), y=fake.pyfloat())

    lifecycle.register_added_callback(component_type=Position, callback=callback1)
    lifecycle.register_added_callback(component_type=Position, callback=callback2)
    lifecycle.register_added_callback(component_type=Position, callback=callback3)

    assert lifecycle.get_added_callback_count(component_type=Position) == 3

    lifecycle.on_component_added(
        entity_id=entity_id,
        component_type=Position,
        component=component,
    )

    callback1.assert_called_once_with(entity_id, Position, component)
    callback2.assert_called_once_with(entity_id, Position, component)
    callback3.assert_called_once_with(entity_id, Position, component)


def test_callbacks_not_invoked_for_unregistered_types() -> None:
    """Test callbacks not invoked for unregistered component types."""
    lifecycle = ComponentLifecycle()
    callback = Mock()
    entity_id = EntityID(fake.uuid4())
    component = Velocity(dx=fake.pyfloat(), dy=fake.pyfloat())

    lifecycle.register_added_callback(component_type=Position, callback=callback)
    lifecycle.on_component_added(
        entity_id=entity_id,
        component_type=Velocity,
        component=component,
    )

    callback.assert_not_called()


def test_unregister_added_callback() -> None:
    """Test unregistering callback for component add."""
    lifecycle = ComponentLifecycle()
    callback = Mock()

    lifecycle.register_added_callback(component_type=Position, callback=callback)
    assert lifecycle.has_added_callbacks(component_type=Position)

    lifecycle.unregister_added_callback(component_type=Position, callback=callback)

    assert not lifecycle.has_added_callbacks(component_type=Position)
    assert lifecycle.get_added_callback_count(component_type=Position) == 0


def test_unregister_removed_callback() -> None:
    """Test unregistering callback for component remove."""
    lifecycle = ComponentLifecycle()
    callback = Mock()

    lifecycle.register_removed_callback(component_type=Position, callback=callback)
    assert lifecycle.has_removed_callbacks(component_type=Position)

    lifecycle.unregister_removed_callback(component_type=Position, callback=callback)

    assert not lifecycle.has_removed_callbacks(component_type=Position)
    assert lifecycle.get_removed_callback_count(component_type=Position) == 0


def test_unregister_callback_raises_if_type_not_registered() -> None:
    """Test unregistering callback raises error if type not registered."""
    lifecycle = ComponentLifecycle()
    callback = Mock()

    with pytest.raises(ValidationError, match="No added callbacks registered"):
        lifecycle.unregister_added_callback(component_type=Position, callback=callback)

    with pytest.raises(ValidationError, match="No removed callbacks registered"):
        lifecycle.unregister_removed_callback(
            component_type=Position, callback=callback
        )


def test_unregister_callback_raises_if_callback_not_registered() -> None:
    """Test unregistering callback raises error if callback not registered."""
    lifecycle = ComponentLifecycle()
    callback1 = Mock()
    callback2 = Mock()

    lifecycle.register_added_callback(component_type=Position, callback=callback1)

    with pytest.raises(ValidationError, match="Callback not registered"):
        lifecycle.unregister_added_callback(component_type=Position, callback=callback2)

    lifecycle.register_removed_callback(component_type=Position, callback=callback1)

    with pytest.raises(ValidationError, match="Callback not registered"):
        lifecycle.unregister_removed_callback(
            component_type=Position, callback=callback2
        )


def test_unregister_one_of_multiple_callbacks() -> None:
    """Test unregistering one callback leaves others intact."""
    lifecycle = ComponentLifecycle()
    callback1 = Mock()
    callback2 = Mock()
    entity_id = EntityID(fake.uuid4())
    component = Position(x=fake.pyfloat(), y=fake.pyfloat())

    lifecycle.register_added_callback(component_type=Position, callback=callback1)
    lifecycle.register_added_callback(component_type=Position, callback=callback2)

    assert lifecycle.get_added_callback_count(component_type=Position) == 2

    lifecycle.unregister_added_callback(component_type=Position, callback=callback1)

    assert lifecycle.get_added_callback_count(component_type=Position) == 1

    lifecycle.on_component_added(
        entity_id=entity_id,
        component_type=Position,
        component=component,
    )

    callback1.assert_not_called()
    callback2.assert_called_once_with(entity_id, Position, component)


def test_callbacks_receive_correct_parameters() -> None:
    """Test callbacks receive correct entity, type, and component."""
    lifecycle = ComponentLifecycle()
    added_callback = Mock()
    removed_callback = Mock()

    entity_id = EntityID(fake.uuid4())
    x_value = fake.pyfloat()
    y_value = fake.pyfloat()
    component = Position(x=x_value, y=y_value)

    lifecycle.register_added_callback(component_type=Position, callback=added_callback)
    lifecycle.register_removed_callback(
        component_type=Position, callback=removed_callback
    )

    lifecycle.on_component_added(
        entity_id=entity_id,
        component_type=Position,
        component=component,
    )

    lifecycle.on_component_removed(
        entity_id=entity_id,
        component_type=Position,
        component=component,
    )

    added_callback.assert_called_once()
    call_args = added_callback.call_args[0]
    assert call_args[0] == entity_id
    assert call_args[1] == Position
    assert call_args[2].x == x_value
    assert call_args[2].y == y_value

    removed_callback.assert_called_once()
    call_args = removed_callback.call_args[0]
    assert call_args[0] == entity_id
    assert call_args[1] == Position
    assert call_args[2].x == x_value
    assert call_args[2].y == y_value


def test_clear_removes_all_callbacks() -> None:
    """Test clear removes all registered callbacks."""
    lifecycle = ComponentLifecycle()
    callback1 = Mock()
    callback2 = Mock()

    lifecycle.register_added_callback(component_type=Position, callback=callback1)
    lifecycle.register_removed_callback(component_type=Velocity, callback=callback2)

    assert lifecycle.has_added_callbacks(component_type=Position)
    assert lifecycle.has_removed_callbacks(component_type=Velocity)

    lifecycle.clear()

    assert not lifecycle.has_added_callbacks(component_type=Position)
    assert not lifecycle.has_removed_callbacks(component_type=Velocity)
    assert lifecycle.get_added_callback_count(component_type=Position) == 0
    assert lifecycle.get_removed_callback_count(component_type=Velocity) == 0


def test_different_component_types_independent() -> None:
    """Test callbacks for different component types are independent."""
    lifecycle = ComponentLifecycle()
    position_callback = Mock()
    velocity_callback = Mock()

    lifecycle.register_added_callback(
        component_type=Position, callback=position_callback
    )
    lifecycle.register_added_callback(
        component_type=Velocity, callback=velocity_callback
    )

    entity_id = EntityID(fake.uuid4())
    position = Position(x=fake.pyfloat(), y=fake.pyfloat())

    lifecycle.on_component_added(
        entity_id=entity_id,
        component_type=Position,
        component=position,
    )

    position_callback.assert_called_once()
    velocity_callback.assert_not_called()
