"""Tests for FSM transition."""

import dataclasses
from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.fsm.transition import Transition

fake = Faker()


@dataclass
class MockContext:
    velocity: float
    position: int
    is_moving: bool


def test_can_transition_returns_true_when_condition_met() -> None:
    velocity = fake.pyfloat(min_value=1.0, max_value=100.0)
    context = MockContext(velocity=velocity, position=0, is_moving=False)

    transition: Transition[MockContext] = Transition(
        from_state=fake.word(),
        to_state=fake.word(),
        condition=lambda ctx: ctx.velocity > 0,
    )

    assert transition.can_transition(context=context) is True


def test_can_transition_returns_false_when_condition_not_met() -> None:
    context = MockContext(velocity=0.0, position=0, is_moving=False)

    transition: Transition[MockContext] = Transition(
        from_state=fake.word(),
        to_state=fake.word(),
        condition=lambda ctx: ctx.velocity > 0,
    )

    assert transition.can_transition(context=context) is False


def test_execute_calls_on_transition_callback() -> None:
    context = MockContext(velocity=0.0, position=0, is_moving=False)
    callback_called = False

    def on_transition(ctx: MockContext) -> None:
        nonlocal callback_called
        callback_called = True

    transition = Transition(
        from_state=fake.word(),
        to_state=fake.word(),
        condition=lambda ctx: True,
        on_transition=on_transition,
    )

    transition.execute(context=context)

    assert callback_called is True


def test_execute_modifies_context_via_callback() -> None:
    context = MockContext(velocity=0.0, position=0, is_moving=False)

    def on_transition(ctx: MockContext) -> None:
        ctx.is_moving = True

    transition = Transition(
        from_state=fake.word(),
        to_state=fake.word(),
        condition=lambda ctx: True,
        on_transition=on_transition,
    )

    transition.execute(context=context)

    assert context.is_moving is True


def test_execute_does_nothing_when_no_callback() -> None:
    context = MockContext(velocity=0.0, position=0, is_moving=False)

    transition: Transition[MockContext] = Transition(
        from_state=fake.word(),
        to_state=fake.word(),
        condition=lambda ctx: True,
        on_transition=None,
    )

    transition.execute(context=context)

    assert context.is_moving is False


def test_transition_is_frozen_dataclass() -> None:
    transition: Transition[MockContext] = Transition(
        from_state=fake.word(),
        to_state=fake.word(),
        condition=lambda ctx: True,
    )

    with pytest.raises(expected_exception=dataclasses.FrozenInstanceError):
        transition.from_state = fake.word()  # type: ignore[misc]


def test_complex_condition_with_multiple_fields() -> None:
    context = MockContext(velocity=5.0, position=10, is_moving=True)

    transition: Transition[MockContext] = Transition(
        from_state=fake.word(),
        to_state=fake.word(),
        condition=lambda ctx: ctx.velocity > 0 and ctx.position > 5 and ctx.is_moving,
    )

    assert transition.can_transition(context=context) is True


def test_complex_condition_fails_when_one_field_invalid() -> None:
    context = MockContext(velocity=5.0, position=3, is_moving=True)

    transition: Transition[MockContext] = Transition(
        from_state=fake.word(),
        to_state=fake.word(),
        condition=lambda ctx: ctx.velocity > 0 and ctx.position > 5 and ctx.is_moving,
    )

    assert transition.can_transition(context=context) is False
