"""Game loop orchestrator for fixed timestep execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yuna.exceptions import StateError

if TYPE_CHECKING:
    from yuna.ecs.world import ECSWorld
    from yuna.events.bus import EventBus
    from yuna.loop.scheduler import SystemScheduler
    from yuna.loop.time import TimeManager
    from yuna.modifiers.pipeline import ModifierPipeline
    from yuna.profiling.monitor import PerformanceMonitor
    from yuna.profiling.stats import CountStats, TimingStats
    from yuna.replay.recorder import GameRecorder
    from yuna.replay.storage import GameRecording


class GameLoop:
    """Orchestrates game loop with fixed timestep execution.

    Responsibilities:
    - Coordinate all game subsystems
    - Execute ticks at fixed intervals
    - Process commands, modifiers, and events
    - Update systems in priority order
    - Maintain deterministic simulation

    The loop executes in this order per tick:
    1. Process modifier pipeline (if present)
    2. Process events (if present)
    3. Update systems via scheduler
    4. End tick for event bus (if present)

    Usage:
        time_manager = TimeManager(fixed_delta=1/60)
        scheduler = SystemScheduler()
        world = ECSWorld()
        event_bus = EventBus()
        modifier_pipeline = ModifierPipeline(config=config)

        game_loop = GameLoop(
            time_manager=time_manager,
            scheduler=scheduler,
            world=world,
            event_bus=event_bus,
            modifier_pipeline=modifier_pipeline,
        )

        elapsed = get_frame_time()
        game_loop.update(elapsed=elapsed)
    """

    def __init__(
        self,
        time_manager: TimeManager,
        scheduler: SystemScheduler,
        world: ECSWorld,
        event_bus: EventBus | None = None,
        modifier_pipeline: ModifierPipeline | None = None,
        recorder: GameRecorder | None = None,
        monitor: PerformanceMonitor | None = None,
    ) -> None:
        self._time_manager = time_manager
        self._scheduler = scheduler
        self._world = world
        self._event_bus = event_bus
        self._modifier_pipeline = modifier_pipeline
        self._recorder = recorder
        self._monitor = monitor
        self._current_tick = 0
        self._recording_enabled = False

    def tick(self) -> None:
        """Execute one game tick.

        Processes all subsystems in deterministic order.
        If recording is enabled, captures world snapshot after tick.
        If profiling is enabled, tracks timing for each subsystem.
        """
        if self._modifier_pipeline is not None:
            if self._monitor is not None:
                with self._monitor.sample(category="loop", name="ModifierPipeline"):
                    self._modifier_pipeline.process(world=self._world)
            else:
                self._modifier_pipeline.process(world=self._world)

        if self._event_bus is not None:
            if self._monitor is not None:
                with self._monitor.sample(category="loop", name="EventProcessing"):
                    self._event_bus.process_events()
            else:
                self._event_bus.process_events()

        for system in self._scheduler.get_ordered_systems():
            if self._monitor is not None:
                system_name = system.__class__.__name__
                with self._monitor.sample(category="systems", name=system_name):
                    system.update(
                        world=self._world, delta_time=self._time_manager.fixed_delta
                    )
            else:
                system.update(
                    world=self._world, delta_time=self._time_manager.fixed_delta
                )

        if self._event_bus is not None:
            self._event_bus.end_tick()

        if self._recording_enabled and self._recorder is not None:
            self._recorder.record_tick(world=self._world, tick=self._current_tick)

        self._current_tick += 1

    def update(self, elapsed: float) -> int:
        """Update game loop with elapsed time.

        Uses fixed timestep to execute appropriate number of ticks.

        Args:
            elapsed: Time elapsed since last update in seconds

        Returns:
            Number of ticks executed
        """
        ticks = self._time_manager.update(elapsed=elapsed)
        for _ in range(ticks):
            self.tick()
        return ticks

    @property
    def fixed_delta(self) -> float:
        """Get fixed timestep value.

        Returns:
            Fixed delta time in seconds
        """
        return self._time_manager.fixed_delta

    @property
    def accumulator(self) -> float:
        """Get current time accumulator.

        Returns:
            Accumulated time in seconds
        """
        return self._time_manager.accumulator

    def reset_time(self) -> None:
        """Reset time manager accumulator to zero."""
        self._time_manager.reset()

    def enable_recording(self, metadata: dict[str, Any] | None = None) -> None:
        """Enable game recording.

        Args:
            metadata: Optional metadata to include in recording

        Raises:
            StateError: If no recorder is configured
        """
        if self._recorder is None:
            raise StateError(
                operation="enable_recording",
                state="no_recorder",
                reason="No recorder configured for game loop",
            )

        if not self._recording_enabled:
            self._recorder.start_recording(world=self._world, metadata=metadata)
            self._recording_enabled = True
            self._current_tick = 0

    def disable_recording(self) -> None:
        """Disable game recording.

        Safe to call even if recording is not enabled.
        """
        self._recording_enabled = False

    def get_recording(self) -> GameRecording:
        """Get current recording and stop recording.

        Returns:
            Complete game recording

        Raises:
            StateError: If no recorder is configured or not recording
        """
        if self._recorder is None:
            raise StateError(
                operation="get_recording",
                state="no_recorder",
                reason="No recorder configured for game loop",
            )

        if not self._recording_enabled:
            raise StateError(
                operation="get_recording",
                state="not_recording",
                reason="Recording is not currently enabled",
            )

        self._recording_enabled = False
        return self._recorder.stop_recording(world=self._world)

    def is_recording(self) -> bool:
        """Check if recording is currently enabled.

        Returns:
            True if recording is enabled
        """
        return self._recording_enabled

    @property
    def current_tick(self) -> int:
        """Get current tick number.

        Returns:
            Current tick count
        """
        return self._current_tick

    def get_performance_stats(
        self,
    ) -> dict[str, dict[str, TimingStats | CountStats]]:
        """Get performance statistics from profiling monitor.

        Returns:
            Dictionary of category to dict of metric name to stats

        Raises:
            StateError: If no monitor is configured
        """
        if self._monitor is None:
            raise StateError(
                operation="get_performance_stats",
                state="no_monitor",
                reason="No monitor configured for game loop",
            )

        result: dict[str, dict[str, TimingStats | CountStats]] = {}
        for category in self._monitor.get_categories():
            result[category] = self._monitor.get_category_stats(category=category)
        return result
