"""Tests for WorldSnapshot."""

from typing import Any

import pytest
from faker import Faker

from yuna.state.snapshot import WorldSnapshot
from yuna.types.identifiers import EntityID

fake = Faker()


def test_world_snapshot_creation() -> None:
    """Test creating a world snapshot."""
    tick = fake.random_int(min=0, max=1000)
    timestamp = fake.pyfloat(min_value=0.0, max_value=999999999.0)
    entities = {
        EntityID(fake.uuid4()): {"Position": {"x": fake.pyfloat(), "y": fake.pyfloat()}}
    }
    metadata = {
        "seed": fake.random_int(),
        "player_count": fake.random_int(min=1, max=8),
    }

    snapshot = WorldSnapshot(
        tick=tick,
        timestamp=timestamp,
        entities=entities,
        metadata=metadata,
    )

    assert snapshot.tick == tick
    assert snapshot.timestamp == timestamp
    assert snapshot.entities == entities
    assert snapshot.metadata == metadata


def test_world_snapshot_default_metadata() -> None:
    """Test world snapshot with default metadata."""
    tick = fake.random_int(min=0, max=1000)
    timestamp = fake.pyfloat(min_value=0.0, max_value=999999999.0)
    entities: dict[EntityID, dict[str, Any]] = {}

    snapshot = WorldSnapshot(
        tick=tick,
        timestamp=timestamp,
        entities=entities,
    )

    assert snapshot.tick == tick
    assert snapshot.timestamp == timestamp
    assert snapshot.entities == entities
    assert snapshot.metadata == {}


def test_world_snapshot_immutability() -> None:
    """Test that world snapshot is immutable."""
    snapshot = WorldSnapshot(
        tick=fake.random_int(),
        timestamp=fake.pyfloat(),
        entities={},
    )

    with pytest.raises(expected_exception=AttributeError):
        snapshot.tick = 999  # type: ignore[misc]


def test_world_snapshot_empty_entities() -> None:
    """Test snapshot with no entities."""
    snapshot = WorldSnapshot(
        tick=fake.random_int(),
        timestamp=fake.pyfloat(),
        entities={},
    )

    assert snapshot.entities == {}
    assert len(snapshot.entities) == 0


def test_world_snapshot_multiple_entities() -> None:
    """Test snapshot with multiple entities."""
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())

    entities: dict[EntityID, dict[str, Any]] = {
        entity_1: {"Position": {"x": 10.0, "y": 20.0}, "Health": {"current": 100}},
        entity_2: {"Position": {"x": 30.0, "y": 40.0}},
        entity_3: {"Health": {"current": 50, "maximum": 100}},
    }

    snapshot = WorldSnapshot(
        tick=fake.random_int(),
        timestamp=fake.pyfloat(),
        entities=entities,
    )

    assert len(snapshot.entities) == 3
    assert entity_1 in snapshot.entities
    assert entity_2 in snapshot.entities
    assert entity_3 in snapshot.entities


def test_world_snapshot_complex_metadata() -> None:
    """Test snapshot with complex metadata."""
    metadata = {
        "seed": fake.random_int(),
        "player_count": fake.random_int(min=1, max=8),
        "game_mode": fake.word(),
        "difficulty": fake.word(),
        "nested": {
            "key": fake.word(),
            "value": fake.random_int(),
        },
    }

    snapshot = WorldSnapshot(
        tick=fake.random_int(),
        timestamp=fake.pyfloat(),
        entities={},
        metadata=metadata,
    )

    assert snapshot.metadata == metadata
    assert snapshot.metadata["seed"] == metadata["seed"]
    assert snapshot.metadata["nested"]["key"] == metadata["nested"]["key"]  # type: ignore[index]


def test_world_snapshot_zero_tick() -> None:
    """Test snapshot with zero tick."""
    snapshot = WorldSnapshot(
        tick=0,
        timestamp=fake.pyfloat(),
        entities={},
    )

    assert snapshot.tick == 0


def test_world_snapshot_large_tick() -> None:
    """Test snapshot with large tick number."""
    large_tick = 999999999

    snapshot = WorldSnapshot(
        tick=large_tick,
        timestamp=fake.pyfloat(),
        entities={},
    )

    assert snapshot.tick == large_tick
