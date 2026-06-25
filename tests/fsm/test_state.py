"""Tests for FSM state."""

from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.fsm.state import State

fake = Faker()


@dataclass
class MockContext:
    velocity: float
    entered: bool = False
    updated: bool = False
    exited: bool = False
    update_count: int = 0


class IdleState(State[MockContext]):
    @property
    def name(self) -> str:
        return "idle"

    def on_enter(self, context: MockContext) -> None:
        context.entered = True
        context.velocity = 0.0

    def on_update(self, context: MockContext, delta_time: float) -> None:
        context.updated = True
        context.update_count += 1

    def on_exit(self, context: MockContext) -> None:
        context.exited = True


class MovingState(State[MockContext]):
    @property
    def name(self) -> str:
        return "moving"


class MinimalState(State[MockContext]):
    def __init__(self, state_name: str) -> None:
        self._state_name = state_name

    @property
    def name(self) -> str:
        return self._state_name


def test_state_has_name_property() -> None:
    state = IdleState()

    assert state.name == "idle"


def test_on_enter_modifies_context() -> None:
    state = IdleState()
    context = MockContext(velocity=fake.pyfloat(min_value=1.0, max_value=100.0))

    state.on_enter(context=context)

    assert context.entered is True
    assert context.velocity == 0.0


def test_on_update_modifies_context() -> None:
    state = IdleState()
    context = MockContext(velocity=0.0)
    delta_time = fake.pyfloat(min_value=0.01, max_value=1.0)

    state.on_update(context=context, delta_time=delta_time)

    assert context.updated is True
    assert context.update_count == 1


def test_on_update_called_multiple_times() -> None:
    state = IdleState()
    context = MockContext(velocity=0.0)
    delta_time = fake.pyfloat(min_value=0.01, max_value=1.0)

    for _ in range(5):
        state.on_update(context=context, delta_time=delta_time)

    assert context.update_count == 5


def test_on_exit_modifies_context() -> None:
    state = IdleState()
    context = MockContext(velocity=0.0)

    state.on_exit(context=context)

    assert context.exited is True


def test_minimal_state_with_only_name() -> None:
    state_name = fake.word()
    state = MinimalState(state_name=state_name)
    context = MockContext(velocity=0.0)

    assert state.name == state_name

    state.on_enter(context=context)
    assert context.entered is False

    state.on_update(context=context, delta_time=0.1)
    assert context.updated is False

    state.on_exit(context=context)
    assert context.exited is False


def test_moving_state_without_lifecycle_hooks() -> None:
    state = MovingState()
    context = MockContext(velocity=0.0)

    state.on_enter(context=context)
    state.on_update(context=context, delta_time=0.1)
    state.on_exit(context=context)

    assert context.entered is False
    assert context.updated is False
    assert context.exited is False


def test_state_cannot_be_instantiated_without_name() -> None:
    class InvalidState(State[MockContext]):
        pass

    with pytest.raises(expected_exception=TypeError):
        InvalidState()  # type: ignore[abstract]


def test_lifecycle_order_is_preserved() -> None:
    context = MockContext(velocity=5.0)
    events: list[str] = []

    class TrackingState(State[MockContext]):
        @property
        def name(self) -> str:
            return "tracking"

        def on_enter(self, context: MockContext) -> None:
            events.append("enter")

        def on_update(self, context: MockContext, delta_time: float) -> None:
            events.append("update")

        def on_exit(self, context: MockContext) -> None:
            events.append("exit")

    tracking = TrackingState()
    tracking.on_enter(context=context)
    tracking.on_update(context=context, delta_time=0.1)
    tracking.on_update(context=context, delta_time=0.1)
    tracking.on_exit(context=context)

    assert events == ["enter", "update", "update", "exit"]
