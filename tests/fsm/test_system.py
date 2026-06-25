"""Tests for FSM system."""

from dataclasses import dataclass

from faker import Faker

from yuna.ecs.world import ECSWorld
from yuna.fsm.component import StateMachineComponent
from yuna.fsm.machine import StateMachine
from yuna.fsm.state import State
from yuna.fsm.system import StateMachineSystem
from yuna.fsm.transition import Transition

fake = Faker()


@dataclass
class MockContext:
    counter: int
    events: list[str]


class IdleState(State[MockContext]):
    @property
    def name(self) -> str:
        return "idle"

    def on_update(self, context: MockContext, delta_time: float) -> None:
        context.events.append("idle_update")
        context.counter += 1


class ActiveState(State[MockContext]):
    @property
    def name(self) -> str:
        return "active"

    def on_enter(self, context: MockContext) -> None:
        context.events.append("active_enter")

    def on_update(self, context: MockContext, delta_time: float) -> None:
        context.events.append("active_update")
        context.counter += 10


def test_system_creation() -> None:
    system = StateMachineSystem()

    assert system.priority == 150


def test_system_with_custom_priority() -> None:
    priority = fake.pyint(min_value=0, max_value=1000)
    system = StateMachineSystem(priority=priority)

    assert system.priority == priority


def test_system_update_calls_machine_update() -> None:
    world = ECSWorld()
    system = StateMachineSystem()
    world.register_system(system=system)

    machine = StateMachine[MockContext]()
    idle = IdleState()
    machine.add_state(state=idle)
    context = MockContext(counter=0, events=[])
    machine.set_state(state_name="idle", context=context)

    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id,
        component=StateMachineComponent(machine=machine, context=context),
    )

    world.update(delta_time=0.1)

    assert "idle_update" in context.events
    assert context.counter == 1


def test_system_updates_multiple_entities() -> None:
    world = ECSWorld()
    system = StateMachineSystem()
    world.register_system(system=system)

    machine1 = StateMachine[MockContext]()
    idle = IdleState()
    machine1.add_state(state=idle)
    context1 = MockContext(counter=0, events=[])
    machine1.set_state(state_name="idle", context=context1)

    machine2 = StateMachine[MockContext]()
    machine2.add_state(state=idle)
    context2 = MockContext(counter=0, events=[])
    machine2.set_state(state_name="idle", context=context2)

    entity1 = world.create_entity()
    entity2 = world.create_entity()
    world.add_component(
        entity_id=entity1,
        component=StateMachineComponent(machine=machine1, context=context1),
    )
    world.add_component(
        entity_id=entity2,
        component=StateMachineComponent(machine=machine2, context=context2),
    )

    world.update(delta_time=0.1)

    assert context1.counter == 1
    assert context2.counter == 1


def test_system_handles_state_transitions() -> None:
    world = ECSWorld()
    system = StateMachineSystem()
    world.register_system(system=system)

    machine = StateMachine[MockContext]()
    idle = IdleState()
    active = ActiveState()
    machine.add_state(state=idle)
    machine.add_state(state=active)

    transition: Transition[MockContext] = Transition(
        from_state="idle",
        to_state="active",
        condition=lambda ctx: ctx.counter >= 5,
    )
    machine.add_transition(transition=transition)

    context = MockContext(counter=0, events=[])
    machine.set_state(state_name="idle", context=context)

    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id,
        component=StateMachineComponent(machine=machine, context=context),
    )

    for _ in range(10):
        world.update(delta_time=0.1)

    assert "active_enter" in context.events
    assert "active_update" in context.events


def test_system_with_no_entities() -> None:
    world = ECSWorld()
    system = StateMachineSystem()
    world.register_system(system=system)

    world.update(delta_time=0.1)


def test_system_multiple_updates() -> None:
    world = ECSWorld()
    system = StateMachineSystem()
    world.register_system(system=system)

    machine = StateMachine[MockContext]()
    idle = IdleState()
    machine.add_state(state=idle)
    context = MockContext(counter=0, events=[])
    machine.set_state(state_name="idle", context=context)

    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id,
        component=StateMachineComponent(machine=machine, context=context),
    )

    world.update(delta_time=0.1)
    world.update(delta_time=0.1)
    world.update(delta_time=0.1)

    assert context.counter == 3
    assert context.events.count("idle_update") == 3


