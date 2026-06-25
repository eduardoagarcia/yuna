"""Tests for GameRecording storage."""

import gzip
import json
import tempfile
from pathlib import Path

from faker import Faker

from yuna.replay.incremental import (
    ComponentChanges,
    EntityChanges,
    IncrementalRecording,
    SnapshotDelta,
)
from yuna.replay.storage import GameRecording
from yuna.state.snapshot import WorldSnapshot
from yuna.types.identifiers import EntityID

fake = Faker()


def test_game_recording_creation() -> None:
    """Test creating a game recording."""
    metadata = {"seed": fake.random_int(), "players": fake.random_int(min=1, max=4)}
    snapshots = [
        WorldSnapshot(
            tick=i,
            timestamp=fake.pyfloat(min_value=0, max_value=1000),
            entities={},
            metadata={},
        )
        for i in range(3)
    ]

    recording = GameRecording(metadata=metadata, snapshots=snapshots)

    assert recording.metadata == metadata
    assert len(recording.snapshots) == 3
    assert recording.events == []
    assert recording.commands == []


def test_game_recording_defaults() -> None:
    """Test game recording with default values."""
    metadata = {"seed": fake.random_int()}
    recording = GameRecording(metadata=metadata)

    assert recording.metadata == metadata
    assert recording.snapshots == []
    assert recording.events == []
    assert recording.commands == []


def test_to_file_compressed() -> None:
    """Test saving recording to compressed file."""
    metadata = {"seed": fake.random_int()}
    snapshot = WorldSnapshot(tick=0, timestamp=1.0, entities={}, metadata={})
    recording = GameRecording(metadata=metadata, snapshots=[snapshot])

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "recording.gz"
        recording.to_file(path=path, compress=True)

        assert path.exists()
        with gzip.open(filename=path, mode="rt", encoding="utf-8") as f:
            data = json.load(fp=f)
            assert data["metadata"] == metadata


def test_to_file_uncompressed() -> None:
    """Test saving recording to uncompressed file."""
    metadata = {"seed": fake.random_int()}
    snapshot = WorldSnapshot(tick=0, timestamp=1.0, entities={}, metadata={})
    recording = GameRecording(metadata=metadata, snapshots=[snapshot])

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "recording.json"
        recording.to_file(path=path, compress=False)

        assert path.exists()
        data = json.loads(s=path.read_text())
        assert data["metadata"] == metadata


def test_to_file_creates_parent_directories() -> None:
    """Test that to_file creates parent directories if needed."""
    metadata = {"seed": fake.random_int()}
    recording = GameRecording(metadata=metadata)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nested" / "dir" / "recording.gz"
        recording.to_file(path=path)

        assert path.exists()
        assert path.parent.exists()


def test_from_file_compressed() -> None:
    """Test loading recording from compressed file."""
    metadata = {"seed": fake.random_int(), "mode": fake.word()}
    tick = fake.random_int(min=0, max=100)
    snapshot = WorldSnapshot(tick=tick, timestamp=1.0, entities={}, metadata={})
    original = GameRecording(metadata=metadata, snapshots=[snapshot])

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "recording.gz"
        original.to_file(path=path, compress=True)

        loaded = GameRecording.from_file(path=path, compressed=True)

        assert loaded.metadata == metadata
        assert len(loaded.snapshots) == 1
        assert loaded.snapshots[0].tick == tick


def test_from_file_uncompressed() -> None:
    """Test loading recording from uncompressed file."""
    metadata = {"seed": fake.random_int()}
    snapshot = WorldSnapshot(tick=0, timestamp=1.0, entities={}, metadata={})
    original = GameRecording(metadata=metadata, snapshots=[snapshot])

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "recording.json"
        original.to_file(path=path, compress=False)

        loaded = GameRecording.from_file(path=path, compressed=False)

        assert loaded.metadata == metadata
        assert len(loaded.snapshots) == 1


