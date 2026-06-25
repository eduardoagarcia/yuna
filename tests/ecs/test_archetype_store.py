"""Tests for ArchetypeStore implementation."""

from dataclasses import dataclass

from faker import Faker

from yuna.ecs.archetype_store import ArchetypeStore
from yuna.ecs.component import Component
from yuna.ecs.lifecycle import ComponentLifecycle
from yuna.types.identifiers import EntityID

fake = Faker()


@dataclass
class Position(Component):
    """Test position component."""

    x: float
    y: float


@dataclass
class Velocity(Component):
    """Test velocity component."""

    x: float
    y: float


@dataclass
class Health(Component):
    """Test health component."""

    current: float
    maximum: float


@dataclass
class Sprite(Component):
    """Test sprite component."""

    texture: str


def test_archetype_store_initialization() -> None:
    """Test ArchetypeStore can be initialized."""
    store = ArchetypeStore()
    assert store.archetype_count == 0


def test_add_component_creates_archetype() -> None:
    """Test adding first component creates new archetype."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.add(entity_id=entity_id, component=Position(x=10.0, y=20.0))

    assert store.archetype_count == 1
    archetype = store.get_archetype(entity_id=entity_id)
    assert archetype is not None
    assert archetype.component_types == frozenset({Position})


def test_add_second_component_migrates_to_new_archetype() -> None:
    """Test adding component migrates entity to new archetype."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.add(entity_id=entity_id, component=Position(x=10.0, y=20.0))
    old_archetype = store.get_archetype(entity_id=entity_id)
    assert old_archetype is not None

    store.add(entity_id=entity_id, component=Velocity(x=1.0, y=2.0))
    new_archetype = store.get_archetype(entity_id=entity_id)
    assert new_archetype is not None

    assert store.archetype_count == 2
    assert new_archetype is not old_archetype
    assert new_archetype.component_types == frozenset({Position, Velocity})
    assert not old_archetype.has_entity(entity_id=entity_id)
    assert new_archetype.has_entity(entity_id=entity_id)


def test_add_replaces_existing_component() -> None:
    """Test adding same component type replaces existing value."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.add(entity_id=entity_id, component=Position(x=10.0, y=20.0))
    store.add(entity_id=entity_id, component=Position(x=50.0, y=60.0))

    position = store.get(entity_id=entity_id, component_type=Position)
    assert position is not None
    assert isinstance(position, Position)
    assert position.x == 50.0
    assert position.y == 60.0
    assert store.archetype_count == 1


def test_remove_component_migrates_archetype() -> None:
    """Test removing component migrates entity to different archetype."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.add(entity_id=entity_id, component=Position(x=10.0, y=20.0))
    store.add(entity_id=entity_id, component=Velocity(x=1.0, y=2.0))

    old_archetype = store.get_archetype(entity_id=entity_id)
    assert old_archetype is not None
    assert old_archetype.component_types == frozenset({Position, Velocity})

    store.remove(entity_id=entity_id, component_type=Velocity)

    new_archetype = store.get_archetype(entity_id=entity_id)
    assert new_archetype is not None
    assert new_archetype.component_types == frozenset({Position})
    assert not old_archetype.has_entity(entity_id=entity_id)
    assert new_archetype.has_entity(entity_id=entity_id)


def test_remove_last_component_removes_from_archetype() -> None:
    """Test removing last component removes entity from archetype system."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.add(entity_id=entity_id, component=Position(x=10.0, y=20.0))
    store.remove(entity_id=entity_id, component_type=Position)

    archetype = store.get_archetype(entity_id=entity_id)
    assert archetype is None


def test_remove_nonexistent_component_is_safe() -> None:
    """Test removing component that doesn't exist is safe."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.remove(entity_id=entity_id, component_type=Position)
    store.add(entity_id=entity_id, component=Position(x=10.0, y=20.0))
    store.remove(entity_id=entity_id, component_type=Velocity)


def test_get_component() -> None:
    """Test getting component from entity."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    position = Position(x=10.0, y=20.0)
    store.add(entity_id=entity_id, component=position)

    retrieved = store.get(entity_id=entity_id, component_type=Position)
    assert retrieved is position


def test_get_component_from_nonexistent_entity() -> None:
    """Test getting component from entity that doesn't exist."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    position = store.get(entity_id=entity_id, component_type=Position)
    assert position is None


def test_get_component_not_on_entity() -> None:
    """Test getting component type entity doesn't have."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.add(entity_id=entity_id, component=Position(x=10.0, y=20.0))
    velocity = store.get(entity_id=entity_id, component_type=Velocity)
    assert velocity is None


def test_has_component() -> None:
    """Test checking if entity has component."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    assert not store.has(entity_id=entity_id, component_type=Position)

    store.add(entity_id=entity_id, component=Position(x=10.0, y=20.0))

    assert store.has(entity_id=entity_id, component_type=Position)
    assert not store.has(entity_id=entity_id, component_type=Velocity)


