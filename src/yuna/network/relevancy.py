"""Relevancy strategies for interest management."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from yuna.types.identifiers import EntityID


class RelevancyStrategy(Protocol):
    """Protocol for relevancy strategies.

    Relevancy strategies determine which entities should be replicated
    to which observers based on various criteria (distance, ownership, etc).
    """

    def is_relevant(
        self,
        entity_id: EntityID,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> bool:
        """Check if entity is relevant to observer.

        Args:
            entity_id: Entity to check
            observer_id: Observer to check against
            entities: All entities with their components

        Returns:
            True if entity should be replicated to observer
        """
        ...  # pragma: no cover

    def get_relevant_entities(
        self,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> set[EntityID]:
        """Get all entities relevant to observer.

        Args:
            observer_id: Observer to get relevant entities for
            entities: All entities with their components

        Returns:
            Set of entity IDs relevant to observer
        """
        ...  # pragma: no cover


class AlwaysRelevant:
    """All entities are always relevant.

    Use for small games where all entities should be replicated to all clients.

    Usage:
        strategy = AlwaysRelevant()
        relevant = strategy.is_relevant(entity_id, observer_id, entities)
    """

    @staticmethod
    def is_relevant(
        entity_id: EntityID,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> bool:
        """All entities are relevant.

        Args:
            entity_id: Entity to check
            observer_id: Observer to check against
            entities: All entities with their components

        Returns:
            Always True
        """
        return True

    @staticmethod
    def get_relevant_entities(
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> set[EntityID]:
        """Get all entities.

        Args:
            observer_id: Observer to get relevant entities for
            entities: All entities with their components

        Returns:
            All entity IDs
        """
        return set(entities.keys())


class DistanceRelevancy:
    """Distance-based relevancy (MMO-style area of interest).

    Entities are relevant if they are within max_distance of the observer.
    Requires Position component with x and y fields.

    Usage:
        strategy = DistanceRelevancy(max_distance=100.0)
        relevant = strategy.is_relevant(entity_id, observer_id, entities)
    """

    def __init__(self, max_distance: float) -> None:
        """Initialize distance-based relevancy.

        Args:
            max_distance: Maximum distance for relevancy
        """
        self.max_distance = max_distance

    def is_relevant(
        self,
        entity_id: EntityID,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> bool:
        """Check if entity is within distance of observer.

        Args:
            entity_id: Entity to check
            observer_id: Observer to check against
            entities: All entities with their components

        Returns:
            True if within max_distance
        """
        if entity_id not in entities or observer_id not in entities:
            return False

        entity_components = entities[entity_id]
        observer_components = entities[observer_id]

        entity_position = entity_components.get("Position")
        observer_position = observer_components.get("Position")

        if entity_position is None or observer_position is None:
            return False

        dx: float = entity_position["x"] - observer_position["x"]
        dy: float = entity_position["y"] - observer_position["y"]
        distance: float = (dx * dx + dy * dy) ** 0.5

        return bool(distance <= self.max_distance)

    def get_relevant_entities(
        self,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> set[EntityID]:
        """Get all entities within distance of observer.

        Args:
            observer_id: Observer to get relevant entities for
            entities: All entities with their components

        Returns:
            Set of entity IDs within max_distance
        """
        relevant: set[EntityID] = set()
        for entity_id in entities:
            if self.is_relevant(
                entity_id=entity_id,
                observer_id=observer_id,
                entities=entities,
            ):
                relevant.add(entity_id)
        return relevant


class OwnershipRelevancy:
    """Ownership-based relevancy with nearby entities.

    Entities are relevant if:
    1. Observer owns the entity (has Owner component matching observer_id), OR
    2. Entity is within max_distance of observer

    Usage:
        strategy = OwnershipRelevancy(max_distance=50.0)
        relevant = strategy.is_relevant(entity_id, observer_id, entities)
    """

    def __init__(self, max_distance: float = 50.0) -> None:
        """Initialize ownership-based relevancy.

        Args:
            max_distance: Maximum distance for nearby entities
        """
        self.max_distance = max_distance
        self._distance_strategy = DistanceRelevancy(max_distance=max_distance)

    def is_relevant(
        self,
        entity_id: EntityID,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> bool:
        """Check if entity is owned by or near observer.

        Args:
            entity_id: Entity to check
            observer_id: Observer to check against
            entities: All entities with their components

        Returns:
            True if owned or within max_distance
        """
        if entity_id not in entities:
            return False

        entity_components = entities[entity_id]
        owner = entity_components.get("Owner")

        if owner is not None and owner.get("id") == observer_id:
            return True

        return self._distance_strategy.is_relevant(
            entity_id=entity_id,
            observer_id=observer_id,
            entities=entities,
        )

    def get_relevant_entities(
        self,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> set[EntityID]:
        """Get all entities owned by or near observer.

        Args:
            observer_id: Observer to get relevant entities for
            entities: All entities with their components

        Returns:
            Set of entity IDs owned or within max_distance
        """
        relevant: set[EntityID] = set()
        for entity_id in entities:
            if self.is_relevant(
                entity_id=entity_id,
                observer_id=observer_id,
                entities=entities,
            ):
                relevant.add(entity_id)
        return relevant


class CustomRelevancy:
    """Custom relevancy using user-provided predicate.

    Allows arbitrary relevancy logic via a predicate function.

    Usage:
        def is_in_same_team(entity_id, observer_id, entities):
            entity_team = entities[entity_id].get("Team", {}).get("id")
            observer_team = entities[observer_id].get("Team", {}).get("id")
            return entity_team == observer_team

        strategy = CustomRelevancy(predicate=is_in_same_team)
        relevant = strategy.is_relevant(entity_id, observer_id, entities)
    """

    def __init__(
        self,
        predicate: Callable[[EntityID, EntityID, dict[EntityID, dict[str, Any]]], bool],
    ) -> None:
        """Initialize custom relevancy.

        Args:
            predicate: Function to determine relevancy
        """
        self.predicate = predicate

    def is_relevant(
        self,
        entity_id: EntityID,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> bool:
        """Check if entity is relevant using custom predicate.

        Args:
            entity_id: Entity to check
            observer_id: Observer to check against
            entities: All entities with their components

        Returns:
            Result of predicate function
        """
        return self.predicate(entity_id, observer_id, entities)

    def get_relevant_entities(
        self,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> set[EntityID]:
        """Get all entities matching custom predicate.

        Args:
            observer_id: Observer to get relevant entities for
            entities: All entities with their components

        Returns:
            Set of entity IDs matching predicate
        """
        relevant: set[EntityID] = set()
        for entity_id in entities:
            if self.is_relevant(
                entity_id=entity_id,
                observer_id=observer_id,
                entities=entities,
            ):
                relevant.add(entity_id)
        return relevant
