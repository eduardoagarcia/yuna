"""State machine transition definition."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Transition[TContext]:
    """Defines a state transition with condition and optional callback.

    Responsibilities:
    - Define source and target states
    - Specify transition condition (predicate)
    - Optional callback on transition
    - Immutable transition configuration

    Usage:
        transition = Transition(
            from_state="idle",
            to_state="moving",
            condition=lambda ctx: ctx.velocity > 0,
            on_transition=lambda ctx: print("Started moving"),
        )
    """

    from_state: str
    to_state: str
    condition: Callable[[TContext], bool]
    on_transition: Callable[[TContext], None] | None = None

    def can_transition(self, context: TContext) -> bool:
        """Check if transition condition is met.

        Args:
            context: State context to evaluate

        Returns:
            True if transition should occur
        """
        return self.condition(context)

    def execute(self, context: TContext) -> None:
        """Execute transition callback if present.

        Args:
            context: State context for callback
        """
        if self.on_transition is not None:
            self.on_transition(context)
