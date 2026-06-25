"""Playback controls configuration."""

from __future__ import annotations

from dataclasses import dataclass

from yuna.exceptions import ValidationError


@dataclass
class PlaybackControls:
    """Configuration for replay playback.

    Responsibilities:
    - Define playback speed multiplier
    - Configure loop behavior
    - Set start and end tick boundaries
    - Provide immutable playback configuration

    Usage:
        controls = PlaybackControls(
            speed=2.0,
            loop=True,
            start_tick=0,
            end_tick=100,
        )
    """

    speed: float = 1.0
    loop: bool = False
    start_tick: int = 0
    end_tick: int | None = None

    def __post_init__(self) -> None:
        """Validate playback controls.

        Raises:
            ValidationError: If speed is not positive or tick range is invalid
        """
        if self.speed <= 0:
            raise ValidationError(
                field="speed",
                value=str(self.speed),
                reason="Playback speed must be positive",
            )

        if self.start_tick < 0:
            raise ValidationError(
                field="start_tick",
                value=str(self.start_tick),
                reason="Start tick must be non-negative",
            )

        if self.end_tick is not None and self.end_tick < self.start_tick:
            raise ValidationError(
                field="end_tick",
                value=str(self.end_tick),
                reason="End tick must be greater than or equal to start tick",
            )
