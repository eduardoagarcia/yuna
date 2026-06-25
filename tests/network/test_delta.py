"""Tests for delta serialization."""

from faker import Faker

from yuna.network.delta import Delta, DeltaSerializer
from yuna.state.snapshot import WorldSnapshot
from yuna.types.identifiers import EntityID

fake = Faker()


def test_delta_creation() -> None:
    """Test Delta can be instantiated."""
    delta = Delta(tick=fake.random_int(min=0, max=1000))
    assert delta is not None


def test_delta_serializer_creation() -> None:
    """Test DeltaSerializer can be instantiated."""
    serializer = DeltaSerializer()
    assert serializer is not None


def test_compute_delta_empty_snapshots() -> None:
    """Test computing delta between two empty snapshots."""
    serializer = DeltaSerializer()
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=1.0, entities={})

    delta = serializer.compute_delta(old_snapshot=snapshot1, new_snapshot=snapshot2)

    assert delta.tick == 1
    assert len(delta.added_entities) == 0
    assert len(delta.removed_entities) == 0
    assert len(delta.modified_components) == 0


def test_compute_delta_added_entity() -> None:
    """Test computing delta with added entity."""
    serializer = DeltaSerializer()
    entity_id = EntityID(fake.uuid4())

    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities={})
    snapshot2 = WorldSnapshot(
        tick=1,
        timestamp=1.0,
        entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )

    delta = serializer.compute_delta(old_snapshot=snapshot1, new_snapshot=snapshot2)

    assert len(delta.added_entities) == 1
    assert entity_id in delta.added_entities
    assert delta.added_entities[entity_id] == {"Position": {"x": 10, "y": 20}}


def test_compute_delta_removed_entity() -> None:
    """Test computing delta with removed entity."""
    serializer = DeltaSerializer()
    entity_id = EntityID(fake.uuid4())

    snapshot1 = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )
    snapshot2 = WorldSnapshot(tick=1, timestamp=1.0, entities={})

    delta = serializer.compute_delta(old_snapshot=snapshot1, new_snapshot=snapshot2)

    assert len(delta.removed_entities) == 1
    assert entity_id in delta.removed_entities


def test_compute_delta_modified_component() -> None:
    """Test computing delta with modified component."""
    serializer = DeltaSerializer()
    entity_id = EntityID(fake.uuid4())

    snapshot1 = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )
    snapshot2 = WorldSnapshot(
        tick=1,
        timestamp=1.0,
        entities={entity_id: {"Position": {"x": 30, "y": 40}}},
    )

    delta = serializer.compute_delta(old_snapshot=snapshot1, new_snapshot=snapshot2)

    assert len(delta.modified_components) == 1
    assert entity_id in delta.modified_components
    assert delta.modified_components[entity_id] == {"Position": {"x": 30, "y": 40}}


def test_compute_delta_added_component() -> None:
    """Test computing delta with added component to existing entity."""
    serializer = DeltaSerializer()
    entity_id = EntityID(fake.uuid4())

    snapshot1 = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )
    snapshot2 = WorldSnapshot(
        tick=1,
        timestamp=1.0,
        entities={
            entity_id: {
                "Position": {"x": 10, "y": 20},
                "Health": {"current": 100, "maximum": 100},
            }
        },
    )

    delta = serializer.compute_delta(old_snapshot=snapshot1, new_snapshot=snapshot2)

    assert entity_id in delta.modified_components
    assert "Health" in delta.modified_components[entity_id]


def test_compute_delta_removed_component() -> None:
    """Test computing delta with removed component from entity."""
    serializer = DeltaSerializer()
    entity_id = EntityID(fake.uuid4())

    snapshot1 = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={
            entity_id: {
                "Position": {"x": 10, "y": 20},
                "Health": {"current": 100, "maximum": 100},
            }
        },
    )
    snapshot2 = WorldSnapshot(
        tick=1,
        timestamp=1.0,
        entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )

    delta = serializer.compute_delta(old_snapshot=snapshot1, new_snapshot=snapshot2)

    assert entity_id in delta.modified_components


def test_compute_delta_unchanged_entity() -> None:
    """Test computing delta with unchanged entity."""
    serializer = DeltaSerializer()
    entity_id = EntityID(fake.uuid4())

    snapshot1 = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )
    snapshot2 = WorldSnapshot(
        tick=1,
        timestamp=1.0,
        entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )

    delta = serializer.compute_delta(old_snapshot=snapshot1, new_snapshot=snapshot2)

    assert entity_id not in delta.modified_components
    assert entity_id not in delta.added_entities
    assert entity_id not in delta.removed_entities


def test_apply_delta_empty() -> None:
    """Test applying empty delta."""
    serializer = DeltaSerializer()
    base_snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities={})
    delta = Delta(tick=1)

    result = serializer.apply_delta(base_snapshot=base_snapshot, delta=delta)

    assert result.tick == 1
    assert len(result.entities) == 0


