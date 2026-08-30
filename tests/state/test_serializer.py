"""Tests for SnapshotSerializer."""

# ruff: noqa: PLC2701
import json
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from dataclasses import make_dataclass
from enum import Enum
from typing import Any

import pytest
from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.world import ECSWorld
from yuna.exceptions import SerializationError, ValidationError
from yuna.network.compression import ZlibCompression
from yuna.state.serializer import (
    SnapshotSerializer,
    _component_plans,
    _is_deeply_immutable_dataclass,
    _is_immutable_annotation,
)
from yuna.state.snapshot import WorldSnapshot
from yuna.types.identifiers import EntityID

fake = Faker()


class ResourceType(Enum):
    """Test enum for resource types."""

    HEALTH = "health"
    POWER = "power"
    AMMO = "ammo"


class StatusEffect(Enum):
    """Test enum for status effects."""

    BURNING = "burning"
    FROZEN = "frozen"
    POISONED = "poisoned"


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


@dataclass
class Velocity(Component):
    """Test component for velocity data."""

    dx: float
    dy: float


@dataclass
class Resource(Component):
    """Test component with enum field."""

    resource_type: ResourceType
    amount: float


@dataclass
class Status(Component):
    """Test component with enum field."""

    effect: StatusEffect
    duration: int


def test_register_component_type() -> None:
    """Test registering component types."""
    serializer = SnapshotSerializer()

    serializer.register_component_type(component_type=Position)
    serializer.register_component_type(component_type=Health)

    assert "Position" in serializer._component_types
    assert "Health" in serializer._component_types
    assert serializer._component_types["Position"] == Position
    assert serializer._component_types["Health"] == Health


def test_register_non_dataclass_component_type() -> None:
    """Test registering a non-dataclass component type raises error."""
    serializer = SnapshotSerializer()

    class NotADataclass:
        pass

    with pytest.raises(SerializationError, match="must be a dataclass"):
        serializer.register_component_type(component_type=NotADataclass)


def test_serialize_empty_world() -> None:
    """Test serializing empty world."""
    world = ECSWorld()
    serializer = SnapshotSerializer()

    tick = fake.random_int(min=0, max=1000)
    metadata = {"seed": fake.random_int()}

    snapshot = serializer.serialize(world=world, tick=tick, metadata=metadata)

    assert snapshot.tick == tick
    assert snapshot.metadata == metadata
    assert len(snapshot.entities) == 0


def test_serialize_world_with_single_entity() -> None:
    """Test serializing world with one entity."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    entity_id = world.create_entity()
    x = fake.pyfloat()
    y = fake.pyfloat()
    world.add_component(entity_id=entity_id, component=Position(x=x, y=y))

    snapshot = serializer.serialize(world=world)

    assert len(snapshot.entities) == 1
    assert entity_id in snapshot.entities
    assert "Position" in snapshot.entities[entity_id]
    assert snapshot.entities[entity_id]["Position"]["x"] == x
    assert snapshot.entities[entity_id]["Position"]["y"] == y


def test_serialize_world_with_multiple_entities() -> None:
    """Test serializing world with multiple entities."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)
    serializer.register_component_type(component_type=Health)

    entity1 = world.create_entity()
    entity2 = world.create_entity()
    entity3 = world.create_entity()

    world.add_component(entity_id=entity1, component=Position(x=1.0, y=2.0))
    world.add_component(entity_id=entity2, component=Health(current=80, maximum=100))
    world.add_component(entity_id=entity3, component=Position(x=3.0, y=4.0))
    world.add_component(entity_id=entity3, component=Health(current=50, maximum=50))

    snapshot = serializer.serialize(world=world)

    assert len(snapshot.entities) == 3
    assert entity1 in snapshot.entities
    assert entity2 in snapshot.entities
    assert entity3 in snapshot.entities
    assert "Position" in snapshot.entities[entity1]
    assert "Health" in snapshot.entities[entity2]
    assert "Position" in snapshot.entities[entity3]
    assert "Health" in snapshot.entities[entity3]


def test_deserialize_empty_world() -> None:
    """Test deserializing empty snapshot."""
    world = ECSWorld()
    serializer = SnapshotSerializer()

    snapshot = WorldSnapshot(
        tick=fake.random_int(),
        timestamp=fake.pyfloat(),
        entities={},
    )

    serializer.deserialize(snapshot=snapshot, world=world)

    assert len(world._entities._entities) == 0


def test_deserialize_world_with_entities() -> None:
    """Test deserializing snapshot with entities."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)
    serializer.register_component_type(component_type=Health)

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    snapshot = WorldSnapshot(
        tick=fake.random_int(),
        timestamp=fake.pyfloat(),
        entities={
            entity1: {"Position": {"x": 10.0, "y": 20.0}},
            entity2: {
                "Position": {"x": 30.0, "y": 40.0},
                "Health": {"current": 75, "maximum": 100},
            },
        },
    )

    serializer.deserialize(snapshot=snapshot, world=world)

    assert world._entities.exists(entity_id=entity1)
    assert world._entities.exists(entity_id=entity2)

    pos1 = world.get_component(entity_id=entity1, component_type=Position)
    assert pos1 is not None
    assert isinstance(pos1, Position)
    assert pos1.x == 10.0
    assert pos1.y == 20.0

    pos2 = world.get_component(entity_id=entity2, component_type=Position)
    health2 = world.get_component(entity_id=entity2, component_type=Health)
    assert pos2 is not None
    assert isinstance(pos2, Position)
    assert pos2.x == 30.0
    assert health2 is not None
    assert isinstance(health2, Health)
    assert health2.current == 75


def test_deserialize_clears_existing_world() -> None:
    """Test deserialization clears existing world state."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    existing_entity = world.create_entity()
    world.add_component(entity_id=existing_entity, component=Position(x=99.0, y=99.0))

    new_entity = EntityID(fake.uuid4())
    snapshot = WorldSnapshot(
        tick=fake.random_int(),
        timestamp=fake.pyfloat(),
        entities={
            new_entity: {"Position": {"x": 1.0, "y": 2.0}},
        },
    )

    serializer.deserialize(snapshot=snapshot, world=world)

    assert not world._entities.exists(entity_id=existing_entity)
    assert world._entities.exists(entity_id=new_entity)
    assert len(world._entities._entities) == 1


