"""Tests for StateManager."""

import time
from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.world import ECSWorld
from yuna.exceptions import ValidationError
from yuna.state.manager import StateManager
from yuna.state.serializer import SnapshotSerializer
from yuna.state.snapshot import WorldSnapshot

fake = Faker()


@dataclass(frozen=True)
class Position(Component):
    """Test position component."""

    x: int
    y: int


@dataclass(frozen=True)
class Velocity(Component):
    """Test velocity component."""

    dx: int
    dy: int


def test_create_snapshot_captures_world_state() -> None:
    """Test that create_snapshot captures complete world state."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)
    serializer.register_component_type(component_type=Velocity)

    manager = StateManager(serializer=serializer)
    world = ECSWorld()

    entity = world.create_entity()
    world.add_component(entity_id=entity, component=Position(x=10, y=20))
    world.add_component(entity_id=entity, component=Velocity(dx=1, dy=2))

    tick = fake.random_int(min=0, max=1000)
    metadata = {"seed": fake.random_int(), "player": fake.name()}

    snapshot = manager.create_snapshot(world=world, tick=tick, metadata=metadata)

    assert snapshot.tick == tick
    assert snapshot.timestamp > 0
    assert entity in snapshot.entities
    assert "Position" in snapshot.entities[entity]
    assert "Velocity" in snapshot.entities[entity]
    assert snapshot.metadata == metadata


def test_create_snapshot_with_defaults() -> None:
    """Test create_snapshot with default tick and metadata."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld()

    snapshot = manager.create_snapshot(world=world)

    assert snapshot.tick == 0
    assert snapshot.metadata == {}
    assert snapshot.timestamp > 0


def test_restore_snapshot_restores_world_state() -> None:
    """Test that restore_snapshot restores exact world state."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)
    serializer.register_component_type(component_type=Velocity)

    manager = StateManager(serializer=serializer)
    world = ECSWorld()

    entity = world.create_entity()
    x = fake.random_int()
    y = fake.random_int()
    dx = fake.random_int()
    dy = fake.random_int()

    world.add_component(entity_id=entity, component=Position(x=x, y=y))
    world.add_component(entity_id=entity, component=Velocity(dx=dx, dy=dy))

    snapshot = manager.create_snapshot(world=world)

    new_world = ECSWorld()
    manager.restore_snapshot(snapshot=snapshot, world=new_world)

    restored_position = new_world.get_component(
        entity_id=entity, component_type=Position
    )
    restored_velocity = new_world.get_component(
        entity_id=entity, component_type=Velocity
    )

    assert restored_position is not None
    assert isinstance(restored_position, Position)
    assert restored_position.x == x
    assert restored_position.y == y
    assert restored_velocity is not None
    assert isinstance(restored_velocity, Velocity)
    assert restored_velocity.dx == dx
    assert restored_velocity.dy == dy


def test_restore_snapshot_clears_existing_entities() -> None:
    """Test that restore_snapshot clears existing entities before restoring."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    manager = StateManager(serializer=serializer)
    world1 = ECSWorld(seed=1)

    entity1 = world1.create_entity()
    world1.add_component(entity_id=entity1, component=Position(x=10, y=20))

    snapshot = manager.create_snapshot(world=world1)

    world2 = ECSWorld(seed=2)
    entity2 = world2.create_entity()
    world2.add_component(entity_id=entity2, component=Position(x=99, y=99))

    manager.restore_snapshot(snapshot=snapshot, world=world2)

    assert entity1 in world2.get_all_entities()
    assert entity2 not in world2.get_all_entities()


def test_validate_snapshot_accepts_valid_snapshot() -> None:
    """Test that validate_snapshot accepts valid snapshots."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)

    snapshot = WorldSnapshot(
        tick=fake.random_int(min=0, max=1000),
        timestamp=time.time(),
        entities={},
        metadata={},
    )

    assert manager.validate_snapshot(snapshot=snapshot) is True


def test_validate_snapshot_rejects_negative_tick() -> None:
    """Test that validate_snapshot rejects negative tick."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)

    snapshot = WorldSnapshot(
        tick=-1,
        timestamp=time.time(),
        entities={},
        metadata={},
    )

    assert manager.validate_snapshot(snapshot=snapshot) is False


