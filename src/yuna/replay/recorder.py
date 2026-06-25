"""Game session recorder."""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from yuna.exceptions import StateError
from yuna.replay.config import RecordingConfig
from yuna.replay.incremental import IncrementalRecorder
from yuna.replay.storage import GameRecording
from yuna.state.serializer import SnapshotSerializer
from yuna.state.snapshot import WorldSnapshot

if TYPE_CHECKING:
    from yuna.commands.invoker import CommandInvoker
    from yuna.ecs.world import ECSWorld
    from yuna.events.bus import EventBus
    from yuna.events.event import Event


class RecordingMode(Enum):
    """Recording mode enumeration."""

    FULL = auto()
    INCREMENTAL = auto()
    KEYFRAME_ONLY = auto()
    DELTA_ONLY = auto()


class GameRecorder:
    """Records game sessions for replay.

    Responsibilities:
    - Track recording state (recording/stopped)
    - Capture world snapshots at each tick
    - Capture events emitted during gameplay
    - Store metadata about the game session
    - Support configurable recording frequency and mode
    - Support incremental recording with keyframes + deltas
    - Support delta-only recording for efficient static world storage
    - Return complete recording when stopped

    Recording modes:
    - FULL: Every tick stores complete world state
    - INCREMENTAL: Keyframes at intervals + deltas between
    - KEYFRAME_ONLY: Sparse keyframes only
    - DELTA_ONLY: Initial snapshot + deltas only (no repeated keyframes)

    Event Recording:
    - If event_bus provided, subscribes to all events during recording
    - Events stored with tick number for replay synchronization
    - Events serialized as dictionaries for JSON compatibility

    Usage:
        recorder = GameRecorder(
            frequency=1,
            mode=RecordingMode.INCREMENTAL,
            event_bus=event_bus,
        )
        recorder.start_recording(world=world, metadata={"seed": 42})
        for tick in range(100):
            recorder.record_tick(world=world, tick=tick)
        recording = recorder.stop_recording()
    """

    def __init__(
        self,
        frequency: int = 1,
        mode: RecordingMode = RecordingMode.FULL,
        keyframe_interval: int = 60,
        event_bus: EventBus | None = None,
        command_invoker: CommandInvoker[Any, Any] | None = None,
        config: RecordingConfig | None = None,
    ) -> None:
        """Initialize recorder.

        Args:
            frequency: Record every Nth tick (1 = every tick, 2 = every other tick)
            mode: Recording mode (FULL, INCREMENTAL, KEYFRAME_ONLY)
            keyframe_interval: Ticks between keyframes for incremental mode
            event_bus: Optional event bus for recording events
            command_invoker: Optional command invoker for recording commands
            config: Optional recording configuration for filtering
        """
        self._frequency = frequency
        self._mode = mode
        self._keyframe_interval = keyframe_interval
        self._event_bus = event_bus
        self._command_invoker = command_invoker
        self._config = config or RecordingConfig()
        self._recording = False
        self._snapshots: list[WorldSnapshot] = []
        self._metadata: dict[str, Any] = {}
        self._tick_count = 0
        self._incremental_recorder: IncrementalRecorder | None = None
        self._events: list[dict[str, Any]] = []
        self._commands: list[dict[str, Any]] = []
        self._current_tick = 0
        self._last_command_count = 0

    def start_recording(
        self,
        world: ECSWorld,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Begin recording a game session.

        Args:
            world: World to record
            metadata: Game metadata (seed, players, etc.)

        Raises:
            StateError: If already recording
        """
        if self._recording:
            raise StateError(
                operation="start_recording",
                state="recording",
                reason="Recording already in progress",
            )

        self._recording = True
        self._snapshots = []
        self._events = []
        self._commands = []
        self._metadata = metadata or {}
        self._tick_count = 0
        self._current_tick = 0

        if self._command_invoker is not None:
            self._last_command_count = self._command_invoker.get_history_count()
        else:
            self._last_command_count = 0

        if self._event_bus is not None:
            self._event_bus.subscribe_all(handler=self._on_event)

        if self._mode in {RecordingMode.INCREMENTAL, RecordingMode.DELTA_ONLY}:
            self._incremental_recorder = IncrementalRecorder(
                keyframe_interval=self._keyframe_interval,
                delta_only=self._mode == RecordingMode.DELTA_ONLY,
                config=self._config,
            )
            self._incremental_recorder.start_recording(
                world=world, metadata=self._metadata
            )
        else:
            snapshot = world.create_snapshot(tick=0, metadata=self._metadata)
            self._snapshots.append(snapshot)

    def record_tick(self, world: ECSWorld, tick: int) -> None:
        """Record a single tick.

        Args:
            world: World to record
            tick: Current tick number

        Raises:
            StateError: If not recording
        """
        if not self._recording:
            raise StateError(
                operation="record_tick",
                state="not_recording",
                reason="Not currently recording",
            )

        self._current_tick = tick
        self._tick_count += 1

        if self._command_invoker is not None:
            self._capture_commands_from_invoker()

        if self._tick_count % self._frequency == 0:
            if self._mode in {RecordingMode.INCREMENTAL, RecordingMode.DELTA_ONLY}:
                if self._incremental_recorder is not None:
                    self._incremental_recorder.record_tick(world=world, tick=tick)
            elif self._mode == RecordingMode.KEYFRAME_ONLY:
                if tick % self._keyframe_interval == 0:
                    snapshot = world.create_snapshot(tick=tick, metadata=self._metadata)
                    self._snapshots.append(snapshot)
            else:
                snapshot = world.create_snapshot(tick=tick, metadata=self._metadata)
                self._snapshots.append(snapshot)

    def update_frame_components(self, world: ECSWorld) -> None:
        """Merge configured components into the most recent recorded frame.

        Records components produced after a frame's primary snapshot into that
        same frame, for the component types listed in
        RecordingConfig.frame_update_components.

        Args:
            world: World to capture from

        Raises:
            StateError: If not recording
        """
        if not self._recording:
            raise StateError(
                operation="update_frame_components",
                state="not_recording",
                reason="Not currently recording",
            )

        if self._incremental_recorder is not None:
            self._incremental_recorder.update_frame_components(
                world=world,
                component_names=self._config.frame_update_components,
            )

    def stop_recording(self, world: ECSWorld) -> GameRecording:
        """Stop recording and return the recording.

        Incremental modes compute deltas during record_tick, so stopping
        only finalizes the last pending frame.

        Args:
            world: World to finalize snapshots from

        Returns:
            Complete game recording

        Raises:
            StateError: If not recording
        """
        if not self._recording:
            raise StateError(
                operation="stop_recording",
                state="not_recording",
                reason="Not currently recording",
            )

        self._recording = False

        if self._event_bus is not None:
            self._event_bus.unsubscribe_all(handler=self._on_event)

        incremental = None
        if (
            self._mode in {RecordingMode.INCREMENTAL, RecordingMode.DELTA_ONLY}
            and self._incremental_recorder is not None
        ):
            incremental = self._incremental_recorder.stop_recording(world=world)

        return GameRecording(
            metadata=self._metadata,
            snapshots=self._snapshots,
            events=self._events,
            commands=self._commands,
            incremental=incremental,
        )

    def is_recording(self) -> bool:
        """Check if currently recording.

        Returns:
            True if recording is in progress
        """
        return self._recording

    def _on_event(self, event: Event) -> None:
        """Handle event emission during recording.

        Args:
            event: Event to record
        """
        if not self._recording:  # pragma: no cover
            return

        if not self._config.should_include_event(event_type=event.event_type):
            return

        event_dict = SnapshotSerializer._normalize_for_serialization(data=asdict(event))
        event_dict["event_type"] = event.event_type
        event_dict["tick"] = event.tick
        self._events.append(event_dict)

    def _capture_commands_from_invoker(self) -> None:
        """Capture new commands from invoker history.

        Serializes commands executed since last capture and associates
        them with current tick.

        Note: This method is only called when command_invoker is not None.
        """
        if not self._config.record_commands:
            current_count = self._command_invoker.get_history_count()  # type: ignore[union-attr]
            self._last_command_count = current_count
            return

        current_count = self._command_invoker.get_history_count()  # type: ignore[union-attr]
        new_commands = current_count - self._last_command_count

        if new_commands <= 0:
            return

        history_items = self._command_invoker._history[  # type: ignore[union-attr]
            self._last_command_count : current_count
        ]

        for command, result in history_items:
            command_dict = {
                "tick": self._current_tick,
                "command_type": command.__class__.__name__,
                "priority": command.priority,
            }

            command_dict.update(command.to_dict())

            if hasattr(result, "value"):
                command_dict["result"] = result.value
            elif result is not None:
                command_dict["result"] = str(result)

            self._commands.append(command_dict)

        self._last_command_count = current_count