def test_round_trip_serialization() -> None:
    """Test serialize then deserialize produces identical state."""
    world1 = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)
    serializer.register_component_type(component_type=Health)
    serializer.register_component_type(component_type=Velocity)

    entity1 = world1.create_entity()
    entity2 = world1.create_entity()
    entity3 = world1.create_entity()

    world1.add_component(entity_id=entity1, component=Position(x=1.0, y=2.0))
    world1.add_component(entity_id=entity1, component=Velocity(dx=0.5, dy=0.3))
    world1.add_component(entity_id=entity2, component=Health(current=80, maximum=100))
    world1.add_component(entity_id=entity3, component=Position(x=10.0, y=20.0))
    world1.add_component(entity_id=entity3, component=Health(current=50, maximum=50))
    world1.add_component(entity_id=entity3, component=Velocity(dx=1.0, dy=2.0))

    snapshot = serializer.serialize(world=world1)

    world2 = ECSWorld()
    serializer.deserialize(snapshot=snapshot, world=world2)

    assert len(world2._entities._entities) == 3
    assert world2._entities.exists(entity_id=entity1)
    assert world2._entities.exists(entity_id=entity2)
    assert world2._entities.exists(entity_id=entity3)

    pos1 = world2.get_component(entity_id=entity1, component_type=Position)
    vel1 = world2.get_component(entity_id=entity1, component_type=Velocity)
    assert pos1 is not None
    assert isinstance(pos1, Position)
    assert pos1.x == 1.0 and pos1.y == 2.0
    assert vel1 is not None
    assert isinstance(vel1, Velocity)
    assert vel1.dx == 0.5 and vel1.dy == 0.3

    health2 = world2.get_component(entity_id=entity2, component_type=Health)
    assert health2 is not None
    assert isinstance(health2, Health)
    assert health2.current == 80

    pos3 = world2.get_component(entity_id=entity3, component_type=Position)
    health3 = world2.get_component(entity_id=entity3, component_type=Health)
    vel3 = world2.get_component(entity_id=entity3, component_type=Velocity)
    assert pos3 is not None
    assert isinstance(pos3, Position)
    assert pos3.x == 10.0
    assert health3 is not None
    assert isinstance(health3, Health)
    assert health3.current == 50
    assert vel3 is not None
    assert isinstance(vel3, Velocity)
    assert vel3.dx == 1.0


def test_to_json_conversion() -> None:
    """Test converting snapshot to JSON."""
    serializer = SnapshotSerializer()

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    snapshot = WorldSnapshot(
        tick=100,
        timestamp=1234567890.5,
        entities={
            entity1: {"Position": {"x": 10.0, "y": 20.0}},
            entity2: {"Health": {"current": 50, "maximum": 100}},
        },
        metadata={"seed": 42},
    )

    json_str = serializer.to_json(snapshot=snapshot)

    assert isinstance(json_str, str)
    data = json.loads(s=json_str)
    assert data["tick"] == 100
    assert data["timestamp"] == 1234567890.5
    assert data["metadata"]["seed"] == 42
    assert entity1 in data["entities"]
    assert entity2 in data["entities"]


def test_from_json_conversion() -> None:
    """Test converting JSON to snapshot."""
    serializer = SnapshotSerializer()

    json_str = """
    {
        "tick": 100,
        "timestamp": 1234567890.5,
        "entities": {
            "test-id-1": {"Position": {"x": 10.0, "y": 20.0}},
            "test-id-2": {"Health": {"current": 50, "maximum": 100}}
        },
        "metadata": {"seed": 42}
    }
    """

    snapshot = serializer.from_json(json_str=json_str)

    assert snapshot.tick == 100
    assert snapshot.timestamp == 1234567890.5
    assert snapshot.metadata["seed"] == 42
    assert EntityID("test-id-1") in snapshot.entities
    assert EntityID("test-id-2") in snapshot.entities
    assert snapshot.entities[EntityID("test-id-1")]["Position"]["x"] == 10.0


def test_json_round_trip() -> None:
    """Test to_json then from_json produces identical snapshot."""
    serializer = SnapshotSerializer()

    entity_id = EntityID(fake.uuid4())
    original = WorldSnapshot(
        tick=fake.random_int(),
        timestamp=fake.pyfloat(),
        entities={
            entity_id: {"Position": {"x": 5.5, "y": 6.6}},
        },
        metadata={"seed": fake.random_int()},
    )

    json_str = serializer.to_json(snapshot=original)
    restored = serializer.from_json(json_str=json_str)

    assert restored.tick == original.tick
    assert restored.timestamp == original.timestamp
    assert restored.entities == original.entities
    assert restored.metadata == original.metadata


