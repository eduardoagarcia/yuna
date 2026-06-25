"""Time management for fixed timestep game loop."""

from __future__ import annotations


class TimeManager:
    """Manages fixed timestep game loop timing.

    Responsibilities:
    - Maintain fixed timestep for deterministic simulation
    - Accumulate elapsed time across frames
    - Calculate number of ticks to execute per frame
    - Prevent time drift with accumulator pattern

    Fixed timestep ensures consistent physics and gameplay regardless
    of frame rate variations.

    Usage:
        time_manager = TimeManager(fixed_delta=1/60)

        while running:
            elapsed = get_frame_time()
            ticks = time_manager.update(elapsed=elapsed)

            for _ in range(ticks):
                update_game_state()
    """

    def __init__(self, fixed_delta: float):
        """Initialize time manager with fixed timestep.

        Args:
            fixed_delta: Fixed time step in seconds (e.g., 1/60 for 60 FPS)
        """
        self._fixed_delta = fixed_delta
        self._accumulator = 0.0

    @property
    def fixed_delta(self) -> float:
        """Get fixed timestep value.

        Returns:
            Fixed delta time in seconds
        """
        return self._fixed_delta

    @property
    def accumulator(self) -> float:
        """Get current accumulator value.

        Returns:
            Accumulated time in seconds
        """
        return self._accumulator

    def update(self, elapsed: float) -> int:
        """Update accumulator and calculate ticks to execute.

        Args:
            elapsed: Time elapsed since last update in seconds

        Returns:
            Number of fixed timestep ticks to execute this frame
        """
        self._accumulator += elapsed
        ticks = 0

        while self._accumulator >= self._fixed_delta:
            self._accumulator -= self._fixed_delta
            ticks += 1

        return ticks

    def reset(self) -> None:
        """Reset accumulator to zero.

        Useful for restarting simulation or handling time discontinuities.
        """
        self._accumulator = 0.0
