"""Tests for FSM state machine."""

from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.exceptions import StateError, ValidationError
from yuna.fsm.machine import StateMachine
from yuna.fsm.state import State
from yuna.fsm.transition import Transition

fake = Faker()


@dataclass
class MockContext:
    velocity: float
    position: int
    events: list[str]


class IdleState(State[MockContext]):
    @property
    def name(self) -> str:
        return "idle"

    def on_enter(self, context: MockContext) -> None:
        context.events.append("idle_enter")
        context.velocity = 0.0

    def on_update(self, context: MockContext, delta_time: float) -> None:
        context.events.append("idle_update")

    def on_exit(self, context: MockContext) -> None:
        context.events.append("idle_exit")


class MovingState(State[MockContext]):
    @property
    def name(self) -> str:
        return "moving"

    def on_enter(self, context: MockContext) -> None:
        context.events.append("moving_enter")

    def on_update(self, context: MockContext, delta_time: float) -> None:
        context.events.append("moving_update")
        context.position += int(context.velocity * delta_time)

    def on_exit(self, context: MockContext) -> None:
        context.events.append("moving_exit")


class StoppedState(State[MockContext]):
    @property
    def name(self) -> str:
        return "stopped"

    def on_enter(self, context: MockContext) -> None:
        context.events.append("stopped_enter")

    def on_update(self, context: MockContext, delta_time: float) -> None:
        context.events.append("stopped_update")

    def on_exit(self, context: MockContext) -> None:
        context.events.append("stopped_exit")


def test_add_state_registers_state() -> None:
    machine = StateMachine[MockContext]()
    state = IdleState()

    machine.add_state(state=state)

    assert machine._states["idle"] == state


def test_add_state_raises_error_for_duplicate() -> None:
    machine = StateMachine[MockContext]()
    state1 = IdleState()
    state2 = IdleState()

    machine.add_state(state=state1)

    with pytest.raises(expected_exception=StateError, match="already registered"):
        machine.add_state(state=state2)


def test_add_transition_registers_transition() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    moving = MovingState()
    machine.add_state(state=idle)
    machine.add_state(state=moving)

    transition: Transition[MockContext] = Transition(
        from_state="idle",
        to_state="moving",
        condition=lambda ctx: ctx.velocity > 0,
    )

    machine.add_transition(transition=transition)

    assert transition in machine._transitions


def test_add_transition_raises_error_for_invalid_from_state() -> None:
    machine = StateMachine[MockContext]()
    moving = MovingState()
    machine.add_state(state=moving)

    transition: Transition[MockContext] = Transition(
        from_state="invalid",
        to_state="moving",
        condition=lambda ctx: True,
    )

    with pytest.raises(expected_exception=ValidationError, match="not registered"):
        machine.add_transition(transition=transition)


def test_add_transition_raises_error_for_invalid_to_state() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    machine.add_state(state=idle)

    transition: Transition[MockContext] = Transition(
        from_state="idle",
        to_state="invalid",
        condition=lambda ctx: True,
    )

    with pytest.raises(expected_exception=ValidationError, match="not registered"):
        machine.add_transition(transition=transition)


def test_set_state_changes_current_state() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    machine.add_state(state=idle)
    context = MockContext(velocity=0.0, position=0, events=[])

    machine.set_state(state_name="idle", context=context)

    assert machine._current_state == idle


def test_set_state_calls_on_enter() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    machine.add_state(state=idle)
    context = MockContext(velocity=5.0, position=0, events=[])

    machine.set_state(state_name="idle", context=context)

    assert "idle_enter" in context.events
    assert context.velocity == 0.0


def test_set_state_calls_on_exit_for_previous_state() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    moving = MovingState()
    machine.add_state(state=idle)
    machine.add_state(state=moving)
    context = MockContext(velocity=0.0, position=0, events=[])

    machine.set_state(state_name="idle", context=context)
    machine.set_state(state_name="moving", context=context)

    assert "idle_exit" in context.events
    assert "moving_enter" in context.events


def test_set_state_raises_error_for_invalid_state() -> None:
    machine = StateMachine[MockContext]()
    context = MockContext(velocity=0.0, position=0, events=[])

    with pytest.raises(expected_exception=ValidationError, match="not registered"):
        machine.set_state(state_name="invalid", context=context)