def test_large_world_serialization() -> None:
    """Test serializing large world with 1000+ entities."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)
    serializer.register_component_type(component_type=Health)

    entity_count = 1500
    for _ in range(entity_count):
        entity = world.create_entity()
        world.add_component(
            entity_id=entity,
            component=Position(x=fake.pyfloat(), y=fake.pyfloat()),
        )
        if fake.boolean():
            world.add_component(
                entity_id=entity,
                component=Health(
                    current=fake.random_int(min=1, max=100),
                    maximum=100,
                ),
            )

    snapshot = serializer.serialize(world=world)

    assert len(snapshot.entities) == entity_count


def test_deserialize_unknown_component_type() -> None:
    """Test deserializing snapshot with unregistered component type."""
    world = ECSWorld()
    serializer = SnapshotSerializer()

    snapshot = WorldSnapshot(
        tick=fake.random_int(),
        timestamp=fake.pyfloat(),
        entities={
            EntityID(fake.uuid4()): {"UnknownComponent": {"data": "test"}},
        },
    )

    with pytest.raises(ValidationError, match="Unknown component type"):
        serializer.deserialize(snapshot=snapshot, world=world)


def test_serialize_component_not_dataclass() -> None:
    """Test serializing component that is not a dataclass."""
    serializer = SnapshotSerializer()

    class NotADataclass:
        def __init__(self) -> None:
            self.value = 42

    component = NotADataclass()

    with pytest.raises(SerializationError, match="must be a dataclass"):
        serializer._serialize_component(component=component)


def test_deserialize_component_not_dataclass() -> None:
    """Test deserializing to component type that is not a dataclass."""
    serializer = SnapshotSerializer()

    class NotADataclass:
        pass

    with pytest.raises(SerializationError, match="must be a dataclass"):
        serializer._deserialize_component(
            component_type=NotADataclass,
            component_data={},
        )


def test_serialize_metadata_preserved() -> None:
    """Test that metadata is preserved during serialization."""
    world = ECSWorld()
    serializer = SnapshotSerializer()

    metadata = {
        "seed": fake.random_int(),
        "player_count": fake.random_int(min=1, max=8),
        "game_mode": fake.word(),
    }

    snapshot = serializer.serialize(world=world, metadata=metadata)

    assert snapshot.metadata == metadata


def test_serialize_default_tick() -> None:
    """Test serializing with default tick value."""
    world = ECSWorld()
    serializer = SnapshotSerializer()

    snapshot = serializer.serialize(world=world)

    assert snapshot.tick == 0


def test_deserialize_with_extra_component_fields() -> None:
    """Test deserializing component data with extra fields."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    entity_id = EntityID(fake.uuid4())
    snapshot = WorldSnapshot(
        tick=fake.random_int(),
        timestamp=fake.pyfloat(),
        entities={
            entity_id: {"Position": {"x": 10.0, "y": 20.0, "extra_field": "ignored"}},
        },
    )

    serializer.deserialize(snapshot=snapshot, world=world)

    pos = world.get_component(entity_id=entity_id, component_type=Position)
    assert pos is not None
    assert isinstance(pos, Position)
    assert pos.x == 10.0
    assert pos.y == 20.0
    assert not hasattr(pos, "extra_field")


def test_serialize_delta_empty_snapshots() -> None:
    """Test serializing delta between empty snapshots."""
    serializer = SnapshotSerializer()

    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=1.0, entities={})

    delta_bytes = serializer.serialize_delta(
        old_snapshot=snapshot1,
        new_snapshot=snapshot2,
    )

    assert isinstance(delta_bytes, bytes)
    assert len(delta_bytes) > 0


def test_deserialize_delta_empty() -> None:
    """Test deserializing empty delta."""
    serializer = SnapshotSerializer()

    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=1.0, entities={})

    delta_bytes = serializer.serialize_delta(
        old_snapshot=snapshot1,
        new_snapshot=snapshot2,
    )
    result = serializer.deserialize_delta(
        base_snapshot=snapshot1,
        delta_bytes=delta_bytes,
    )

    assert result.tick == 1
    assert len(result.entities) == 0


def test_serialize_delta_with_changes() -> None:
    """Test serializing delta with entity changes."""
    serializer = SnapshotSerializer()
    entity_id = EntityID(fake.uuid4())

    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities={})
    snapshot2 = WorldSnapshot(
        tick=1,
        timestamp=1.0,
        entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )

    delta_bytes = serializer.serialize_delta(
        old_snapshot=snapshot1,
        new_snapshot=snapshot2,
    )

    assert isinstance(delta_bytes, bytes)
    assert len(delta_bytes) > 0


def test_round_trip_delta_serialization() -> None:
    """Test delta serialization round trip."""
    serializer = SnapshotSerializer()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    snapshot1 = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={entity1: {"Position": {"x": 10, "y": 20}}},
    )
    snapshot2 = WorldSnapshot(
        tick=1,
        timestamp=1.0,
        entities={
            entity1: {"Position": {"x": 30, "y": 40}},
            entity2: {"Health": {"current": 100, "maximum": 100}},
        },
    )

    delta_bytes = serializer.serialize_delta(
        old_snapshot=snapshot1,
        new_snapshot=snapshot2,
    )
    result = serializer.deserialize_delta(
        base_snapshot=snapshot1,
        delta_bytes=delta_bytes,
    )

    assert result.tick == snapshot2.tick
    assert result.entities == snapshot2.entities


