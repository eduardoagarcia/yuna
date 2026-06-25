"""Interest management for network replication."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from yuna.exceptions import StateError
from yuna.network.budget import BandwidthBudget
from yuna.network.priority import EntityPriority, PriorityCalculator
from yuna.network.relevancy import RelevancyStrategy
from yuna.types.identifiers import EntityID


class InterestManager:
    """Manages area of interest for network replication.

    Responsibilities:
    - Track which entities are relevant to which observers
    - Calculate interest sets based on relevancy strategies
    - Optimize recalculation with dirty tracking
    - Support entity creation/destruction events

    Usage:
        manager = InterestManager()
        manager.register_observer(
            observer_id=player1,
            strategy=DistanceRelevancy(100.0),
        )
        manager.update_interests(entities=world.entities)
        interest_set = manager.get_interest_set(observer_id=player1)
    """

    def __init__(
        self,
        priority_calculator: PriorityCalculator | None = None,
        bandwidth_budget: BandwidthBudget | None = None,
    ) -> None:
        """Initialize interest manager.

        Args:
            priority_calculator: Optional priority calculator for entity prioritization
            bandwidth_budget: Optional bandwidth budget manager for budget enforcement
        """
        self._observers: dict[EntityID, RelevancyStrategy] = {}
        self._interest_sets: dict[EntityID, set[EntityID]] = {}
        self._entity_observers: dict[EntityID, set[EntityID]] = {}
        self._dirty_observers: set[EntityID] = set()
        self._priority_calculator = priority_calculator
        self._bandwidth_budget = bandwidth_budget

    def register_observer(
        self,
        observer_id: EntityID,
        strategy: RelevancyStrategy,
    ) -> None:
        """Register an observer with a relevancy strategy.

        Args:
            observer_id: Observer to register
            strategy: Relevancy strategy for this observer
        """
        self._observers[observer_id] = strategy
        self._interest_sets[observer_id] = set()
        self._dirty_observers.add(observer_id)

    def unregister_observer(self, observer_id: EntityID) -> None:
        """Unregister an observer.

        Args:
            observer_id: Observer to unregister
        """
        if observer_id not in self._observers:
            return

        old_interest_set = self._interest_sets.get(observer_id, set())
        for entity_id in old_interest_set:
            if entity_id in self._entity_observers:
                self._entity_observers[entity_id].discard(observer_id)
                if not self._entity_observers[entity_id]:
                    del self._entity_observers[entity_id]

        del self._observers[observer_id]
        del self._interest_sets[observer_id]
        self._dirty_observers.discard(observer_id)

    def mark_dirty(self, observer_id: EntityID) -> None:
        """Mark an observer as dirty for recalculation.

        Args:
            observer_id: Observer to mark dirty
        """
        if observer_id in self._observers:
            self._dirty_observers.add(observer_id)

    def mark_all_dirty(self) -> None:
        """Mark all observers as dirty for recalculation."""
        self._dirty_observers = set(self._observers.keys())

    def update_interests(self, entities: dict[EntityID, dict[str, Any]]) -> None:
        """Recalculate interest sets for dirty observers.

        Args:
            entities: All entities with their components
        """
        for observer_id in list(self._dirty_observers):
            if observer_id not in self._observers:
                self._dirty_observers.discard(observer_id)
                continue

            strategy = self._observers[observer_id]
            old_interest_set = self._interest_sets.get(observer_id, set())
            new_interest_set = strategy.get_relevant_entities(
                observer_id=observer_id,
                entities=entities,
            )

            removed_entities = old_interest_set - new_interest_set
            for entity_id in removed_entities:
                if entity_id in self._entity_observers:
                    self._entity_observers[entity_id].discard(observer_id)
                    if not self._entity_observers[entity_id]:
                        del self._entity_observers[entity_id]

            added_entities = new_interest_set - old_interest_set
            for entity_id in added_entities:
                if entity_id not in self._entity_observers:
                    self._entity_observers[entity_id] = set()
                self._entity_observers[entity_id].add(observer_id)

            self._interest_sets[observer_id] = new_interest_set

        self._dirty_observers.clear()

    def get_interest_set(self, observer_id: EntityID) -> set[EntityID]:
        """Get entities relevant to observer.

        Args:
            observer_id: Observer to get interest set for

        Returns:
            Set of entity IDs to replicate to observer
        """
        return self._interest_sets.get(observer_id, set()).copy()

    def get_observers_for_entity(self, entity_id: EntityID) -> set[EntityID]:
        """Get observers that can see an entity.

        Args:
            entity_id: Entity to get observers for

        Returns:
            Set of observer IDs that see this entity
        """
        return self._entity_observers.get(entity_id, set()).copy()

    def on_entity_created(
        self,
        entity_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> None:
        """Handle entity creation event.

        Args:
            entity_id: Newly created entity
            entities: All entities with their components
        """
        for observer_id, strategy in self._observers.items():
            if strategy.is_relevant(
                entity_id=entity_id,
                observer_id=observer_id,
                entities=entities,
            ):
                self._interest_sets[observer_id].add(entity_id)
                if entity_id not in self._entity_observers:
                    self._entity_observers[entity_id] = set()
                self._entity_observers[entity_id].add(observer_id)

    def on_entity_destroyed(self, entity_id: EntityID) -> None:
        """Handle entity destruction event.

        Args:
            entity_id: Destroyed entity
        """
        if entity_id in self._entity_observers:
            observers = self._entity_observers[entity_id].copy()
            for observer_id in observers:
                if observer_id in self._interest_sets:
                    self._interest_sets[observer_id].discard(entity_id)
            del self._entity_observers[entity_id]

        if entity_id in self._observers:
            self.unregister_observer(observer_id=entity_id)

    def get_prioritized_entities(
        self,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
    ) -> list[EntityPriority]:
        """Get entities relevant to observer sorted by priority.

        Args:
            observer_id: Observer to get prioritized entities for
            entities: All entities with their components

        Returns:
            List of EntityPriority sorted by priority (highest first)

        Raises:
            StateError: If no priority calculator is configured
        """
        if self._priority_calculator is None:
            raise StateError(
                operation="get_prioritized_entities",
                reason="No priority calculator configured",
            )

        interest_set = self.get_interest_set(observer_id=observer_id)
        return self._priority_calculator.calculate_priorities(
            observer_id=observer_id,
            entity_ids=interest_set,
            entities=entities,
        )

    def get_entities_within_budget(
        self,
        observer_id: EntityID,
        entities: dict[EntityID, dict[str, Any]],
        size_calculator: Callable[[EntityID, dict[EntityID, dict[str, Any]]], int],
        critical_predicate: (
            Callable[[EntityID, dict[EntityID, dict[str, Any]]], bool] | None
        ) = None,
    ) -> list[EntityID]:
        """Get entities within bandwidth budget, prioritized.

        Args:
            observer_id: Observer to get entities for
            entities: All entities with their components
            size_calculator: Function to calculate entity size in bytes
            critical_predicate: Optional predicate to identify critical entities

        Returns:
            List of entity IDs within budget, sorted by priority

        Raises:
            StateError: If no priority calculator or budget is configured
        """
        if self._priority_calculator is None:
            raise StateError(
                operation="get_entities_within_budget",
                reason="No priority calculator configured",
            )
        if self._bandwidth_budget is None:
            raise StateError(
                operation="get_entities_within_budget",
                reason="No bandwidth budget configured",
            )

        prioritized = self.get_prioritized_entities(
            observer_id=observer_id,
            entities=entities,
        )

        result: list[EntityID] = []
        critical_entities: list[EntityID] = []

        if critical_predicate is not None:
            for entity_priority in prioritized:
                entity_id = entity_priority.entity_id
                if critical_predicate(entity_id, entities):
                    critical_entities.append(entity_id)
                    size = size_calculator(entity_id, entities)
                    self._bandwidth_budget.spend(
                        observer_id=observer_id, bytes_spent=size
                    )

        for entity_priority in prioritized:
            entity_id = entity_priority.entity_id

            if entity_id in critical_entities:
                result.append(entity_id)
                continue

            size = size_calculator(entity_id, entities)

            if self._bandwidth_budget.can_afford(
                observer_id=observer_id,
                bytes_needed=size,
            ):
                self._bandwidth_budget.spend(observer_id=observer_id, bytes_spent=size)
                result.append(entity_id)

        return result
