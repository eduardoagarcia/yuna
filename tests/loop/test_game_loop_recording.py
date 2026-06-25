"""Tests for GameLoop recording integration."""

from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.exceptions import StateError
from yuna.loop.game_loop import GameLoop
from yuna.loop.scheduler import SystemScheduler
from yuna.loop.time import TimeManager
from yuna.replay.recorder import GameRecorder
from yuna.state.manager import StateManager
from yuna.state.serializer import SnapshotSerializer

fake = Faker()


@dataclass(frozen=True)
class Position(Component):
    """Test position component."""

    x: int
    y: int


class TestSystem(System):
    """Test system for recording tests."""

    def __init__(self) -> None:
        self.update_count = 0

    def update(self, world: ECSWorld, delta_time: float) -> None:
        """Update system."""
        self.update_count += 1

    @property
    def priority(self) -> int:
        """System priority."""
        return 100


def create_game_loop_with_recorder() -> tuple[GameLoop, GameRecorder]:
    """Create game loop with recorder configured."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    time_manager = TimeManager(fixed_delta=1.0)
    scheduler = SystemScheduler()
    recorder = GameRecorder()

    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        recorder=recorder,
    )

    return game_loop, recorder


def test_game_loop_initial_state() -> None:
    """Test game loop starts with recording disabled."""
    game_loop, _ = create_game_loop_with_recorder()

    assert game_loop.is_recording() is False
    assert game_loop.current_tick == 0


def test_enable_recording() -> None:
    """Test enabling recording."""
    game_loop, _ = create_game_loop_with_recorder()

    metadata = {"seed": fake.random_int()}
    game_loop.enable_recording(metadata=metadata)

    assert game_loop.is_recording() is True


def test_enable_recording_without_recorder() -> None:
    """Test that enabling recording without recorder raises error."""
    world = ECSWorld()
    time_manager = TimeManager(fixed_delta=1.0)
    scheduler = SystemScheduler()

    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )

    with pytest.raises(StateError, match="No recorder configured for game loop"):
        game_loop.enable_recording()


def test_enable_recording_multiple_times() -> None:
    """Test enabling recording multiple times is safe."""
    game_loop, recorder = create_game_loop_with_recorder()

    game_loop.enable_recording(metadata={"attempt": 1})
    game_loop.enable_recording(metadata={"attempt": 2})

    assert game_loop.is_recording() is True
    assert recorder.is_recording() is True


def test_disable_recording() -> None:
    """Test disabling recording."""
    game_loop, _ = create_game_loop_with_recorder()

    game_loop.enable_recording()
    game_loop.disable_recording()

    assert game_loop.is_recording() is False


def test_disable_recording_when_not_enabled() -> None:
    """Test disabling recording when not enabled is safe."""
    game_loop, _ = create_game_loop_with_recorder()

    game_loop.disable_recording()

    assert game_loop.is_recording() is False


def test_recording_captures_ticks() -> None:
    """Test that recording captures tick snapshots."""
    game_loop, _ = create_game_loop_with_recorder()

    game_loop.enable_recording()
    game_loop.tick()
    game_loop.tick()
    game_loop.tick()

    recording = game_loop.get_recording()

    assert len(recording.snapshots) == 4


def test_recording_doesnt_affect_tick_execution() -> None:
    """Test that recording doesn't affect normal tick execution."""
    serializer = SnapshotSerializer()
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    time_manager = TimeManager(fixed_delta=1.0)
    scheduler = SystemScheduler()
    test_system = TestSystem()
    scheduler.register(system=test_system)
    recorder = GameRecorder()

    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        recorder=recorder,
    )

    game_loop.enable_recording()
    game_loop.tick()
    game_loop.tick()

    assert test_system.update_count == 2


def test_tick_counter_increments() -> None:
    """Test that tick counter increments correctly."""
    game_loop, _ = create_game_loop_with_recorder()

    assert game_loop.current_tick == 0

    game_loop.tick()
    assert game_loop.current_tick == 1

    game_loop.tick()
    assert game_loop.current_tick == 2