def test_delta_serialization_with_compression() -> None:
    """Test delta serialization with compression strategy."""
    serializer = SnapshotSerializer(compression_strategy=ZlibCompression())
    entity_id = EntityID(fake.uuid4())

    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities={})
    snapshot2 = WorldSnapshot(
        tick=1,
        timestamp=1.0,
        entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )

    delta_bytes = serializer.serialize_delta(
        old_snapshot=snapshot1,
        new_snapshot=snapshot2,
    )
    result = serializer.deserialize_delta(
        base_snapshot=snapshot1,
        delta_bytes=delta_bytes,
    )

    assert result.entities == snapshot2.entities


def test_delta_smaller_than_full_snapshot() -> None:
    """Test delta is smaller than full snapshot for small changes."""
    serializer = SnapshotSerializer()

    entities = {
        EntityID(fake.uuid4()): {"Position": {"x": i, "y": i}} for i in range(100)
    }
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities)

    modified_entities = dict(entities)
    one_entity = list(modified_entities.keys())[0]
    modified_entities[one_entity] = {"Position": {"x": 999, "y": 999}}
    snapshot2 = WorldSnapshot(tick=1, timestamp=1.0, entities=modified_entities)

    delta_bytes = serializer.serialize_delta(
        old_snapshot=snapshot1,
        new_snapshot=snapshot2,
    )
    full_bytes = serializer.to_json(snapshot=snapshot2).encode(encoding="utf-8")

    assert len(delta_bytes) < len(full_bytes)


def test_serialize_component_with_enum() -> None:
    """Test serializing component with enum converts to value."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Resource)

    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id,
        component=Resource(resource_type=ResourceType.HEALTH, amount=100.0),
    )

    snapshot = serializer.serialize(world=world)

    assert len(snapshot.entities) == 1
    assert entity_id in snapshot.entities
    assert "Resource" in snapshot.entities[entity_id]
    assert snapshot.entities[entity_id]["Resource"]["resource_type"] == "health"
    assert snapshot.entities[entity_id]["Resource"]["amount"] == 100.0


def test_deserialize_component_with_enum() -> None:
    """Test deserializing component with enum reconstructs enum instance."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Resource)

    entity_id = EntityID(fake.uuid4())
    snapshot = WorldSnapshot(
        tick=fake.random_int(),
        timestamp=fake.pyfloat(),
        entities={
            entity_id: {"Resource": {"resource_type": "power", "amount": 50.0}},
        },
    )

    serializer.deserialize(snapshot=snapshot, world=world)

    resource = world.get_component(entity_id=entity_id, component_type=Resource)
    assert resource is not None
    assert isinstance(resource, Resource)
    assert resource.resource_type == ResourceType.POWER
    assert isinstance(resource.resource_type, ResourceType)
    assert resource.amount == 50.0


def test_round_trip_serialization_with_enums() -> None:
    """Test serialize then deserialize with enums preserves types."""
    world1 = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Resource)
    serializer.register_component_type(component_type=Status)

    entity1 = world1.create_entity()
    entity2 = world1.create_entity()

    world1.add_component(
        entity_id=entity1,
        component=Resource(resource_type=ResourceType.HEALTH, amount=75.0),
    )
    world1.add_component(
        entity_id=entity2,
        component=Status(effect=StatusEffect.BURNING, duration=10),
    )

    snapshot = serializer.serialize(world=world1)

    world2 = ECSWorld()
    serializer.deserialize(snapshot=snapshot, world=world2)

    resource1 = world2.get_component(entity_id=entity1, component_type=Resource)
    status2 = world2.get_component(entity_id=entity2, component_type=Status)

    assert resource1 is not None
    assert isinstance(resource1, Resource)
    assert resource1.resource_type == ResourceType.HEALTH
    assert isinstance(resource1.resource_type, ResourceType)
    assert resource1.amount == 75.0

    assert status2 is not None
    assert isinstance(status2, Status)
    assert status2.effect == StatusEffect.BURNING
    assert isinstance(status2.effect, StatusEffect)
    assert status2.duration == 10


def test_to_json_with_enum_components() -> None:
    """Test converting snapshot with enum components to JSON."""
    serializer = SnapshotSerializer()

    entity_id = EntityID(fake.uuid4())
    snapshot = WorldSnapshot(
        tick=100,
        timestamp=1234567890.5,
        entities={
            entity_id: {"Resource": {"resource_type": "ammo", "amount": 200.0}},
        },
        metadata={"seed": 42},
    )

    json_str = serializer.to_json(snapshot=snapshot)

    assert isinstance(json_str, str)
    data = json.loads(s=json_str)
    assert data["entities"][entity_id]["Resource"]["resource_type"] == "ammo"
    assert data["entities"][entity_id]["Resource"]["amount"] == 200.0


