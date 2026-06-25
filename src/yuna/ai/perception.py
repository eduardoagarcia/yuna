"""Perception system for AI entities."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from yuna.ai.events import EntityLost, EntityPerceived
from yuna.ecs.component import Component
from yuna.ecs.system import System
from yuna.spatial.integration import Position
from yuna.types.vector import Vector2

if TYPE_CHECKING:
    from yuna.ecs.world import ECSWorld
    from yuna.events.bus import EventBus
    from yuna.types.identifiers import EntityID


@dataclass
class VisionCone(Component):
    """Vision perception for AI.

    Defines vision cone geometry for line-of-sight checks.

    Attributes:
        range: Maximum sight distance
        fov_angle: Field of view angle in radians (0-2π)
        direction: Direction looking in radians (0 = east, π/2 = north)
        update_interval: Ticks between perception updates (optimization)
    """

    range: float
    fov_angle: float = 1.57
    direction: float = 0.0
    update_interval: int = 5


@dataclass
class HearingRadius(Component):
    """Hearing perception for AI.

    Defines hearing radius for sound detection.

    Attributes:
        range: Maximum hearing distance
        update_interval: Ticks between perception updates (optimization)
    """

    range: float
    update_interval: int = 10


@dataclass
class PerceivedEntities(Component):
    """Entities currently perceived by AI.

    Updated by PerceptionSystem, read by AI logic.

    Attributes:
        visible: Entities in vision cone
        audible: Entities in hearing range
        last_update_tick: When last updated
        history: Recently perceived entities (for memory)
    """

    visible: set[EntityID] = field(default_factory=set)
    audible: set[EntityID] = field(default_factory=set)
    last_update_tick: int = 0
    history: dict[EntityID, Vector2] = field(default_factory=dict)

    def add_visible(self, entity_id: EntityID) -> bool:
        """Add entity to visible set.

        Args:
            entity_id: Entity that became visible

        Returns:
            True if newly added (wasn't visible before)
        """
        was_new = entity_id not in self.visible
        self.visible.add(entity_id)
        return was_new

    def remove_visible(self, entity_id: EntityID) -> bool:
        """Remove entity from visible set.

        Args:
            entity_id: Entity that became invisible

        Returns:
            True if was visible before removal
        """
        was_visible = entity_id in self.visible
        self.visible.discard(entity_id)
        return was_visible

    def add_audible(self, entity_id: EntityID) -> bool:
        """Add entity to audible set.

        Args:
            entity_id: Entity that became audible

        Returns:
            True if newly added (wasn't audible before)
        """
        was_new = entity_id not in self.audible
        self.audible.add(entity_id)
        return was_new

    def remove_audible(self, entity_id: EntityID) -> bool:
        """Remove entity from audible set.

        Args:
            entity_id: Entity that became inaudible

        Returns:
            True if was audible before removal
        """
        was_audible = entity_id in self.audible
        self.audible.discard(entity_id)
        return was_audible

    def update_history(self, entity_id: EntityID, position: Vector2) -> None:
        """Update perception history (last known position).

        Args:
            entity_id: Entity to remember
            position: Last known position
        """
        self.history[entity_id] = position


@dataclass
class Perceivable(Component):
    """Marks entity as perceivable by AI.

    Entities without this component are invisible to perception system.

    Attributes:
        visible: Can be seen (vision)
        audible: Can be heard (hearing)
        sight_priority: Priority for sight (higher = detected first)
        sound_priority: Priority for sound (higher = detected first)
    """

    visible: bool = True
    audible: bool = False
    sight_priority: int = 0
    sound_priority: int = 0


class PerceptionSystem(System):
    """Updates AI perception using spatial queries.

    Game-agnostic - checks geometry, doesn't know what entities mean.

    Responsibilities:
    - Find entities in vision cones (spatial queries + geometry)
    - Find entities in hearing range (spatial radius queries)
    - Update PerceivedEntities components
    - Emit perception events (EntityPerceived, EntityLost)

    Performance:
    - Uses spatial grid for efficient queries
    - Staggered updates (update_interval per entity)
    - Early exit optimizations

    Priority: 100 (Before AI decisions)
    """

    def __init__(
        self,
        spatial_grid: Any,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize perception system.

        Args:
            spatial_grid: Spatial grid for entity queries
            event_bus: Optional event bus for perception events
        """
        self._spatial_grid = spatial_grid
        self._event_bus = event_bus
        self._current_tick = 0

    @property
    def priority(self) -> int:
        """Get system execution priority.

        Returns:
            Priority value (lower executes first)
        """
        return 100

    def update(self, world: ECSWorld, delta_time: float) -> None:
        """Update perception for all AI entities.

        Args:
            world: ECS world
            delta_time: Time since last update
        """
        self._current_tick += 1

        self._update_vision(world=world)
        self._update_hearing(world=world)

    def _update_vision(self, world: ECSWorld) -> None:
        """Update vision perception for all AI entities.

        Args:
            world: ECS world
        """
        query = world.query().with_components(VisionCone, PerceivedEntities, Position)

        for entity_id, (vision_raw, perceived_raw, position_raw) in query.iterator():
            vision = cast(VisionCone, vision_raw)
            perceived = cast(PerceivedEntities, perceived_raw)
            position = cast(Position, position_raw)

            if self._current_tick % vision.update_interval != 0:
                continue

            previous_visible = set(perceived.visible)
            perceived.visible.clear()

            nearby_entities = self._spatial_grid.get_in_radius(
                position=position.position,
                radius=vision.range,
            )

            for target_id in nearby_entities:
                if target_id == entity_id:
                    continue

                perceivable_raw = world.get_component(
                    entity_id=target_id,
                    component_type=Perceivable,
                )

                if perceivable_raw is None:
                    continue

                perceivable = cast(Perceivable, perceivable_raw)

                if not perceivable.visible:
                    continue

                target_position_raw = world.get_component(
                    entity_id=target_id,
                    component_type=Position,
                )

                if target_position_raw is None:
                    continue

                target_position = cast(Position, target_position_raw)

                if self._is_in_vision_cone(
                    observer_pos=position.position,
                    observer_direction=vision.direction,
                    fov_angle=vision.fov_angle,
                    target_pos=target_position.position,
                    max_range=vision.range,
                ):
                    perceived.add_visible(entity_id=target_id)
                    perceived.update_history(
                        entity_id=target_id,
                        position=target_position.position,
                    )

                    if target_id not in previous_visible:
                        self._emit_perceived_event(
                            perceiver=entity_id,
                            perceived=target_id,
                            perception_type="vision",
                            position=target_position.position,
                        )

            for lost_id in previous_visible - perceived.visible:
                last_pos = perceived.history.get(lost_id, Vector2(x=0.0, y=0.0))
                self._emit_lost_event(
                    perceiver=entity_id,
                    lost=lost_id,
                    perception_type="vision",
                    last_known_position=last_pos,
                )

            perceived.last_update_tick = self._current_tick

    def _update_hearing(self, world: ECSWorld) -> None:
        """Update hearing perception for all AI entities.

        Args:
            world: ECS world
        """
        query = world.query().with_components(
            HearingRadius, PerceivedEntities, Position
        )

        for entity_id, (hearing_raw, perceived_raw, position_raw) in query.iterator():
            hearing = cast(HearingRadius, hearing_raw)
            perceived = cast(PerceivedEntities, perceived_raw)
            position = cast(Position, position_raw)

            if self._current_tick % hearing.update_interval != 0:
                continue

            previous_audible = set(perceived.audible)
            perceived.audible.clear()

            nearby_entities = self._spatial_grid.get_in_radius(
                position=position.position,
                radius=hearing.range,
            )

            for target_id in nearby_entities:
                if target_id == entity_id:
                    continue

                perceivable_raw = world.get_component(
                    entity_id=target_id,
                    component_type=Perceivable,
                )

                if perceivable_raw is None:
                    continue

                perceivable = cast(Perceivable, perceivable_raw)

                if not perceivable.audible:
                    continue

                target_position_raw = world.get_component(
                    entity_id=target_id,
                    component_type=Position,
                )

                if target_position_raw is None:
                    continue

                target_position = cast(Position, target_position_raw)

                distance = position.position.distance(other=target_position.position)

                if distance <= hearing.range:
                    perceived.add_audible(entity_id=target_id)
                    perceived.update_history(
                        entity_id=target_id,
                        position=target_position.position,
                    )

                    if target_id not in previous_audible:
                        self._emit_perceived_event(
                            perceiver=entity_id,
                            perceived=target_id,
                            perception_type="hearing",
                            position=target_position.position,
                        )

            for lost_id in previous_audible - perceived.audible:
                last_pos = perceived.history.get(lost_id, Vector2(x=0.0, y=0.0))
                self._emit_lost_event(
                    perceiver=entity_id,
                    lost=lost_id,
                    perception_type="hearing",
                    last_known_position=last_pos,
                )

            perceived.last_update_tick = self._current_tick

    @staticmethod
    def _is_in_vision_cone(
        observer_pos: Vector2,
        observer_direction: float,
        fov_angle: float,
        target_pos: Vector2,
        max_range: float,
    ) -> bool:
        """Check if target is in vision cone.

        Args:
            observer_pos: Observer position
            observer_direction: Observer look direction (radians)
            fov_angle: Field of view angle (radians)
            target_pos: Target position
            max_range: Maximum vision range

        Returns:
            True if target is in cone
        """
        to_target = target_pos.subtract(other=observer_pos)
        distance = to_target.magnitude()

        if distance == 0.0 or distance > max_range:
            return False

        angle_to_target = math.atan2(to_target.y, to_target.x)
        angle_diff = abs(angle_to_target - observer_direction)

        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi

        angle_diff = abs(angle_diff)

        return angle_diff <= fov_angle / 2

    def _emit_perceived_event(
        self,
        perceiver: EntityID,
        perceived: EntityID,
        perception_type: str,
        position: Vector2,
    ) -> None:
        """Emit EntityPerceived event.

        Args:
            perceiver: AI entity
            perceived: Perceived entity
            perception_type: Type (vision, hearing)
            position: Where perceived
        """
        if self._event_bus is not None:
            self._event_bus.emit(
                event=EntityPerceived(
                    timestamp=0.0,
                    tick=self._current_tick,
                    perceiver=perceiver,
                    perceived=perceived,
                    perception_type=perception_type,
                    position=position,
                )
            )

    def _emit_lost_event(
        self,
        perceiver: EntityID,
        lost: EntityID,
        perception_type: str,
        last_known_position: Vector2,
    ) -> None:
        """Emit EntityLost event.

        Args:
            perceiver: AI entity
            lost: Lost entity
            perception_type: Type (vision, hearing)
            last_known_position: Last position
        """
        if self._event_bus is not None:
            self._event_bus.emit(
                event=EntityLost(
                    timestamp=0.0,
                    tick=self._current_tick,
                    perceiver=perceiver,
                    lost=lost,
                    perception_type=perception_type,
                    last_known_position=last_known_position,
                )
            )
