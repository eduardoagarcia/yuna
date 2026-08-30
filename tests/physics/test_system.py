"""Tests for physics system."""

from yuna.ecs.world import ECSWorld
from yuna.events.bus import EventBus
from yuna.physics.body import PhysicsBody
from yuna.physics.shapes import CircleShape
from yuna.physics.system import PhysicsSystem
from yuna.spatial.integration import Position
from yuna.types.vector import Vector2


def test_physics_system_creation() -> None:
    """Test physics system creation."""
    system = PhysicsSystem()

    assert system.priority == 100
    assert system.engine is not None


def test_physics_system_with_event_bus() -> None:
    """Test physics system with event bus."""
    event_bus = EventBus()
    system = PhysicsSystem(event_bus=event_bus)

    assert system._event_bus is event_bus


def test_physics_system_with_custom_priority() -> None:
    """Test physics system with custom priority."""
    system = PhysicsSystem(priority=50)

    assert system.priority == 50


def test_update_syncs_bodies_to_engine() -> None:
    """Test update syncs bodies to physics engine."""
    world = ECSWorld()
    system = PhysicsSystem()

    entity_id = world.create_entity()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    world.add_component(
        entity_id=entity_id, component=PhysicsBody(mass=10.0, shape=shape)
    )
    world.add_component(
        entity_id=entity_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    system.update(world=world, delta_time=0.1)

    position = system.engine.get_position(entity_id=str(entity_id))
    assert position is not None


def test_update_syncs_positions_from_engine() -> None:
    """Test update syncs positions back to ECS."""
    world = ECSWorld()
    system = PhysicsSystem(gravity=Vector2(x=0.0, y=-9.8))

    entity_id = world.create_entity()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    world.add_component(
        entity_id=entity_id, component=PhysicsBody(mass=1.0, shape=shape)
    )
    world.add_component(
        entity_id=entity_id,
        component=Position(position=Vector2(x=0.0, y=100.0)),
    )

    system.update(world=world, delta_time=1.0)

    position_component = world.get_component(
        entity_id=entity_id, component_type=Position
    )
    assert position_component is not None
    assert isinstance(position_component, Position)
    assert position_component.position.y < 100.0


def test_update_removes_destroyed_entities() -> None:
    """Test update removes destroyed entities from engine."""
    world = ECSWorld()
    system = PhysicsSystem()

    entity_id = world.create_entity()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))
    world.add_component(
        entity_id=entity_id, component=PhysicsBody(mass=10.0, shape=shape)
    )
    world.add_component(
        entity_id=entity_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    system.update(world=world, delta_time=0.1)
    world.destroy_entity(entity_id=entity_id)
    system.update(world=world, delta_time=0.1)

    position = system.engine.get_position(entity_id=str(entity_id))
    assert position is None


def test_update_emits_collision_events() -> None:
    """Test update emits collision events to event bus."""
    world = ECSWorld()
    event_bus = EventBus()
    system = PhysicsSystem(event_bus=event_bus)

    events_received = []

    def handler(event):
        events_received.append(event)

    event_bus.subscribe(event_type="CollisionEvent", handler=handler)

    entity1 = world.create_entity()
    entity2 = world.create_entity()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))

    world.add_component(
        entity_id=entity1, component=PhysicsBody(mass=10.0, shape=shape)
    )
    world.add_component(
        entity_id=entity1,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=entity2, component=PhysicsBody(mass=10.0, shape=shape)
    )
    world.add_component(
        entity_id=entity2,
        component=Position(position=Vector2(x=8.0, y=0.0)),
    )

    system.update(world=world, delta_time=0.1)
    event_bus.process_events()

    assert len(events_received) > 0


def test_update_without_event_bus_does_not_crash() -> None:
    """Test update without event bus does not crash."""
    world = ECSWorld()
    system = PhysicsSystem()

    entity1 = world.create_entity()
    entity2 = world.create_entity()
    shape = CircleShape(radius=5.0, offset=Vector2(x=0.0, y=0.0))

    world.add_component(
        entity_id=entity1, component=PhysicsBody(mass=10.0, shape=shape)
    )
    world.add_component(
        entity_id=entity1,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=entity2, component=PhysicsBody(mass=10.0, shape=shape)
    )
    world.add_component(
        entity_id=entity2,
        component=Position(position=Vector2(x=8.0, y=0.0)),
    )

    system.update(world=world, delta_time=0.1)


def test_update_increments_tick_counter() -> None:
    """Test update increments internal tick counter."""
    world = ECSWorld()
    system = PhysicsSystem()

    assert system._tick_counter == 0

    system.update(world=world, delta_time=0.1)
    assert system._tick_counter == 1

    system.update(world=world, delta_time=0.1)
    assert system._tick_counter == 2