def test_from_json_with_enum_components() -> None:
    """Test converting JSON with enum components to snapshot."""
    serializer = SnapshotSerializer()

    entity_id = fake.uuid4()
    json_str = f"""
    {{
        "tick": 100,
        "timestamp": 1234567890.5,
        "entities": {{
            "{entity_id}": {{"Status": {{"effect": "frozen", "duration": 5}}}}
        }},
        "metadata": {{"seed": 42}}
    }}
    """

    snapshot = serializer.from_json(json_str=json_str)

    assert EntityID(entity_id) in snapshot.entities
    assert snapshot.entities[EntityID(entity_id)]["Status"]["effect"] == "frozen"
    assert snapshot.entities[EntityID(entity_id)]["Status"]["duration"] == 5


def test_normalize_for_serialization_nested_enums() -> None:
    """Test normalizing nested structures with enums."""
    serializer = SnapshotSerializer()

    nested_data = {
        "simple_enum": ResourceType.HEALTH,
        "nested_dict": {"status": StatusEffect.POISONED, "value": 42},
        "enum_list": [ResourceType.POWER, ResourceType.AMMO],
        "primitive": "unchanged",
    }

    normalized = serializer._normalize_for_serialization(data=nested_data)

    assert normalized["simple_enum"] == "health"
    assert normalized["nested_dict"]["status"] == "poisoned"
    assert normalized["nested_dict"]["value"] == 42
    assert normalized["enum_list"] == ["power", "ammo"]
    assert normalized["primitive"] == "unchanged"


def test_serialize_component_with_to_dict_method() -> None:
    """Test serializing component that has to_dict method uses it."""

    @dataclass
    class CustomComponent(Component):
        value: int
        name: str

        def to_dict(self) -> dict[str, Any]:
            return {"custom_value": self.value * 2, "custom_name": self.name.upper()}

    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=CustomComponent)

    world = ECSWorld()
    entity = world.create_entity()
    component = CustomComponent(value=10, name="test")
    world.add_component(entity_id=entity, component=component)

    snapshot = serializer.serialize(world=world)

    assert entity in snapshot.entities
    assert "CustomComponent" in snapshot.entities[entity]
    assert snapshot.entities[entity]["CustomComponent"]["custom_value"] == 20
    assert snapshot.entities[entity]["CustomComponent"]["custom_name"] == "TEST"


def test_normalize_for_serialization_with_to_dict_objects() -> None:
    """Test normalizing nested objects with to_dict method."""

    class CustomObject:
        def __init__(self, value: int):
            self.value = value

        def to_dict(self) -> dict[str, Any]:
            return {"doubled": self.value * 2}

    class NestedObject:
        def __init__(self, inner: CustomObject):
            self.inner = inner

        def to_dict(self) -> dict[str, Any]:
            return {"inner": self.inner}

    serializer = SnapshotSerializer()

    data = {"nested": NestedObject(inner=CustomObject(value=5)), "simple": 42}

    normalized = serializer._normalize_for_serialization(data=data)

    assert normalized["nested"]["inner"]["doubled"] == 10
    assert normalized["simple"] == 42


def test_serialize_component_without_to_dict_uses_asdict() -> None:
    """Test serializing component without to_dict uses asdict."""

    @dataclass
    class SimpleComponent(Component):
        x: int
        y: int

    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=SimpleComponent)

    world = ECSWorld()
    entity = world.create_entity()
    component = SimpleComponent(x=5, y=10)
    world.add_component(entity_id=entity, component=component)

    snapshot = serializer.serialize(world=world)

    assert entity in snapshot.entities
    assert "SimpleComponent" in snapshot.entities[entity]
    assert snapshot.entities[entity]["SimpleComponent"]["x"] == 5
    assert snapshot.entities[entity]["SimpleComponent"]["y"] == 10


def test_capture_creates_raw_snapshot_without_serialization() -> None:
    """Test that capture creates raw snapshot with serialized components."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)
    serializer.register_component_type(component_type=Health)

    entity1 = world.create_entity()
    entity2 = world.create_entity()

    pos = Position(x=fake.pyfloat(), y=fake.pyfloat())
    health = Health(current=fake.random_int(min=1, max=100), maximum=100)

    world.add_component(entity_id=entity1, component=pos)
    world.add_component(entity_id=entity2, component=health)

    tick = fake.random_int(min=0, max=1000)
    metadata = {"seed": fake.random_int()}

    raw_snapshot = serializer.capture(world=world, tick=tick, metadata=metadata)

    assert raw_snapshot.tick == tick
    assert raw_snapshot.metadata == metadata
    assert len(raw_snapshot.entities) == 2
    assert entity1 in raw_snapshot.entities
    assert entity2 in raw_snapshot.entities
    assert isinstance(raw_snapshot.entities[entity1]["Position"], dict)
    assert isinstance(raw_snapshot.entities[entity2]["Health"], dict)


def test_finalize_converts_raw_snapshot_to_world_snapshot() -> None:
    """Test that finalize converts raw snapshot to world snapshot."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)

    entity = world.create_entity()
    x = fake.pyfloat()
    y = fake.pyfloat()
    world.add_component(entity_id=entity, component=Position(x=x, y=y))

    raw_snapshot = serializer.capture(world=world, tick=0, metadata={})

    world_snapshot = serializer.finalize(raw_snapshot=raw_snapshot)

    assert world_snapshot.tick == raw_snapshot.tick
    assert world_snapshot.timestamp == raw_snapshot.timestamp
    assert world_snapshot.metadata == raw_snapshot.metadata
    assert len(world_snapshot.entities) == 1
    assert entity in world_snapshot.entities
    assert isinstance(world_snapshot.entities[entity]["Position"], dict)
    assert world_snapshot.entities[entity]["Position"]["x"] == x
    assert world_snapshot.entities[entity]["Position"]["y"] == y


