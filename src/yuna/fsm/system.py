"""State machine system for ECS integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from yuna.ecs.system import System
from yuna.fsm.component import StateMachineComponent

if TYPE_CHECKING:
    from yuna.commands.invoker import CommandInvoker
    from yuna.ecs.world import ECSWorld
    from yuna.events.bus import EventBus


class StateMachineSystem(System):
    """System that updates all state machines.

    Responsibilities:
    - Query entities with StateMachineComponent
    - Update each state machine with its context
    - Execute state transitions based on conditions

    Usage:
        event_bus = EventBus()
        command_invoker = CommandInvoker()
        system = StateMachineSystem(
            event_bus=event_bus,
            command_invoker=command_invoker,
        )
        world.register_system(system=system)

        entity_id = world.create_entity()
        world.add_component(
            entity_id=entity_id,
            component=StateMachineComponent(machine=machine, context=context),
        )

        world.update(delta_time=0.016)
    """

    def __init__(
        self,
        event_bus: EventBus | None = None,
        command_invoker: CommandInvoker[ECSWorld, Any] | None = None,
        priority: int = 150,
    ) -> None:
        """Initialize state machine system.

        Args:
            event_bus: Optional event bus for state machine events
            command_invoker: Optional command invoker for state machine commands
            priority: System execution priority (default: 150)
        """
        self._event_bus = event_bus
        self._command_invoker = command_invoker
        self._priority = priority

    @property
    def priority(self) -> int:
        """Execution priority for this system.

        Returns:
            Priority value (200 by default)
        """
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:  # noqa: PLR6301
        """Update all state machines.

        Args:
            world: ECS world containing entities and components
            delta_time: Time elapsed since last update in seconds
        """
        query = world.query().with_components(StateMachineComponent)

        for _entity_id, (component,) in query.iterator():
            state_machine = cast(StateMachineComponent, component)
            state_machine.machine.update(
                context=state_machine.context, delta_time=delta_time
            )
