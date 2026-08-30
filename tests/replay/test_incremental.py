"""Tests for incremental delta recording."""

from dataclasses import dataclass
from typing import Any

import pytest
from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.world import ECSWorld
from yuna.exceptions import StateError
from yuna.replay.config import RecordingConfig
from yuna.replay.incremental import (
    ComponentChanges,
    EntityChanges,
    IncrementalRecorder,
    IncrementalRecording,
    SnapshotDelta,
    apply_delta,
    compute_component_level_delta,
    compute_delta,
)
from yuna.state.manager import StateManager
from yuna.state.raw_snapshot import RawSnapshot
from yuna.state.serializer import SnapshotSerializer
from yuna.state.snapshot import WorldSnapshot
from yuna.types.identifiers import EntityID

fake = Faker()


def test_snapshot_delta_dataclass() -> None:
    """Test SnapshotDelta dataclass."""
    tick = fake.random_int(min=1, max=1000)
    entity_id = EntityID(fake.uuid4())
    removed_id = EntityID(fake.uuid4())
    modified_id = EntityID(fake.uuid4())
    delta = SnapshotDelta(
        tick=tick,
        entities=EntityChanges(
            added={entity_id: {"Position": {"x": 1.0, "y": 2.0}}},
            removed={removed_id},
        ),
        components=ComponentChanges(
            modified={modified_id: {"Health": {"value": 50}}},
        ),
    )

    assert delta.tick == tick
    assert entity_id in delta.entities.added
    assert len(delta.entities.removed) == 1
    assert len(delta.components.modified) == 1


def test_snapshot_delta_empty() -> None:
    """Test empty SnapshotDelta."""
    tick = fake.random_int(min=1, max=1000)
    delta = SnapshotDelta(tick=tick)

    assert delta.tick == tick
    assert len(delta.entities.added) == 0
    assert len(delta.entities.removed) == 0
    assert len(delta.components.modified) == 0


def test_compute_delta_no_changes() -> None:
    """Test compute_delta with identical snapshots."""
    entities: dict[EntityID, dict[str, Any]] = {
        EntityID(fake.uuid4()): {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities, metadata={})

    delta = compute_delta(previous=snapshot1, current=snapshot2)

    assert delta.tick == 1
    assert len(delta.entities.added) == 0
    assert len(delta.entities.removed) == 0
    assert len(delta.components.modified) == 0


def test_compute_delta_added_entity() -> None:
    """Test compute_delta with added entity."""
    entity_id1 = EntityID(fake.uuid4())
    entity_id2 = EntityID(fake.uuid4())
    entities1: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}}
    }
    entities2: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}},
        entity_id2: {"Health": {"value": 100}},
    }
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities1, metadata={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities2, metadata={})

    delta = compute_delta(previous=snapshot1, current=snapshot2)

    assert delta.tick == 1
    assert len(delta.entities.added) == 1
    assert entity_id2 in delta.entities.added
    assert delta.entities.added[entity_id2] == {"Health": {"value": 100}}
    assert len(delta.entities.removed) == 0
    assert len(delta.components.modified) == 0


def test_compute_delta_removed_entity() -> None:
    """Test compute_delta with removed entity."""
    entity_id1 = EntityID(fake.uuid4())
    entity_id2 = EntityID(fake.uuid4())
    entities1: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}},
        entity_id2: {"Health": {"value": 100}},
    }
    entities2: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities1, metadata={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities2, metadata={})

    delta = compute_delta(previous=snapshot1, current=snapshot2)

    assert delta.tick == 1
    assert len(delta.entities.added) == 0
    assert len(delta.entities.removed) == 1
    assert entity_id2 in delta.entities.removed
    assert len(delta.components.modified) == 0


def test_compute_delta_modified_components() -> None:
    """Test compute_delta with modified components."""
    entity_id = EntityID(fake.uuid4())
    entities1: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 1.0, "y": 2.0}}
    }
    entities2: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 3.0, "y": 4.0}}
    }
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities1, metadata={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities2, metadata={})

    delta = compute_delta(previous=snapshot1, current=snapshot2)

    assert delta.tick == 1
    assert len(delta.entities.added) == 0
    assert len(delta.entities.removed) == 0
    assert len(delta.components.modified) == 1
    assert entity_id in delta.components.modified
    assert delta.components.modified[entity_id] == {"Position": {"x": 3.0, "y": 4.0}}


