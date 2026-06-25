"""Tests for dirty flag system integration."""

from dataclasses import dataclass

from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.dirty import DirtyFlag
from yuna.ecs.query import Query
from yuna.ecs.store import ComponentStore
from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.types.identifiers import EntityID

fake = Faker()


@dataclass
class Position(Component):
    x: float
    y: float


@dataclass
class Velocity(Component):
    dx: float
    dy: float


@dataclass
class Sprite(Component):
    texture: str


def test_query_only_dirty_filters_to_dirty_entities() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity3, component=Position(x=3.0, y=3.0))

    dirty.clear_dirty(entity_id=entity2, component_type=Position)

    query = store._world.query() if hasattr(store, "_world") else None
    if query is None:
        query = Query(store=store)

    dirty_query = query.with_components(Position).only_dirty()
    dirty_entities = dirty_query.get_entities()

    assert len(dirty_entities) == 2
    assert entity1 in dirty_entities
    assert entity2 not in dirty_entities
    assert entity3 in dirty_entities


def test_query_only_dirty_with_multiple_components() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity1, component=Velocity(dx=0.5, dy=0.5))
    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity2, component=Velocity(dx=1.0, dy=1.0))
    store.add(entity_id=entity3, component=Position(x=3.0, y=3.0))
    store.add(entity_id=entity3, component=Velocity(dx=1.5, dy=1.5))

    dirty.clear_dirty(entity_id=entity1, component_type=Position)
    dirty.clear_dirty(entity_id=entity2, component_type=Velocity)

    query = Query(store=store)
    dirty_query = query.with_components(Position, Velocity).only_dirty()
    dirty_entities = dirty_query.get_entities()

    assert entity1 in dirty_entities
    assert entity2 in dirty_entities
    assert entity3 in dirty_entities


def test_query_only_dirty_returns_empty_when_no_dirty_entities() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))

    dirty.clear_dirty(entity_id=entity1, component_type=Position)
    dirty.clear_dirty(entity_id=entity2, component_type=Position)

    query = Query(store=store)
    dirty_query = query.with_components(Position).only_dirty()
    dirty_entities = dirty_query.get_entities()

    assert len(dirty_entities) == 0


def test_query_only_dirty_iterator_returns_dirty_entities() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity3, component=Position(x=3.0, y=3.0))

    dirty.clear_dirty(entity_id=entity2, component_type=Position)

    query = Query(store=store)
    dirty_query = query.with_components(Position).only_dirty()
    results = list(dirty_query.iterator())

    assert len(results) == 2
    entity_ids = {entity_id for entity_id, _ in results}
    assert entity1 in entity_ids
    assert entity2 not in entity_ids
    assert entity3 in entity_ids


def test_query_only_dirty_with_without_components() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity2, component=Velocity(dx=1.0, dy=1.0))
    store.add(entity_id=entity3, component=Position(x=3.0, y=3.0))

    query = Query(store=store)
    dirty_query = (
        query.with_components(Position).without_components(Velocity).only_dirty()
    )
    dirty_entities = dirty_query.get_entities()

    assert len(dirty_entities) == 2
    assert entity1 in dirty_entities
    assert entity2 not in dirty_entities
    assert entity3 in dirty_entities


def test_system_process_dirty_only_default_is_false() -> None:
    class TestSystem(System):
        @property
        def priority(self) -> int:
            return 100

        def update(self, world: ECSWorld, delta_time: float) -> None:
            pass

    system = TestSystem()

    assert system.process_dirty_only is False


def test_system_process_dirty_only_can_be_overridden() -> None:
    class DirtyOnlySystem(System):
        @property
        def priority(self) -> int:
            return 100

        @property
        def process_dirty_only(self) -> bool:
            return True

        def update(self, world: ECSWorld, delta_time: float) -> None:
            pass

    system = DirtyOnlySystem()

    assert system.process_dirty_only is True


def test_system_with_dirty_query_only_processes_dirty_entities() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity3, component=Position(x=3.0, y=3.0))

    dirty.clear_dirty(entity_id=entity2, component_type=Position)

    query = Query(store=store)
    dirty_query = query.with_components(Position).only_dirty()

    dirty_entities = set()
    for entity_id, _ in dirty_query.iterator():
        dirty_entities.add(entity_id)

    assert len(dirty_entities) == 2
    assert entity1 in dirty_entities
    assert entity2 not in dirty_entities
    assert entity3 in dirty_entities


def test_query_count_with_only_dirty() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity3, component=Position(x=3.0, y=3.0))

    dirty.clear_dirty(entity_id=entity2, component_type=Position)

    query = Query(store=store)
    dirty_query = query.with_components(Position).only_dirty()

    assert dirty_query.count() == 2
