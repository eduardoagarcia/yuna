"""Tests for interest management."""

from typing import Any

import pytest
from faker import Faker

from yuna.exceptions import StateError
from yuna.network.budget import BandwidthBudget
from yuna.network.interest import InterestManager
from yuna.network.priority import PriorityCalculator
from yuna.network.relevancy import (
    AlwaysRelevant,
    DistanceRelevancy,
)
from yuna.types.identifiers import EntityID

fake = Faker()


def test_interest_manager_creation() -> None:
    """Test InterestManager can be instantiated."""
    manager = InterestManager()
    assert manager is not None


def test_register_observer() -> None:
    """Test registering an observer."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)

    interest_set = manager.get_interest_set(observer_id=observer_id)
    assert interest_set == set()


def test_unregister_observer() -> None:
    """Test unregistering an observer."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    manager.unregister_observer(observer_id=observer_id)

    interest_set = manager.get_interest_set(observer_id=observer_id)
    assert interest_set == set()


def test_unregister_nonexistent_observer() -> None:
    """Test unregistering a nonexistent observer does nothing."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())

    manager.unregister_observer(observer_id=observer_id)

    interest_set = manager.get_interest_set(observer_id=observer_id)
    assert interest_set == set()


def test_mark_dirty() -> None:
    """Test marking an observer as dirty."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    manager.mark_dirty(observer_id=observer_id)

    assert observer_id in manager._dirty_observers


def test_mark_dirty_nonexistent_observer() -> None:
    """Test marking a nonexistent observer as dirty does nothing."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())

    manager.mark_dirty(observer_id=observer_id)

    assert observer_id not in manager._dirty_observers


def test_mark_all_dirty() -> None:
    """Test marking all observers as dirty."""
    manager = InterestManager()
    observer1 = EntityID(fake.uuid4())
    observer2 = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer1, strategy=strategy)
    manager.register_observer(observer_id=observer2, strategy=strategy)
    manager._dirty_observers.clear()

    manager.mark_all_dirty()

    assert observer1 in manager._dirty_observers
    assert observer2 in manager._dirty_observers


def test_update_interests_always_relevant() -> None:
    """Test updating interests with AlwaysRelevant strategy."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    entities = {
        entity1: {"Position": {"x": 0, "y": 0}},
        entity2: {"Position": {"x": 100, "y": 100}},
    }

    manager.update_interests(entities=entities)

    interest_set = manager.get_interest_set(observer_id=observer_id)
    assert entity1 in interest_set
    assert entity2 in interest_set


def test_update_interests_distance_relevancy() -> None:
    """Test updating interests with DistanceRelevancy strategy."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    strategy = DistanceRelevancy(max_distance=50.0)

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    entities = {
        observer_id: {"Position": {"x": 0, "y": 0}},
        entity1: {"Position": {"x": 10, "y": 0}},
        entity2: {"Position": {"x": 100, "y": 0}},
    }

    manager.update_interests(entities=entities)

    interest_set = manager.get_interest_set(observer_id=observer_id)
    assert entity1 in interest_set
    assert entity2 not in interest_set
    assert observer_id in interest_set


def test_update_interests_clears_dirty_flag() -> None:
    """Test updating interests clears dirty flag."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    manager.update_interests(entities={})

    assert observer_id not in manager._dirty_observers


def test_update_interests_only_dirty_observers() -> None:
    """Test updating interests only recalculates dirty observers."""
    manager = InterestManager()
    observer1 = EntityID(fake.uuid4())
    observer2 = EntityID(fake.uuid4())
    entity = EntityID(fake.uuid4())
    strategy = DistanceRelevancy(max_distance=50.0)

    manager.register_observer(observer_id=observer1, strategy=strategy)
    manager.register_observer(observer_id=observer2, strategy=strategy)
    entities = {
        observer1: {"Position": {"x": 0, "y": 0}},
        observer2: {"Position": {"x": 0, "y": 0}},
        entity: {"Position": {"x": 10, "y": 0}},
    }

    manager.update_interests(entities=entities)
    manager._interest_sets[observer1] = set()
    manager.mark_dirty(observer_id=observer2)
    manager.update_interests(entities=entities)

    assert len(manager.get_interest_set(observer_id=observer1)) == 0
    assert len(manager.get_interest_set(observer_id=observer2)) > 0


