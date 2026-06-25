"""Game replay player."""

from __future__ import annotations

from enum import Enum, auto

from yuna.exceptions import StateError, ValidationError
from yuna.replay.controls import PlaybackControls
from yuna.replay.storage import GameRecording
from yuna.state.snapshot import WorldSnapshot


class PlaybackState(Enum):
    """Playback state enumeration."""

    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


class GamePlayer:
    """Plays back recorded game sessions.

    Responsibilities:
    - Load and manage game recordings
    - Control playback (play, pause, resume, seek)
    - Track current playback position
    - Apply playback controls (speed, loop, boundaries)
    - Provide snapshot access at any tick

    Usage:
        player = GamePlayer()
        player.load_recording(recording=recording)
        player.play()
        while player.get_state() == PlaybackState.PLAYING:
            snapshot = player.get_snapshot(tick=player.get_current_tick())
            player.advance()
    """

    def __init__(self, controls: PlaybackControls | None = None) -> None:
        """Initialize player.

        Args:
            controls: Playback controls (default: standard controls)
        """
        self._controls = controls or PlaybackControls()
        self._recording: GameRecording | None = None
        self._state = PlaybackState.STOPPED
        self._current_tick = self._controls.start_tick

    def load_recording(self, recording: GameRecording) -> None:
        """Load a recording for playback.

        Args:
            recording: Recording to load
        """
        self._recording = recording
        self._state = PlaybackState.STOPPED
        self._current_tick = self._controls.start_tick

    def play(self) -> None:
        """Start playback from beginning.

        Raises:
            StateError: If no recording is loaded
        """
        if self._recording is None:
            raise StateError(
                operation="play",
                state="no_recording",
                reason="No recording loaded",
            )

        self._current_tick = self._controls.start_tick
        self._state = PlaybackState.PLAYING

    def play_from(self, tick: int) -> None:
        """Start playback from specific tick.

        Args:
            tick: Tick number to start from

        Raises:
            StateError: If no recording is loaded
            ValidationError: If tick is out of range or not available
        """
        if self._recording is None:
            raise StateError(
                operation="play_from",
                state="no_recording",
                reason="No recording loaded",
            )

        if tick < 0:
            raise ValidationError(
                field="tick",
                value=str(tick),
                reason="Tick must be non-negative",
            )

        if self._recording.incremental is not None:
            if self._recording.incremental.get_snapshot(tick=tick) is None:
                raise ValidationError(
                    field="tick",
                    value=str(tick),
                    reason="Tick not available in incremental recording",
                )
        elif tick >= len(self._recording.snapshots):
            raise ValidationError(
                field="tick",
                value=str(tick),
                reason="Tick is out of range",
            )

        self._current_tick = tick
        self._state = PlaybackState.PLAYING

    def pause(self) -> None:
        """Pause playback.

        Raises:
            StateError: If not currently playing
        """
        if self._state != PlaybackState.PLAYING:
            raise StateError(
                operation="pause",
                state=self._state.name.lower(),
                reason="Not currently playing",
            )

        self._state = PlaybackState.PAUSED

    def resume(self) -> None:
        """Resume playback from pause.

        Raises:
            StateError: If not currently paused
        """
        if self._state != PlaybackState.PAUSED:
            raise StateError(
                operation="resume",
                state=self._state.name.lower(),
                reason="Not currently paused",
            )

        self._state = PlaybackState.PLAYING

    def seek(self, tick: int) -> None:
        """Jump to specific tick.

        Args:
            tick: Tick number to jump to

        Raises:
            StateError: If no recording is loaded
            ValidationError: If tick is out of range or not available
        """
        if self._recording is None:
            raise StateError(
                operation="seek",
                state="no_recording",
                reason="No recording loaded",
            )

        if tick < 0:
            raise ValidationError(
                field="tick",
                value=str(tick),
                reason="Tick must be non-negative",
            )

        if self._recording.incremental is not None:
            if self._recording.incremental.get_snapshot(tick=tick) is None:
                raise ValidationError(
                    field="tick",
                    value=str(tick),
                    reason="Tick not available in incremental recording",
                )
        elif tick >= len(self._recording.snapshots):
            raise ValidationError(
                field="tick",
                value=str(tick),
                reason="Tick is out of range",
            )

        self._current_tick = tick

    def get_current_tick(self) -> int:
        """Get current playback position.

        Returns:
            Current tick number
        """
        return self._current_tick

    def get_snapshot(self, tick: int) -> WorldSnapshot:
        """Get snapshot at specific tick.

        Args:
            tick: Tick number to get snapshot for

        Returns:
            World snapshot at that tick

        Raises:
            StateError: If no recording is loaded
            ValidationError: If tick is out of range or not available
        """
        if self._recording is None:
            raise StateError(
                operation="get_snapshot",
                state="no_recording",
                reason="No recording loaded",
            )

        if self._recording.incremental is not None:
            snapshot = self._recording.incremental.get_snapshot(tick=tick)
            if snapshot is None:
                raise ValidationError(
                    field="tick",
                    value=str(tick),
                    reason="Tick not available in incremental recording",
                )
            return snapshot
        else:
            if tick < 0 or tick >= len(self._recording.snapshots):
                raise ValidationError(
                    field="tick",
                    value=str(tick),
                    reason="Tick is out of range",
                )
            return self._recording.snapshots[tick]

    def get_state(self) -> PlaybackState:
        """Get current playback state.

        Returns:
            Current playback state
        """
        return self._state

    def advance(self) -> bool:
        """Advance playback by one tick.

        Returns:
            True if advanced, False if reached end

        Raises:
            StateError: If not currently playing or no recording loaded
        """
        if self._state != PlaybackState.PLAYING:
            raise StateError(
                operation="advance",
                state=self._state.name.lower(),
                reason="Not currently playing",
            )

        if self._recording is None:
            raise StateError(
                operation="advance",
                state="no_recording",
                reason="No recording loaded",
            )

        next_tick = self._current_tick + 1
        end_tick = self._controls.end_tick
        if end_tick is None:
            if self._recording.incremental is not None:
                keyframe_ticks = self._recording.incremental.get_keyframe_ticks()
                delta_ticks = self._recording.incremental.get_delta_ticks()
                all_ticks = sorted(keyframe_ticks + delta_ticks)
                end_tick = all_ticks[-1] if all_ticks else 0
            else:
                end_tick = len(self._recording.snapshots) - 1

        if next_tick > end_tick:
            if self._controls.loop:
                self._current_tick = self._controls.start_tick
                return True
            else:
                self._state = PlaybackState.STOPPED
                return False

        self._current_tick = next_tick
        return True

    def set_controls(self, controls: PlaybackControls) -> None:
        """Update playback controls.

        Args:
            controls: New playback controls
        """
        self._controls = controls
