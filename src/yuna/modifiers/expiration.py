"""Expiration tracking for time-limited modifiers."""

from dataclasses import dataclass

from yuna.modifiers.modifier import Modifier


@dataclass
class TrackedModifier:
    """Wrapper for modifiers with expiration tracking.

    Attributes:
        modifier: The actual modifier being tracked
        applied_tick: Tick when modifier was applied
        expires_tick: Tick when modifier expires (None = permanent)

    Usage:
        tracked = TrackedModifier(
            modifier=damage_modifier,
            applied_tick=100,
            expires_tick=150,
        )

        if tracked.is_expired(current_tick=160):
            # Remove modifier
            pass
    """

    modifier: Modifier
    applied_tick: int
    expires_tick: int | None

    def is_expired(self, current_tick: int) -> bool:
        """Check if modifier has expired.

        Args:
            current_tick: Current game tick

        Returns:
            True if modifier expired, False otherwise
        """
        if self.expires_tick is None:
            return False
        return current_tick >= self.expires_tick

    def ticks_remaining(self, current_tick: int) -> int | None:
        """Get number of ticks until expiration.

        Args:
            current_tick: Current game tick

        Returns:
            Number of ticks remaining, None if permanent, 0 if expired
        """
        if self.expires_tick is None:
            return None
        remaining = self.expires_tick - current_tick
        return max(0, remaining)