def test_compute_delta_multiple_changes() -> None:
    """Test compute_delta with multiple types of changes."""
    entity_id1 = EntityID(fake.uuid4())
    entity_id2 = EntityID(fake.uuid4())
    entity_id3 = EntityID(fake.uuid4())
    entity_id4 = EntityID(fake.uuid4())

    entities1: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}},
        entity_id2: {"Health": {"value": 100}},
        entity_id3: {"Energy": {"value": 50}},
    }
    entities2: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 5.0, "y": 6.0}},
        entity_id3: {"Energy": {"value": 50}},
        entity_id4: {"Speed": {"value": 10}},
    }

    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities1, metadata={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities2, metadata={})

    delta = compute_delta(previous=snapshot1, current=snapshot2)

    assert delta.tick == 1
    assert len(delta.entities.added) == 1
    assert entity_id4 in delta.entities.added
    assert len(delta.entities.removed) == 1
    assert entity_id2 in delta.entities.removed
    assert len(delta.components.modified) == 1
    assert entity_id1 in delta.components.modified


def test_apply_delta_add_entity() -> None:
    """Test apply_delta with added entity."""
    entity_id1 = EntityID(fake.uuid4())
    entity_id2 = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    delta = SnapshotDelta(
        tick=1,
        entities=EntityChanges(added={entity_id2: {"Health": {"value": 100}}}),
    )

    result = apply_delta(snapshot=snapshot, delta=delta)

    assert result.tick == 1
    assert len(result.entities) == 2
    assert entity_id1 in result.entities
    assert entity_id2 in result.entities
    assert result.entities[entity_id2] == {"Health": {"value": 100}}


def test_apply_delta_remove_entity() -> None:
    """Test apply_delta with removed entity."""
    entity_id1 = EntityID(fake.uuid4())
    entity_id2 = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}},
        entity_id2: {"Health": {"value": 100}},
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    delta = SnapshotDelta(tick=1, entities=EntityChanges(removed={entity_id2}))

    result = apply_delta(snapshot=snapshot, delta=delta)

    assert result.tick == 1
    assert len(result.entities) == 1
    assert entity_id1 in result.entities
    assert entity_id2 not in result.entities


def test_apply_delta_modify_components() -> None:
    """Test apply_delta with modified components."""
    entity_id = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    delta = SnapshotDelta(
        tick=1,
        components=ComponentChanges(
            modified={entity_id: {"Position": {"x": 3.0, "y": 4.0}}},
        ),
    )

    result = apply_delta(snapshot=snapshot, delta=delta)

    assert result.tick == 1
    assert result.entities[entity_id] == {"Position": {"x": 3.0, "y": 4.0}}


def test_apply_delta_remove_nonexistent_entity() -> None:
    """Test apply_delta handles removing nonexistent entity gracefully."""
    entity_id1 = EntityID(fake.uuid4())
    entity_id2 = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    delta = SnapshotDelta(tick=1, entities=EntityChanges(removed={entity_id2}))

    result = apply_delta(snapshot=snapshot, delta=delta)

    assert result.tick == 1
    assert len(result.entities) == 1
    assert entity_id1 in result.entities


def test_apply_delta_multiple_operations() -> None:
    """Test apply_delta with multiple operations."""
    entity_id1 = EntityID(fake.uuid4())
    entity_id2 = EntityID(fake.uuid4())
    entity_id3 = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}},
        entity_id2: {"Health": {"value": 100}},
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    delta = SnapshotDelta(
        tick=1,
        entities=EntityChanges(
            added={entity_id3: {"Speed": {"value": 5}}},
            removed={entity_id2},
        ),
        components=ComponentChanges(
            modified={entity_id1: {"Position": {"x": 10.0, "y": 20.0}}},
        ),
    )

    result = apply_delta(snapshot=snapshot, delta=delta)

    assert result.tick == 1
    assert len(result.entities) == 2
    assert entity_id1 in result.entities
    assert entity_id2 not in result.entities
    assert entity_id3 in result.entities
    assert result.entities[entity_id1] == {"Position": {"x": 10.0, "y": 20.0}}
    assert result.entities[entity_id3] == {"Speed": {"value": 5}}


