"""Tests for GameRecorder."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import msgpack
import pytest
from faker import Faker

from yuna.commands.command import Command
from yuna.commands.invoker import CommandInvoker
from yuna.commands.permissions import ActionPermission
from yuna.ecs.component import Component
from yuna.ecs.world import ECSWorld
from yuna.events.bus import EventBus
from yuna.events.event import Event
from yuna.exceptions import StateError
from yuna.replay.config import RecordingConfig
from yuna.replay.recorder import GameRecorder, RecordingMode
from yuna.state.manager import StateManager
from yuna.state.serializer import SnapshotSerializer

fake = Faker()


@dataclass(frozen=True)
class TestEvent(Event):
    """Test event for recording."""

    test_value: str


class TestResult(Enum):
    """Test result enum with value attribute."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class EnumFieldEvent(Event):
    """Test event carrying enum and set fields for serialization checks."""

    result: TestResult
    tags: frozenset[str]


class TestCommand(Command[ECSWorld, str]):
    """Test command for recording."""

    def __init__(self, test_param: str) -> None:
        self.test_param = test_param

    @property
    def priority(self) -> int:
        """Command priority."""
        return 100

    def permission(self, context: ECSWorld) -> ActionPermission:
        """Command permission."""
        return ActionPermission()

    def can_execute(self, context: ECSWorld) -> tuple[bool, str]:
        """Check if command can execute."""
        return True, ""

    def execute(self, context: ECSWorld) -> str:
        """Execute command."""
        return f"executed_{self.test_param}"

    def undo(self, context: ECSWorld, result: str) -> None:
        """Undo command."""
        pass

    def to_dict(self) -> dict[str, Any]:
        """Serialize command to dictionary for recording."""
        return {"test_param": self.test_param}


class TestEnumCommand(Command[ECSWorld, TestResult]):
    """Test command that returns enum result."""

    def __init__(self, test_param: str, success: bool = True) -> None:
        self.test_param = test_param
        self._success = success

    @property
    def priority(self) -> int:
        """Command priority."""
        return 100

    def permission(self, context: ECSWorld) -> ActionPermission:
        """Command permission."""
        return ActionPermission()

    def can_execute(self, context: ECSWorld) -> tuple[bool, str]:
        """Check if command can execute."""
        return True, ""

    def execute(self, context: ECSWorld) -> TestResult:
        """Execute command."""
        return TestResult.SUCCESS if self._success else TestResult.FAILURE

    def undo(self, context: ECSWorld, result: TestResult) -> None:
        """Undo command."""
        pass

    def to_dict(self) -> dict[str, Any]:
        """Serialize command to dictionary for recording."""
        return {"test_param": self.test_param}


class TestCommandWithoutToDict(Command[ECSWorld, str]):
    """Test command that does not override to_dict."""

    @property
    def priority(self) -> int:
        """Command priority."""
        return 100

    def permission(self, context: ECSWorld) -> ActionPermission:
        """Command permission."""
        return ActionPermission()

    def can_execute(self, context: ECSWorld) -> tuple[bool, str]:
        """Check if command can execute."""
        return True, ""

    def execute(self, context: ECSWorld) -> str:
        """Execute command."""
        return "executed"

    def undo(self, context: ECSWorld, result: str) -> None:
        """Undo command."""
        pass


def test_recorder_initial_state() -> None:
    """Test recorder starts in correct state."""
    recorder = GameRecorder()

    assert recorder.is_recording() is False


def test_start_recording() -> None:
    """Test starting a recording."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    metadata = {"seed": fake.random_int(), "players": fake.random_int(min=1, max=4)}
    recorder.start_recording(world=world, metadata=metadata)

    assert recorder.is_recording() is True


def test_start_recording_without_metadata() -> None:
    """Test starting recording without metadata."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    recorder.start_recording(world=world)

    assert recorder.is_recording() is True


