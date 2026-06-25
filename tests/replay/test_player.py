"""Tests for GamePlayer."""

from typing import Any

import pytest
from faker import Faker

from yuna.exceptions import StateError, ValidationError
from yuna.replay.controls import PlaybackControls
from yuna.replay.incremental import (
    ComponentChanges,
    IncrementalRecording,
    SnapshotDelta,
)
from yuna.replay.player import GamePlayer, PlaybackState
from yuna.replay.storage import GameRecording
from yuna.state.snapshot import WorldSnapshot
from yuna.types.identifiers import EntityID

fake = Faker()


def create_test_recording(num_snapshots: int = 10) -> GameRecording:
    """Create a test recording with snapshots."""
    snapshots = [
        WorldSnapshot(tick=i, timestamp=float(i), entities={}, metadata={})
        for i in range(num_snapshots)
    ]
    return GameRecording(metadata={"test": True}, snapshots=snapshots)


def test_player_initial_state() -> None:
    """Test player starts in correct state."""
    player = GamePlayer()

    assert player.get_state() == PlaybackState.STOPPED
    assert player.get_current_tick() == 0


def test_player_with_custom_controls() -> None:
    """Test player with custom controls."""
    controls = PlaybackControls(speed=2.0, start_tick=5)
    player = GamePlayer(controls=controls)

    assert player.get_current_tick() == 5


def test_load_recording() -> None:
    """Test loading a recording."""
    player = GamePlayer()
    recording = create_test_recording()

    player.load_recording(recording=recording)

    assert player.get_state() == PlaybackState.STOPPED


def test_play_without_recording() -> None:
    """Test that play raises error without recording."""
    player = GamePlayer()

    with pytest.raises(StateError, match="No recording loaded"):
        player.play()


def test_play_starts_playback() -> None:
    """Test that play starts playback."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    player.play()

    assert player.get_state() == PlaybackState.PLAYING
    assert player.get_current_tick() == 0


def test_play_resets_to_start() -> None:
    """Test that play resets to start tick."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    player.seek(tick=5)
    player.play()

    assert player.get_current_tick() == 0


def test_play_from_specific_tick() -> None:
    """Test playing from specific tick."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    tick = fake.random_int(min=0, max=9)
    player.play_from(tick=tick)

    assert player.get_state() == PlaybackState.PLAYING
    assert player.get_current_tick() == tick


def test_play_from_without_recording() -> None:
    """Test that play_from raises error without recording."""
    player = GamePlayer()

    with pytest.raises(StateError, match="No recording loaded"):
        player.play_from(tick=0)


def test_play_from_negative_tick() -> None:
    """Test that play_from rejects negative tick."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    with pytest.raises(ValidationError, match="Tick must be non-negative"):
        player.play_from(tick=-1)


def test_play_from_out_of_range() -> None:
    """Test that play_from rejects out of range tick."""
    player = GamePlayer()
    recording = create_test_recording(num_snapshots=10)
    player.load_recording(recording=recording)

    with pytest.raises(ValidationError, match="Tick is out of range"):
        player.play_from(tick=10)


def test_pause_while_playing() -> None:
    """Test pausing playback."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    player.play()
    player.pause()

    assert player.get_state() == PlaybackState.PAUSED


def test_pause_while_not_playing() -> None:
    """Test that pause raises error when not playing."""
    player = GamePlayer()

    with pytest.raises(StateError, match="Not currently playing"):
        player.pause()


def test_resume_after_pause() -> None:
    """Test resuming after pause."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    player.play()
    player.pause()
    player.resume()

    assert player.get_state() == PlaybackState.PLAYING


def test_resume_while_not_paused() -> None:
    """Test that resume raises error when not paused."""
    player = GamePlayer()

    with pytest.raises(StateError, match="Not currently paused"):
        player.resume()


def test_seek_to_tick() -> None:
    """Test seeking to specific tick."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    tick = fake.random_int(min=0, max=9)
    player.seek(tick=tick)

    assert player.get_current_tick() == tick


def test_seek_without_recording() -> None:
    """Test that seek raises error without recording."""
    player = GamePlayer()

    with pytest.raises(StateError, match="No recording loaded"):
        player.seek(tick=0)


def test_seek_negative_tick() -> None:
    """Test that seek rejects negative tick."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    with pytest.raises(ValidationError, match="Tick must be non-negative"):
        player.seek(tick=-1)


def test_seek_out_of_range() -> None:
    """Test that seek rejects out of range tick."""
    player = GamePlayer()
    recording = create_test_recording(num_snapshots=10)
    player.load_recording(recording=recording)

    with pytest.raises(ValidationError, match="Tick is out of range"):
        player.seek(tick=10)


