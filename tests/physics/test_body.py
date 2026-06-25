"""Tests for physics body component."""

from yuna.physics.body import PhysicsBody
from yuna.physics.shapes import CircleShape
from yuna.types.vector import Vector2


def test_physics_body_creation() -> None:
    """Test physics body creation."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)

    assert body.mass == 10.0
    assert body.shape == shape
    assert body.velocity.x == 0.0
    assert body.velocity.y == 0.0
    assert body.angular_velocity == 0.0
    assert body.friction == 0.3
    assert body.restitution == 0.2
    assert body.is_static is False
    assert body.gravity_scale == 1.0


def test_physics_body_is_kinematic_zero_mass() -> None:
    """Test kinematic body detection with zero mass."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=0.0, shape=shape)

    assert body.is_kinematic is True


def test_physics_body_is_kinematic_nonzero_mass() -> None:
    """Test kinematic body detection with nonzero mass."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)

    assert body.is_kinematic is False


def test_physics_body_inverse_mass_normal() -> None:
    """Test inverse mass calculation for normal body."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)

    assert body.inverse_mass == 0.1


def test_physics_body_inverse_mass_static() -> None:
    """Test inverse mass for static body."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape, is_static=True)

    assert body.inverse_mass == 0.0


def test_physics_body_inverse_mass_kinematic() -> None:
    """Test inverse mass for kinematic body."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=0.0, shape=shape)

    assert body.inverse_mass == 0.0


def test_apply_force() -> None:
    """Test applying force to body."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)

    body.apply_force(force=Vector2(x=100.0, y=0.0), delta_time=0.1)

    assert body.velocity.x == 1.0
    assert body.velocity.y == 0.0


def test_apply_force_to_static_body() -> None:
    """Test applying force to static body has no effect."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape, is_static=True)

    body.apply_force(force=Vector2(x=100.0, y=0.0), delta_time=0.1)

    assert body.velocity.x == 0.0
    assert body.velocity.y == 0.0


def test_apply_impulse() -> None:
    """Test applying impulse to body."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)

    body.apply_impulse(impulse=Vector2(x=50.0, y=0.0))

    assert body.velocity.x == 5.0
    assert body.velocity.y == 0.0


def test_apply_impulse_to_static_body() -> None:
    """Test applying impulse to static body has no effect."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape, is_static=True)

    body.apply_impulse(impulse=Vector2(x=50.0, y=0.0))

    assert body.velocity.x == 0.0
    assert body.velocity.y == 0.0


def test_apply_force_accumulates() -> None:
    """Test applying multiple forces accumulates."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)

    body.apply_force(force=Vector2(x=100.0, y=0.0), delta_time=0.1)
    body.apply_force(force=Vector2(x=100.0, y=0.0), delta_time=0.1)

    assert body.velocity.x == 2.0


def test_apply_impulse_accumulates() -> None:
    """Test applying multiple impulses accumulates."""
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)

    body.apply_impulse(impulse=Vector2(x=50.0, y=0.0))
    body.apply_impulse(impulse=Vector2(x=50.0, y=0.0))

    assert body.velocity.x == 10.0