def test_start_recording_captures_initial_snapshot() -> None:
    """Test that start_recording captures initial world state."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    recorder.start_recording(world=world)
    recording = recorder.stop_recording(world=world)

    assert len(recording.snapshots) == 1
    assert recording.snapshots[0].tick == 0


def test_start_recording_while_already_recording() -> None:
    """Test that starting recording twice raises error."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    recorder.start_recording(world=world)

    with pytest.raises(StateError, match="Recording already in progress"):
        recorder.start_recording(world=world)


def test_record_tick() -> None:
    """Test recording a single tick."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    recorder.start_recording(world=world)
    tick = fake.random_int(min=1, max=100)
    recorder.record_tick(world=world, tick=tick)
    recording = recorder.stop_recording(world=world)

    assert len(recording.snapshots) == 2
    assert recording.snapshots[1].tick == tick


def test_record_tick_without_recording() -> None:
    """Test that recording tick without starting raises error."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    with pytest.raises(StateError, match="Not currently recording"):
        recorder.record_tick(world=world, tick=1)


def test_record_multiple_ticks() -> None:
    """Test recording multiple ticks."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    recorder.start_recording(world=world)
    for i in range(1, 6):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert len(recording.snapshots) == 6
    assert recording.snapshots[0].tick == 0
    assert recording.snapshots[5].tick == 5


def test_stop_recording() -> None:
    """Test stopping a recording."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    recorder.start_recording(world=world)
    recording = recorder.stop_recording(world=world)

    assert recorder.is_recording() is False
    assert recording is not None


def test_stop_recording_without_recording() -> None:
    """Test that stopping without recording raises error."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    with pytest.raises(StateError, match="Not currently recording"):
        recorder.stop_recording(world=world)


def test_stop_recording_returns_metadata() -> None:
    """Test that stopped recording contains metadata."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    metadata = {"seed": fake.random_int(), "mode": fake.word()}
    recorder.start_recording(world=world, metadata=metadata)
    recording = recorder.stop_recording(world=world)

    assert recording.metadata == metadata


def test_stop_recording_returns_snapshots() -> None:
    """Test that stopped recording contains all snapshots."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    recorder.start_recording(world=world)
    for i in range(1, 11):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert len(recording.snapshots) == 11


def test_recording_frequency_every_tick() -> None:
    """Test recording with frequency=1 (every tick)."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(frequency=1)

    recorder.start_recording(world=world)
    for i in range(1, 6):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert len(recording.snapshots) == 6


def test_recording_frequency_every_other_tick() -> None:
    """Test recording with frequency=2 (every other tick)."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(frequency=2)

    recorder.start_recording(world=world)
    for i in range(1, 11):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert len(recording.snapshots) == 6


def test_recording_frequency_every_fifth_tick() -> None:
    """Test recording with frequency=5."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(frequency=5)

    recorder.start_recording(world=world)
    for i in range(1, 26):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert len(recording.snapshots) == 6


def test_multiple_recording_sessions() -> None:
    """Test that recorder can be reused for multiple sessions."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    recorder.start_recording(world=world, metadata={"session": 1})
    recorder.record_tick(world=world, tick=1)
    recording1 = recorder.stop_recording(world=world)

    recorder.start_recording(world=world, metadata={"session": 2})
    recorder.record_tick(world=world, tick=1)
    recorder.record_tick(world=world, tick=2)
    recording2 = recorder.stop_recording(world=world)

    assert len(recording1.snapshots) == 2
    assert len(recording2.snapshots) == 3
    assert recording1.metadata["session"] == 1
    assert recording2.metadata["session"] == 2


def test_recording_isolation() -> None:
    """Test that multiple recorders don't interfere with each other."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world1 = ECSWorld(state_manager=manager)
    world2 = ECSWorld(state_manager=manager)

    recorder1 = GameRecorder()
    recorder2 = GameRecorder()

    recorder1.start_recording(world=world1, metadata={"id": 1})
    recorder2.start_recording(world=world2, metadata={"id": 2})

    recorder1.record_tick(world=world1, tick=1)
    recorder2.record_tick(world=world2, tick=1)
    recorder2.record_tick(world=world2, tick=2)

    recording1 = recorder1.stop_recording(world=world1)
    recording2 = recorder2.stop_recording(world=world2)

    assert len(recording1.snapshots) == 2
    assert len(recording2.snapshots) == 3
    assert recording1.metadata["id"] == 1
    assert recording2.metadata["id"] == 2