def test_incremental_recorder_initial_state() -> None:
    """Test IncrementalRecorder starts in correct state."""
    recorder = IncrementalRecorder()

    assert recorder.is_recording() is False


def test_incremental_recorder_custom_keyframe_interval() -> None:
    """Test IncrementalRecorder with custom keyframe interval."""
    interval = fake.random_int(min=10, max=100)
    recorder = IncrementalRecorder(keyframe_interval=interval)

    assert recorder._keyframe_interval == interval


def test_incremental_recorder_start_recording() -> None:
    """Test starting incremental recording."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder()

    metadata = {"seed": fake.random_int()}
    recorder.start_recording(world=world, metadata=metadata)

    assert recorder.is_recording() is True


def test_incremental_recorder_start_recording_captures_keyframe() -> None:
    """Test that start_recording captures initial keyframe."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder()

    recorder.start_recording(world=world)
    recording = recorder.stop_recording(world=world)

    assert 0 in recording.keyframes
    assert recording.keyframes[0].tick == 0


def test_incremental_recorder_start_recording_twice() -> None:
    """Test that starting recording twice raises error."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder()

    recorder.start_recording(world=world)

    with pytest.raises(StateError, match="Recording already in progress"):
        recorder.start_recording(world=world)


def test_incremental_recorder_record_tick_delta() -> None:
    """Test recording non-keyframe tick creates delta."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder(keyframe_interval=60)

    recorder.start_recording(world=world)
    recorder.record_tick(world=world, tick=1)
    recording = recorder.stop_recording(world=world)

    assert 1 in recording.deltas
    assert recording.deltas[1].tick == 1


def test_incremental_recorder_record_tick_keyframe() -> None:
    """Test recording keyframe tick creates keyframe."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder(keyframe_interval=60)

    recorder.start_recording(world=world)
    recorder.record_tick(world=world, tick=60)
    recording = recorder.stop_recording(world=world)

    assert 60 in recording.keyframes
    assert recording.keyframes[60].tick == 60


def test_incremental_recorder_record_tick_without_recording() -> None:
    """Test that recording tick without starting raises error."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder()

    with pytest.raises(StateError, match="Not currently recording"):
        recorder.record_tick(world=world, tick=1)


def test_incremental_recorder_record_multiple_ticks() -> None:
    """Test recording multiple ticks with keyframes and deltas."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder(keyframe_interval=10)

    recorder.start_recording(world=world)
    for i in range(1, 26):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert 0 in recording.keyframes
    assert 10 in recording.keyframes
    assert 20 in recording.keyframes
    assert 1 in recording.deltas
    assert 5 in recording.deltas
    assert 15 in recording.deltas
    assert 25 in recording.deltas


def test_incremental_recorder_stop_recording() -> None:
    """Test stopping incremental recording."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder()

    recorder.start_recording(world=world)
    recording = recorder.stop_recording(world=world)

    assert recorder.is_recording() is False
    assert recording is not None


def test_incremental_recorder_stop_recording_without_recording() -> None:
    """Test that stopping without recording raises error."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder()

    with pytest.raises(StateError, match="Not currently recording"):
        recorder.stop_recording(world=world)


def test_incremental_recorder_stop_recording_returns_metadata() -> None:
    """Test that stopped recording contains metadata."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder()

    metadata = {"seed": fake.random_int(), "mode": fake.word()}
    recorder.start_recording(world=world, metadata=metadata)
    recording = recorder.stop_recording(world=world)

    assert recording.metadata == metadata


def test_incremental_recording_get_snapshot_keyframe() -> None:
    """Test get_snapshot returns keyframe directly."""
    keyframe_interval = fake.random_int(min=10, max=100)
    entities: dict[EntityID, dict[str, Any]] = {
        EntityID(fake.uuid4()): {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    recording = IncrementalRecording(
        metadata={},
        keyframe_interval=keyframe_interval,
        keyframes={0: snapshot},
        deltas={},
    )

    result = recording.get_snapshot(tick=0)

    assert result == snapshot


def test_incremental_recording_get_snapshot_reconstruct() -> None:
    """Test get_snapshot reconstructs from keyframe + delta."""
    entity_id = EntityID(fake.uuid4())
    entities1: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 1.0, "y": 2.0}}
    }
    entities2: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 3.0, "y": 4.0}}
    }
    snapshot0 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities1, metadata={})
    snapshot1 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities2, metadata={})

    delta = compute_delta(previous=snapshot0, current=snapshot1)

    recording = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={0: snapshot0},
        deltas={1: delta},
    )

    result = recording.get_snapshot(tick=1)

    assert result is not None
    assert result.tick == 1
    assert result.entities[entity_id] == {"Position": {"x": 3.0, "y": 4.0}}


