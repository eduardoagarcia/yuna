"""AI-related events for perception, pathfinding, and blackboard changes."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from yuna.events.event import Event
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2


@dataclass(frozen=True)
class BlackboardValueChanged(Event):
    """Emitted when blackboard value changes.

    Responsibilities:
    - Notify observers of AI state changes
    - Enable event-driven AI reactions
    - Track old and new values for debugging

    Enables event-driven AI that reacts to state changes instead of
    polling every frame. Games can subscribe to specific key changes
    for reactive behavior.

    Usage:
        def on_target_changed(event: BlackboardValueChanged) -> None:
            if event.key == "target" and event.new_value is not None:
                print(f"AI {event.entity_id} acquired target {event.new_value}")

        bus.subscribe(
            event_type="BlackboardValueChanged",
            handler=on_target_changed,
        )
    """

    entity_id: EntityID
    key: str
    old_value: Any
    new_value: Any

    @classmethod
    def create(
        cls,
        tick: int,
        entity_id: EntityID,
        key: str,
        old_value: Any,
        new_value: Any,
    ) -> BlackboardValueChanged:
        """Create a blackboard-value-changed event with auto timestamp.

        Args:
            tick: Game tick when the value changed
            entity_id: Entity owning the blackboard
            key: Blackboard key that changed
            old_value: Previous value
            new_value: New value

        Returns:
            BlackboardValueChanged instance
        """
        return cls(
            timestamp=time.time(),
            tick=tick,
            entity_id=entity_id,
            key=key,
            old_value=old_value,
            new_value=new_value,
        )


@dataclass(frozen=True)
class EntityPerceived(Event):
    """Emitted when AI perceives an entity through vision or hearing.

    Responsibilities:
    - Notify when entity enters perception range
    - Track perception type (vision/hearing)
    - Record position where perceived

    Usage:
        def on_entity_perceived(event: EntityPerceived) -> None:
            if event.perception_type == "vision":
                print(f"AI {event.perceiver} saw {event.perceived}")

        bus.subscribe(
            event_type="EntityPerceived",
            handler=on_entity_perceived,
        )
    """

    perceiver: EntityID
    perceived: EntityID
    perception_type: str
    position: Vector2


@dataclass(frozen=True)
class EntityLost(Event):
    """Emitted when AI loses perception of entity.

    Responsibilities:
    - Notify when entity leaves perception range
    - Track last known position
    - Record how perception was lost

    Usage:
        def on_entity_lost(event: EntityLost) -> None:
            blackboard.set_value(
                key="last_known_position",
                value=event.last_known_position,
            )

        bus.subscribe(
            event_type="EntityLost",
            handler=on_entity_lost,
        )
    """

    perceiver: EntityID
    lost: EntityID
    perception_type: str
    last_known_position: Vector2


@dataclass(frozen=True)
class PathBlocked(Event):
    """Emitted when pathfinding encounters obstacle.

    Responsibilities:
    - Notify when path is blocked
    - Track where blockage occurred
    - Provide original goal for recalculation

    Usage:
        def on_path_blocked(event: PathBlocked) -> None:
            path_component.recalculate_on_blocked = True

        bus.subscribe(
            event_type="PathBlocked",
            handler=on_path_blocked,
        )
    """

    entity_id: EntityID
    blocked_at: Vector2
    goal: Vector2


@dataclass(frozen=True)
class PathCompleted(Event):
    """Emitted when AI reaches final waypoint.

    Responsibilities:
    - Notify when destination reached
    - Provide final position
    - Enable next action selection

    Usage:
        def on_path_completed(event: PathCompleted) -> None:
            blackboard.set_value(
                key="patrol_complete",
                value=True,
            )

        bus.subscribe(
            event_type="PathCompleted",
            handler=on_path_completed,
        )
    """

    entity_id: EntityID
    final_position: Vector2
