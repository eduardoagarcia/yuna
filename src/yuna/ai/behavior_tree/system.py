"""Behavior tree system for executing AI decision trees."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from yuna.ai.behavior_tree.component import BehaviorTreeComponent
from yuna.ai.behavior_tree.types import BehaviorContext
from yuna.ai.blackboard import Blackboard
from yuna.ecs.system import System

if TYPE_CHECKING:
    from yuna.ai.behavior_tree.node import BehaviorNode
    from yuna.commands.invoker import CommandInvoker
    from yuna.ecs.world import ECSWorld
    from yuna.events.bus import EventBus


class BehaviorTreeSystem(System):
    """Execute behavior trees for AI entities.

    Responsibilities:
    - Query entities with behavior trees
    - Tick trees at specified intervals
    - Pass execution context to nodes
    - Handle tree execution errors

    Queries for entities with BehaviorTreeComponent and Blackboard,
    then executes their behavior tree root nodes with proper context.

    Usage:
        event_bus = EventBus()
        command_invoker = CommandInvoker()
        system = BehaviorTreeSystem(
            event_bus=event_bus,
            command_invoker=command_invoker,
        )
        world.add_system(system=system)

        # System automatically executes during world update
    """

    def __init__(
        self,
        event_bus: EventBus | None = None,
        command_invoker: CommandInvoker[ECSWorld, Any] | None = None,
        priority: int = 200,
    ) -> None:
        """Initialize behavior tree system.

        Args:
            event_bus: Optional event bus for AI events
            command_invoker: Optional command invoker for AI actions
            priority: System execution priority (default: 200)
        """
        self._event_bus = event_bus
        self._command_invoker = command_invoker
        self._priority = priority

    @property
    def priority(self) -> int:
        """Execution priority for behavior tree system.

        Returns:
            Priority value (default: 200 = normal priority, after input/physics)
        """
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:  # noqa: PLR6301
        """Execute behavior trees for all AI entities.

        Args:
            world: ECS world containing entities and components
            delta_time: Time elapsed since last update in seconds
        """
        query = world.query().with_components(BehaviorTreeComponent, Blackboard)

        for entity_id in sorted(query.get_entities()):
            tree_component_raw = world.get_component(
                entity_id=entity_id,
                component_type=BehaviorTreeComponent,
            )
            blackboard_raw = world.get_component(
                entity_id=entity_id,
                component_type=Blackboard,
            )

            if tree_component_raw is None or blackboard_raw is None:
                continue

            tree_component = cast(BehaviorTreeComponent, tree_component_raw)
            blackboard = cast(Blackboard, blackboard_raw)

            if not tree_component.should_tick():
                continue

            root = cast("BehaviorNode", tree_component.root)

            context = BehaviorContext(
                world=world,
                entity_id=entity_id,
                blackboard=blackboard,
                delta_time=delta_time,
            )

            root.tick(context=context)