def test_incremental_recording_get_snapshot_multiple_deltas() -> None:
    """Test get_snapshot reconstructs from multiple deltas."""
    entity_id = EntityID(fake.uuid4())
    entities0: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 0.0, "y": 0.0}}
    }
    entities1: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 1.0, "y": 1.0}}
    }
    entities2: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 2.0, "y": 2.0}}
    }
    entities3: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 3.0, "y": 3.0}}
    }

    snapshot0 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities0, metadata={})
    snapshot1 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities1, metadata={})
    snapshot2 = WorldSnapshot(tick=2, timestamp=0.2, entities=entities2, metadata={})
    snapshot3 = WorldSnapshot(tick=3, timestamp=0.3, entities=entities3, metadata={})

    delta1 = compute_delta(previous=snapshot0, current=snapshot1)
    delta2 = compute_delta(previous=snapshot1, current=snapshot2)
    delta3 = compute_delta(previous=snapshot2, current=snapshot3)

    recording = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={0: snapshot0},
        deltas={1: delta1, 2: delta2, 3: delta3},
    )

    result = recording.get_snapshot(tick=3)

    assert result is not None
    assert result.tick == 3
    assert result.entities[entity_id] == {"Position": {"x": 3.0, "y": 3.0}}


def test_incremental_recording_get_snapshot_missing_keyframe() -> None:
    """Test get_snapshot returns None when keyframe missing."""
    recording = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={},
        deltas={},
    )

    result = recording.get_snapshot(tick=1)

    assert result is None


def test_incremental_recording_get_snapshot_missing_delta() -> None:
    """Test get_snapshot returns None when delta missing."""
    entities: dict[EntityID, dict[str, Any]] = {
        EntityID(fake.uuid4()): {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    recording = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={0: snapshot},
        deltas={},
    )

    result = recording.get_snapshot(tick=1)

    assert result is None


def test_incremental_recording_get_keyframe_ticks() -> None:
    """Test get_keyframe_ticks returns sorted list."""
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities={}, metadata={})
    snapshot2 = WorldSnapshot(tick=60, timestamp=6.0, entities={}, metadata={})
    snapshot3 = WorldSnapshot(tick=120, timestamp=12.0, entities={}, metadata={})

    recording = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={120: snapshot3, 0: snapshot1, 60: snapshot2},
        deltas={},
    )

    ticks = recording.get_keyframe_ticks()

    assert ticks == [0, 60, 120]


def test_incremental_recording_get_delta_ticks() -> None:
    """Test get_delta_ticks returns sorted list."""
    delta1 = SnapshotDelta(tick=1)
    delta2 = SnapshotDelta(tick=5)
    delta3 = SnapshotDelta(tick=10)

    recording = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={},
        deltas={10: delta3, 1: delta1, 5: delta2},
    )

    ticks = recording.get_delta_ticks()

    assert ticks == [1, 5, 10]


def test_incremental_recording_empty() -> None:
    """Test empty incremental recording."""
    recording = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={},
        deltas={},
    )

    assert recording.get_keyframe_ticks() == []
    assert recording.get_delta_ticks() == []


def test_incremental_recorder_large_recording() -> None:
    """Test incremental recording with 1000+ ticks."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder(keyframe_interval=60)

    recorder.start_recording(world=world)
    for i in range(1, 1001):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    keyframe_count = len(recording.keyframes)
    delta_count = len(recording.deltas)

    assert keyframe_count == 17
    assert delta_count == 984
    assert keyframe_count + delta_count == 1001


def test_round_trip_reconstruction() -> None:
    """Test full round trip: record → store → reconstruct."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder(keyframe_interval=10)

    recorder.start_recording(world=world)
    for i in range(1, 26):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    for tick in range(26):
        snapshot = recording.get_snapshot(tick=tick)
        assert snapshot is not None
        assert snapshot.tick == tick


