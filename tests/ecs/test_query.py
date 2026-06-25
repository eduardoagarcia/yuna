"""Tests for component queries."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from faker import Faker

from yuna.ecs.archetype_store import ArchetypeStore
from yuna.ecs.component import Component
from yuna.ecs.query import Query
from yuna.ecs.store import ComponentStore
from yuna.types.identifiers import EntityID

fake = Faker()


@dataclass
class Position(Component):
    """Test component for position data."""

    x: float
    y: float


@dataclass
class Velocity(Component):
    """Test component for velocity data."""

    dx: float
    dy: float


@dataclass
class Health(Component):
    """Test component for health data."""

    current: int
    maximum: int


@dataclass
class Dead(Component):
    """Test marker component for dead entities."""

    pass


def test_query_creation() -> None:
    """Test Query can be instantiated."""
    store = ComponentStore()
    query = Query(store=store)
    assert query is not None


def test_with_components_single_type() -> None:
    """Test querying entities with a single component type."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_3, component=Health(current=100, maximum=100))
    query = Query(store=store).with_components(Position)
    entities = query.get_entities()
    assert len(entities) == 2
    assert entity_1 in entities
    assert entity_2 in entities
    assert entity_3 not in entities


def test_with_components_multiple_types() -> None:
    """Test querying entities with multiple component types (AND logic)."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_1, component=Velocity(dx=0.5, dy=0.5))
    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_3, component=Velocity(dx=1.0, dy=1.0))
    query = Query(store=store).with_components(Position, Velocity)
    entities = query.get_entities()
    assert len(entities) == 1
    assert entity_1 in entities


def test_without_components_single_type() -> None:
    """Test querying entities without a specific component type."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_2, component=Dead())
    store.add(entity_id=entity_3, component=Position(x=3.0, y=3.0))
    query = Query(store=store).with_components(Position).without_components(Dead)
    entities = query.get_entities()
    assert len(entities) == 2
    assert entity_1 in entities
    assert entity_3 in entities
    assert entity_2 not in entities


def test_without_components_multiple_types() -> None:
    """Test querying entities without multiple component types."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_2, component=Dead())
    store.add(entity_id=entity_3, component=Position(x=3.0, y=3.0))
    store.add(entity_id=entity_3, component=Health(current=0, maximum=100))
    query = (
        Query(store=store).with_components(Position).without_components(Dead, Health)
    )
    entities = query.get_entities()
    assert len(entities) == 1
    assert entity_1 in entities


def test_iterator_single_component() -> None:
    """Test iterating over query results with single component."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=10.0, y=20.0))
    store.add(entity_id=entity_2, component=Position(x=30.0, y=40.0))
    query = Query(store=store).with_components(Position)
    results = list(query.iterator())
    assert len(results) == 2
    entity_ids = {entity_id for entity_id, _ in results}
    assert entity_1 in entity_ids
    assert entity_2 in entity_ids


def test_iterator_multiple_components() -> None:
    """Test iterating over query results with multiple components."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=5.0, y=10.0))
    store.add(entity_id=entity_1, component=Velocity(dx=1.0, dy=2.0))
    query = Query(store=store).with_components(Position, Velocity)
    results = list(query.iterator())
    assert len(results) == 1
    entity_id, (position, velocity) = results[0]
    assert entity_id == entity_1
    assert isinstance(position, Position)
    assert isinstance(velocity, Velocity)
    assert position.x == 5.0
    assert velocity.dx == 1.0


def test_iterator_returns_components_in_order() -> None:
    """Test iterator returns components in same order as with_components."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=2.0))
    store.add(entity_id=entity_1, component=Velocity(dx=3.0, dy=4.0))
    store.add(entity_id=entity_1, component=Health(current=100, maximum=100))
    query = Query(store=store).with_components(Health, Position, Velocity)
    results = list(query.iterator())
    entity_id, (health, position, velocity) = results[0]
    assert isinstance(health, Health)
    assert isinstance(position, Position)
    assert isinstance(velocity, Velocity)


def test_query_empty_results() -> None:
    """Test query returns empty results when no entities match."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    query = Query(store=store).with_components(Velocity)
    entities = query.get_entities()
    assert len(entities) == 0


def test_query_empty_store() -> None:
    """Test query on empty store returns no results."""
    store = ComponentStore()
    query = Query(store=store).with_components(Position)
    entities = query.get_entities()
    assert len(entities) == 0


def test_query_count() -> None:
    """Test counting matching entities."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_3, component=Health(current=100, maximum=100))
    query = Query(store=store).with_components(Position)
    assert query.count() == 2


