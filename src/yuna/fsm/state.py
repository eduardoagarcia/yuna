"""State machine state definition."""

from __future__ import annotations

from abc import ABC, abstractmethod


class State[TContext](ABC):
    """Abstract base class for state machine states.

    Responsibilities:
    - Define state behavior through lifecycle hooks
    - Provide state name for identification
    - Manage state entry, update, and exit logic
    - Declare available transitions (optional)

    Lifecycle:
    1. on_enter() - called once when entering state
    2. on_update() - called every frame while in state
    3. on_exit() - called once when leaving state

    Usage:
        class IdleState(State[GameContext]):
            @property
            def name(self) -> str:
                return "idle"

            def on_enter(self, context: GameContext) -> None:
                context.velocity = 0

            def on_update(self, context: GameContext, delta_time: float) -> None:
                pass

            def on_exit(self, context: GameContext) -> None:
                pass
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get state name.

        Returns:
            Unique state identifier
        """
        ...  # pragma: no cover

    def on_enter(self, context: TContext) -> None:  # noqa: PLR6301
        """Called when entering this state.

        Override this method to execute logic when entering the state.
        Default implementation is a no-op.

        Args:
            context: State context
        """
        _ = context

    def on_update(self, context: TContext, delta_time: float) -> None:  # noqa: PLR6301
        """Called every frame while in this state.

        Override this method to execute logic during state updates.
        Default implementation is a no-op.

        Args:
            context: State context
            delta_time: Time elapsed since last update
        """
        _ = context
        _ = delta_time

    def on_exit(self, context: TContext) -> None:  # noqa: PLR6301
        """Called when leaving this state.

        Override this method to execute cleanup logic when exiting the state.
        Default implementation is a no-op.

        Args:
            context: State context
        """
        _ = context