def test_tick_counter_resets_on_enable() -> None:
    """Test that tick counter resets when recording is enabled."""
    game_loop, _ = create_game_loop_with_recorder()

    game_loop.tick()
    game_loop.tick()
    assert game_loop.current_tick == 2

    game_loop.enable_recording()
    assert game_loop.current_tick == 0


def test_get_recording() -> None:
    """Test getting recording."""
    game_loop, _ = create_game_loop_with_recorder()

    metadata = {"seed": fake.random_int()}
    game_loop.enable_recording(metadata=metadata)
    game_loop.tick()

    recording = game_loop.get_recording()

    assert recording.metadata == metadata
    assert len(recording.snapshots) == 2
    assert game_loop.is_recording() is False


def test_get_recording_without_recorder() -> None:
    """Test that get_recording without recorder raises error."""
    world = ECSWorld()
    time_manager = TimeManager(fixed_delta=1.0)
    scheduler = SystemScheduler()

    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )

    with pytest.raises(StateError, match="No recorder configured for game loop"):
        game_loop.get_recording()


def test_get_recording_when_not_recording() -> None:
    """Test that get_recording when not recording raises error."""
    game_loop, _ = create_game_loop_with_recorder()

    with pytest.raises(StateError, match="Recording is not currently enabled"):
        game_loop.get_recording()


def test_recording_with_update() -> None:
    """Test recording with update() method."""
    game_loop, _ = create_game_loop_with_recorder()

    game_loop.enable_recording()
    ticks = game_loop.update(elapsed=3.5)

    assert ticks == 3
    assert game_loop.current_tick == 3

    recording = game_loop.get_recording()
    assert len(recording.snapshots) == 4


def test_multiple_recording_sessions() -> None:
    """Test multiple recording sessions."""
    game_loop, _ = create_game_loop_with_recorder()

    game_loop.enable_recording(metadata={"session": 1})
    game_loop.tick()
    recording1 = game_loop.get_recording()

    game_loop.enable_recording(metadata={"session": 2})
    game_loop.tick()
    game_loop.tick()
    recording2 = game_loop.get_recording()

    assert len(recording1.snapshots) == 2
    assert len(recording2.snapshots) == 3
    assert recording1.metadata["session"] == 1
    assert recording2.metadata["session"] == 2


def test_recording_without_metadata() -> None:
    """Test recording without metadata."""
    game_loop, _ = create_game_loop_with_recorder()

    game_loop.enable_recording()
    game_loop.tick()
    recording = game_loop.get_recording()

    assert recording.metadata == {}


def test_disable_then_enable_recording() -> None:
    """Test disabling then re-enabling recording."""
    game_loop, _ = create_game_loop_with_recorder()

    game_loop.enable_recording()
    game_loop.tick()
    game_loop.disable_recording()

    game_loop.tick()
    game_loop.tick()

    assert game_loop.is_recording() is False


def test_recording_preserves_world_state() -> None:
    """Test that recording preserves world state."""
    serializer = SnapshotSerializer()
    serializer.register_component_type(component_type=Position)
    manager = StateManager(serializer=serializer)
    world = ECSWorld(state_manager=manager)

    time_manager = TimeManager(fixed_delta=1.0)
    scheduler = SystemScheduler()
    recorder = GameRecorder()

    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        recorder=recorder,
    )

    entity = world.create_entity()
    world.add_component(entity_id=entity, component=Position(x=10, y=20))

    game_loop.enable_recording()
    game_loop.tick()

    world.remove_component(entity_id=entity, component_type=Position)
    world.add_component(entity_id=entity, component=Position(x=30, y=40))

    game_loop.tick()

    recording = game_loop.get_recording()

    assert len(recording.snapshots) == 3
    first_snapshot = recording.snapshots[1]
    assert first_snapshot.entities[entity]["Position"]["x"] == 10
    assert first_snapshot.entities[entity]["Position"]["y"] == 20