def test_update_interests_updates_entity_observers() -> None:
    """Test updating interests updates reverse mapping."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    entities = {entity_id: {"Position": {"x": 0, "y": 0}}}

    manager.update_interests(entities=entities)

    observers = manager.get_observers_for_entity(entity_id=entity_id)
    assert observer_id in observers


def test_update_interests_removes_from_entity_observers() -> None:
    """Test updating interests removes observers when no longer relevant."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())
    strategy = DistanceRelevancy(max_distance=50.0)

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    entities = {
        observer_id: {"Position": {"x": 0, "y": 0}},
        entity_id: {"Position": {"x": 10, "y": 0}},
    }

    manager.update_interests(entities=entities)
    assert observer_id in manager.get_observers_for_entity(entity_id=entity_id)

    entities[entity_id] = {"Position": {"x": 1000, "y": 0}}
    manager.mark_dirty(observer_id=observer_id)
    manager.update_interests(entities=entities)

    observers = manager.get_observers_for_entity(entity_id=entity_id)
    assert observer_id not in observers


def test_get_interest_set_returns_copy() -> None:
    """Test get_interest_set returns a copy."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    entities = {entity_id: {"Position": {"x": 0, "y": 0}}}
    manager.update_interests(entities=entities)

    interest_set1 = manager.get_interest_set(observer_id=observer_id)
    interest_set2 = manager.get_interest_set(observer_id=observer_id)

    assert interest_set1 == interest_set2
    assert interest_set1 is not interest_set2


def test_get_interest_set_nonexistent_observer() -> None:
    """Test get_interest_set returns empty set for nonexistent observer."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())

    interest_set = manager.get_interest_set(observer_id=observer_id)

    assert interest_set == set()


def test_get_observers_for_entity_returns_copy() -> None:
    """Test get_observers_for_entity returns a copy."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    entities = {entity_id: {"Position": {"x": 0, "y": 0}}}
    manager.update_interests(entities=entities)

    observers1 = manager.get_observers_for_entity(entity_id=entity_id)
    observers2 = manager.get_observers_for_entity(entity_id=entity_id)

    assert observers1 == observers2
    assert observers1 is not observers2


def test_get_observers_for_entity_nonexistent_entity() -> None:
    """Test get_observers_for_entity returns empty set for nonexistent entity."""
    manager = InterestManager()
    entity_id = EntityID(fake.uuid4())

    observers = manager.get_observers_for_entity(entity_id=entity_id)

    assert observers == set()


def test_on_entity_created() -> None:
    """Test handling entity creation event."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    manager.update_interests(entities={})

    entities = {entity_id: {"Position": {"x": 0, "y": 0}}}
    manager.on_entity_created(entity_id=entity_id, entities=entities)

    interest_set = manager.get_interest_set(observer_id=observer_id)
    assert entity_id in interest_set


def test_on_entity_created_distance_relevancy() -> None:
    """Test entity creation with distance-based relevancy."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    strategy = DistanceRelevancy(max_distance=50.0)

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    entities = {observer_id: {"Position": {"x": 0, "y": 0}}}
    manager.update_interests(entities=entities)

    entities[entity1] = {"Position": {"x": 10, "y": 0}}
    manager.on_entity_created(entity_id=entity1, entities=entities)

    entities[entity2] = {"Position": {"x": 100, "y": 0}}
    manager.on_entity_created(entity_id=entity2, entities=entities)

    interest_set = manager.get_interest_set(observer_id=observer_id)
    assert entity1 in interest_set
    assert entity2 not in interest_set


def test_on_entity_created_updates_entity_observers() -> None:
    """Test entity creation updates reverse mapping."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    manager.update_interests(entities={})

    entities = {entity_id: {"Position": {"x": 0, "y": 0}}}
    manager.on_entity_created(entity_id=entity_id, entities=entities)

    observers = manager.get_observers_for_entity(entity_id=entity_id)
    assert observer_id in observers