def test_query_count_zero() -> None:
    """Test count returns zero when no entities match."""
    store = ComponentStore()
    query = Query(store=store).with_components(Position)
    assert query.count() == 0


def test_query_chaining() -> None:
    """Test query methods can be chained."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_1, component=Velocity(dx=0.5, dy=0.5))
    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_2, component=Velocity(dx=1.0, dy=1.0))
    store.add(entity_id=entity_2, component=Dead())
    query = (
        Query(store=store)
        .with_components(Position)
        .with_components(Velocity)
        .without_components(Dead)
    )
    entities = query.get_entities()
    assert len(entities) == 1
    assert entity_1 in entities


def test_query_without_with_components() -> None:
    """Test query without calling with_components returns no results."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    query = Query(store=store)
    entities = query.get_entities()
    assert len(entities) == 0


def test_iterator_empty_when_no_with_components() -> None:
    """Test iterator returns nothing when no with_components specified."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    query = Query(store=store)
    results = list(query.iterator())
    assert len(results) == 0


def test_query_immutability() -> None:
    """Test query operations return new query instances."""
    store = ComponentStore()
    query1 = Query(store=store)
    query2 = query1.with_components(Position)
    query3 = query2.without_components(Dead)
    assert query1 is not query2
    assert query2 is not query3
    assert query1 is not query3


def test_complex_query_scenario() -> None:
    """Test complex query with multiple entities and conditions."""
    store = ComponentStore()
    player = EntityID(fake.uuid4())
    enemy_alive = EntityID(fake.uuid4())
    enemy_dead = EntityID(fake.uuid4())
    obstacle = EntityID(fake.uuid4())
    store.add(entity_id=player, component=Position(x=0.0, y=0.0))
    store.add(entity_id=player, component=Velocity(dx=1.0, dy=0.0))
    store.add(entity_id=player, component=Health(current=100, maximum=100))
    store.add(entity_id=enemy_alive, component=Position(x=50.0, y=50.0))
    store.add(entity_id=enemy_alive, component=Velocity(dx=0.0, dy=1.0))
    store.add(entity_id=enemy_alive, component=Health(current=50, maximum=50))
    store.add(entity_id=enemy_dead, component=Position(x=100.0, y=100.0))
    store.add(entity_id=enemy_dead, component=Dead())
    store.add(entity_id=obstacle, component=Position(x=25.0, y=25.0))
    alive_movers = (
        Query(store=store)
        .with_components(Position, Velocity, Health)
        .without_components(Dead)
    )
    assert alive_movers.count() == 2
    entities = alive_movers.get_entities()
    assert player in entities
    assert enemy_alive in entities
    assert enemy_dead not in entities
    assert obstacle not in entities


def test_query_uses_smallest_component_set_for_efficiency() -> None:
    """Test query optimizes by starting with smallest component set."""
    store = ComponentStore()
    for i in range(100):
        entity = EntityID(fake.uuid4())
        store.add(entity_id=entity, component=Position(x=float(i), y=float(i)))
    for i in range(10):
        entity = EntityID(fake.uuid4())
        store.add(entity_id=entity, component=Position(x=float(i), y=float(i)))
        store.add(entity_id=entity, component=Velocity(dx=1.0, dy=1.0))
    query = Query(store=store).with_components(Position, Velocity)
    assert query.count() == 10


def test_query_iterator_with_archetype_store() -> None:
    """Test query iterates correctly over an archetype-backed store."""
    store = ArchetypeStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())

    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_1, component=Velocity(dx=0.5, dy=0.5))

    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_2, component=Velocity(dx=1.0, dy=1.0))

    store.add(entity_id=entity_3, component=Position(x=3.0, y=3.0))

    query = Query(store=store).with_components(Position, Velocity)
    results = list(query.iterator())

    assert len(results) == 2
    entity_ids = {entity_id for entity_id, _ in results}
    assert entity_1 in entity_ids
    assert entity_2 in entity_ids
    assert entity_3 not in entity_ids


def test_archetype_query_iterator() -> None:
    """Test query uses archetype iterator when use_archetypes=True."""
    store = ArchetypeStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())

    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_1, component=Velocity(dx=0.5, dy=0.5))

    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_2, component=Velocity(dx=1.0, dy=1.0))

    store.add(entity_id=entity_3, component=Position(x=3.0, y=3.0))

    query = Query(store=store, use_archetypes=True).with_components(Position, Velocity)
    results = list(query.iterator())

    assert len(results) == 2
    entity_ids = {entity_id for entity_id, _ in results}
    assert entity_1 in entity_ids
    assert entity_2 in entity_ids
    assert entity_3 not in entity_ids


def test_archetype_query_iterator_is_sorted_by_entity_id() -> None:
    """Test archetype iteration yields entities in sorted entity id order."""
    store = ArchetypeStore()
    entity_ids = sorted(EntityID(fake.uuid4()) for _ in range(10))

    for index, entity_id in enumerate(reversed(entity_ids)):
        store.add(entity_id=entity_id, component=Position(x=float(index), y=0.0))
        store.add(entity_id=entity_id, component=Velocity(dx=1.0, dy=1.0))

    query = Query(store=store, use_archetypes=True).with_components(Position, Velocity)
    yielded = [entity_id for entity_id, _ in query.iterator()]

    assert yielded == entity_ids


def test_archetype_query_with_without_components() -> None:
    """Test archetype query filters out excluded components."""
    store = ArchetypeStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())

    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_1, component=Velocity(dx=0.5, dy=0.5))

    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_2, component=Velocity(dx=1.0, dy=1.0))
    store.add(entity_id=entity_2, component=Dead())

    query = (
        Query(store=store, use_archetypes=True)
        .with_components(Position, Velocity)
        .without_components(Dead)
    )
    results = list(query.iterator())

    assert len(results) == 1
    entity_id, _ = results[0]
    assert entity_id == entity_1


def test_archetype_query_multiple_archetypes() -> None:
    """Test archetype query works across multiple archetypes."""
    store = ArchetypeStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())

    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))

    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_2, component=Velocity(dx=1.0, dy=1.0))

    store.add(entity_id=entity_3, component=Position(x=3.0, y=3.0))
    store.add(entity_id=entity_3, component=Velocity(dx=2.0, dy=2.0))
    store.add(entity_id=entity_3, component=Health(current=100, maximum=100))

    query = Query(store=store, use_archetypes=True).with_components(Position)
    results = list(query.iterator())

    assert len(results) == 3
    entity_ids = {entity_id for entity_id, _ in results}
    assert entity_1 in entity_ids
    assert entity_2 in entity_ids
    assert entity_3 in entity_ids


def test_archetype_iterator_with_component_store_returns_empty() -> None:
    """Test archetype iterator returns empty when store is not ArchetypeStore."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())

    store.add(entity_id=entity_id, component=Position(x=1.0, y=1.0))

    query = Query(store=store, use_archetypes=True).with_components(Position)
    results = list(query.iterator())

    assert len(results) == 0