def test_capture_and_finalize_round_trip() -> None:
    """Test that capture then finalize produces correct snapshot."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)
    serializer.register_component_type(component_type=Health)
    serializer.register_component_type(component_type=Velocity)

    entity1 = world.create_entity()
    entity2 = world.create_entity()

    world.add_component(entity_id=entity1, component=Position(x=10.0, y=20.0))
    world.add_component(entity_id=entity1, component=Velocity(dx=1.0, dy=2.0))
    world.add_component(entity_id=entity2, component=Health(current=75, maximum=100))

    tick = fake.random_int(min=1, max=1000)
    metadata = {"seed": fake.random_int()}

    raw_snapshot = serializer.capture(world=world, tick=tick, metadata=metadata)
    world_snapshot = serializer.finalize(raw_snapshot=raw_snapshot)

    assert world_snapshot.tick == tick
    assert world_snapshot.metadata == metadata
    assert len(world_snapshot.entities) == 2
    assert entity1 in world_snapshot.entities
    assert entity2 in world_snapshot.entities
    assert world_snapshot.entities[entity1]["Position"]["x"] == 10.0
    assert world_snapshot.entities[entity1]["Position"]["y"] == 20.0
    assert world_snapshot.entities[entity1]["Velocity"]["dx"] == 1.0
    assert world_snapshot.entities[entity1]["Velocity"]["dy"] == 2.0
    assert world_snapshot.entities[entity2]["Health"]["current"] == 75
    assert world_snapshot.entities[entity2]["Health"]["maximum"] == 100


def test_normalize_for_serialization_with_dataclass_having_dict() -> None:
    """Test _normalize_for_serialization with dataclass that has __dict__."""

    @dataclass
    class SimpleComponent:
        value: int
        name: str

    component = SimpleComponent(value=42, name=fake.word())
    normalized = SnapshotSerializer._normalize_for_serialization(data=component)

    assert isinstance(normalized, dict)
    assert normalized["value"] == 42
    assert normalized["name"] == component.name


def test_normalize_for_serialization_with_slotted_dataclass() -> None:
    """Test _normalize_for_serialization with slotted dataclass (no __dict__)."""

    @dataclass(slots=True)
    class SlottedComponent:
        value: int
        name: str

    component = SlottedComponent(value=99, name="test")
    normalized = SnapshotSerializer._normalize_for_serialization(data=component)

    assert isinstance(normalized, dict)
    assert normalized["value"] == 99
    assert normalized["name"] == "test"


def test_normalize_for_serialization_with_set_and_frozenset() -> None:
    """Test _normalize_for_serialization converts sets and frozensets to lists."""
    set_tags = {fake.unique.word(), fake.unique.word(), fake.unique.word()}
    data_with_set = {"tags": set_tags}

    normalized_set = SnapshotSerializer._normalize_for_serialization(data=data_with_set)

    assert isinstance(normalized_set["tags"], list)
    assert set(normalized_set["tags"]) == set_tags

    frozen_tags = frozenset([
        fake.unique.word(),
        fake.unique.word(),
        fake.unique.word(),
    ])
    data_with_frozenset = {"immutable_tags": frozen_tags}

    normalized_frozenset = SnapshotSerializer._normalize_for_serialization(
        data=data_with_frozenset
    )

    assert isinstance(normalized_frozenset["immutable_tags"], list)
    assert set(normalized_frozenset["immutable_tags"]) == frozen_tags


def test_capture_components_returns_only_named_components() -> None:
    """capture_components captures only the requested component types."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    entity_id = world.create_entity()
    x = fake.pyfloat()
    world.add_component(entity_id=entity_id, component=Position(x=x, y=fake.pyfloat()))
    world.add_component(
        entity_id=entity_id,
        component=Health(current=fake.random_int(), maximum=fake.random_int()),
    )

    captured = serializer.capture_components(
        world=world, included_components={"Position"}
    )

    assert "Position" in captured[entity_id]
    assert "Health" not in captured[entity_id]
    assert captured[entity_id]["Position"]["x"] == x


def test_capture_components_empty_set_returns_empty() -> None:
    """capture_components returns an empty mapping when nothing is requested."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id, component=Position(x=fake.pyfloat(), y=fake.pyfloat())
    )

    assert serializer.capture_components(world=world, included_components=set()) == {}


def test_capture_components_is_independent_copy() -> None:
    """capture_components data is independent of later component mutation."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    entity_id = world.create_entity()
    original_x = fake.pyfloat()
    position = Position(x=original_x, y=fake.pyfloat())
    world.add_component(entity_id=entity_id, component=position)

    captured = serializer.capture_components(
        world=world, included_components={"Position"}
    )
    position.x = fake.pyfloat()

    assert captured[entity_id]["Position"]["x"] == original_x