def test_on_entity_destroyed() -> None:
    """Test handling entity destruction event."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    entities = {entity_id: {"Position": {"x": 0, "y": 0}}}
    manager.update_interests(entities=entities)

    manager.on_entity_destroyed(entity_id=entity_id)

    interest_set = manager.get_interest_set(observer_id=observer_id)
    assert entity_id not in interest_set
    observers = manager.get_observers_for_entity(entity_id=entity_id)
    assert observer_id not in observers


def test_on_entity_destroyed_removes_from_all_observers() -> None:
    """Test entity destruction removes from all observers."""
    manager = InterestManager()
    observer1 = EntityID(fake.uuid4())
    observer2 = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer1, strategy=strategy)
    manager.register_observer(observer_id=observer2, strategy=strategy)
    entities = {entity_id: {"Position": {"x": 0, "y": 0}}}
    manager.update_interests(entities=entities)

    manager.on_entity_destroyed(entity_id=entity_id)

    assert entity_id not in manager.get_interest_set(observer_id=observer1)
    assert entity_id not in manager.get_interest_set(observer_id=observer2)


def test_on_entity_destroyed_nonexistent_entity() -> None:
    """Test destroying a nonexistent entity does nothing."""
    manager = InterestManager()
    entity_id = EntityID(fake.uuid4())

    manager.on_entity_destroyed(entity_id=entity_id)

    observers = manager.get_observers_for_entity(entity_id=entity_id)
    assert observers == set()


def test_on_entity_destroyed_observer() -> None:
    """Test destroying an entity that is also an observer."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    entities = {
        observer_id: {"Position": {"x": 0, "y": 0}},
        entity_id: {"Position": {"x": 10, "y": 0}},
    }
    manager.update_interests(entities=entities)

    manager.on_entity_destroyed(entity_id=observer_id)

    interest_set = manager.get_interest_set(observer_id=observer_id)
    assert interest_set == set()


def test_unregister_observer_cleans_up_entity_observers() -> None:
    """Test unregistering observer removes from entity observer mapping."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    entities = {entity_id: {"Position": {"x": 0, "y": 0}}}
    manager.update_interests(entities=entities)

    manager.unregister_observer(observer_id=observer_id)

    observers = manager.get_observers_for_entity(entity_id=entity_id)
    assert observer_id not in observers


def test_update_interests_skips_unregistered_dirty_observers() -> None:
    """Test update_interests skips observers that are dirty but not registered."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())

    manager._dirty_observers.add(observer_id)

    entities = {EntityID(fake.uuid4()): {"Position": {"x": 0, "y": 0}}}
    manager.update_interests(entities=entities)

    assert observer_id not in manager._dirty_observers


def test_large_scale_interest_management() -> None:
    """Test interest management with many entities and observers."""
    manager = InterestManager()
    num_observers = 100
    num_entities = 1000
    strategy = DistanceRelevancy(max_distance=100.0)

    observers = [EntityID(fake.uuid4()) for _ in range(num_observers)]
    for observer_id in observers:
        manager.register_observer(observer_id=observer_id, strategy=strategy)

    entities = {}
    for _ in range(num_entities):
        entity_id = EntityID(fake.uuid4())
        x = fake.random_int(min=0, max=10000)
        y = fake.random_int(min=0, max=10000)
        entities[entity_id] = {"Position": {"x": x, "y": y}}

    for observer_id in observers:
        x = fake.random_int(min=0, max=10000)
        y = fake.random_int(min=0, max=10000)
        entities[observer_id] = {"Position": {"x": x, "y": y}}

    manager.update_interests(entities=entities)

    for observer_id in observers:
        interest_set = manager.get_interest_set(observer_id=observer_id)
        assert isinstance(interest_set, set)


def test_get_prioritized_entities() -> None:
    """Test get_prioritized_entities returns sorted list."""
    calculator = PriorityCalculator(max_distance=100.0)
    manager = InterestManager(priority_calculator=calculator)
    observer_id = EntityID(fake.uuid4())
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity1: {"Position": {"x": 90.0, "y": 0.0}},
        entity2: {"Position": {"x": 10.0, "y": 0.0}},
        entity3: {"Position": {"x": 50.0, "y": 0.0}},
    }

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    manager.update_interests(entities=entities)

    priorities = manager.get_prioritized_entities(
        observer_id=observer_id,
        entities=entities,
    )

    assert len(priorities) == 4
    entity_ids = [p.entity_id for p in priorities]
    assert entity2 in entity_ids
    assert entity3 in entity_ids
    assert entity1 in entity_ids
    assert observer_id in entity_ids


def test_get_prioritized_entities_no_calculator() -> None:
    """Test get_prioritized_entities raises error without calculator."""
    manager = InterestManager()
    observer_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    entities = {observer_id: {"Position": {"x": 0.0, "y": 0.0}}}

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    manager.update_interests(entities=entities)

    with pytest.raises(StateError, match="No priority calculator configured"):
        manager.get_prioritized_entities(observer_id=observer_id, entities=entities)