def test_get_all_components() -> None:
    """Test getting all components of a type."""
    store = ArchetypeStore()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity3, component=Velocity(x=3.0, y=3.0))

    all_positions = store.get_all(component_type=Position)
    assert len(all_positions) == 2
    assert entity1 in all_positions
    assert entity2 in all_positions
    assert entity3 not in all_positions


def test_iter_items_returns_matching_pairs() -> None:
    """iter_items yields only entities holding the requested component."""
    store = ArchetypeStore()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    first_position = Position(x=1.0, y=1.0)
    store.add(entity_id=entity1, component=first_position)
    store.add(entity_id=entity2, component=Velocity(x=2.0, y=2.0))

    assert store.iter_items(component_type=Position) == [(entity1, first_position)]
    assert store.iter_items(component_type=Health) == []


def test_get_map_returns_matching_components() -> None:
    """get_map returns the entity-to-component mapping for the type."""
    store = ArchetypeStore()
    entity1 = EntityID(fake.uuid4())
    first_position = Position(x=1.0, y=1.0)
    store.add(entity_id=entity1, component=first_position)

    assert store.get_map(component_type=Position) == {entity1: first_position}
    assert store.get_map(component_type=Health) == {}


def test_remove_all_components() -> None:
    """Test removing all components from entity."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.add(entity_id=entity_id, component=Position(x=10.0, y=20.0))
    store.add(entity_id=entity_id, component=Velocity(x=1.0, y=2.0))
    store.add(entity_id=entity_id, component=Health(current=100.0, maximum=100.0))

    store.remove_all(entity_id=entity_id)

    assert not store.has(entity_id=entity_id, component_type=Position)
    assert not store.has(entity_id=entity_id, component_type=Velocity)
    assert not store.has(entity_id=entity_id, component_type=Health)
    assert store.get_archetype(entity_id=entity_id) is None


def test_remove_all_from_nonexistent_entity_is_safe() -> None:
    """Test remove_all on entity with no components is safe."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.remove_all(entity_id=entity_id)


def test_get_component_types() -> None:
    """Test getting all registered component types."""
    store = ArchetypeStore()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity2, component=Velocity(x=2.0, y=2.0))

    types = store.get_component_types()
    assert len(types) == 2
    assert Position in types
    assert Velocity in types


def test_count_components() -> None:
    """Test counting entities with specific component type."""
    store = ArchetypeStore()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity3, component=Velocity(x=3.0, y=3.0))

    assert store.count(component_type=Position) == 2
    assert store.count(component_type=Velocity) == 1
    assert store.count(component_type=Health) == 0


def test_query_archetypes() -> None:
    """Test querying archetypes by component types."""
    store = ArchetypeStore()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity1, component=Velocity(x=1.0, y=1.0))

    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity2, component=Velocity(x=2.0, y=2.0))
    store.add(entity_id=entity2, component=Health(current=100.0, maximum=100.0))

    store.add(entity_id=entity3, component=Position(x=3.0, y=3.0))

    matching = store.query_archetypes(component_types={Position, Velocity})
    assert len(matching) == 2

    for archetype in matching:
        assert Position in archetype.component_types
        assert Velocity in archetype.component_types


def test_query_archetypes_subset_match() -> None:
    """Test query matches archetypes with superset of components."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.add(entity_id=entity_id, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_id, component=Velocity(x=1.0, y=1.0))
    store.add(entity_id=entity_id, component=Health(current=100.0, maximum=100.0))

    matching = store.query_archetypes(component_types={Position})
    assert len(matching) == 3
    for archetype in matching:
        assert Position in archetype.component_types


def test_query_archetypes_no_matches() -> None:
    """Test query returns empty list when no archetypes match."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.add(entity_id=entity_id, component=Position(x=1.0, y=1.0))

    matching = store.query_archetypes(component_types={Velocity, Health})
    assert len(matching) == 0


def test_archetype_reuse() -> None:
    """Test entities with same final signature share archetype."""
    store = ArchetypeStore()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity1, component=Velocity(x=1.0, y=1.0))

    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity2, component=Velocity(x=2.0, y=2.0))

    archetype1 = store.get_archetype(entity_id=entity1)
    archetype2 = store.get_archetype(entity_id=entity2)

    assert archetype1 is archetype2
    assert archetype1 is not None
    assert archetype1.entity_count == 2