def test_system_passes_delta_time_to_machine() -> None:
    world = ECSWorld()
    system = StateMachineSystem()
    world.register_system(system=system)

    delta_times: list[float] = []

    class DeltaTrackingState(State[MockContext]):
        @property
        def name(self) -> str:
            return "tracking"

        def on_update(self, context: MockContext, delta_time: float) -> None:
            delta_times.append(delta_time)

    machine = StateMachine[MockContext]()
    tracking = DeltaTrackingState()
    machine.add_state(state=tracking)
    context = MockContext(counter=0, events=[])
    machine.set_state(state_name="tracking", context=context)

    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id,
        component=StateMachineComponent(machine=machine, context=context),
    )

    world.update(delta_time=0.016)

    assert len(delta_times) == 1
    assert delta_times[0] == 0.016


def test_system_with_different_contexts_per_entity() -> None:
    world = ECSWorld()
    system = StateMachineSystem()
    world.register_system(system=system)

    idle = IdleState()
    active = ActiveState()

    machine1 = StateMachine[MockContext]()
    machine1.add_state(state=idle)
    context1 = MockContext(counter=0, events=[])
    machine1.set_state(state_name="idle", context=context1)

    machine2 = StateMachine[MockContext]()
    machine2.add_state(state=active)
    context2 = MockContext(counter=0, events=[])
    machine2.set_state(state_name="active", context=context2)

    entity1 = world.create_entity()
    entity2 = world.create_entity()
    world.add_component(
        entity_id=entity1,
        component=StateMachineComponent(machine=machine1, context=context1),
    )
    world.add_component(
        entity_id=entity2,
        component=StateMachineComponent(machine=machine2, context=context2),
    )

    world.update(delta_time=0.1)

    assert context1.counter == 1
    assert context2.counter == 10


def test_system_query_only_returns_entities_with_component() -> None:
    world = ECSWorld()
    system = StateMachineSystem()
    world.register_system(system=system)

    machine = StateMachine[MockContext]()
    idle = IdleState()
    machine.add_state(state=idle)
    context = MockContext(counter=0, events=[])
    machine.set_state(state_name="idle", context=context)

    entity_with_component = world.create_entity()
    world.create_entity()

    world.add_component(
        entity_id=entity_with_component,
        component=StateMachineComponent(machine=machine, context=context),
    )

    world.update(delta_time=0.1)

    assert context.counter == 1


def test_system_executes_at_correct_priority() -> None:
    world = ECSWorld()
    execution_order: list[str] = []

    class TrackingSystem(StateMachineSystem):
        def __init__(self, priority: int, name: str) -> None:
            super().__init__(priority=priority)
            self._name = name

        def update(self, world: ECSWorld, delta_time: float) -> None:
            execution_order.append(self._name)
            super().update(world=world, delta_time=delta_time)

    system1 = TrackingSystem(priority=100, name="first")
    system2 = TrackingSystem(priority=200, name="second")
    system3 = TrackingSystem(priority=300, name="third")

    world.register_system(system=system2)
    world.register_system(system=system1)
    world.register_system(system=system3)

    world.update(delta_time=0.1)

    assert execution_order == ["first", "second", "third"]


def test_system_updates_entities_in_sorted_entity_order() -> None:
    """FSMs update in sorted entity-id order regardless of insertion order."""
    world = ECSWorld()
    system = StateMachineSystem()
    world.register_system(system=system)

    update_order: list[str] = []

    @dataclass
    class OrderContext:
        entity_id: str

    class RecordingState(State[OrderContext]):
        @property
        def name(self) -> str:
            return "recording"

        def on_update(self, context: OrderContext, delta_time: float) -> None:
            update_order.append(context.entity_id)

    entity_ids = [world.create_entity() for _ in range(5)]

    for entity_id in reversed(entity_ids):
        machine = StateMachine[OrderContext]()
        machine.add_state(state=RecordingState())
        context = OrderContext(entity_id=entity_id)
        machine.set_state(state_name="recording", context=context)
        world.add_component(
            entity_id=entity_id,
            component=StateMachineComponent(machine=machine, context=context),
        )

    world.update(delta_time=0.1)

    assert update_order == sorted(entity_ids)


def test_system_continues_after_entity_destroyed() -> None:
    world = ECSWorld()
    system = StateMachineSystem()
    world.register_system(system=system)

    machine = StateMachine[MockContext]()
    idle = IdleState()
    machine.add_state(state=idle)
    context = MockContext(counter=0, events=[])
    machine.set_state(state_name="idle", context=context)

    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id,
        component=StateMachineComponent(machine=machine, context=context),
    )

    world.update(delta_time=0.1)
    assert context.counter == 1

    world.destroy_entity(entity_id=entity_id)
    world.update(delta_time=0.1)

    query = world.query().with_components(StateMachineComponent)
    assert query.count() == 0
