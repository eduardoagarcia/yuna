"""Tests for dirty flag tracking."""

from dataclasses import dataclass

from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.dirty import DirtyFlag
from yuna.ecs.store import ComponentStore
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


def test_dirty_flag_creation() -> None:
    dirty = DirtyFlag()

    assert dirty is not None


def test_mark_dirty_marks_component() -> None:
    dirty = DirtyFlag()
    entity_id = EntityID(fake.uuid4())

    dirty.mark_dirty(entity_id=entity_id, component_type=Position)

    assert dirty.is_dirty(entity_id=entity_id, component_type=Position) is True


def test_is_dirty_returns_false_when_not_marked() -> None:
    dirty = DirtyFlag()
    entity_id = EntityID(fake.uuid4())

    assert dirty.is_dirty(entity_id=entity_id, component_type=Position) is False


def test_clear_dirty_clears_flag() -> None:
    dirty = DirtyFlag()
    entity_id = EntityID(fake.uuid4())
    dirty.mark_dirty(entity_id=entity_id, component_type=Position)

    dirty.clear_dirty(entity_id=entity_id, component_type=Position)

    assert dirty.is_dirty(entity_id=entity_id, component_type=Position) is False


def test_clear_dirty_on_non_dirty_component_does_nothing() -> None:
    dirty = DirtyFlag()
    entity_id = EntityID(fake.uuid4())

    dirty.clear_dirty(entity_id=entity_id, component_type=Position)

    assert dirty.is_dirty(entity_id=entity_id, component_type=Position) is False


def test_clear_all_clears_all_flags() -> None:
    dirty = DirtyFlag()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    dirty.mark_dirty(entity_id=entity1, component_type=Position)
    dirty.mark_dirty(entity_id=entity2, component_type=Position)
    dirty.mark_dirty(entity_id=entity1, component_type=Velocity)

    dirty.clear_all()

    assert dirty.is_dirty(entity_id=entity1, component_type=Position) is False
    assert dirty.is_dirty(entity_id=entity2, component_type=Position) is False
    assert dirty.is_dirty(entity_id=entity1, component_type=Velocity) is False


def test_get_dirty_entities_returns_marked_entities() -> None:
    dirty = DirtyFlag()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    dirty.mark_dirty(entity_id=entity1, component_type=Position)
    dirty.mark_dirty(entity_id=entity2, component_type=Position)

    dirty_entities = dirty.get_dirty_entities(component_type=Position)

    assert entity1 in dirty_entities
    assert entity2 in dirty_entities
    assert len(dirty_entities) == 2


def test_get_dirty_entities_returns_empty_when_none_dirty() -> None:
    dirty = DirtyFlag()

    dirty_entities = dirty.get_dirty_entities(component_type=Position)

    assert len(dirty_entities) == 0


def test_get_dirty_entities_returns_copy() -> None:
    dirty = DirtyFlag()
    entity1 = EntityID(fake.uuid4())
    dirty.mark_dirty(entity_id=entity1, component_type=Position)

    dirty_entities = dirty.get_dirty_entities(component_type=Position)
    dirty_entities.add(EntityID(fake.uuid4()))

    assert len(dirty.get_dirty_entities(component_type=Position)) == 1


def test_different_component_types_tracked_separately() -> None:
    dirty = DirtyFlag()
    entity1 = EntityID(fake.uuid4())
    dirty.mark_dirty(entity_id=entity1, component_type=Position)

    assert dirty.is_dirty(entity_id=entity1, component_type=Position) is True
    assert dirty.is_dirty(entity_id=entity1, component_type=Velocity) is False


def test_mark_dirty_multiple_times_same_entity() -> None:
    dirty = DirtyFlag()
    entity1 = EntityID(fake.uuid4())

    dirty.mark_dirty(entity_id=entity1, component_type=Position)
    dirty.mark_dirty(entity_id=entity1, component_type=Position)

    dirty_entities = dirty.get_dirty_entities(component_type=Position)
    assert len(dirty_entities) == 1


def test_clear_dirty_does_not_affect_other_entities() -> None:
    dirty = DirtyFlag()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    dirty.mark_dirty(entity_id=entity1, component_type=Position)
    dirty.mark_dirty(entity_id=entity2, component_type=Position)

    dirty.clear_dirty(entity_id=entity1, component_type=Position)

    assert dirty.is_dirty(entity_id=entity1, component_type=Position) is False
    assert dirty.is_dirty(entity_id=entity2, component_type=Position) is True