def test_large_recording() -> None:
    """Test recording with 1000+ ticks."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    recorder.start_recording(world=world)
    for i in range(1, 1001):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert len(recording.snapshots) == 1001
    assert recording.snapshots[0].tick == 0
    assert recording.snapshots[1000].tick == 1000


def test_recorder_incremental_mode() -> None:
    """Test recorder with incremental mode."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(mode=RecordingMode.INCREMENTAL, keyframe_interval=60)

    recorder.start_recording(world=world)
    for i in range(1, 121):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert recording.incremental is not None
    assert len(recording.incremental.keyframes) == 3
    assert 0 in recording.incremental.keyframes
    assert 60 in recording.incremental.keyframes
    assert 120 in recording.incremental.keyframes


def test_recorder_incremental_mode_deltas() -> None:
    """Test recorder creates deltas in incremental mode."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(mode=RecordingMode.INCREMENTAL, keyframe_interval=10)

    recorder.start_recording(world=world)
    for i in range(1, 16):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert recording.incremental is not None
    assert len(recording.incremental.deltas) == 14
    assert 1 in recording.incremental.deltas
    assert 9 in recording.incremental.deltas
    assert 11 in recording.incremental.deltas
    assert 15 in recording.incremental.deltas


def test_recorder_keyframe_only_mode() -> None:
    """Test recorder with keyframe-only mode."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(mode=RecordingMode.KEYFRAME_ONLY, keyframe_interval=10)

    recorder.start_recording(world=world)
    for i in range(1, 26):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert len(recording.snapshots) == 3
    assert recording.snapshots[0].tick == 0
    assert recording.snapshots[1].tick == 10
    assert recording.snapshots[2].tick == 20


def test_recorder_full_mode_default() -> None:
    """Test recorder defaults to full mode."""
    recorder = GameRecorder()

    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    recorder.start_recording(world=world)
    for i in range(1, 6):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert len(recording.snapshots) == 6
    assert recording.incremental is None


def test_recorder_incremental_mode_with_frequency() -> None:
    """Test incremental mode with frequency setting."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(
        mode=RecordingMode.INCREMENTAL, keyframe_interval=10, frequency=2
    )

    recorder.start_recording(world=world)
    for i in range(1, 21):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert recording.incremental is not None
    keyframe_count = len(recording.incremental.keyframes)
    delta_count = len(recording.incremental.deltas)
    assert keyframe_count + delta_count == 11


def test_recorder_custom_keyframe_interval() -> None:
    """Test recorder with custom keyframe interval."""
    interval = fake.random_int(min=20, max=50)
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(mode=RecordingMode.INCREMENTAL, keyframe_interval=interval)

    recorder.start_recording(world=world)
    for i in range(1, interval + 1):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert recording.incremental is not None
    assert 0 in recording.incremental.keyframes
    assert interval in recording.incremental.keyframes


def test_recorder_delta_only_mode() -> None:
    """Test recorder with delta-only mode creates no keyframes after tick 0."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(mode=RecordingMode.DELTA_ONLY, keyframe_interval=10)

    recorder.start_recording(world=world)
    for i in range(1, 101):
        recorder.record_tick(world=world, tick=i)
    recording = recorder.stop_recording(world=world)

    assert recording.incremental is not None
    assert len(recording.incremental.keyframes) == 1
    assert 0 in recording.incremental.keyframes
    assert 10 not in recording.incremental.keyframes
    assert 20 not in recording.incremental.keyframes
    assert 50 not in recording.incremental.keyframes
    assert len(recording.incremental.deltas) == 100


