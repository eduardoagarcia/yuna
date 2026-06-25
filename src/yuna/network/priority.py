"""Priority calculation for network replication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from yuna.types.identifiers import EntityID

STATIC_ENTITY_MOVEMENT_THRESHOLD = 0.01


@dataclass
class PriorityWeights:
    """Configurable weights for priority calculation."""

    distance: float = 1.0
    movement: float = 0.5
    importance: float = 2.0


@dataclass
class EntityPriority:
    """Entity with calculated priority score."""

    entity_id: EntityID
    priority: float


class PriorityCalculator:
    """Calculate entity priority for network replication.

    Responsibilities:
    - Calculate priority based on distance, movement, and importance
    - Support configurable priority weights
    - Apply priority decay for static entities
    - Normalize priorities to 0-1 range

    Priority factors:
    - Distance: Closer entities have higher priority (inverse distance)
    - Movement: Moving entities have higher priority (velocity magnitude)
    - Importance: Tagged entities (critical, player, threat) have higher priority
    - Decay: Static entities decay over time to reduce bandwidth

    Usage:
        calculator = PriorityCalculator(
            weights=PriorityWeights(distance=1.0, movement=0.5, importance=2.0),
            decay_rate=0.95,
        )
        priorities = calculator.calculate_priorities(
            observer_id=player1,
            entity_ids={entity1, entity2},
            entities=world.entities,
        )
    """

    def __init__(
        self,
        weights: PriorityWeights | None = None,
        decay_rate: float = 0.95,
        max_distance: float = 100.0,
    ) -> None:
        """Initialize priority calculator.

        Args:
            weights: Priority weights for each factor
            decay_rate: Decay factor for static entities (0.0-1.0)
            max_distance: Maximum distance for normalization
        """
        self.weights = weights or PriorityWeights()
        self.decay_rate = decay_rate
        self.max_distance = max_distance
        self._static_decay: dict[EntityID, float] = {}

    def calculate_priorities(
        self,
        observer_id: EntityID,
        entity_ids: set[EntityID],
        entities: dict[EntityID, dict[str, Any]],
    ) -> list[EntityPriority]:
        """Calculate priorities for all entities.

        Args:
            observer_id: Observer to calculate priorities for
            entity_ids: Entity IDs to prioritize
            entities: All entities with their components

        Returns:
            List of EntityPriority sorted by priority (highest first)
        """
        priorities: list[EntityPriority] = []

        for entity_id in entity_ids:
            priority = self.calculate_priority(
                entity_id=entity_id,
                observer_id=observer_id,
                entities=entities,
            )
            priorities.append(EntityPriority(entity_id=entity_id, priority=priority))

        return sorted(priorities, key=lambda p: p.priority, reverse=True)

    def calculate_priority(
        self,
        entity_id: EntityID,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> float:
        """Calculate priority for a single entity.

        Args:
            entity_id: Entity to calculate priority for
            observer_id: Observer to calculate priority against
            entities: All entities with their components

        Returns:
            Priority score (higher = more important)
        """
        if entity_id not in entities or observer_id not in entities:
            return 0.0

        distance_priority = self._calculate_distance_priority(
            entity_id=entity_id,
            observer_id=observer_id,
            entities=entities,
        )
        movement_priority = self._calculate_movement_priority(
            entity_id=entity_id,
            entities=entities,
        )
        importance_priority = self._calculate_importance_priority(
            entity_id=entity_id,
            entities=entities,
        )

        weighted_priority = (
            distance_priority * self.weights.distance
            + movement_priority * self.weights.movement
            + importance_priority * self.weights.importance
        )

        if movement_priority < STATIC_ENTITY_MOVEMENT_THRESHOLD:
            decay = self._get_static_decay(entity_id=entity_id)
            weighted_priority *= decay

        return weighted_priority

    def _calculate_distance_priority(
        self,
        entity_id: EntityID,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> float:
        """Calculate priority based on distance (closer = higher).

        Args:
            entity_id: Entity to calculate for
            observer_id: Observer to calculate against
            entities: All entities with their components

        Returns:
            Distance priority (0.0-1.0, closer = higher)
        """
        entity_components = entities.get(entity_id, {})
        observer_components = entities.get(observer_id, {})

        entity_position = entity_components.get("Position")
        observer_position = observer_components.get("Position")

        if entity_position is None or observer_position is None:
            return 0.0

        dx: float = entity_position["x"] - observer_position["x"]
        dy: float = entity_position["y"] - observer_position["y"]
        distance: float = (dx * dx + dy * dy) ** 0.5

        normalized_distance = min(distance / self.max_distance, 1.0)
        return 1.0 - normalized_distance

    @staticmethod
    def _calculate_movement_priority(
        entity_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> float:
        """Calculate priority based on movement (faster = higher).

        Args:
            entity_id: Entity to calculate for
            entities: All entities with their components

        Returns:
            Movement priority (0.0-1.0, faster = higher)
        """
        entity_components = entities.get(entity_id, {})
        velocity = entity_components.get("Velocity")

        if velocity is None:
            return 0.0

        vx: float = velocity.get("x", 0.0)
        vy: float = velocity.get("y", 0.0)
        speed: float = (vx * vx + vy * vy) ** 0.5

        max_speed = 10.0
        return min(speed / max_speed, 1.0)

    @staticmethod
    def _calculate_importance_priority(
        entity_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> float:
        """Calculate priority based on importance tags.

        Args:
            entity_id: Entity to calculate for
            entities: All entities with their components

        Returns:
            Importance priority (0.0-1.0, critical = 1.0)
        """
        entity_components = entities.get(entity_id, {})
        importance = entity_components.get("Importance")

        if importance is None:
            return 0.0

        tag = importance.get("tag", "normal")

        if tag == "critical":
            return 1.0
        if tag == "high":
            return 0.75
        if tag == "normal":
            return 0.5
        if tag == "low":
            return 0.25
        return 0.0

    def _get_static_decay(self, entity_id: EntityID) -> float:
        """Get or calculate decay factor for static entity.

        Args:
            entity_id: Entity to get decay for

        Returns:
            Decay multiplier (0.0-1.0)
        """
        if entity_id not in self._static_decay:
            self._static_decay[entity_id] = 1.0
        else:
            self._static_decay[entity_id] *= self.decay_rate

        return self._static_decay[entity_id]

    def reset_decay(self, entity_id: EntityID) -> None:
        """Reset decay for entity (call when entity starts moving).

        Args:
            entity_id: Entity to reset decay for
        """
        self._static_decay.pop(entity_id, None)

    def clear_decay(self) -> None:
        """Clear all decay tracking."""
        self._static_decay.clear()