def test_incremental_recorder_delta_only_no_keyframes_after_initial() -> None:
    """Test delta-only mode never creates keyframes after tick 0."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder(keyframe_interval=10, delta_only=True)

    recorder.start_recording(world=world)
    for i in range(1, 101):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert 0 in recording.keyframes
    assert 10 not in recording.keyframes
    assert 20 not in recording.keyframes
    assert 50 not in recording.keyframes
    assert 100 not in recording.keyframes
    assert len(recording.keyframes) == 1
    assert len(recording.deltas) == 100


def test_incremental_recorder_delta_only_vs_standard() -> None:
    """Test delta-only mode produces different results than standard mode."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world_standard = ECSWorld(state_manager=manager)
    world_delta = ECSWorld(state_manager=manager)

    recorder_standard = IncrementalRecorder(keyframe_interval=10, delta_only=False)
    recorder_delta = IncrementalRecorder(keyframe_interval=10, delta_only=True)

    recorder_standard.start_recording(world=world_standard)
    recorder_delta.start_recording(world=world_delta)

    for i in range(1, 26):
        recorder_standard.record_tick(world=world_standard, tick=i)
        recorder_delta.record_tick(world=world_delta, tick=i)

    recording_standard = recorder_standard.stop_recording(world=world_standard)
    recording_delta = recorder_delta.stop_recording(world=world_delta)

    assert len(recording_standard.keyframes) == 3
    assert len(recording_delta.keyframes) == 1
    assert 10 in recording_standard.keyframes
    assert 20 in recording_standard.keyframes
    assert 10 not in recording_delta.keyframes
    assert 20 not in recording_delta.keyframes


def test_incremental_recorder_delta_only_initial_keyframe() -> None:
    """Test delta-only mode creates initial keyframe at tick 0."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder(keyframe_interval=60, delta_only=True)

    recorder.start_recording(world=world)
    recording = recorder.stop_recording(world=world)

    assert 0 in recording.keyframes
    assert recording.keyframes[0].tick == 0
    assert len(recording.keyframes) == 1


def test_compute_delta_component_added_to_existing_entity() -> None:
    """Test compute_delta when component is added to existing entity."""
    entity_id = EntityID(fake.uuid4())
    entities1: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 1.0, "y": 2.0}}
    }
    entities2: dict[EntityID, dict[str, Any]] = {
        entity_id: {
            "Position": {"x": 1.0, "y": 2.0},
            "Health": {"value": 100},
        }
    }
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities1, metadata={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities2, metadata={})

    delta = compute_delta(previous=snapshot1, current=snapshot2)

    assert delta.tick == 1
    assert len(delta.entities.added) == 0
    assert len(delta.entities.removed) == 0
    assert len(delta.components.modified) == 1
    assert entity_id in delta.components.modified
    assert "Health" in delta.components.modified[entity_id]
    assert delta.components.modified[entity_id]["Health"] == {"value": 100}


def test_compute_delta_component_removed_from_entity() -> None:
    """Test compute_delta when component is removed from entity."""
    entity_id = EntityID(fake.uuid4())
    entities1: dict[EntityID, dict[str, Any]] = {
        entity_id: {
            "Position": {"x": 1.0, "y": 2.0},
            "Health": {"value": 100},
        }
    }
    entities2: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities1, metadata={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities2, metadata={})

    delta = compute_delta(previous=snapshot1, current=snapshot2)

    assert delta.tick == 1
    assert len(delta.entities.added) == 0
    assert len(delta.entities.removed) == 0
    assert entity_id in delta.components.modified
    assert "Health" not in delta.components.modified[entity_id]
    assert "Position" in delta.components.modified[entity_id]


def test_apply_delta_modify_nonexistent_entity() -> None:
    """Test apply_delta when modifying entity that doesn't exist in snapshot."""
    entity_id1 = EntityID(fake.uuid4())
    entity_id2 = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id1: {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities=entities, metadata={})

    delta = SnapshotDelta(
        tick=1,
        components=ComponentChanges(modified={entity_id2: {"Health": {"value": 50}}}),
    )

    result = apply_delta(snapshot=snapshot, delta=delta)

    assert result.tick == 1
    assert entity_id2 in result.entities
    assert result.entities[entity_id2] == {"Health": {"value": 50}}
    assert entity_id1 in result.entities


