"""Tests for relevancy strategies."""

from typing import Any

from faker import Faker

from yuna.network.relevancy import (
    AlwaysRelevant,
    CustomRelevancy,
    DistanceRelevancy,
    OwnershipRelevancy,
)
from yuna.types.identifiers import EntityID

fake = Faker()


def test_always_relevant_creation() -> None:
    """Test AlwaysRelevant can be instantiated."""
    strategy = AlwaysRelevant()
    assert strategy is not None


def test_always_relevant_is_relevant() -> None:
    """Test AlwaysRelevant returns True for all entities."""
    strategy = AlwaysRelevant()
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {}

    assert strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_always_relevant_get_relevant_entities() -> None:
    """Test AlwaysRelevant returns all entities."""
    strategy = AlwaysRelevant()
    observer_id = EntityID(fake.uuid4())
    entities = {
        EntityID(fake.uuid4()): {"Position": {"x": 0, "y": 0}},
        EntityID(fake.uuid4()): {"Position": {"x": 10, "y": 10}},
        EntityID(fake.uuid4()): {"Position": {"x": 20, "y": 20}},
    }

    relevant = strategy.get_relevant_entities(
        observer_id=observer_id,
        entities=entities,
    )

    assert len(relevant) == 3
    assert relevant == set(entities.keys())


def test_distance_relevancy_creation() -> None:
    """Test DistanceRelevancy can be instantiated."""
    max_distance = fake.random_int(min=1, max=1000)
    strategy = DistanceRelevancy(max_distance=max_distance)
    assert strategy.max_distance == max_distance


def test_distance_relevancy_within_range() -> None:
    """Test DistanceRelevancy returns True for entities within range."""
    strategy = DistanceRelevancy(max_distance=100.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Position": {"x": 10, "y": 0}},
        observer_id: {"Position": {"x": 0, "y": 0}},
    }

    assert strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_distance_relevancy_outside_range() -> None:
    """Test DistanceRelevancy returns False for entities outside range."""
    strategy = DistanceRelevancy(max_distance=10.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Position": {"x": 100, "y": 0}},
        observer_id: {"Position": {"x": 0, "y": 0}},
    }

    assert not strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_distance_relevancy_exactly_at_max_distance() -> None:
    """Test DistanceRelevancy returns True for entities exactly at max distance."""
    strategy = DistanceRelevancy(max_distance=10.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Position": {"x": 10, "y": 0}},
        observer_id: {"Position": {"x": 0, "y": 0}},
    }

    assert strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_distance_relevancy_diagonal_distance() -> None:
    """Test DistanceRelevancy calculates diagonal distance correctly."""
    strategy = DistanceRelevancy(max_distance=10.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Position": {"x": 6, "y": 8}},
        observer_id: {"Position": {"x": 0, "y": 0}},
    }

    assert strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_distance_relevancy_missing_entity() -> None:
    """Test DistanceRelevancy returns False for missing entity."""
    strategy = DistanceRelevancy(max_distance=100.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities = {
        observer_id: {"Position": {"x": 0, "y": 0}},
    }

    assert not strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_distance_relevancy_missing_observer() -> None:
    """Test DistanceRelevancy returns False for missing observer."""
    strategy = DistanceRelevancy(max_distance=100.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Position": {"x": 0, "y": 0}},
    }

    assert not strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_distance_relevancy_missing_entity_position() -> None:
    """Test DistanceRelevancy returns False for entity without Position."""
    strategy = DistanceRelevancy(max_distance=100.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Health": {"current": 100}},
        observer_id: {"Position": {"x": 0, "y": 0}},
    }

    assert not strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_distance_relevancy_missing_observer_position() -> None:
    """Test DistanceRelevancy returns False for observer without Position."""
    strategy = DistanceRelevancy(max_distance=100.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Position": {"x": 0, "y": 0}},
        observer_id: {"Health": {"current": 100}},
    }

    assert not strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_distance_relevancy_get_relevant_entities() -> None:
    """Test DistanceRelevancy returns entities within range."""
    strategy = DistanceRelevancy(max_distance=50.0)
    observer_id = EntityID(fake.uuid4())
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())
    entities = {
        observer_id: {"Position": {"x": 0, "y": 0}},
        entity1: {"Position": {"x": 10, "y": 0}},
        entity2: {"Position": {"x": 100, "y": 0}},
        entity3: {"Position": {"x": 30, "y": 40}},
    }

    relevant = strategy.get_relevant_entities(
        observer_id=observer_id,
        entities=entities,
    )

    assert entity1 in relevant
    assert entity2 not in relevant
    assert entity3 in relevant
    assert observer_id in relevant