def test_get_snapshot() -> None:
    """Test getting snapshot at specific tick."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    tick = fake.random_int(min=0, max=9)
    snapshot = player.get_snapshot(tick=tick)

    assert snapshot.tick == tick


def test_get_snapshot_without_recording() -> None:
    """Test that get_snapshot raises error without recording."""
    player = GamePlayer()

    with pytest.raises(StateError, match="No recording loaded"):
        player.get_snapshot(tick=0)


def test_get_snapshot_out_of_range() -> None:
    """Test that get_snapshot rejects out of range tick."""
    player = GamePlayer()
    recording = create_test_recording(num_snapshots=10)
    player.load_recording(recording=recording)

    with pytest.raises(ValidationError, match="Tick is out of range"):
        player.get_snapshot(tick=10)


def test_advance_increments_tick() -> None:
    """Test that advance increments current tick."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    player.play()
    result = player.advance()

    assert result is True
    assert player.get_current_tick() == 1


def test_advance_without_playing() -> None:
    """Test that advance raises error when not playing."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    with pytest.raises(StateError, match="Not currently playing"):
        player.advance()


def test_advance_without_recording() -> None:
    """Test that advance raises error without recording."""
    player = GamePlayer()

    with pytest.raises(StateError, match="Not currently playing"):
        player.advance()


def test_advance_with_recording_cleared() -> None:
    """Test that advance raises error if recording is cleared while playing."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)
    player.play()

    player._recording = None

    with pytest.raises(StateError, match="No recording loaded"):
        player.advance()


def test_advance_stops_at_end() -> None:
    """Test that advance stops at end of recording."""
    player = GamePlayer()
    recording = create_test_recording(num_snapshots=3)
    player.load_recording(recording=recording)

    player.play()
    player.advance()
    player.advance()
    result = player.advance()

    assert result is False
    assert player.get_state() == PlaybackState.STOPPED


def test_advance_with_loop() -> None:
    """Test that advance loops when enabled."""
    controls = PlaybackControls(loop=True)
    player = GamePlayer(controls=controls)
    recording = create_test_recording(num_snapshots=3)
    player.load_recording(recording=recording)

    player.play()
    player.advance()
    player.advance()
    result = player.advance()

    assert result is True
    assert player.get_current_tick() == 0
    assert player.get_state() == PlaybackState.PLAYING


def test_advance_respects_end_tick() -> None:
    """Test that advance respects end_tick control."""
    controls = PlaybackControls(start_tick=0, end_tick=2)
    player = GamePlayer(controls=controls)
    recording = create_test_recording(num_snapshots=10)
    player.load_recording(recording=recording)

    player.play()
    player.advance()
    player.advance()
    result = player.advance()

    assert result is False
    assert player.get_state() == PlaybackState.STOPPED


def test_advance_with_loop_and_boundaries() -> None:
    """Test advance with loop and start/end boundaries."""
    controls = PlaybackControls(loop=True, start_tick=2, end_tick=4)
    player = GamePlayer(controls=controls)
    recording = create_test_recording(num_snapshots=10)
    player.load_recording(recording=recording)

    player.play()
    assert player.get_current_tick() == 2

    player.advance()
    assert player.get_current_tick() == 3

    player.advance()
    assert player.get_current_tick() == 4

    result = player.advance()
    assert result is True
    assert player.get_current_tick() == 2


def test_set_controls() -> None:
    """Test updating playback controls."""
    player = GamePlayer()
    new_controls = PlaybackControls(speed=2.0, loop=True)

    player.set_controls(controls=new_controls)

    recording = create_test_recording(num_snapshots=3)
    player.load_recording(recording=recording)
    player.play()
    player.advance()
    player.advance()
    result = player.advance()

    assert result is True
    assert player.get_current_tick() == 0