def test_recorder_delta_only_vs_incremental() -> None:
    """Test delta-only produces different results than incremental mode."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world_incremental = ECSWorld(state_manager=manager)
    world_delta = ECSWorld(state_manager=manager)

    recorder_incremental = GameRecorder(
        mode=RecordingMode.INCREMENTAL, keyframe_interval=10
    )
    recorder_delta = GameRecorder(mode=RecordingMode.DELTA_ONLY, keyframe_interval=10)

    recorder_incremental.start_recording(world=world_incremental)
    recorder_delta.start_recording(world=world_delta)

    for i in range(1, 26):
        recorder_incremental.record_tick(world=world_incremental, tick=i)
        recorder_delta.record_tick(world=world_delta, tick=i)

    recording_incremental = recorder_incremental.stop_recording(world=world_incremental)
    recording_delta = recorder_delta.stop_recording(world=world_delta)

    assert recording_incremental.incremental is not None
    assert recording_delta.incremental is not None
    assert len(recording_incremental.incremental.keyframes) == 3
    assert len(recording_delta.incremental.keyframes) == 1
    assert 10 in recording_incremental.incremental.keyframes
    assert 20 in recording_incremental.incremental.keyframes
    assert 10 not in recording_delta.incremental.keyframes
    assert 20 not in recording_delta.incremental.keyframes


def test_recorder_captures_events() -> None:
    """Test that recorder captures events when event_bus is provided."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    event_bus = EventBus()
    recorder = GameRecorder(event_bus=event_bus)

    recorder.start_recording(world=world)

    event_value = fake.word()
    event_bus.emit(
        event=TestEvent(timestamp=fake.pyfloat(), tick=0, test_value=event_value)
    )
    event_bus.process_events()

    recorder.record_tick(world=world, tick=1)
    recording = recorder.stop_recording(world=world)

    assert len(recording.events) == 1
    assert recording.events[0]["test_value"] == event_value
    assert recording.events[0]["tick"] == 0


def test_recorder_normalizes_enum_and_set_event_fields() -> None:
    """Recorded events with enum/set fields stay msgpack-serializable."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    event_bus = EventBus()
    recorder = GameRecorder(event_bus=event_bus)

    recorder.start_recording(world=world)
    event_bus.emit(
        event=EnumFieldEvent(
            timestamp=fake.pyfloat(),
            tick=0,
            result=TestResult.SUCCESS,
            tags=frozenset({"alpha", "beta"}),
        )
    )
    event_bus.process_events()
    recorder.record_tick(world=world, tick=1)
    recording = recorder.stop_recording(world=world)

    recorded = recording.events[0]
    assert recorded["result"] == "success"
    assert sorted(recorded["tags"]) == ["alpha", "beta"]
    msgpack.packb(recorded, use_bin_type=True)


def test_recorder_captures_multiple_events() -> None:
    """Test that recorder captures multiple events across ticks."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    event_bus = EventBus()
    recorder = GameRecorder(event_bus=event_bus)

    recorder.start_recording(world=world)

    event_bus.emit(
        event=TestEvent(timestamp=fake.pyfloat(), tick=0, test_value="first")
    )
    event_bus.process_events()
    recorder.record_tick(world=world, tick=1)

    event_bus.emit(
        event=TestEvent(timestamp=fake.pyfloat(), tick=1, test_value="second")
    )
    event_bus.process_events()
    recorder.record_tick(world=world, tick=2)

    event_bus.emit(
        event=TestEvent(timestamp=fake.pyfloat(), tick=2, test_value="third")
    )
    event_bus.process_events()
    recorder.record_tick(world=world, tick=3)

    recording = recorder.stop_recording(world=world)

    assert len(recording.events) == 3
    assert recording.events[0]["test_value"] == "first"
    assert recording.events[0]["tick"] == 0
    assert recording.events[1]["test_value"] == "second"
    assert recording.events[1]["tick"] == 1
    assert recording.events[2]["test_value"] == "third"
    assert recording.events[2]["tick"] == 2


