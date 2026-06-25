"""Tests for FSM component."""

from dataclasses import dataclass

from faker import Faker

from yuna.fsm.component import StateMachineComponent
from yuna.fsm.machine import StateMachine
from yuna.fsm.state import State

fake = Faker()


@dataclass
class MockContext:
    value: int
    name: str


class TestState(State[MockContext]):
    @property
    def name(self) -> str:
        return "test"


def test_component_creation() -> None:
    machine = StateMachine[MockContext]()
    context = MockContext(value=fake.pyint(), name=fake.word())

    component = StateMachineComponent(machine=machine, context=context)

    assert component.machine == machine
    assert component.context == context


def test_component_stores_machine() -> None:
    machine = StateMachine[MockContext]()
    state = TestState()
    machine.add_state(state=state)
    context = MockContext(value=0, name=fake.word())
    machine.set_state(state_name="test", context=context)

    component = StateMachineComponent(machine=machine, context=context)

    assert component.machine.get_current_state() == state


def test_component_stores_context() -> None:
    machine = StateMachine[MockContext]()
    value = fake.pyint()
    name = fake.word()
    context = MockContext(value=value, name=name)

    component = StateMachineComponent(machine=machine, context=context)

    assert component.context.value == value
    assert component.context.name == name


def test_component_context_is_mutable() -> None:
    machine = StateMachine[MockContext]()
    context = MockContext(value=10, name=fake.word())
    component = StateMachineComponent(machine=machine, context=context)

    component.context.value = 20

    assert component.context.value == 20


def test_component_with_metadata() -> None:
    machine = StateMachine[MockContext]()
    context = MockContext(value=0, name=fake.word())
    metadata = {fake.word(): fake.word(), fake.word(): fake.pyint()}

    component = StateMachineComponent(
        machine=machine,
        context=context,
        metadata=metadata,
    )

    assert component.metadata == metadata


def test_component_metadata_defaults_to_empty_dict() -> None:
    machine = StateMachine[MockContext]()
    context = MockContext(value=0, name=fake.word())

    component = StateMachineComponent(machine=machine, context=context)

    assert component.metadata == {}


def test_component_metadata_is_mutable() -> None:
    machine = StateMachine[MockContext]()
    context = MockContext(value=0, name=fake.word())
    component = StateMachineComponent(machine=machine, context=context)

    key = fake.word()
    value = fake.word()
    component.metadata[key] = value

    assert component.metadata[key] == value


def test_multiple_components_with_different_machines() -> None:
    machine1 = StateMachine[MockContext]()
    machine2 = StateMachine[MockContext]()
    context1 = MockContext(value=1, name=fake.word())
    context2 = MockContext(value=2, name=fake.word())

    component1 = StateMachineComponent(machine=machine1, context=context1)
    component2 = StateMachineComponent(machine=machine2, context=context2)

    assert component1.machine != component2.machine
    assert component1.context != component2.context


def test_multiple_components_can_share_same_machine_type() -> None:
    state = TestState()
    machine1 = StateMachine[MockContext]()
    machine1.add_state(state=state)
    machine2 = StateMachine[MockContext]()
    machine2.add_state(state=state)

    context1 = MockContext(value=0, name=fake.word())
    context2 = MockContext(value=0, name=fake.word())
    machine1.set_state(state_name="test", context=context1)
    machine2.set_state(state_name="test", context=context2)

    component1 = StateMachineComponent(machine=machine1, context=context1)
    component2 = StateMachineComponent(machine=machine2, context=context2)

    assert component1.machine.get_current_state().name == "test"
    assert component2.machine.get_current_state().name == "test"


def test_component_is_dataclass() -> None:
    machine = StateMachine[MockContext]()
    context = MockContext(value=0, name=fake.word())

    component = StateMachineComponent(machine=machine, context=context)

    assert hasattr(component, "__dataclass_fields__")


def test_component_to_dict_serializes_machine_state() -> None:
    """Test that to_dict serializes machine state but not context."""
    machine = StateMachine[MockContext]()
    state = TestState()
    machine.add_state(state=state)
    context = MockContext(value=fake.pyint(), name=fake.word())
    machine.set_state(state_name="test", context=context)

    component = StateMachineComponent(machine=machine, context=context)

    result = component.to_dict()

    assert "machine" in result
    assert "metadata" in result
    assert "context" not in result
    assert result["machine"]["current_state"] == "test"


def test_component_to_dict_includes_metadata() -> None:
    """Test that to_dict includes metadata."""
    machine = StateMachine[MockContext]()
    context = MockContext(value=0, name=fake.word())
    metadata = {fake.word(): fake.word(), "count": fake.pyint()}

    component = StateMachineComponent(
        machine=machine, context=context, metadata=metadata
    )

    result = component.to_dict()

    assert result["metadata"] == metadata


def test_component_to_dict_excludes_context() -> None:
    """Test that to_dict excludes context (contains runtime references)."""
    machine = StateMachine[MockContext]()
    context = MockContext(value=fake.pyint(), name=fake.word())

    component = StateMachineComponent(machine=machine, context=context)

    result = component.to_dict()

    assert "context" not in result


def test_component_to_dict_with_empty_metadata() -> None:
    """Test that to_dict works with empty metadata."""
    machine = StateMachine[MockContext]()
    context = MockContext(value=0, name=fake.word())

    component = StateMachineComponent(machine=machine, context=context)

    result = component.to_dict()

    assert result["metadata"] == {}