def test_update_calls_current_state_on_update() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    machine.add_state(state=idle)
    context = MockContext(velocity=0.0, position=0, events=[])
    machine.set_state(state_name="idle", context=context)
    delta_time = fake.pyfloat(min_value=0.01, max_value=1.0)

    machine.update(context=context, delta_time=delta_time)

    assert "idle_update" in context.events


def test_update_raises_error_when_no_current_state() -> None:
    machine = StateMachine[MockContext]()
    context = MockContext(velocity=0.0, position=0, events=[])
    delta_time = fake.pyfloat(min_value=0.01, max_value=1.0)

    with pytest.raises(expected_exception=StateError, match="No current state"):
        machine.update(context=context, delta_time=delta_time)


def test_update_triggers_transition_when_condition_met() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    moving = MovingState()
    machine.add_state(state=idle)
    machine.add_state(state=moving)

    transition: Transition[MockContext] = Transition(
        from_state="idle",
        to_state="moving",
        condition=lambda ctx: ctx.velocity > 0,
    )
    machine.add_transition(transition=transition)

    context = MockContext(velocity=0.0, position=0, events=[])
    machine.set_state(state_name="idle", context=context)

    context.velocity = 5.0
    machine.update(context=context, delta_time=0.1)

    assert machine._current_state == moving
    assert "idle_exit" in context.events
    assert "moving_enter" in context.events


def test_update_does_not_trigger_transition_when_condition_not_met() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    moving = MovingState()
    machine.add_state(state=idle)
    machine.add_state(state=moving)

    transition: Transition[MockContext] = Transition(
        from_state="idle",
        to_state="moving",
        condition=lambda ctx: ctx.velocity > 0,
    )
    machine.add_transition(transition=transition)

    context = MockContext(velocity=0.0, position=0, events=[])
    machine.set_state(state_name="idle", context=context)

    machine.update(context=context, delta_time=0.1)

    assert machine._current_state == idle
    assert "moving_enter" not in context.events


def test_update_executes_transition_callback() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    moving = MovingState()
    machine.add_state(state=idle)
    machine.add_state(state=moving)

    callback_called = False

    def on_transition(ctx: MockContext) -> None:
        nonlocal callback_called
        callback_called = True

    transition: Transition[MockContext] = Transition(
        from_state="idle",
        to_state="moving",
        condition=lambda ctx: ctx.velocity > 0,
        on_transition=on_transition,
    )
    machine.add_transition(transition=transition)

    context = MockContext(velocity=0.0, position=0, events=[])
    machine.set_state(state_name="idle", context=context)

    context.velocity = 5.0
    machine.update(context=context, delta_time=0.1)

    assert callback_called is True


def test_get_current_state_returns_active_state() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    machine.add_state(state=idle)
    context = MockContext(velocity=0.0, position=0, events=[])
    machine.set_state(state_name="idle", context=context)

    current = machine.get_current_state()

    assert current == idle


def test_get_current_state_raises_error_when_no_state_set() -> None:
    machine = StateMachine[MockContext]()

    with pytest.raises(expected_exception=StateError, match="No current state"):
        machine.get_current_state()


def test_get_state_history_returns_transition_history() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    moving = MovingState()
    machine.add_state(state=idle)
    machine.add_state(state=moving)
    context = MockContext(velocity=0.0, position=0, events=[])

    machine.set_state(state_name="idle", context=context)
    machine.set_state(state_name="moving", context=context)
    machine.set_state(state_name="idle", context=context)

    history = machine.get_state_history()

    assert history == ["idle", "moving", "idle"]


def test_get_state_history_returns_copy() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    machine.add_state(state=idle)
    context = MockContext(velocity=0.0, position=0, events=[])
    machine.set_state(state_name="idle", context=context)

    history = machine.get_state_history()
    history.append("modified")

    assert machine.get_state_history() == ["idle"]


def test_multiple_transitions_checks_all_in_order() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    moving = MovingState()
    stopped = StoppedState()
    machine.add_state(state=idle)
    machine.add_state(state=moving)
    machine.add_state(state=stopped)

    transition1: Transition[MockContext] = Transition(
        from_state="idle",
        to_state="moving",
        condition=lambda ctx: ctx.velocity > 10,
    )
    transition2: Transition[MockContext] = Transition(
        from_state="idle",
        to_state="stopped",
        condition=lambda ctx: ctx.velocity > 0,
    )
    machine.add_transition(transition=transition1)
    machine.add_transition(transition=transition2)

    context = MockContext(velocity=0.0, position=0, events=[])
    machine.set_state(state_name="idle", context=context)

    context.velocity = 5.0
    machine.update(context=context, delta_time=0.1)

    assert machine._current_state == stopped


