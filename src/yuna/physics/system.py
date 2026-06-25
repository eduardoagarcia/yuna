"""Physics system for ECS integration."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, cast

from yuna.ecs.system import System
from yuna.physics.body import PhysicsBody
from yuna.physics.engine import PhysicsEngine
from yuna.spatial.integration import Position
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

if TYPE_CHECKING:
    from yuna.commands.invoker import CommandInvoker
    from yuna.ecs.world import ECSWorld
    from yuna.events.bus import EventBus


class PhysicsSystem(System):
    """ECS system for physics simulation.

    Integrates PhysicsEngine with ECS world, syncing entity positions
    and physics bodies.

    Usage:
        event_bus = EventBus()
        system = PhysicsSystem(event_bus=event_bus, gravity=Vector2(x=0.0, y=-9.8))
        world.register_system(system=system)
    """

    def __init__(
        self,
        event_bus: EventBus | None = None,
        command_invoker: CommandInvoker[ECSWorld, Any] | None = None,
        gravity: Vector2 | None = None,
        priority: int = 100,
    ) -> None:
        """Initialize physics system.

        Args:
            event_bus: Optional event bus for collision events
            command_invoker: Optional command invoker for physics commands
            gravity: Global gravity vector
            priority: System execution priority
        """
        self.engine = PhysicsEngine(gravity=gravity)
        self._event_bus = event_bus
        self._command_invoker = command_invoker
        self._priority = priority
        self._registered_entities: set[str] = set()
        self._tick_counter = 0

    @property
    def priority(self) -> int:
        """Get system execution priority.

        Returns:
            Priority value (lower executes first)
        """
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:
        """Update physics simulation.

        Args:
            world: ECS world
            delta_time: Time step in seconds
        """
        self._tick_counter += 1
        self._sync_bodies_to_engine(world=world)
        collision_events = self.engine.step(
            delta_time=delta_time,
            timestamp=time.time(),
            tick=self._tick_counter,
        )
        self._sync_positions_from_engine(world=world)
        self._emit_collision_events(events=collision_events)

    def _sync_bodies_to_engine(self, world: ECSWorld) -> None:
        """Sync PhysicsBody components to physics engine.

        Args:
            world: ECS world
        """
        query = world.query().with_components(PhysicsBody, Position)
        active_entities = world.get_all_entities()
        current_entity_ids = {
            str(eid) for eid in query.get_entities() if eid in active_entities
        }

        entities_to_add = current_entity_ids - self._registered_entities
        for entity_id_str in sorted(entities_to_add):
            entity_id = EntityID(entity_id_str)
            body_raw = world.get_component(
                entity_id=entity_id, component_type=PhysicsBody
            )
            position_raw = world.get_component(
                entity_id=entity_id, component_type=Position
            )

            if body_raw and position_raw:
                body = cast(PhysicsBody, body_raw)
                position = cast(Position, position_raw)
                self.engine.add_body(
                    entity_id=entity_id_str,
                    body=body,
                    position=position.position,
                )
                self._registered_entities.add(entity_id_str)

        entities_to_remove = self._registered_entities - current_entity_ids
        for entity_id_str in sorted(entities_to_remove):
            self.engine.remove_body(entity_id=entity_id_str)
            self._registered_entities.discard(entity_id_str)

    def _sync_positions_from_engine(self, world: ECSWorld) -> None:
        """Sync positions from physics engine to ECS components.

        Args:
            world: ECS world
        """
        query = world.query().with_components(PhysicsBody, Position)

        for entity_id, (_body, current_position) in query.iterator():
            entity_id_str = str(entity_id)
            engine_position = self.engine.get_position(entity_id=entity_id_str)

            if engine_position is None:
                continue

            position = cast(Position, current_position)
            if position.position != engine_position:
                world.add_component(
                    entity_id=entity_id,
                    component=Position(position=engine_position),
                )

    def _emit_collision_events(self, events: list) -> None:
        """Emit collision events to event bus.

        Args:
            events: List of collision events
        """
        if self._event_bus is None:
            return

        for event in events:
            self._event_bus.emit(event=event)