def test_apply_delta_added_entity() -> None:
    """Test applying delta with added entity."""
    serializer = DeltaSerializer()
    entity_id = EntityID(fake.uuid4())

    base_snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities={})
    delta = Delta(
        tick=1,
        added_entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )

    result = serializer.apply_delta(base_snapshot=base_snapshot, delta=delta)

    assert entity_id in result.entities
    assert result.entities[entity_id] == {"Position": {"x": 10, "y": 20}}


def test_apply_delta_removed_entity() -> None:
    """Test applying delta with removed entity."""
    serializer = DeltaSerializer()
    entity_id = EntityID(fake.uuid4())

    base_snapshot = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )
    delta = Delta(
        tick=1,
        removed_entities={entity_id},
    )

    result = serializer.apply_delta(base_snapshot=base_snapshot, delta=delta)

    assert entity_id not in result.entities


def test_apply_delta_modified_component() -> None:
    """Test applying delta with modified component."""
    serializer = DeltaSerializer()
    entity_id = EntityID(fake.uuid4())

    base_snapshot = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )
    delta = Delta(
        tick=1,
        modified_components={entity_id: {"Position": {"x": 30, "y": 40}}},
    )

    result = serializer.apply_delta(base_snapshot=base_snapshot, delta=delta)

    assert result.entities[entity_id]["Position"] == {"x": 30, "y": 40}


def test_apply_delta_multiple_entities() -> None:
    """Test applying delta with multiple entity changes."""
    serializer = DeltaSerializer()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    base_snapshot = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={
            entity1: {"Position": {"x": 10, "y": 20}},
            entity2: {"Position": {"x": 30, "y": 40}},
        },
    )
    delta = Delta(
        tick=1,
        added_entities={entity3: {"Position": {"x": 50, "y": 60}}},
        removed_entities={entity2},
        modified_components={entity1: {"Position": {"x": 15, "y": 25}}},
    )

    result = serializer.apply_delta(base_snapshot=base_snapshot, delta=delta)

    assert entity1 in result.entities
    assert result.entities[entity1]["Position"] == {"x": 15, "y": 25}
    assert entity2 not in result.entities
    assert entity3 in result.entities
    assert result.entities[entity3] == {"Position": {"x": 50, "y": 60}}


def test_round_trip_delta() -> None:
    """Test computing and applying delta produces correct snapshot."""
    serializer = DeltaSerializer()
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

    delta = serializer.compute_delta(old_snapshot=snapshot1, new_snapshot=snapshot2)
    result = serializer.apply_delta(base_snapshot=snapshot1, delta=delta)

    assert result.tick == snapshot2.tick
    assert result.entities == snapshot2.entities


def test_delta_with_metadata_preserved() -> None:
    """Test delta application preserves metadata."""
    serializer = DeltaSerializer()
    entity_id = EntityID(fake.uuid4())

    base_snapshot = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={},
        metadata={"seed": 42, "player_count": 4},
    )
    delta = Delta(
        tick=1,
        added_entities={entity_id: {"Position": {"x": 10, "y": 20}}},
    )

    result = serializer.apply_delta(base_snapshot=base_snapshot, delta=delta)

    assert result.metadata == base_snapshot.metadata


def test_large_delta() -> None:
    """Test computing delta with many entities."""
    serializer = DeltaSerializer()

    entities1 = {
        EntityID(fake.uuid4()): {"Position": {"x": i, "y": i}} for i in range(100)
    }
    entities2 = {
        EntityID(fake.uuid4()): {"Position": {"x": i * 2, "y": i * 2}}
        for i in range(100)
    }

    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities1)
    snapshot2 = WorldSnapshot(tick=1, timestamp=1.0, entities=entities2)

    delta = serializer.compute_delta(old_snapshot=snapshot1, new_snapshot=snapshot2)

    assert len(delta.added_entities) == 100
    assert len(delta.removed_entities) == 100


def test_apply_delta_removed_component() -> None:
    """Test applying delta with removed component."""
    serializer = DeltaSerializer()
    entity_id = EntityID(fake.uuid4())

    base_snapshot = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={
            entity_id: {
                "Position": {"x": 10, "y": 20},
                "Health": {"current": 100, "maximum": 100},
            }
        },
    )
    delta = Delta(
        tick=1,
        modified_components={entity_id: {"Health": None}},
    )

    result = serializer.apply_delta(base_snapshot=base_snapshot, delta=delta)

    assert "Position" in result.entities[entity_id]
    assert "Health" not in result.entities[entity_id]


def test_apply_delta_unchanged_entity() -> None:
    """Test applying delta with unchanged entity."""
    serializer = DeltaSerializer()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    base_snapshot = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={
            entity1: {"Position": {"x": 10, "y": 20}},
            entity2: {"Position": {"x": 30, "y": 40}},
        },
    )
    delta = Delta(
        tick=1,
        modified_components={entity1: {"Position": {"x": 15, "y": 25}}},
    )

    result = serializer.apply_delta(base_snapshot=base_snapshot, delta=delta)

    assert result.entities[entity1]["Position"] == {"x": 15, "y": 25}
    assert result.entities[entity2]["Position"] == {"x": 30, "y": 40}