def test_validate_snapshot_rejects_invalid_timestamp() -> None:
    """Test that validate_snapshot rejects invalid timestamp."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)

    snapshot = WorldSnapshot(
        tick=0,
        timestamp=0,
        entities={},
        metadata={},
    )

    assert manager.validate_snapshot(snapshot=snapshot) is False


def test_validate_snapshot_rejects_invalid_entities() -> None:
    """Test that validate_snapshot rejects invalid entities."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)

    snapshot = WorldSnapshot(
        tick=0,
        timestamp=time.time(),
        entities="not a dict",  # type: ignore[arg-type]
        metadata={},
    )

    assert manager.validate_snapshot(snapshot=snapshot) is False


def test_validate_snapshot_rejects_invalid_metadata() -> None:
    """Test that validate_snapshot rejects invalid metadata."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)

    snapshot = WorldSnapshot(
        tick=0,
        timestamp=time.time(),
        entities={},
        metadata="not a dict",  # type: ignore[arg-type]
    )

    assert manager.validate_snapshot(snapshot=snapshot) is False


def test_restore_snapshot_raises_on_invalid_snapshot() -> None:
    """Test that restore_snapshot raises ValueError on invalid snapshot."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld()

    snapshot = WorldSnapshot(
        tick=-1,
        timestamp=time.time(),
        entities={},
        metadata={},
    )

    with pytest.raises(ValidationError, match="Snapshot validation failed"):
        manager.restore_snapshot(snapshot=snapshot, world=world)


def test_multiple_snapshots_dont_interfere() -> None:
    """Test that multiple snapshots are independent."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    manager = StateManager(serializer=serializer)
    world = ECSWorld()

    entity1 = world.create_entity()
    world.add_component(entity_id=entity1, component=Position(x=10, y=20))
    snapshot1 = manager.create_snapshot(world=world, tick=1)

    entity2 = world.create_entity()
    world.add_component(entity_id=entity2, component=Position(x=30, y=40))
    snapshot2 = manager.create_snapshot(world=world, tick=2)

    assert snapshot1.tick == 1
    assert snapshot2.tick == 2
    assert len(snapshot1.entities) == 1
    assert len(snapshot2.entities) == 2
    assert entity1 in snapshot1.entities
    assert entity1 in snapshot2.entities
    assert entity2 in snapshot2.entities
    assert entity2 not in snapshot1.entities


def test_snapshot_isolation_from_world_changes() -> None:
    """Test that snapshots are immutable and isolated from world changes."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    manager = StateManager(serializer=serializer)
    world = ECSWorld()

    entity = world.create_entity()
    world.add_component(entity_id=entity, component=Position(x=10, y=20))

    snapshot = manager.create_snapshot(world=world)
    original_position = snapshot.entities[entity]["Position"]

    world.remove_component(entity_id=entity, component_type=Position)
    world.add_component(entity_id=entity, component=Position(x=99, y=99))

    assert snapshot.entities[entity]["Position"] == original_position
    assert snapshot.entities[entity]["Position"]["x"] == 10
    assert snapshot.entities[entity]["Position"]["y"] == 20


def test_capture_components_returns_named_components() -> None:
    """capture_components delegates to the serializer for the named components."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld()
    entity = world.create_entity()
    x = fake.random_int()
    world.add_component(entity_id=entity, component=Position(x=x, y=fake.random_int()))
    world.add_component(
        entity_id=entity,
        component=Velocity(dx=fake.random_int(), dy=fake.random_int()),
    )

    captured = manager.capture_components(world=world, included_components={"Position"})

    assert captured[entity]["Position"]["x"] == x
    assert "Velocity" not in captured[entity]