def test_ownership_relevancy_creation() -> None:
    """Test OwnershipRelevancy can be instantiated."""
    max_distance = fake.random_int(min=1, max=1000)
    strategy = OwnershipRelevancy(max_distance=max_distance)
    assert strategy.max_distance == max_distance


def test_ownership_relevancy_owned_entity() -> None:
    """Test OwnershipRelevancy returns True for owned entities."""
    strategy = OwnershipRelevancy(max_distance=10.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id: {
            "Position": {"x": 1000, "y": 1000},
            "Owner": {"id": observer_id},
        },
        observer_id: {"Position": {"x": 0, "y": 0}},
    }

    assert strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_ownership_relevancy_nearby_entity() -> None:
    """Test OwnershipRelevancy returns True for nearby entities."""
    strategy = OwnershipRelevancy(max_distance=50.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Position": {"x": 30, "y": 0}},
        observer_id: {"Position": {"x": 0, "y": 0}},
    }

    assert strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_ownership_relevancy_not_owned_and_far() -> None:
    """Test OwnershipRelevancy returns False for non-owned and far entities."""
    strategy = OwnershipRelevancy(max_distance=10.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    other_owner = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id: {
            "Position": {"x": 1000, "y": 1000},
            "Owner": {"id": other_owner},
        },
        observer_id: {"Position": {"x": 0, "y": 0}},
    }

    assert not strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_ownership_relevancy_missing_entity() -> None:
    """Test OwnershipRelevancy returns False for missing entity."""
    strategy = OwnershipRelevancy(max_distance=100.0)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities = {
        observer_id: {"Position": {"x": 0, "y": 0}},
    }

    assert not strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_ownership_relevancy_get_relevant_entities() -> None:
    """Test OwnershipRelevancy returns owned and nearby entities."""
    strategy = OwnershipRelevancy(max_distance=50.0)
    observer_id = EntityID(fake.uuid4())
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        observer_id: {"Position": {"x": 0, "y": 0}},
        entity1: {
            "Position": {"x": 1000, "y": 1000},
            "Owner": {"id": observer_id},
        },
        entity2: {"Position": {"x": 100, "y": 0}},
        entity3: {"Position": {"x": 30, "y": 0}},
    }

    relevant = strategy.get_relevant_entities(
        observer_id=observer_id,
        entities=entities,
    )

    assert entity1 in relevant
    assert entity2 not in relevant
    assert entity3 in relevant


def test_custom_relevancy_creation() -> None:
    """Test CustomRelevancy can be instantiated."""

    def predicate(
        e: EntityID, o: EntityID, entities: dict[EntityID, dict[str, Any]]
    ) -> bool:
        return True

    strategy = CustomRelevancy(predicate=predicate)
    assert strategy.predicate is predicate


def test_custom_relevancy_with_predicate() -> None:
    """Test CustomRelevancy uses custom predicate."""

    def predicate(
        e: EntityID, o: EntityID, entities: dict[EntityID, dict[str, Any]]
    ) -> bool:
        return bool(
            entities[e].get("Team", {}).get("id")
            == entities[o].get("Team", {}).get("id")
        )

    strategy = CustomRelevancy(predicate=predicate)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    team_id = fake.uuid4()
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Team": {"id": team_id}},
        observer_id: {"Team": {"id": team_id}},
    }

    assert strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_custom_relevancy_predicate_false() -> None:
    """Test CustomRelevancy returns False when predicate returns False."""

    def predicate(
        e: EntityID, o: EntityID, entities: dict[EntityID, dict[str, Any]]
    ) -> bool:
        return False

    strategy = CustomRelevancy(predicate=predicate)
    entity_id = EntityID(fake.uuid4())
    observer_id = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {}

    assert not strategy.is_relevant(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )


def test_custom_relevancy_get_relevant_entities() -> None:
    """Test CustomRelevancy returns entities matching predicate."""
    team_a = fake.uuid4()
    team_b = fake.uuid4()

    def predicate(
        e: EntityID, o: EntityID, entities: dict[EntityID, dict[str, Any]]
    ) -> bool:
        return bool(
            entities.get(e, {}).get("Team", {}).get("id")
            == entities.get(o, {}).get("Team", {}).get("id")
        )

    strategy = CustomRelevancy(predicate=predicate)
    observer_id = EntityID(fake.uuid4())
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        observer_id: {"Team": {"id": team_a}},
        entity1: {"Team": {"id": team_a}},
        entity2: {"Team": {"id": team_b}},
        entity3: {"Team": {"id": team_a}},
    }

    relevant = strategy.get_relevant_entities(
        observer_id=observer_id,
        entities=entities,
    )

    assert entity1 in relevant
    assert entity2 not in relevant
    assert entity3 in relevant
    assert observer_id in relevant