def test_migration_preserves_components() -> None:
    """Test component migration preserves all existing components."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    position = Position(x=10.0, y=20.0)
    velocity = Velocity(x=1.0, y=2.0)

    store.add(entity_id=entity_id, component=position)
    store.add(entity_id=entity_id, component=velocity)
    store.add(entity_id=entity_id, component=Health(current=100.0, maximum=100.0))

    retrieved_position = store.get(entity_id=entity_id, component_type=Position)
    retrieved_velocity = store.get(entity_id=entity_id, component_type=Velocity)

    assert retrieved_position is position
    assert retrieved_velocity is velocity


def test_get_dirty_components() -> None:
    """Test getting dirty components."""
    store = ArchetypeStore()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity2, component=Position(x=2.0, y=2.0))

    dirty = store.get_dirty_components(component_type=Position)
    assert len(dirty) == 2
    assert entity1 in dirty
    assert entity2 in dirty


def test_lifecycle_hooks_called_on_add() -> None:
    """Test lifecycle hooks called when adding component."""
    added_components: list[tuple[EntityID, type, Component]] = []

    def on_add(entity_id: EntityID, component_type: type, component: Component) -> None:
        added_components.append((entity_id, component_type, component))

    lifecycle = ComponentLifecycle()
    lifecycle.register_added_callback(component_type=Position, callback=on_add)

    store = ArchetypeStore(lifecycle=lifecycle)
    entity_id = EntityID(fake.uuid4())
    position = Position(x=10.0, y=20.0)

    store.add(entity_id=entity_id, component=position)

    assert len(added_components) == 1
    assert added_components[0] == (entity_id, Position, position)


def test_lifecycle_hooks_called_on_remove() -> None:
    """Test lifecycle hooks called when removing component."""
    removed_components: list[tuple[EntityID, type, Component]] = []

    def on_remove(
        entity_id: EntityID, component_type: type, component: Component
    ) -> None:
        removed_components.append((entity_id, component_type, component))

    lifecycle = ComponentLifecycle()
    lifecycle.register_removed_callback(component_type=Position, callback=on_remove)

    store = ArchetypeStore(lifecycle=lifecycle)
    entity_id = EntityID(fake.uuid4())
    position = Position(x=10.0, y=20.0)

    store.add(entity_id=entity_id, component=position)
    store.remove(entity_id=entity_id, component_type=Position)

    assert len(removed_components) == 1
    assert removed_components[0] == (entity_id, Position, position)


def test_large_scale_entity_migration() -> None:
    """Test archetype system handles large-scale migrations efficiently."""
    store = ArchetypeStore()
    entities = [EntityID(fake.uuid4()) for _ in range(1000)]

    for entity_id in entities:
        store.add(entity_id=entity_id, component=Position(x=1.0, y=1.0))

    assert store.archetype_count == 1
    archetype_before = store.get_archetype(entity_id=entities[0])
    assert archetype_before is not None
    assert archetype_before.entity_count == 1000

    for entity_id in entities:
        store.add(entity_id=entity_id, component=Velocity(x=1.0, y=1.0))

    assert store.archetype_count == 2
    archetype_after = store.get_archetype(entity_id=entities[0])
    assert archetype_after is not None
    assert archetype_after.entity_count == 1000
    assert archetype_before.entity_count == 0


def test_multiple_archetypes_coexist() -> None:
    """Test multiple different archetypes can coexist."""
    store = ArchetypeStore()

    entity1 = EntityID(fake.uuid4())
    store.add(entity_id=entity1, component=Position(x=1.0, y=1.0))

    entity2 = EntityID(fake.uuid4())
    store.add(entity_id=entity2, component=Velocity(x=2.0, y=2.0))

    entity3 = EntityID(fake.uuid4())
    store.add(entity_id=entity3, component=Health(current=100.0, maximum=100.0))

    entity4 = EntityID(fake.uuid4())
    store.add(entity_id=entity4, component=Position(x=4.0, y=4.0))
    store.add(entity_id=entity4, component=Velocity(x=4.0, y=4.0))

    assert store.archetype_count == 4


def test_remove_component_without_archetype_entry() -> None:
    """Test removing component when entity has no archetype entry."""
    store = ArchetypeStore()
    entity_id = EntityID(fake.uuid4())

    store.add(entity_id=entity_id, component=Position(x=10.0, y=20.0))
    store.add(entity_id=entity_id, component=Velocity(x=1.0, y=2.0))

    del store._entity_to_archetype[entity_id]

    store.remove(entity_id=entity_id, component_type=Position)

    assert not store.has(entity_id=entity_id, component_type=Position)
    assert store.has(entity_id=entity_id, component_type=Velocity)