def test_get_candidate_entities_returns_empty_when_no_components() -> None:
    """Test _get_candidate_entities returns no candidates with no with_types."""
    store = ComponentStore()
    query = Query(store=store)
    result = query._get_candidate_entities()
    assert result == []


def test_candidate_entities_are_not_aliased_across_calls() -> None:
    """Test each call returns a distinct candidate list, not shared state."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    store.add(entity_id=entity_id, component=Position(x=1.0, y=1.0))

    query = Query(store=store).with_components(Position)
    first = query._get_candidate_entities()
    second = query._get_candidate_entities()

    assert first == second == [entity_id]
    assert first is not second


def test_candidate_entities_come_from_smallest_component_type() -> None:
    """Candidates are snapshotted from the least-populated component type."""
    store = ComponentStore()
    shared_entity = EntityID(fake.uuid4())
    store.add(entity_id=shared_entity, component=Position(x=1.0, y=1.0))
    store.add(entity_id=shared_entity, component=Health(current=10, maximum=10))
    store.add(entity_id=EntityID(fake.uuid4()), component=Position(x=2.0, y=2.0))

    query = Query(store=store).with_components(Position, Health)

    assert query._get_candidate_entities() == [shared_entity]


def test_concurrent_queries_return_correct_independent_results() -> None:
    """Test concurrent query iteration is thread-safe and deterministic."""
    store = ComponentStore()
    matching_entities: set[EntityID] = set()

    entity_count = 200
    for index in range(entity_count):
        entity_id = EntityID(fake.uuid4())
        store.add(entity_id=entity_id, component=Position(x=float(index), y=0.0))
        if index % 2 == 0:
            store.add(entity_id=entity_id, component=Velocity(dx=1.0, dy=1.0))
            matching_entities.add(entity_id)

    def run_query(_: int) -> set[EntityID]:
        query = Query(store=store).with_components(Position, Velocity)
        return {entity_id for entity_id, _ in query.iterator()}

    worker_count = 4
    invocation_count = 64
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        results = list(executor.map(run_query, range(invocation_count)))

    assert len(results) == invocation_count
    for result in results:
        assert result == matching_entities