def test_clear_dirty_does_not_affect_other_component_types() -> None:
    dirty = DirtyFlag()
    entity1 = EntityID(fake.uuid4())
    dirty.mark_dirty(entity_id=entity1, component_type=Position)
    dirty.mark_dirty(entity_id=entity1, component_type=Velocity)

    dirty.clear_dirty(entity_id=entity1, component_type=Position)

    assert dirty.is_dirty(entity_id=entity1, component_type=Position) is False
    assert dirty.is_dirty(entity_id=entity1, component_type=Velocity) is True


def test_multiple_entities_multiple_component_types() -> None:
    dirty = DirtyFlag()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    dirty.mark_dirty(entity_id=entity1, component_type=Position)
    dirty.mark_dirty(entity_id=entity2, component_type=Position)
    dirty.mark_dirty(entity_id=entity2, component_type=Velocity)
    dirty.mark_dirty(entity_id=entity3, component_type=Velocity)

    position_dirty = dirty.get_dirty_entities(component_type=Position)
    velocity_dirty = dirty.get_dirty_entities(component_type=Velocity)

    assert len(position_dirty) == 2
    assert len(velocity_dirty) == 2
    assert entity1 in position_dirty
    assert entity2 in position_dirty
    assert entity2 in velocity_dirty
    assert entity3 in velocity_dirty


def test_store_has_dirty_tracking_by_default() -> None:
    store = ComponentStore()

    assert store is not None


def test_store_with_custom_dirty_flag() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)

    assert store is not None


def test_add_component_marks_dirty() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity_id = EntityID(fake.uuid4())
    position = Position(x=fake.pyfloat(), y=fake.pyfloat())

    store.add(entity_id=entity_id, component=position)

    assert dirty.is_dirty(entity_id=entity_id, component_type=Position) is True


def test_add_component_without_dirty_flag_does_not_crash() -> None:
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    position = Position(x=fake.pyfloat(), y=fake.pyfloat())

    store.add(entity_id=entity_id, component=position)

    assert store.has(entity_id=entity_id, component_type=Position) is True


def test_modify_component_marks_dirty() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity_id = EntityID(fake.uuid4())
    position1 = Position(x=10.0, y=20.0)
    position2 = Position(x=30.0, y=40.0)

    store.add(entity_id=entity_id, component=position1)
    dirty.clear_dirty(entity_id=entity_id, component_type=Position)
    store.add(entity_id=entity_id, component=position2)

    assert dirty.is_dirty(entity_id=entity_id, component_type=Position) is True


def test_get_dirty_components_returns_only_dirty() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity3, component=Position(x=3.0, y=3.0))

    dirty.clear_dirty(entity_id=entity2, component_type=Position)

    dirty_components = store.get_dirty_components(component_type=Position)

    assert len(dirty_components) == 2
    assert entity1 in dirty_components
    assert entity2 not in dirty_components
    assert entity3 in dirty_components


def test_get_dirty_components_with_default_dirty_flag() -> None:
    store = ComponentStore()
    entity1 = EntityID(fake.uuid4())
    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))

    dirty_components = store.get_dirty_components(component_type=Position)

    assert len(dirty_components) == 1
    assert entity1 in dirty_components


def test_get_dirty_components_with_no_components_returns_empty() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)

    dirty_components = store.get_dirty_components(component_type=Position)

    assert len(dirty_components) == 0


def test_multiple_component_types_marked_dirty_independently() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity1 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity1, component=Velocity(dx=0.5, dy=0.5))

    assert dirty.is_dirty(entity_id=entity1, component_type=Position) is True
    assert dirty.is_dirty(entity_id=entity1, component_type=Velocity) is True


def test_dirty_components_have_correct_data() -> None:
    dirty = DirtyFlag()
    store = ComponentStore(dirty_flag=dirty)
    entity1 = EntityID(fake.uuid4())
    x = fake.pyfloat()
    y = fake.pyfloat()

    store.add(entity_id=entity1, component=Position(x=x, y=y))

    dirty_components = store.get_dirty_components(component_type=Position)
    position = dirty_components[entity1]

    assert isinstance(position, Position)
    assert position.x == x
    assert position.y == y