def test_capture_components_across_multiple_entities() -> None:
    """capture_components collects the named component from every entity."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    world.add_component(entity_id=entity1, component=Position(x=1.0, y=2.0))
    world.add_component(entity_id=entity2, component=Position(x=3.0, y=4.0))
    world.add_component(entity_id=entity2, component=Health(current=10, maximum=20))

    captured = serializer.capture_components(
        world=world, included_components={"Position"}
    )

    assert set(captured.keys()) == {entity1, entity2}
    assert captured[entity2]["Position"]["x"] == 3.0
    assert "Health" not in captured[entity2]


def test_capture_components_multiple_components_same_entity() -> None:
    """capture_components collects every requested component for one entity."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id, component=Position(x=fake.pyfloat(), y=fake.pyfloat())
    )
    world.add_component(
        entity_id=entity_id,
        component=Health(current=fake.random_int(), maximum=fake.random_int()),
    )

    captured = serializer.capture_components(
        world=world, included_components={"Position", "Health"}
    )

    assert "Position" in captured[entity_id]
    assert "Health" in captured[entity_id]


def test_component_plan_cached_per_type() -> None:
    """Repeated serialization of one type reuses a single cached plan."""

    @dataclass
    class PlanCachedComponent(Component):
        value: int

    first = SnapshotSerializer._serialize_component(
        component=PlanCachedComponent(value=fake.random_int())
    )
    second = SnapshotSerializer._serialize_component(
        component=PlanCachedComponent(value=fake.random_int())
    )

    assert set(first.keys()) == set(second.keys()) == {"value"}
    assert _component_plans[PlanCachedComponent].field_names == ("value",)
    assert _component_plans[PlanCachedComponent].uses_to_dict is False


def test_component_plan_detects_to_dict() -> None:
    """Plan building records a to_dict method and serialization uses it."""

    @dataclass
    class PlanToDictComponent(Component):
        value: int

        def to_dict(self) -> dict[str, Any]:
            return {"doubled": self.value * 2}

    serialized = SnapshotSerializer._serialize_component(
        component=PlanToDictComponent(value=21)
    )

    assert serialized == {"doubled": 42}
    assert _component_plans[PlanToDictComponent].uses_to_dict is True


def test_normalize_primitive_fast_path() -> None:
    """Exact primitive values return unchanged."""
    for value in ("text", 7, 3.5, True, None):
        assert SnapshotSerializer._normalize_for_serialization(data=value) == value


def test_normalize_exact_dict_with_mixed_leaves() -> None:
    """Exact dicts normalize nested enums while passing primitives through."""
    normalized = SnapshotSerializer._normalize_for_serialization(
        data={"speed": 1.5, "status": StatusEffect.FROZEN, "tags": [1, "a"]}
    )

    assert normalized == {"speed": 1.5, "status": "frozen", "tags": [1, "a"]}


def test_normalize_dict_subclass_uses_generic_path() -> None:
    """Dict subclasses still normalize through the isinstance branch."""

    class TrackedDict(dict):
        pass

    normalized = SnapshotSerializer._normalize_for_serialization(
        data=TrackedDict({"effect": StatusEffect.BURNING})
    )

    assert normalized == {"effect": "burning"}


def test_normalize_list_subclass_uses_generic_path() -> None:
    """List subclasses still normalize through the isinstance branch."""

    class TrackedList(list):
        pass

    normalized = SnapshotSerializer._normalize_for_serialization(
        data=TrackedList([StatusEffect.POISONED, 2])
    )

    assert normalized == ["poisoned", 2]


def test_serialize_component_mixed_primitive_and_nested_fields() -> None:
    """Primitive fields skip normalization while nested values still convert."""

    @dataclass
    class MixedComponent(Component):
        label: str
        effect: StatusEffect
        offsets: list[int]

    serialized = SnapshotSerializer._serialize_component(
        component=MixedComponent(
            label="anchor",
            effect=StatusEffect.BURNING,
            offsets=[1, 2],
        )
    )

    assert serialized == {
        "label": "anchor",
        "effect": "burning",
        "offsets": [1, 2],
    }


@dataclass(frozen=True)
class FrozenVector:
    """Deeply immutable helper for cache tests."""

    x: float
    y: float


@dataclass(frozen=True)
class FrozenAnchorComponent(Component):
    """Deeply immutable component eligible for serialization reuse."""

    label: str
    offset: FrozenVector
    effect: StatusEffect | None
    tags: frozenset[str]


@dataclass(frozen=True)
class FrozenBagComponent(Component):
    """Frozen component with a mutable field, ineligible for reuse."""

    values: dict[str, float]


def test_capture_reuses_serialized_dict_for_unchanged_immutable_component() -> None:
    """Unchanged deeply immutable components share one serialized dict."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id,
        component=FrozenAnchorComponent(
            label="wall",
            offset=FrozenVector(x=1.0, y=2.0),
            effect=None,
            tags=frozenset({"static"}),
        ),
    )

    first = serializer.capture(world=world, tick=0)
    second = serializer.capture(world=world, tick=1)

    assert (
        first.entities[entity_id]["FrozenAnchorComponent"]
        is second.entities[entity_id]["FrozenAnchorComponent"]
    )


def test_capture_recomputes_after_immutable_component_replaced() -> None:
    """Replacing a frozen component instance produces a fresh serialized dict."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id,
        component=FrozenAnchorComponent(
            label="wall",
            offset=FrozenVector(x=1.0, y=2.0),
            effect=None,
            tags=frozenset(),
        ),
    )

    first = serializer.capture(world=world, tick=0)
    world.add_component(
        entity_id=entity_id,
        component=FrozenAnchorComponent(
            label="moved",
            offset=FrozenVector(x=3.0, y=4.0),
            effect=StatusEffect.FROZEN,
            tags=frozenset(),
        ),
    )
    second = serializer.capture(world=world, tick=1)

    assert (
        first.entities[entity_id]["FrozenAnchorComponent"]
        is not second.entities[entity_id]["FrozenAnchorComponent"]
    )
    assert second.entities[entity_id]["FrozenAnchorComponent"]["label"] == "moved"
    assert second.entities[entity_id]["FrozenAnchorComponent"]["effect"] == "frozen"