def test_playback_state_transitions() -> None:
    """Test all playback state transitions."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    assert player.get_state() == PlaybackState.STOPPED

    player.play()
    assert player.get_state() == PlaybackState.PLAYING

    player.pause()
    assert player.get_state() == PlaybackState.PAUSED

    player.resume()
    assert player.get_state() == PlaybackState.PLAYING


def test_seek_during_playback() -> None:
    """Test seeking while playing."""
    player = GamePlayer()
    recording = create_test_recording()
    player.load_recording(recording=recording)

    player.play()
    player.advance()
    player.seek(tick=5)

    assert player.get_current_tick() == 5
    assert player.get_state() == PlaybackState.PLAYING


def test_multiple_recordings() -> None:
    """Test loading different recordings."""
    player = GamePlayer()

    recording1 = create_test_recording(num_snapshots=5)
    player.load_recording(recording=recording1)
    player.play()
    assert len(recording1.snapshots) == 5

    recording2 = create_test_recording(num_snapshots=10)
    player.load_recording(recording=recording2)
    assert player.get_state() == PlaybackState.STOPPED
    assert player.get_current_tick() == 0


def test_player_incremental_get_snapshot() -> None:
    """Test get_snapshot with incremental recording."""
    entity_id = EntityID(fake.uuid4())
    entities0: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 0.0, "y": 0.0}}
    }

    snapshot0 = WorldSnapshot(tick=0, timestamp=0.0, entities=entities0, metadata={})

    delta1 = SnapshotDelta(
        tick=1,
        components=ComponentChanges(
            modified={entity_id: {"Position": {"x": 1.0, "y": 1.0}}},
        ),
    )

    incremental = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={0: snapshot0},
        deltas={1: delta1},
    )

    recording = GameRecording(metadata={}, incremental=incremental)
    player = GamePlayer()
    player.load_recording(recording=recording)

    result = player.get_snapshot(tick=1)

    assert result.tick == 1
    assert result.entities[entity_id] == {"Position": {"x": 1.0, "y": 1.0}}


def test_player_incremental_play_from() -> None:
    """Test play_from with incremental recording."""
    snapshot0 = WorldSnapshot(tick=0, timestamp=0.0, entities={}, metadata={})
    delta1 = SnapshotDelta(tick=1)

    incremental = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={0: snapshot0},
        deltas={1: delta1},
    )

    recording = GameRecording(metadata={}, incremental=incremental)
    player = GamePlayer()
    player.load_recording(recording=recording)

    player.play_from(tick=1)

    assert player.get_current_tick() == 1
    assert player.get_state() == PlaybackState.PLAYING


def test_player_incremental_play_from_unavailable_tick() -> None:
    """Test play_from raises error for unavailable tick in incremental recording."""
    snapshot0 = WorldSnapshot(tick=0, timestamp=0.0, entities={}, metadata={})

    incremental = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={0: snapshot0},
        deltas={},
    )

    recording = GameRecording(metadata={}, incremental=incremental)
    player = GamePlayer()
    player.load_recording(recording=recording)

    with pytest.raises(ValidationError, match="not available in incremental recording"):
        player.play_from(tick=1)


def test_player_incremental_seek() -> None:
    """Test seek with incremental recording."""
    snapshot0 = WorldSnapshot(tick=0, timestamp=0.0, entities={}, metadata={})
    delta1 = SnapshotDelta(tick=1)

    incremental = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={0: snapshot0},
        deltas={1: delta1},
    )

    recording = GameRecording(metadata={}, incremental=incremental)
    player = GamePlayer()
    player.load_recording(recording=recording)
    player.play()

    player.seek(tick=1)

    assert player.get_current_tick() == 1


def test_player_incremental_seek_unavailable_tick() -> None:
    """Test seek raises error for unavailable tick in incremental recording."""
    snapshot0 = WorldSnapshot(tick=0, timestamp=0.0, entities={}, metadata={})

    incremental = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={0: snapshot0},
        deltas={},
    )

    recording = GameRecording(metadata={}, incremental=incremental)
    player = GamePlayer()
    player.load_recording(recording=recording)
    player.play()

    with pytest.raises(ValidationError, match="not available in incremental recording"):
        player.seek(tick=1)


def test_player_incremental_get_snapshot_unavailable() -> None:
    """Test get_snapshot raises error for unavailable tick."""
    snapshot0 = WorldSnapshot(tick=0, timestamp=0.0, entities={}, metadata={})

    incremental = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={0: snapshot0},
        deltas={},
    )

    recording = GameRecording(metadata={}, incremental=incremental)
    player = GamePlayer()
    player.load_recording(recording=recording)

    with pytest.raises(ValidationError, match="not available in incremental recording"):
        player.get_snapshot(tick=1)


def test_player_incremental_advance() -> None:
    """Test advance with incremental recording."""
    snapshot0 = WorldSnapshot(tick=0, timestamp=0.0, entities={}, metadata={})
    delta1 = SnapshotDelta(tick=1)
    delta2 = SnapshotDelta(tick=2)

    incremental = IncrementalRecording(
        metadata={},
        keyframe_interval=60,
        keyframes={0: snapshot0},
        deltas={1: delta1, 2: delta2},
    )

    recording = GameRecording(metadata={}, incremental=incremental)
    player = GamePlayer()
    player.load_recording(recording=recording)
    player.play()

    result = player.advance()

    assert result is True
    assert player.get_current_tick() == 1
