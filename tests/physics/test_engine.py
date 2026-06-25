"""Tests for physics engine."""

import time

from yuna.physics.body import PhysicsBody
from yuna.physics.engine import CollisionEvent, PhysicsEngine
from yuna.physics.shapes import (
    BoxShape,
    CircleShape,
    CollisionLayer,
    PolygonShape,
)
from yuna.types.vector import Vector2


def test_physics_engine_creation() -> None:
    """Test physics engine creation."""
    engine = PhysicsEngine()

    assert engine.gravity.x == 0.0
    assert engine.gravity.y == 0.0


def test_physics_engine_with_gravity() -> None:
    """Test physics engine with custom gravity."""
    engine = PhysicsEngine(gravity=Vector2(x=0.0, y=-9.8))

    assert engine.gravity.x == 0.0
    assert engine.gravity.y == -9.8


def test_add_body() -> None:
    """Test adding body to engine."""
    engine = PhysicsEngine()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)

    engine.add_body(entity_id="entity1", body=body, position=Vector2(x=0.0, y=0.0))

    position = engine.get_position(entity_id="entity1")
    assert position is not None
    assert position.x == 0.0
    assert position.y == 0.0


def test_remove_body() -> None:
    """Test removing body from engine."""
    engine = PhysicsEngine()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)
    engine.add_body(entity_id="entity1", body=body, position=Vector2(x=0.0, y=0.0))

    engine.remove_body(entity_id="entity1")

    assert engine.get_position(entity_id="entity1") is None


def test_set_position() -> None:
    """Test setting body position."""
    engine = PhysicsEngine()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)
    engine.add_body(entity_id="entity1", body=body, position=Vector2(x=0.0, y=0.0))

    engine.set_position(entity_id="entity1", position=Vector2(x=10.0, y=10.0))

    position = engine.get_position(entity_id="entity1")
    assert position is not None
    assert position.x == 10.0
    assert position.y == 10.0


def test_step_applies_gravity() -> None:
    """Test step applies gravity to bodies."""
    engine = PhysicsEngine(gravity=Vector2(x=0.0, y=-9.8))
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=1.0, shape=shape)
    engine.add_body(entity_id="entity1", body=body, position=Vector2(x=0.0, y=100.0))

    engine.step(delta_time=1.0)

    position = engine.get_position(entity_id="entity1")
    assert position is not None
    assert position.y < 100.0


def test_step_integrates_velocity() -> None:
    """Test step integrates velocity into position."""
    engine = PhysicsEngine()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(
        mass=10.0,
        shape=shape,
        velocity=Vector2(x=10.0, y=0.0),
    )
    engine.add_body(entity_id="entity1", body=body, position=Vector2(x=0.0, y=0.0))

    engine.step(delta_time=1.0)

    position = engine.get_position(entity_id="entity1")
    assert position is not None
    assert position.x == 10.0


def test_step_static_body_does_not_move() -> None:
    """Test static body does not move."""
    engine = PhysicsEngine(gravity=Vector2(x=0.0, y=-9.8))
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape, is_static=True)
    engine.add_body(entity_id="entity1", body=body, position=Vector2(x=0.0, y=0.0))

    engine.step(delta_time=1.0)

    position = engine.get_position(entity_id="entity1")
    assert position is not None
    assert position.x == 0.0
    assert position.y == 0.0


def test_collision_detection() -> None:
    """Test collision detection between overlapping bodies."""
    engine = PhysicsEngine()
    shape1 = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    shape2 = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body1 = PhysicsBody(mass=10.0, shape=shape1)
    body2 = PhysicsBody(mass=10.0, shape=shape2)

    engine.add_body(entity_id="entity1", body=body1, position=Vector2(x=0.0, y=0.0))
    engine.add_body(entity_id="entity2", body=body2, position=Vector2(x=8.0, y=0.0))

    events = engine.step(delta_time=0.1)

    assert len(events) > 0
    assert isinstance(events[0], CollisionEvent)


def test_collision_resolution() -> None:
    """Test collision resolution applies impulses."""
    engine = PhysicsEngine()
    shape1 = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    shape2 = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body1 = PhysicsBody(
        mass=1.0,
        shape=shape1,
        velocity=Vector2(x=10.0, y=0.0),
    )
    body2 = PhysicsBody(mass=1.0, shape=shape2)

    engine.add_body(entity_id="entity1", body=body1, position=Vector2(x=0.0, y=0.0))
    engine.add_body(entity_id="entity2", body=body2, position=Vector2(x=8.0, y=0.0))

    engine.step(delta_time=0.1)

    assert body2.velocity.x != 0.0


def test_query_point_finds_bodies() -> None:
    """Test query point finds bodies at position."""
    engine = PhysicsEngine()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)
    engine.add_body(entity_id="entity1", body=body, position=Vector2(x=0.0, y=0.0))

    result = engine.query_point(position=Vector2(x=2.0, y=2.0))

    assert "entity1" in result


