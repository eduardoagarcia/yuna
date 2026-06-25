"""State machine implementation."""

from __future__ import annotations

from typing import Any

from yuna.exceptions import StateError, ValidationError
from yuna.fsm.state import State
from yuna.fsm.transition import Transition


class StateMachine[TContext]:
    """Manages state transitions and lifecycle.

    Responsibilities:
    - Register states and transitions
    - Track current state and history
    - Execute state lifecycle (enter/update/exit)
    - Evaluate and execute transitions
    - Force state changes when needed

    Usage:
        machine = StateMachine[GameContext]()
        machine.add_state(state=idle_state)
        machine.add_state(state=moving_state)
        machine.add_transition(transition=idle_to_moving)
        machine.set_state(state_name="idle")
        machine.update(context=ctx, delta_time=0.016)
    """

    def __init__(self) -> None:
        self._states: dict[str, State[TContext]] = {}
        self._transitions: list[Transition[TContext]] = []
        self._current_state: State[TContext] | None = None
        self._state_history: list[str] = []

    def add_state(self, state: State[TContext]) -> None:
        """Register a state with the state machine.

        Args:
            state: State instance to register

        Raises:
            StateError: If state with same name already exists
        """
        if state.name in self._states:
            raise StateError(
                operation="add_state",
                reason=f"State '{state.name}' already registered",
            )
        self._states[state.name] = state

    def add_transition(self, transition: Transition[TContext]) -> None:
        """Register a transition with the state machine.

        Args:
            transition: Transition instance to register

        Raises:
            ValidationError: If from_state or to_state not registered
        """
        if transition.from_state not in self._states:
            raise ValidationError(
                reason=f"State '{transition.from_state}' not registered",
                field="from_state",
                value=transition.from_state,
            )
        if transition.to_state not in self._states:
            raise ValidationError(
                reason=f"State '{transition.to_state}' not registered",
                field="to_state",
                value=transition.to_state,
            )
        self._transitions.append(transition)

    def set_state(self, state_name: str, context: TContext) -> None:
        """Force a state change.

        Args:
            state_name: Name of state to transition to
            context: State context for lifecycle hooks

        Raises:
            ValidationError: If state_name not registered
        """
        if state_name not in self._states:
            raise ValidationError(
                reason=f"State '{state_name}' not registered",
                field="state_name",
                value=state_name,
            )

        new_state = self._states[state_name]

        if self._current_state is not None:
            self._current_state.on_exit(context=context)

        self._current_state = new_state
        self._state_history.append(state_name)
        self._current_state.on_enter(context=context)

    def update(self, context: TContext, delta_time: float) -> None:
        """Update current state and check for transitions.

        Args:
            context: State context for updates and transitions
            delta_time: Time elapsed since last update

        Raises:
            StateError: If no state is currently set
        """
        if self._current_state is None:
            raise StateError(
                operation="update",
                reason="No current state set",
            )

        self._current_state.on_update(context=context, delta_time=delta_time)

        for transition in self._transitions:
            if transition.from_state != self._current_state.name:
                continue

            if transition.can_transition(context=context):
                self._current_state.on_exit(context=context)
                transition.execute(context=context)
                self._current_state = self._states[transition.to_state]
                self._state_history.append(transition.to_state)
                self._current_state.on_enter(context=context)
                break

    def get_current_state(self) -> State[TContext]:
        """Get the currently active state.

        Returns:
            Current state instance

        Raises:
            StateError: If no state is currently set
        """
        if self._current_state is None:
            raise StateError(
                operation="get_current_state",
                reason="No current state set",
            )
        return self._current_state

    def get_state_history(self) -> list[str]:
        """Get the history of state transitions.

        Returns:
            List of state names in chronological order
        """
        return self._state_history.copy()

    def to_dict(self) -> dict[str, Any]:
        """Convert state machine to JSON-serializable dictionary.

        Returns only the current state and history for replay purposes.
        States and transitions are not serialized as they are defined in code.

        Returns:
            Dictionary with current_state and state_history
        """
        return {
            "current_state": self._current_state.name if self._current_state else None,
            "state_history": self._state_history.copy(),
        }