def test_incremental_recorder_with_component_level_deltas() -> None:
    """Test recorder using component-level delta computation."""

    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    config = RecordingConfig()
    recorder = IncrementalRecorder(
        keyframe_interval=10,
        component_level_deltas=True,
        config=config,
    )

    recorder.start_recording(world=world)

    for tick in range(5):
        recorder.record_tick(world=world, tick=tick)

    recording = recorder.stop_recording(world=world)

    assert len(recording.deltas) > 0


def test_incremental_recorder_with_component_filtering() -> None:
    """Test recorder filtering components based on config."""

    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    config = RecordingConfig(
        included_components={"Position", "Health"},
        skip_empty_marker_components=True,
    )
    recorder = IncrementalRecorder(keyframe_interval=10, config=config)

    recorder.start_recording(world=world)

    for tick in range(3):
        recorder.record_tick(world=world, tick=tick)

    recording = recorder.stop_recording(world=world)

    assert len(recording.keyframes) >= 1


def test_incremental_recorder_skip_empty_marker_components() -> None:
    """Test recorder skips empty marker components when configured."""

    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    config = RecordingConfig(skip_empty_marker_components=True)
    recorder = IncrementalRecorder(keyframe_interval=10, config=config)

    recorder.start_recording(world=world)
    recorder.record_tick(world=world, tick=0)
    recording = recorder.stop_recording(world=world)

    assert len(recording.keyframes) >= 1


def test_compute_component_level_delta_modified_component() -> None:
    """Test component-level delta only includes changed components."""
    entity_id = EntityID(fake.uuid4())
    entities1: dict[EntityID, dict[str, Any]] = {
        entity_id: {
            "Position": {"x": 1.0, "y": 2.0},
            "Health": {"value": 100},
            "Energy": {"value": 50},
        }
    }
    entities2: dict[EntityID, dict[str, Any]] = {
        entity_id: {
            "Position": {"x": 1.0, "y": 2.0},
            "Health": {"value": 75},
            "Energy": {"value": 50},
        }
    }
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities1, metadata={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities2, metadata={})

    delta = compute_component_level_delta(previous=snapshot1, current=snapshot2)

    assert delta.tick == 1
    assert len(delta.entities.added) == 0
    assert len(delta.entities.removed) == 0
    assert len(delta.components.modified) == 1
    assert entity_id in delta.components.modified
    assert "Health" in delta.components.modified[entity_id]
    assert "Position" not in delta.components.modified[entity_id]
    assert "Energy" not in delta.components.modified[entity_id]
    assert delta.components.modified[entity_id]["Health"]["value"] == 75


def test_compute_component_level_delta_component_removed() -> None:
    """Test component-level delta when component is removed."""
    entity_id = EntityID(fake.uuid4())
    entities1: dict[EntityID, dict[str, Any]] = {
        entity_id: {
            "Position": {"x": 1.0, "y": 2.0},
            "Health": {"value": 100},
        }
    }
    entities2: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 1.0, "y": 2.0}}
    }
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities1, metadata={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities2, metadata={})

    delta = compute_component_level_delta(previous=snapshot1, current=snapshot2)

    assert delta.tick == 1
    assert len(delta.entities.added) == 0
    assert len(delta.entities.removed) == 0
    assert len(delta.components.modified) == 0
    assert len(delta.components.removed) == 1
    assert entity_id in delta.components.removed
    assert "Health" in delta.components.removed[entity_id]