def test_transition_only_triggers_once_per_update() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    moving = MovingState()
    stopped = StoppedState()
    machine.add_state(state=idle)
    machine.add_state(state=moving)
    machine.add_state(state=stopped)

    transition1: Transition[MockContext] = Transition(
        from_state="idle",
        to_state="moving",
        condition=lambda ctx: True,
    )
    transition2: Transition[MockContext] = Transition(
        from_state="moving",
        to_state="stopped",
        condition=lambda ctx: True,
    )
    machine.add_transition(transition=transition1)
    machine.add_transition(transition=transition2)

    context = MockContext(velocity=0.0, position=0, events=[])
    machine.set_state(state_name="idle", context=context)
    machine.update(context=context, delta_time=0.1)

    assert machine._current_state == moving
    assert "stopped_enter" not in context.events


def test_complex_state_machine_workflow() -> None:
    machine = StateMachine[MockContext]()
    idle = IdleState()
    moving = MovingState()
    stopped = StoppedState()
    machine.add_state(state=idle)
    machine.add_state(state=moving)
    machine.add_state(state=stopped)

    idle_to_moving: Transition[MockContext] = Transition(
        from_state="idle",
        to_state="moving",
        condition=lambda ctx: ctx.velocity > 0,
    )
    moving_to_stopped: Transition[MockContext] = Transition(
        from_state="moving",
        to_state="stopped",
        condition=lambda ctx: ctx.velocity == 0,
    )
    stopped_to_idle: Transition[MockContext] = Transition(
        from_state="stopped",
        to_state="idle",
        condition=lambda ctx: ctx.position == 0,
    )

    machine.add_transition(transition=idle_to_moving)
    machine.add_transition(transition=moving_to_stopped)
    machine.add_transition(transition=stopped_to_idle)

    context = MockContext(velocity=0.0, position=0, events=[])
    machine.set_state(state_name="idle", context=context)

    context.velocity = 10.0
    machine.update(context=context, delta_time=0.1)
    assert machine.get_current_state() == moving

    context.velocity = 0.0
    machine.update(context=context, delta_time=0.1)
    assert machine.get_current_state() == stopped

    context.position = 0
    machine.update(context=context, delta_time=0.1)
    assert machine.get_current_state() == idle

    history = machine.get_state_history()
    assert history == ["idle", "moving", "stopped", "idle"]


def test_to_dict_serializes_current_state_and_history() -> None:
    """Test that to_dict serializes current state and history."""
    machine = StateMachine[MockContext]()
    idle = IdleState()
    moving = MovingState()
    machine.add_state(state=idle)
    machine.add_state(state=moving)
    context = MockContext(velocity=0.0, position=0, events=[])

    machine.set_state(state_name="idle", context=context)
    machine.set_state(state_name="moving", context=context)

    result = machine.to_dict()

    assert result["current_state"] == "moving"
    assert result["state_history"] == ["idle", "moving"]


def test_to_dict_with_no_current_state() -> None:
    """Test that to_dict returns None for current_state when not set."""
    machine = StateMachine[MockContext]()

    result = machine.to_dict()

    assert result["current_state"] is None
    assert result["state_history"] == []


def test_to_dict_preserves_state_history() -> None:
    """Test that to_dict includes complete state history."""
    machine = StateMachine[MockContext]()
    idle = IdleState()
    moving = MovingState()
    stopped = StoppedState()
    machine.add_state(state=idle)
    machine.add_state(state=moving)
    machine.add_state(state=stopped)
    context = MockContext(velocity=0.0, position=0, events=[])

    machine.set_state(state_name="idle", context=context)
    machine.set_state(state_name="moving", context=context)
    machine.set_state(state_name="stopped", context=context)
    machine.set_state(state_name="idle", context=context)

    result = machine.to_dict()

    assert result["state_history"] == ["idle", "moving", "stopped", "idle"]


def test_to_dict_state_history_is_copy() -> None:
    """Test that to_dict returns a copy of state history."""
    machine = StateMachine[MockContext]()
    idle = IdleState()
    machine.add_state(state=idle)
    context = MockContext(velocity=0.0, position=0, events=[])
    machine.set_state(state_name="idle", context=context)

    result = machine.to_dict()
    result["state_history"].append("modified")

    assert machine.get_state_history() == ["idle"]