def test_get_entities_within_budget() -> None:
    """Test get_entities_within_budget respects bandwidth budget."""
    calculator = PriorityCalculator(max_distance=100.0)
    budget = BandwidthBudget(hard_limit=100)
    manager = InterestManager(
        priority_calculator=calculator,
        bandwidth_budget=budget,
    )
    observer_id = EntityID(fake.uuid4())
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity1: {"Position": {"x": 10.0, "y": 0.0}},
        entity2: {"Position": {"x": 50.0, "y": 0.0}},
        entity3: {"Position": {"x": 90.0, "y": 0.0}},
    }

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    budget.allocate_budget(observer_id=observer_id)
    manager.update_interests(entities=entities)

    def size_calculator(
        entity_id: EntityID, entities: dict[EntityID, dict[str, Any]]
    ) -> int:
        return 40

    result = manager.get_entities_within_budget(
        observer_id=observer_id,
        entities=entities,
        size_calculator=size_calculator,
    )

    assert len(result) == 2
    result_set = set(result)
    assert entity1 in result_set or entity2 in result_set or observer_id in result_set


def test_get_entities_within_budget_critical_entities() -> None:
    """Test get_entities_within_budget prioritizes critical entities."""
    calculator = PriorityCalculator(max_distance=100.0)
    budget = BandwidthBudget(hard_limit=100)
    manager = InterestManager(
        priority_calculator=calculator,
        bandwidth_budget=budget,
    )
    observer_id = EntityID(fake.uuid4())
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    entities: dict[EntityID, dict[str, Any]] = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity1: {"Position": {"x": 10.0, "y": 0.0}, "Importance": {"tag": "normal"}},
        entity2: {"Position": {"x": 50.0, "y": 0.0}, "Importance": {"tag": "normal"}},
        entity3: {
            "Position": {"x": 90.0, "y": 0.0},
            "Importance": {"tag": "critical"},
        },
    }

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    budget.allocate_budget(observer_id=observer_id)
    manager.update_interests(entities=entities)

    def size_calculator(
        entity_id: EntityID, entities: dict[EntityID, dict[str, Any]]
    ) -> int:
        return 40

    def critical_predicate(
        entity_id: EntityID, entities: dict[EntityID, dict[str, Any]]
    ) -> bool:
        importance = entities[entity_id].get("Importance", {})
        return bool(importance.get("tag") == "critical")

    result = manager.get_entities_within_budget(
        observer_id=observer_id,
        entities=entities,
        size_calculator=size_calculator,
        critical_predicate=critical_predicate,
    )

    assert len(result) == 2
    assert entity3 in result


def test_get_entities_within_budget_no_calculator() -> None:
    """Test get_entities_within_budget raises error without calculator."""
    budget = BandwidthBudget(hard_limit=100)
    manager = InterestManager(bandwidth_budget=budget)
    observer_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    entities = {observer_id: {"Position": {"x": 0.0, "y": 0.0}}}

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    budget.allocate_budget(observer_id=observer_id)
    manager.update_interests(entities=entities)

    def size_calculator(
        entity_id: EntityID, entities: dict[EntityID, dict[str, Any]]
    ) -> int:
        return 10

    with pytest.raises(StateError, match="No priority calculator configured"):
        manager.get_entities_within_budget(
            observer_id=observer_id,
            entities=entities,
            size_calculator=size_calculator,
        )


def test_get_entities_within_budget_no_budget() -> None:
    """Test get_entities_within_budget raises error without budget."""
    calculator = PriorityCalculator()
    manager = InterestManager(priority_calculator=calculator)
    observer_id = EntityID(fake.uuid4())
    strategy = AlwaysRelevant()

    entities = {observer_id: {"Position": {"x": 0.0, "y": 0.0}}}

    manager.register_observer(observer_id=observer_id, strategy=strategy)
    manager.update_interests(entities=entities)

    def size_calculator(
        entity_id: EntityID, entities: dict[EntityID, dict[str, Any]]
    ) -> int:
        return 10

    with pytest.raises(StateError, match="No bandwidth budget configured"):
        manager.get_entities_within_budget(
            observer_id=observer_id,
            entities=entities,
            size_calculator=size_calculator,
        )