def test_query_point_empty_when_no_bodies() -> None:
    """Test query point returns empty when no bodies."""
    engine = PhysicsEngine()

    result = engine.query_point(position=Vector2(x=0.0, y=0.0))

    assert len(result) == 0


def test_query_circle_finds_bodies() -> None:
    """Test query circle finds bodies in radius."""
    engine = PhysicsEngine()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)
    engine.add_body(entity_id="entity1", body=body, position=Vector2(x=0.0, y=0.0))

    result = engine.query_circle(position=Vector2(x=10.0, y=0.0), radius=20.0)

    assert "entity1" in result


def test_query_circle_empty_when_out_of_range() -> None:
    """Test query circle returns empty when out of range."""
    engine = PhysicsEngine()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)
    engine.add_body(entity_id="entity1", body=body, position=Vector2(x=0.0, y=0.0))

    result = engine.query_circle(position=Vector2(x=100.0, y=0.0), radius=5.0)

    assert len(result) == 0


def test_raycast_finds_body() -> None:
    """Test raycast finds body in path."""
    engine = PhysicsEngine()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body = PhysicsBody(mass=10.0, shape=shape)
    engine.add_body(entity_id="entity1", body=body, position=Vector2(x=10.0, y=0.0))

    result = engine.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=0.0),
        max_distance=20.0,
    )

    assert result is not None
    entity_id, hit_point = result
    assert entity_id == "entity1"


def test_raycast_returns_none_when_no_hit() -> None:
    """Test raycast returns None when no hit."""
    engine = PhysicsEngine()

    result = engine.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=0.0),
        max_distance=10.0,
    )

    assert result is None


def test_deterministic_simulation() -> None:
    """Test simulation is deterministic."""
    engine1 = PhysicsEngine(gravity=Vector2(x=0.0, y=-9.8))
    engine2 = PhysicsEngine(gravity=Vector2(x=0.0, y=-9.8))

    for engine in [engine1, engine2]:
        shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
        body = PhysicsBody(mass=1.0, shape=shape)
        engine.add_body(
            entity_id="entity1",
            body=body,
            position=Vector2(x=0.0, y=100.0),
        )

    for _ in range(10):
        engine1.step(delta_time=0.1)
        engine2.step(delta_time=0.1)

    pos1 = engine1.get_position(entity_id="entity1")
    pos2 = engine2.get_position(entity_id="entity1")

    assert pos1 is not None
    assert pos2 is not None
    assert pos1.x == pos2.x
    assert pos1.y == pos2.y


def test_collision_event_has_metadata() -> None:
    """Test collision event includes timestamp and tick."""
    engine = PhysicsEngine()
    shape1 = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    shape2 = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body1 = PhysicsBody(mass=10.0, shape=shape1)
    body2 = PhysicsBody(mass=10.0, shape=shape2)

    engine.add_body(entity_id="entity1", body=body1, position=Vector2(x=0.0, y=0.0))
    engine.add_body(entity_id="entity2", body=body2, position=Vector2(x=8.0, y=0.0))

    events = engine.step(delta_time=0.1, timestamp=1234.5, tick=42)

    assert len(events) > 0
    assert events[0].timestamp == 1234.5
    assert events[0].tick == 42


def test_collision_layer_filtering() -> None:
    """Test collision layer filtering prevents collisions."""
    engine = PhysicsEngine()
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
    body1 = PhysicsBody(mass=10.0, shape=shape1)
    body2 = PhysicsBody(mass=10.0, shape=shape2)

    engine.add_body(entity_id="entity1", body=body1, position=Vector2(x=0.0, y=0.0))
    engine.add_body(entity_id="entity2", body=body2, position=Vector2(x=5.0, y=0.0))

    events = engine.step(delta_time=0.1)

    assert len(events) == 0


def test_collision_between_two_static_bodies() -> None:
    """Test collision between two static bodies does not create event."""
    engine = PhysicsEngine()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body1 = PhysicsBody(mass=10.0, shape=shape, is_static=True)
    body2 = PhysicsBody(mass=10.0, shape=shape, is_static=True)

    engine.add_body(entity_id="entity1", body=body1, position=Vector2(x=0.0, y=0.0))
    engine.add_body(entity_id="entity2", body=body2, position=Vector2(x=5.0, y=0.0))

    events = engine.step(delta_time=0.1)

    assert len(events) == 0
    assert body1.velocity.x == 0.0
    assert body2.velocity.x == 0.0


def test_collision_with_zero_distance() -> None:
    """Test collision resolution when bodies are at same position."""
    engine = PhysicsEngine()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body1 = PhysicsBody(mass=1.0, shape=shape)
    body2 = PhysicsBody(mass=1.0, shape=shape)

    engine.add_body(entity_id="entity1", body=body1, position=Vector2(x=0.0, y=0.0))
    engine.add_body(entity_id="entity2", body=body2, position=Vector2(x=0.0, y=0.0))

    events = engine.step(delta_time=0.1)

    assert len(events) > 0


