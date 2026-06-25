"""Tests for ECSWorld snapshot integration."""

from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.world import ECSWorld
from yuna.exceptions import StateError, ValidationError
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
class Health(Component):
    """Test health component."""

    value: int


def test_world_create_snapshot() -> None:
    """Test that world can create snapshots."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    entity = world.create_entity()
    world.add_component(entity_id=entity, component=Position(x=10, y=20))

    tick = fake.random_int(min=0, max=1000)
    snapshot = world.create_snapshot(tick=tick)

    assert snapshot.tick == tick
    assert entity in snapshot.entities
    assert "Position" in snapshot.entities[entity]


def test_world_restore_snapshot() -> None:
    """Test that world can restore from snapshots."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    manager = StateManager(serializer=serializer)
    world1 = ECSWorld(state_manager=manager)

    entity = world1.create_entity()
    x = fake.random_int()
    y = fake.random_int()
    world1.add_component(entity_id=entity, component=Position(x=x, y=y))

    snapshot = world1.create_snapshot()

    world2 = ECSWorld(state_manager=manager)
    world2.restore_snapshot(snapshot=snapshot)

    restored_position = world2.get_component(entity_id=entity, component_type=Position)
    assert restored_position is not None
    assert isinstance(restored_position, Position)
    assert restored_position.x == x
    assert restored_position.y == y


def test_world_create_snapshot_without_state_manager() -> None:
    """Test that create_snapshot raises error without state manager."""
    world = ECSWorld()

    with pytest.raises(StateError, match="No state manager configured for world"):
        world.create_snapshot()


def test_world_restore_snapshot_without_state_manager() -> None:
    """Test that restore_snapshot raises error without state manager."""
    world = ECSWorld()
    snapshot = WorldSnapshot(tick=0, timestamp=1.0, entities={}, metadata={})

    with pytest.raises(StateError, match="No state manager configured for world"):
        world.restore_snapshot(snapshot=snapshot)


def test_world_create_snapshot_with_metadata() -> None:
    """Test creating snapshot with custom metadata."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    metadata = {"seed": fake.random_int(), "mode": fake.word()}
    snapshot = world.create_snapshot(metadata=metadata)

    assert snapshot.metadata == metadata


def test_world_snapshot_isolation() -> None:
    """Test that snapshots are isolated from world changes."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    entity = world.create_entity()
    world.add_component(entity_id=entity, component=Position(x=10, y=20))

    snapshot = world.create_snapshot()

    world.remove_component(entity_id=entity, component_type=Position)
    world.add_component(entity_id=entity, component=Position(x=99, y=99))

    assert snapshot.entities[entity]["Position"]["x"] == 10
    assert snapshot.entities[entity]["Position"]["y"] == 20


def test_world_multiple_snapshots() -> None:
    """Test that multiple snapshots don't interfere with each other."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    entity1 = world.create_entity()
    world.add_component(entity_id=entity1, component=Position(x=10, y=20))
    snapshot1 = world.create_snapshot(tick=1)

    entity2 = world.create_entity()
    world.add_component(entity_id=entity2, component=Position(x=30, y=40))
    snapshot2 = world.create_snapshot(tick=2)

    assert snapshot1.tick == 1
    assert snapshot2.tick == 2
    assert len(snapshot1.entities) == 1
    assert len(snapshot2.entities) == 2


def test_world_restore_clears_existing_state() -> None:
    """Test that restore_snapshot clears existing world state."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    manager = StateManager(serializer=serializer)
    world1 = ECSWorld(state_manager=manager, seed=1)

    entity1 = world1.create_entity()
    world1.add_component(entity_id=entity1, component=Position(x=10, y=20))
    snapshot = world1.create_snapshot()

    world2 = ECSWorld(state_manager=manager, seed=2)
    entity2 = world2.create_entity()
    world2.add_component(entity_id=entity2, component=Position(x=99, y=99))

    world2.restore_snapshot(snapshot=snapshot)

    assert entity1 in world2.get_all_entities()
    assert entity2 not in world2.get_all_entities()


def test_world_snapshot_with_multiple_components() -> None:
    """Test snapshots with multiple component types."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)
    serializer.register_component_type(component_type=Health)

    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    entity = world.create_entity()
    x = fake.random_int()
    y = fake.random_int()
    health = fake.random_int(min=1, max=100)

    world.add_component(entity_id=entity, component=Position(x=x, y=y))
    world.add_component(entity_id=entity, component=Health(value=health))

    snapshot = world.create_snapshot()

    new_world = ECSWorld(state_manager=manager)
    new_world.restore_snapshot(snapshot=snapshot)

    restored_position = new_world.get_component(
        entity_id=entity, component_type=Position
    )
    restored_health = new_world.get_component(entity_id=entity, component_type=Health)

    assert restored_position is not None
    assert isinstance(restored_position, Position)
    assert restored_position.x == x
    assert restored_position.y == y
    assert restored_health is not None
    assert isinstance(restored_health, Health)
    assert restored_health.value == health


def test_world_snapshot_with_multiple_entities() -> None:
    """Test snapshots with multiple entities."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    entities = []
    positions = []
    for _ in range(5):
        entity = world.create_entity()
        x = fake.random_int()
        y = fake.random_int()
        world.add_component(entity_id=entity, component=Position(x=x, y=y))
        entities.append(entity)
        positions.append((x, y))

    snapshot = world.create_snapshot()

    new_world = ECSWorld(state_manager=manager)
    new_world.restore_snapshot(snapshot=snapshot)

    for entity, (x, y) in zip(entities, positions, strict=False):
        restored_position = new_world.get_component(
            entity_id=entity, component_type=Position
        )
        assert restored_position is not None
        assert isinstance(restored_position, Position)
        assert restored_position.x == x
        assert restored_position.y == y


def test_world_restore_invalid_snapshot() -> None:
    """Test that restoring invalid snapshot raises ValueError."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    snapshot = WorldSnapshot(tick=-1, timestamp=1.0, entities={}, metadata={})

    with pytest.raises(ValidationError, match="validation failed"):
        world.restore_snapshot(snapshot=snapshot)
