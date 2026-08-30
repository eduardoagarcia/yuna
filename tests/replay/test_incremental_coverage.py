"""Additional tests for incremental.py coverage edge cases."""

from typing import Any

from faker import Faker

from yuna.replay.incremental import (
    ComponentChanges,
    IncrementalRecorder,
    SnapshotDelta,
    apply_delta,
    compute_component_level_delta,
)
from yuna.state.snapshot import WorldSnapshot
from yuna.types.identifiers import EntityID

fake = Faker()


def test_apply_delta_add_component_to_nonexistent_entity() -> None:
    """Test apply_delta when adding component to entity not in snapshot."""
    entity_id1 = EntityID(fake.uuid4())
    entity_id2 = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    delta = SnapshotDelta(
        tick=1,
        components=ComponentChanges(added={entity_id2: {"Health": {"value": 100}}}),
    )

    result = apply_delta(snapshot=snapshot, delta=delta)

    assert result.tick == 1
    assert entity_id2 in result.entities
    assert result.entities[entity_id2] == {"Health": {"value": 100}}
    assert entity_id1 in result.entities


def test_apply_delta_add_component_to_existing_entity() -> None:
    """Test apply_delta when adding component to entity already in snapshot."""
    entity_id = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    delta = SnapshotDelta(
        tick=1,
        components=ComponentChanges(added={entity_id: {"Health": {"value": 100}}}),
    )

    result = apply_delta(snapshot=snapshot, delta=delta)

    assert result.tick == 1
    assert entity_id in result.entities
    assert result.entities[entity_id] == {
        "Position": {"x": 1.0, "y": 2.0},
        "Health": {"value": 100},
    }


def test_apply_delta_remove_component_from_entity() -> None:
    """Test apply_delta when removing component from entity."""
    entity_id = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id: {
            "Position": {"x": 1.0, "y": 2.0},
            "Health": {"value": 100},
            "Energy": {"value": 50},
        }
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    delta = SnapshotDelta(
        tick=1,
        components=ComponentChanges(removed={entity_id: {"Health", "Energy"}}),
    )

    result = apply_delta(snapshot=snapshot, delta=delta)

    assert result.tick == 1
    assert entity_id in result.entities
    assert result.entities[entity_id] == {"Position": {"x": 1.0, "y": 2.0}}
    assert "Health" not in result.entities[entity_id]
    assert "Energy" not in result.entities[entity_id]


def test_apply_delta_remove_component_from_nonexistent_entity() -> None:
    """Test apply_delta when removing component from nonexistent entity."""
    entity_id1 = EntityID(fake.uuid4())
    entity_id2 = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    delta = SnapshotDelta(
        tick=1,
        components=ComponentChanges(removed={entity_id2: {"Health"}}),
    )

    result = apply_delta(snapshot=snapshot, delta=delta)

    assert result.tick == 1
    assert entity_id1 in result.entities
    assert entity_id2 not in result.entities


def test_component_level_delta_skips_identical_component_objects() -> None:
    """A component object shared by both snapshots produces no change."""
    entity_id = EntityID(fake.uuid4())
    shared_component = {"x": 1.0, "y": 2.0}
    previous = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={entity_id: {"Position": shared_component}},
        metadata={},
    )
    current = WorldSnapshot(
        tick=1,
        timestamp=1.0,
        entities={entity_id: {"Position": shared_component}},
        metadata={},
    )

    delta = compute_component_level_delta(previous=previous, current=current)

    assert delta.components.added == {}
    assert delta.components.modified == {}
    assert delta.components.removed == {}


def test_finalize_pending_frame_without_pending_frame_is_noop() -> None:
    """Finalizing with no pending frame leaves the recorder untouched."""
    recorder = IncrementalRecorder()

    recorder._finalize_pending_frame(world=None)

    assert recorder._pending_frame is None
    assert recorder._keyframes == {}
    assert recorder._deltas == {}