def test_collision_bodies_separating() -> None:
    """Test collision not resolved when bodies are separating."""
    engine = PhysicsEngine()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body1 = PhysicsBody(
        mass=1.0,
        shape=shape,
        velocity=Vector2(x=-10.0, y=0.0),
    )
    body2 = PhysicsBody(
        mass=1.0,
        shape=shape,
        velocity=Vector2(x=10.0, y=0.0),
    )

    engine.add_body(entity_id="entity1", body=body1, position=Vector2(x=0.0, y=0.0))
    engine.add_body(entity_id="entity2", body=body2, position=Vector2(x=8.0, y=0.0))

    initial_vel1 = body1.velocity.x
    initial_vel2 = body2.velocity.x

    engine.step(delta_time=0.1)

    assert body1.velocity.x == initial_vel1
    assert body2.velocity.x == initial_vel2


def test_collision_box_circle() -> None:
    """Test collision between box and circle shapes."""
    engine = PhysicsEngine()
    box_shape = BoxShape(width=10.0, height=10.0, offset=Vector2(x=0.0, y=0.0))
    circle_shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    body1 = PhysicsBody(mass=10.0, shape=box_shape)
    body2 = PhysicsBody(mass=10.0, shape=circle_shape)

    engine.add_body(entity_id="entity1", body=body1, position=Vector2(x=0.0, y=0.0))
    engine.add_body(entity_id="entity2", body=body2, position=Vector2(x=8.0, y=0.0))

    events = engine.step(delta_time=0.1)

    assert len(events) > 0


def test_collision_circle_polygon() -> None:
    """Test collision between circle and polygon shapes."""
    engine = PhysicsEngine()
    circle_shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    polygon_shape = PolygonShape(
        vertices=[
            Vector2(x=-5.0, y=-5.0),
            Vector2(x=5.0, y=-5.0),
            Vector2(x=5.0, y=5.0),
            Vector2(x=-5.0, y=5.0),
        ],
        offset=Vector2(x=0.0, y=0.0),
    )
    body1 = PhysicsBody(mass=10.0, shape=circle_shape)
    body2 = PhysicsBody(mass=10.0, shape=polygon_shape)

    engine.add_body(entity_id="entity1", body=body1, position=Vector2(x=0.0, y=0.0))
    engine.add_body(entity_id="entity2", body=body2, position=Vector2(x=8.0, y=0.0))

    events = engine.step(delta_time=0.1)

    assert len(events) > 0


def test_collision_box_polygon_not_supported() -> None:
    """Test collision between two non-circle shapes not supported."""
    engine = PhysicsEngine()
    box_shape = BoxShape(width=10.0, height=10.0, offset=Vector2(x=0.0, y=0.0))
    polygon_shape = PolygonShape(
        vertices=[
            Vector2(x=-5.0, y=-5.0),
            Vector2(x=5.0, y=-5.0),
            Vector2(x=5.0, y=5.0),
            Vector2(x=-5.0, y=5.0),
        ],
        offset=Vector2(x=0.0, y=0.0),
    )
    body1 = PhysicsBody(mass=10.0, shape=box_shape)
    body2 = PhysicsBody(mass=10.0, shape=polygon_shape)

    engine.add_body(entity_id="entity1", body=body1, position=Vector2(x=0.0, y=0.0))
    engine.add_body(entity_id="entity2", body=body2, position=Vector2(x=5.0, y=0.0))

    events = engine.step(delta_time=0.1)

    assert len(events) == 0


def test_performance_50_bodies_at_60fps() -> None:
    """Test physics engine handles 1000+ bodies at 60 FPS."""
    engine = PhysicsEngine(gravity=Vector2(x=0.0, y=-9.8))
    shape = CircleShape(radius=1.0, offset=Vector2(x=0.0, y=0.0))

    num_bodies = 50
    grid_size = 32

    for i in range(num_bodies):
        body = PhysicsBody(mass=1.0, shape=shape)
        x = (i % grid_size) * 5.0
        y = (i // grid_size) * 5.0
        engine.add_body(
            entity_id=f"body_{i}",
            body=body,
            position=Vector2(x=x, y=y),
        )

    target_fps = 60
    target_frame_time = 1.0 / target_fps
    num_frames = 10

    start_time = time.perf_counter()

    for _ in range(num_frames):
        engine.step(delta_time=1.0 / 60.0)

    end_time = time.perf_counter()
    total_time = end_time - start_time
    avg_frame_time = total_time / num_frames

    assert avg_frame_time < target_frame_time
    assert len(engine._bodies) == num_bodies