def test_round_trip_with_compression() -> None:
    """Test saving and loading recording maintains data."""
    metadata = {
        "seed": fake.random_int(),
        "players": fake.random_int(min=1, max=4),
        "mode": fake.word(),
    }
    snapshots = [
        WorldSnapshot(
            tick=i,
            timestamp=fake.pyfloat(min_value=0, max_value=1000),
            entities={EntityID(fake.uuid4()): {"Position": {"x": i, "y": i * 2}}},
            metadata={"tick_info": fake.word()},
        )
        for i in range(5)
    ]
    events = [{"type": fake.word(), "data": fake.word()} for _ in range(3)]
    commands = [{"name": fake.word(), "params": fake.word()} for _ in range(2)]

    original = GameRecording(
        metadata=metadata,
        snapshots=snapshots,
        events=events,
        commands=commands,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "recording.gz"
        original.to_file(path=path)
        loaded = GameRecording.from_file(path=path)

        assert loaded.metadata == original.metadata
        assert len(loaded.snapshots) == len(original.snapshots)
        assert loaded.events == original.events
        assert loaded.commands == original.commands

        for orig_snap, loaded_snap in zip(
            original.snapshots, loaded.snapshots, strict=False
        ):
            assert orig_snap.tick == loaded_snap.tick
            assert orig_snap.timestamp == loaded_snap.timestamp
            assert orig_snap.metadata == loaded_snap.metadata


def test_large_recording() -> None:
    """Test recording with many snapshots (1000+ ticks)."""
    metadata = {"seed": fake.random_int()}
    snapshots = [
        WorldSnapshot(tick=i, timestamp=float(i), entities={}, metadata={})
        for i in range(1000)
    ]

    recording = GameRecording(metadata=metadata, snapshots=snapshots)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "large.gz"
        recording.to_file(path=path)

        loaded = GameRecording.from_file(path=path)

        assert len(loaded.snapshots) == 1000
        assert loaded.snapshots[0].tick == 0
        assert loaded.snapshots[999].tick == 999


def test_empty_snapshots() -> None:
    """Test recording with no snapshots."""
    metadata = {"seed": fake.random_int()}
    recording = GameRecording(metadata=metadata, snapshots=[])

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "empty.gz"
        recording.to_file(path=path)

        loaded = GameRecording.from_file(path=path)

        assert loaded.metadata == metadata
        assert len(loaded.snapshots) == 0


def test_events_and_commands_optional() -> None:
    """Test that events and commands are optional in saved files."""
    metadata = {"seed": fake.random_int()}
    snapshot = WorldSnapshot(tick=0, timestamp=1.0, entities={}, metadata={})
    recording = GameRecording(metadata=metadata, snapshots=[snapshot])

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "recording.gz"
        recording.to_file(path=path)

        data_dict = recording._to_dict()
        del data_dict["events"]
        del data_dict["commands"]

        json_str = json.dumps(obj=data_dict)
        path_manual = Path(tmpdir) / "manual.gz"
        with gzip.open(filename=path_manual, mode="wt", encoding="utf-8") as f:
            f.write(json_str)

        loaded = GameRecording.from_file(path=path_manual)

        assert loaded.events == []
        assert loaded.commands == []


def test_snapshot_entities_preserved() -> None:
    """Test that entity data in snapshots is preserved."""
    entity_id = EntityID(fake.uuid4())
    entities_data = {entity_id: {"Position": {"x": 10, "y": 20}}}
    snapshot = WorldSnapshot(tick=0, timestamp=1.0, entities=entities_data, metadata={})
    recording = GameRecording(metadata={}, snapshots=[snapshot])

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "entities.gz"
        recording.to_file(path=path)

        loaded = GameRecording.from_file(path=path)

        assert entity_id in loaded.snapshots[0].entities
        assert loaded.snapshots[0].entities[entity_id] == entities_data[entity_id]


def test_compression_reduces_file_size() -> None:
    """Test that compression actually reduces file size."""
    metadata = {"seed": fake.random_int()}
    snapshots = [
        WorldSnapshot(
            tick=i,
            timestamp=float(i),
            entities={
                EntityID(fake.uuid4()): {"Position": {"x": j, "y": j}}
                for j in range(10)
            },
            metadata={},
        )
        for i in range(100)
    ]
    recording = GameRecording(metadata=metadata, snapshots=snapshots)

    with tempfile.TemporaryDirectory() as tmpdir:
        compressed_path = Path(tmpdir) / "compressed.gz"
        uncompressed_path = Path(tmpdir) / "uncompressed.json"

        recording.to_file(path=compressed_path, compress=True)
        recording.to_file(path=uncompressed_path, compress=False)

        compressed_size = compressed_path.stat().st_size
        uncompressed_size = uncompressed_path.stat().st_size

        assert compressed_size < uncompressed_size


def test_incremental_recording_serialization() -> None:
    """Test serialization of incremental recording."""
    entity_id = EntityID(fake.uuid4())
    keyframe = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={entity_id: {"Position": {"x": 0, "y": 0}}},
        metadata={},
    )
    delta = SnapshotDelta(
        tick=1,
        components=ComponentChanges(
            modified={entity_id: {"Position": {"x": 1, "y": 1}}},
        ),
    )

    incremental = IncrementalRecording(
        metadata={"seed": fake.random_int()},
        keyframe_interval=60,
        keyframes={0: keyframe},
        deltas={1: delta},
    )

    recording = GameRecording(
        metadata={"seed": fake.random_int()}, incremental=incremental
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "incremental.gz"
        recording.to_file(path=path)

        loaded = GameRecording.from_file(path=path)

        assert loaded.incremental is not None
        assert loaded.incremental.keyframe_interval == 60
        assert 0 in loaded.incremental.keyframes
        assert 1 in loaded.incremental.deltas


def test_incremental_recording_round_trip() -> None:
    """Test incremental recording survives round trip."""
    entity_id1 = EntityID(fake.uuid4())
    entity_id2 = EntityID(fake.uuid4())

    keyframe0 = WorldSnapshot(
        tick=0,
        timestamp=0.0,
        entities={entity_id1: {"Health": {"value": 100}}},
        metadata={},
    )
    keyframe60 = WorldSnapshot(
        tick=60,
        timestamp=6.0,
        entities={
            entity_id1: {"Health": {"value": 50}},
            entity_id2: {"Speed": {"value": 5}},
        },
        metadata={},
    )

    delta1 = SnapshotDelta(
        tick=1,
        components=ComponentChanges(
            modified={entity_id1: {"Health": {"value": 99}}},
        ),
    )
    delta2 = SnapshotDelta(
        tick=2,
        entities=EntityChanges(
            added={entity_id2: {"Speed": {"value": 10}}},
        ),
    )

    incremental = IncrementalRecording(
        metadata={"seed": fake.random_int()},
        keyframe_interval=60,
        keyframes={0: keyframe0, 60: keyframe60},
        deltas={1: delta1, 2: delta2},
    )

    recording = GameRecording(metadata={"game": "test"}, incremental=incremental)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "round_trip.gz"
        recording.to_file(path=path)

        loaded = GameRecording.from_file(path=path)

        assert loaded.incremental is not None
        assert len(loaded.incremental.keyframes) == 2
        assert len(loaded.incremental.deltas) == 2
        assert 0 in loaded.incremental.keyframes
        assert 60 in loaded.incremental.keyframes
        assert 1 in loaded.incremental.deltas
        assert 2 in loaded.incremental.deltas

        reconstructed = loaded.incremental.get_snapshot(tick=2)
        assert reconstructed is not None
        assert entity_id1 in reconstructed.entities
        assert entity_id2 in reconstructed.entities


def test_incremental_recording_serialization_complete() -> None:
    """Test that incremental recording serializes all data correctly."""
    entity_id = EntityID(fake.uuid4())

    full_snapshots = [
        WorldSnapshot(
            tick=i,
            timestamp=float(i) * 0.1,
            entities={entity_id: {"Position": {"x": i * 0.1, "y": i * 0.1}}},
            metadata={},
        )
        for i in range(100)
    ]

    keyframes = {i: full_snapshots[i] for i in range(0, 100, 10)}
    deltas = {}
    for i in range(1, 100):
        if i % 10 != 0:
            delta = SnapshotDelta(
                tick=i,
                components=ComponentChanges(
                    modified={entity_id: {"Position": {"x": i * 0.1, "y": i * 0.1}}},
                ),
            )
            deltas[i] = delta

    incremental = IncrementalRecording(
        metadata={"seed": fake.random_int()},
        keyframe_interval=10,
        keyframes=keyframes,
        deltas=deltas,
    )

    incremental_recording = GameRecording(
        metadata={"seed": fake.random_int()}, incremental=incremental
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "incremental.gz"
        incremental_recording.to_file(path=path)
        loaded = GameRecording.from_file(path=path)

        assert loaded.incremental is not None
        assert len(loaded.incremental.keyframes) == 10
        assert len(loaded.incremental.deltas) == 90


def test_game_recording_with_both_snapshots_and_incremental() -> None:
    """Test recording can have both snapshot list and incremental data."""
    snapshot = WorldSnapshot(tick=0, timestamp=0.0, entities={}, metadata={})
    keyframe = WorldSnapshot(tick=0, timestamp=0.0, entities={}, metadata={})

    incremental = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={0: keyframe},
        deltas={},
    )

    recording = GameRecording(
        metadata={"test": True},
        snapshots=[snapshot],
        incremental=incremental,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "both.gz"
        recording.to_file(path=path)

        loaded = GameRecording.from_file(path=path)

        assert len(loaded.snapshots) == 1
        assert loaded.incremental is not None


def test_incremental_none_serialization() -> None:
    """Test that incremental=None is handled correctly."""
    recording = GameRecording(metadata={"test": True}, incremental=None)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "no_incremental.gz"
        recording.to_file(path=path)

        loaded = GameRecording.from_file(path=path)

        assert loaded.incremental is None