def test_capture_does_not_reuse_dicts_for_mutable_components() -> None:
    """Components with mutable fields are re-serialized every capture."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id, component=FrozenBagComponent(values={"speed": 1.0})
    )

    first = serializer.capture(world=world, tick=0)
    second = serializer.capture(world=world, tick=1)

    assert (
        first.entities[entity_id]["FrozenBagComponent"]
        is not second.entities[entity_id]["FrozenBagComponent"]
    )


def test_frozen_component_with_to_dict_is_not_cacheable() -> None:
    """A to_dict method disables reuse even on deeply immutable types."""

    @dataclass(frozen=True)
    class FrozenToDictComponent(Component):
        value: int

        def to_dict(self) -> dict[str, Any]:
            return {"value": self.value}

    SnapshotSerializer._serialize_component(component=FrozenToDictComponent(value=1))

    assert _component_plans[FrozenToDictComponent].cacheable is False


def test_non_frozen_dataclass_is_not_deeply_immutable() -> None:
    """Mutable dataclasses are never eligible for serialization reuse."""

    @dataclass
    class MutablePoint:
        x: float

    assert _is_deeply_immutable_dataclass(dataclass_type=MutablePoint) is False


def test_unresolvable_annotations_are_not_deeply_immutable() -> None:
    """Unresolvable forward references conservatively disable reuse."""
    forward_ref_component = make_dataclass(
        cls_name="ForwardRefComponent",
        fields=[("value", "MissingType")],
        frozen=True,
    )

    assert _is_deeply_immutable_dataclass(dataclass_type=forward_ref_component) is False


def test_immutable_annotation_rejects_plain_containers() -> None:
    """Bare mutable containers and unparameterized sets are not immutable."""
    assert _is_immutable_annotation(annotation=dict) is False
    assert _is_immutable_annotation(annotation=list[int]) is False
    assert _is_immutable_annotation(annotation=frozenset) is False


@dataclass
class VersionedBagComponent(Component):
    """Mutable component opted into version-counted serialization reuse."""

    values: dict[str, float] = dataclass_field(default_factory=dict)
    serialization_version: int = dataclass_field(default=0, compare=False)


def test_versioned_component_excludes_version_from_serialization() -> None:
    """The serialization_version field never appears in serialized output."""
    serialized = SnapshotSerializer._serialize_component(
        component=VersionedBagComponent(values={"speed": 1.0})
    )

    assert serialized == {"values": {"speed": 1.0}}


def test_versioned_component_reuses_dict_while_version_unchanged() -> None:
    """Unchanged versioned components share one serialized dict."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id, component=VersionedBagComponent(values={"speed": 1.0})
    )

    first = serializer.capture(world=world, tick=0)
    second = serializer.capture(world=world, tick=1)

    assert (
        first.entities[entity_id]["VersionedBagComponent"]
        is second.entities[entity_id]["VersionedBagComponent"]
    )


def test_versioned_component_recomputes_after_version_bump() -> None:
    """Bumping serialization_version invalidates the cached dict."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    entity_id = world.create_entity()
    bag = VersionedBagComponent(values={"speed": 1.0})
    world.add_component(entity_id=entity_id, component=bag)

    first = serializer.capture(world=world, tick=0)
    bag.values["speed"] = 2.0
    bag.serialization_version += 1
    second = serializer.capture(world=world, tick=1)

    assert first.entities[entity_id]["VersionedBagComponent"] == {
        "values": {"speed": 1.0}
    }
    assert second.entities[entity_id]["VersionedBagComponent"] == {
        "values": {"speed": 2.0}
    }


def test_versioned_component_recomputes_after_instance_replacement() -> None:
    """Replacing the component instance invalidates the cached dict."""
    world = ECSWorld()
    serializer = SnapshotSerializer()
    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id, component=VersionedBagComponent(values={"speed": 1.0})
    )

    serializer.capture(world=world, tick=0)
    world.add_component(
        entity_id=entity_id, component=VersionedBagComponent(values={"speed": 3.0})
    )
    second = serializer.capture(world=world, tick=1)

    assert second.entities[entity_id]["VersionedBagComponent"] == {
        "values": {"speed": 3.0}
    }


def test_immutable_annotation_accepts_immutable_shapes() -> None:
    """Primitives, enums, unions, and immutable containers are accepted."""
    assert _is_immutable_annotation(annotation=float) is True
    assert _is_immutable_annotation(annotation=StatusEffect) is True
    assert _is_immutable_annotation(annotation=int | None) is True
    assert _is_immutable_annotation(annotation=frozenset[str]) is True
    assert _is_immutable_annotation(annotation=tuple[int, ...]) is True
    assert _is_immutable_annotation(annotation=FrozenVector) is True


def test_normalize_for_serialization_passes_unhandled_types_through() -> None:
    """Types with no normalization rule fall through unchanged."""
    unhandled = (fake.pyint(), fake.word())

    assert SnapshotSerializer._normalize_for_serialization(data=unhandled) is unhandled