def test_compute_component_level_delta_component_added() -> None:
    """Test component-level delta when component is added."""
    entity_id = EntityID(fake.uuid4())
    entities1: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 1.0, "y": 2.0}}
    }
    entities2: dict[EntityID, dict[str, Any]] = {
        entity_id: {
            "Position": {"x": 1.0, "y": 2.0},
            "Health": {"value": 100},
        }
    }
    snapshot1 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities1, metadata={})
    snapshot2 = WorldSnapshot(tick=1, timestamp=0.1, entities=entities2, metadata={})

    delta = compute_component_level_delta(previous=snapshot1, current=snapshot2)

    assert delta.tick == 1
    assert len(delta.entities.added) == 0
    assert len(delta.entities.removed) == 0
    assert len(delta.components.added) == 1
    assert entity_id in delta.components.added
    assert "Health" in delta.components.added[entity_id]
    assert "Position" not in delta.components.added[entity_id]
    assert delta.components.added[entity_id]["Health"]["value"] == 100


def test_incremental_recorder_without_component_level_deltas() -> None:
    """Test recorder using regular delta computation (not component-level)."""

    @dataclass
    class TestPosition(Component):
        x: float
        y: float

    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=TestPosition)
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    recorder = IncrementalRecorder(
        keyframe_interval=10,
        component_level_deltas=False,
    )

    recorder.start_recording(world=world)

    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=TestPosition(x=1.0, y=2.0))

    recorder.record_tick(world=world, tick=1)

    world.get_component(entity_id=entity_id, component_type=TestPosition)
    world.add_component(entity_id=entity_id, component=TestPosition(x=3.0, y=4.0))

    recorder.record_tick(world=world, tick=2)

    recording = recorder.stop_recording(world=world)

    assert len(recording.deltas) > 0
    assert 2 in recording.deltas


def test_incremental_recorder_filters_excluded_components() -> None:
    """Test recorder filters out excluded components."""

    @dataclass
    class IncludedComponent(Component):
        value: int

    @dataclass
    class ExcludedComponent(Component):
        data: str

    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=IncludedComponent)
    serializer.register_component_type(component_type=ExcludedComponent)
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    config = RecordingConfig(
        excluded_components={"ExcludedComponent"},
        skip_empty_marker_components=True,
    )
    recorder = IncrementalRecorder(keyframe_interval=10, config=config)

    recorder.start_recording(world=world)

    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id,
        component=IncludedComponent(value=42),
    )
    world.add_component(
        entity_id=entity_id,
        component=ExcludedComponent(data="excluded"),
    )

    recorder.record_tick(world=world, tick=1)
    recording = recorder.stop_recording(world=world)

    assert 0 in recording.keyframes
    snapshot = recording.get_snapshot(tick=1)
    assert snapshot is not None
    assert entity_id in snapshot.entities
    assert "IncludedComponent" in snapshot.entities[entity_id]
    assert "ExcludedComponent" not in snapshot.entities[entity_id]


def test_incremental_recorder_skips_empty_components() -> None:
    """Test recorder skips empty marker components."""

    @dataclass
    class MarkerComponent(Component):
        pass

    @dataclass
    class DataComponent(Component):
        value: int

    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=MarkerComponent)
    serializer.register_component_type(component_type=DataComponent)
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    config = RecordingConfig(skip_empty_marker_components=True)
    recorder = IncrementalRecorder(keyframe_interval=10, config=config)

    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=MarkerComponent())
    world.add_component(entity_id=entity_id, component=DataComponent(value=100))

    raw_snapshot = RawSnapshot(
        tick=1,
        timestamp=0.0,
        entities={
            entity_id: {
                "MarkerComponent": {},
                "DataComponent": DataComponent(value=100),
            }
        },
        metadata={},
    )

    filtered = recorder._filter_snapshot(raw_snapshot=raw_snapshot)

    assert entity_id in filtered.entities
    assert "MarkerComponent" not in filtered.entities[entity_id]
    assert "DataComponent" in filtered.entities[entity_id]


def test_filter_snapshot_with_component_exclusion() -> None:
    """Test filtering snapshot with component exclusion list."""

    @dataclass
    class ExcludedComponent(Component):
        pass

    @dataclass
    class IncludedComponent(Component):
        value: int

    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=ExcludedComponent)
    serializer.register_component_type(component_type=IncludedComponent)
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    config = RecordingConfig(excluded_components={"ExcludedComponent"})
    recorder = IncrementalRecorder(keyframe_interval=10, config=config)

    entity_id = world.create_entity()

    raw_snapshot = RawSnapshot(
        tick=1,
        timestamp=0.0,
        entities={
            entity_id: {
                "ExcludedComponent": ExcludedComponent(),
                "IncludedComponent": IncludedComponent(value=42),
            }
        },
        metadata={},
    )

    filtered = recorder._filter_snapshot(raw_snapshot=raw_snapshot)

    assert entity_id in filtered.entities
    assert "ExcludedComponent" not in filtered.entities[entity_id]
    assert "IncludedComponent" in filtered.entities[entity_id]