def test_recorder_without_event_bus() -> None:
    """Test that recorder works without event_bus (no events captured)."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    recorder.start_recording(world=world)
    recorder.record_tick(world=world, tick=1)
    recording = recorder.stop_recording(world=world)

    assert len(recording.events) == 0


def test_recorder_captures_commands() -> None:
    """Test that recorder captures commands when command_invoker is provided."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    command_invoker = CommandInvoker[ECSWorld, str]()
    recorder = GameRecorder(command_invoker=command_invoker)

    recorder.start_recording(world=world)

    test_param = fake.word()
    command = TestCommand(test_param=test_param)
    command_invoker.execute(command=command, context=world)

    recorder.record_tick(world=world, tick=1)
    recording = recorder.stop_recording(world=world)

    assert len(recording.commands) == 1
    assert recording.commands[0]["command_type"] == "TestCommand"
    assert recording.commands[0]["priority"] == 100
    assert recording.commands[0]["test_param"] == test_param
    assert recording.commands[0]["tick"] == 1


def test_recorder_captures_multiple_commands() -> None:
    """Test that recorder captures multiple commands across ticks."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    command_invoker = CommandInvoker[ECSWorld, str]()
    recorder = GameRecorder(command_invoker=command_invoker)

    recorder.start_recording(world=world)

    command_invoker.execute(command=TestCommand(test_param="first"), context=world)
    recorder.record_tick(world=world, tick=1)

    command_invoker.execute(command=TestCommand(test_param="second"), context=world)
    command_invoker.execute(command=TestCommand(test_param="third"), context=world)
    recorder.record_tick(world=world, tick=2)

    recording = recorder.stop_recording(world=world)

    assert len(recording.commands) == 3
    assert recording.commands[0]["test_param"] == "first"
    assert recording.commands[0]["tick"] == 1
    assert recording.commands[1]["test_param"] == "second"
    assert recording.commands[1]["tick"] == 2
    assert recording.commands[2]["test_param"] == "third"
    assert recording.commands[2]["tick"] == 2


def test_recorder_without_command_invoker() -> None:
    """Test that recorder works without command_invoker (no commands captured)."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder()

    recorder.start_recording(world=world)
    recorder.record_tick(world=world, tick=1)
    recording = recorder.stop_recording(world=world)

    assert len(recording.commands) == 0


def test_recorder_captures_events_and_commands() -> None:
    """Test that recorder captures both events and commands together."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    event_bus = EventBus()
    command_invoker = CommandInvoker[ECSWorld, str]()
    recorder = GameRecorder(event_bus=event_bus, command_invoker=command_invoker)

    recorder.start_recording(world=world)

    event_bus.emit(
        event=TestEvent(timestamp=fake.pyfloat(), tick=0, test_value="event_1")
    )
    event_bus.process_events()
    command_invoker.execute(command=TestCommand(test_param="command_1"), context=world)
    recorder.record_tick(world=world, tick=1)

    event_bus.emit(
        event=TestEvent(timestamp=fake.pyfloat(), tick=1, test_value="event_2")
    )
    event_bus.process_events()
    command_invoker.execute(command=TestCommand(test_param="command_2"), context=world)
    recorder.record_tick(world=world, tick=2)

    recording = recorder.stop_recording(world=world)

    assert len(recording.events) == 2
    assert len(recording.commands) == 2
    assert recording.events[0]["test_value"] == "event_1"
    assert recording.commands[0]["test_param"] == "command_1"
    assert recording.events[1]["test_value"] == "event_2"
    assert recording.commands[1]["test_param"] == "command_2"


def test_recorder_event_bus_unsubscribe_on_stop() -> None:
    """Test that recorder unsubscribes from event bus when stopped."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    event_bus = EventBus()
    recorder = GameRecorder(event_bus=event_bus)

    recorder.start_recording(world=world)
    event_bus.emit(
        event=TestEvent(timestamp=fake.pyfloat(), tick=0, test_value="during")
    )
    event_bus.process_events()
    recorder.record_tick(world=world, tick=1)
    recording = recorder.stop_recording(world=world)

    event_bus.emit(
        event=TestEvent(timestamp=fake.pyfloat(), tick=1, test_value="after")
    )
    event_bus.process_events()

    assert len(recording.events) == 1
    assert recording.events[0]["test_value"] == "during"