def test_update_frame_components_merges_into_last_frame() -> None:
    """update_frame_components re-captures named components into the latest frame."""

    @dataclass
    class FramePosition(Component):
        x: float
        y: float

    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder()

    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=FramePosition(x=1.0, y=1.0))
    recorder.start_recording(world=world)
    recorder.record_tick(world=world, tick=1)

    updated = fake.pyfloat()
    world.add_component(entity_id=entity_id, component=FramePosition(x=updated, y=2.0))
    recorder.update_frame_components(world=world, component_names={"FramePosition"})

    frame = recorder._pending_frame
    assert frame is not None
    assert frame.entities[entity_id]["FramePosition"]["x"] == updated


def test_update_frame_components_requires_recording() -> None:
    """update_frame_components raises when not recording."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder()

    with pytest.raises(StateError, match="Not currently recording"):
        recorder.update_frame_components(world=world, component_names={"Anything"})


def test_update_frame_components_empty_set_is_noop() -> None:
    """update_frame_components does nothing when no components are named."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder()

    recorder.start_recording(world=world)
    recorder.record_tick(world=world, tick=1)
    frame = recorder._pending_frame
    assert frame is not None
    before = dict(frame.entities)

    recorder.update_frame_components(world=world, component_names=set())

    assert frame.entities == before


def test_update_frame_components_without_pending_frame_is_noop() -> None:
    """update_frame_components is a no-op when no frame is pending."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder()

    recorder.start_recording(world=world)
    recorder._pending_frame = None

    recorder.update_frame_components(world=world, component_names={"Anything"})

    assert recorder._pending_frame is None


def test_tick_zero_recorded_twice_overwrites_initial_keyframe() -> None:
    """A second tick-0 record replaces keyframe 0, matching legacy batching."""

    @dataclass
    class CounterComponent(Component):
        value: int

    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder(delta_only=True)

    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=CounterComponent(value=1))
    recorder.start_recording(world=world)

    world.add_component(entity_id=entity_id, component=CounterComponent(value=2))
    recorder.record_tick(world=world, tick=0)

    recording = recorder.stop_recording(world=world)

    assert recording.keyframes[0].entities[entity_id]["CounterComponent"] == {
        "value": 2
    }
    assert recording.deltas == {}


def test_streaming_deltas_match_per_tick_changes() -> None:
    """Deltas accumulate per tick and raw frames are not retained."""

    @dataclass
    class StreamComponent(Component):
        value: int

    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder(delta_only=True)

    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=StreamComponent(value=0))
    recorder.start_recording(world=world)

    for tick in range(1, 4):
        world.add_component(entity_id=entity_id, component=StreamComponent(value=tick))
        recorder.record_tick(world=world, tick=tick)
        if tick > 1:
            assert tick - 1 in recorder._deltas

    recording = recorder.stop_recording(world=world)

    assert recorder._pending_frame is None
    for tick in range(1, 4):
        assert recording.deltas[tick].components.modified[entity_id] == {
            "StreamComponent": {"value": tick}
        }


def test_streaming_keyframes_in_incremental_mode() -> None:
    """Interval keyframes finalize unfiltered while delta ticks accumulate."""

    @dataclass
    class IntervalComponent(Component):
        value: int

    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = IncrementalRecorder(keyframe_interval=2, delta_only=False)

    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=IntervalComponent(value=0))
    recorder.start_recording(world=world)

    for tick in range(1, 5):
        world.add_component(
            entity_id=entity_id, component=IntervalComponent(value=tick)
        )
        recorder.record_tick(world=world, tick=tick)

    recording = recorder.stop_recording(world=world)

    assert sorted(recording.keyframes.keys()) == [0, 2, 4]
    assert sorted(recording.deltas.keys()) == [1, 3]
    assert recording.keyframes[4].entities[entity_id]["IntervalComponent"] == {
        "value": 4
    }