def test_recorder_multiple_sessions_clears_events_and_commands() -> None:
    """Test that multiple recording sessions don't leak events/commands."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    event_bus = EventBus()
    command_invoker = CommandInvoker[ECSWorld, str]()
    recorder = GameRecorder(event_bus=event_bus, command_invoker=command_invoker)

    recorder.start_recording(world=world)
    event_bus.emit(
        event=TestEvent(timestamp=fake.pyfloat(), tick=0, test_value="session1")
    )
    event_bus.process_events()
    command_invoker.execute(command=TestCommand(test_param="session1"), context=world)
    recorder.record_tick(world=world, tick=1)
    recording1 = recorder.stop_recording(world=world)

    recorder.start_recording(world=world)
    event_bus.emit(
        event=TestEvent(timestamp=fake.pyfloat(), tick=0, test_value="session2")
    )
    event_bus.process_events()
    command_invoker.execute(command=TestCommand(test_param="session2"), context=world)
    recorder.record_tick(world=world, tick=1)
    recording2 = recorder.stop_recording(world=world)

    assert len(recording1.events) == 1
    assert len(recording1.commands) == 1
    assert recording1.events[0]["test_value"] == "session1"
    assert recording1.commands[0]["test_param"] == "session1"

    assert len(recording2.events) == 1
    assert len(recording2.commands) == 1
    assert recording2.events[0]["test_value"] == "session2"
    assert recording2.commands[0]["test_param"] == "session2"


def test_recorder_no_commands_between_ticks() -> None:
    """Test recorder handles ticks with no new commands."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    command_invoker = CommandInvoker[ECSWorld, str]()
    recorder = GameRecorder(command_invoker=command_invoker)

    recorder.start_recording(world=world)

    command_invoker.execute(command=TestCommand(test_param="first"), context=world)
    recorder.record_tick(world=world, tick=1)

    recorder.record_tick(world=world, tick=2)
    recorder.record_tick(world=world, tick=3)

    command_invoker.execute(command=TestCommand(test_param="second"), context=world)
    recorder.record_tick(world=world, tick=4)

    recording = recorder.stop_recording(world=world)

    assert len(recording.commands) == 2
    assert recording.commands[0]["test_param"] == "first"
    assert recording.commands[0]["tick"] == 1
    assert recording.commands[1]["test_param"] == "second"
    assert recording.commands[1]["tick"] == 4


def test_recorder_captures_enum_result() -> None:
    """Test that recorder serializes enum result using .value attribute."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    command_invoker = CommandInvoker[ECSWorld, TestResult]()
    recorder = GameRecorder(command_invoker=command_invoker)

    recorder.start_recording(world=world)

    test_param = fake.word()
    command_invoker.execute(
        command=TestEnumCommand(test_param=test_param, success=True), context=world
    )
    recorder.record_tick(world=world, tick=1)

    recording = recorder.stop_recording(world=world)

    assert len(recording.commands) == 1
    assert recording.commands[0]["command_type"] == "TestEnumCommand"
    assert recording.commands[0]["test_param"] == test_param
    assert recording.commands[0]["result"] == "success"
    assert recording.commands[0]["tick"] == 1


def test_recorder_default_to_dict() -> None:
    """Test that recorder handles commands without custom to_dict implementation."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    command_invoker = CommandInvoker[ECSWorld, str]()
    recorder = GameRecorder(command_invoker=command_invoker)

    recorder.start_recording(world=world)

    command_invoker.execute(command=TestCommandWithoutToDict(), context=world)
    recorder.record_tick(world=world, tick=1)

    recording = recorder.stop_recording(world=world)

    assert len(recording.commands) == 1
    assert recording.commands[0]["command_type"] == "TestCommandWithoutToDict"
    assert recording.commands[0]["priority"] == 100
    assert recording.commands[0]["result"] == "executed"
    assert recording.commands[0]["tick"] == 1
    assert "test_param" not in recording.commands[0]


def test_recorder_does_not_record_event_when_not_recording() -> None:
    """Test that recorder does not record events when not actively recording."""
    event_bus = EventBus()
    recorder = GameRecorder(event_bus=event_bus, config=RecordingConfig())

    assert not recorder.is_recording()

    test_event = TestEvent(timestamp=0.0, tick=0, test_value=fake.word())
    event_bus.emit(event=test_event)
    event_bus.process_events()

    assert len(recorder._events) == 0


def test_recorder_filters_excluded_event_types() -> None:
    """Test that recorder filters out excluded event types."""

    @dataclass(frozen=True)
    class ExcludedEvent(Event):
        value: str

    @dataclass(frozen=True)
    class IncludedEvent(Event):
        value: str

    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    event_bus = EventBus()

    config = RecordingConfig(excluded_event_types={"ExcludedEvent"})
    recorder = GameRecorder(event_bus=event_bus, config=config)

    recorder.start_recording(world=world)

    excluded_value = fake.word()
    excluded_event = ExcludedEvent(timestamp=0.0, tick=0, value=excluded_value)
    event_bus.emit(event=excluded_event)

    included_value = fake.word()
    included_event = IncludedEvent(timestamp=0.0, tick=0, value=included_value)
    event_bus.emit(event=included_event)

    event_bus.process_events()

    recording = recorder.stop_recording(world=world)

    assert len(recording.events) == 1
    assert recording.events[0]["value"] == included_value


def test_recorder_does_not_record_commands_when_disabled() -> None:
    """Test that recorder tracks command count but does not record when disabled."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    command_invoker: CommandInvoker = CommandInvoker()

    config = RecordingConfig(record_commands=False)
    recorder = GameRecorder(command_invoker=command_invoker, config=config)

    recorder.start_recording(world=world)

    command_invoker.execute(command=TestCommand(test_param=fake.word()), context=world)
    recorder.record_tick(world=world, tick=1)

    recording = recorder.stop_recording(world=world)

    assert len(recording.commands) == 0


def test_update_frame_components_merges_into_current_frame() -> None:
    """update_frame_components records configured components into the frame."""

    @dataclass
    class FrameStat(Component):
        value: int

    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=FrameStat)
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(
        mode=RecordingMode.DELTA_ONLY,
        config=RecordingConfig(frame_update_components={"FrameStat"}),
    )

    entity = world.create_entity()
    world.add_component(entity_id=entity, component=FrameStat(value=1))
    recorder.start_recording(world=world)
    recorder.record_tick(world=world, tick=1)
    new_value = fake.random_int(min=2, max=100)
    world.add_component(entity_id=entity, component=FrameStat(value=new_value))

    recorder.update_frame_components(world=world)

    assert recorder._incremental_recorder is not None
    frame = recorder._incremental_recorder._pending_frame
    assert frame is not None
    assert frame.entities[entity]["FrameStat"]["value"] == new_value


def test_update_frame_components_without_recording() -> None:
    """update_frame_components raises when not recording."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(config=RecordingConfig(frame_update_components={"X"}))

    with pytest.raises(StateError, match="Not currently recording"):
        recorder.update_frame_components(world=world)


def test_update_frame_components_noop_without_incremental_recorder() -> None:
    """update_frame_components is a no-op for non-incremental recording modes."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)
    recorder = GameRecorder(
        mode=RecordingMode.FULL,
        config=RecordingConfig(frame_update_components={"X"}),
    )

    recorder.start_recording(world=world)
    recorder.record_tick(world=world, tick=1)
    recorder.update_frame_components(world=world)

    assert recorder._incremental_recorder is None
