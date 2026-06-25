"""Tests for component storage."""

from dataclasses import dataclass

from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.store import ComponentStore
from yuna.types.identifiers import EntityID

fake = Faker()


@dataclass
class Position(Component):
    """Test component for position data."""

    x: float
    y: float


@dataclass
class Health(Component):
    """Test component for health data."""

    current: int
    maximum: int


@dataclass
class Velocity(Component):
    """Test component for velocity data."""

    dx: float
    dy: float


def test_component_store_creation() -> None:
    """Test ComponentStore can be instantiated."""
    store = ComponentStore()
    assert store is not None


def test_add_component_to_entity() -> None:
    """Test adding a component to an entity."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    position = Position(x=10.0, y=20.0)
    store.add(entity_id=entity_id, component=position)
    assert store.has(entity_id=entity_id, component_type=Position)


def test_get_component_from_entity() -> None:
    """Test getting a component from an entity."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    position = Position(x=15.0, y=25.0)
    store.add(entity_id=entity_id, component=position)
    retrieved = store.get(entity_id=entity_id, component_type=Position)
    assert retrieved is not None
    assert retrieved.x == 15.0
    assert retrieved.y == 25.0


def test_get_non_existent_component_returns_none() -> None:
    """Test getting a component that doesn't exist returns None."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    result = store.get(entity_id=entity_id, component_type=Position)
    assert result is None


def test_has_returns_false_for_non_existent_component() -> None:
    """Test has returns False for component not on entity."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    assert store.has(entity_id=entity_id, component_type=Position) is False


def test_remove_component_from_entity() -> None:
    """Test removing a component from an entity."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    position = Position(x=5.0, y=10.0)
    store.add(entity_id=entity_id, component=position)
    store.remove(entity_id=entity_id, component_type=Position)
    assert store.has(entity_id=entity_id, component_type=Position) is False


def test_remove_non_existent_component_is_safe() -> None:
    """Test removing a component that doesn't exist is safe."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    store.remove(entity_id=entity_id, component_type=Position)


def test_add_multiple_components_to_same_entity() -> None:
    """Test adding multiple different component types to same entity."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    position = Position(x=1.0, y=2.0)
    health = Health(current=80, maximum=100)
    store.add(entity_id=entity_id, component=position)
    store.add(entity_id=entity_id, component=health)
    assert store.has(entity_id=entity_id, component_type=Position)
    assert store.has(entity_id=entity_id, component_type=Health)


def test_add_same_component_type_to_multiple_entities() -> None:
    """Test adding same component type to multiple entities."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_3, component=Position(x=3.0, y=3.0))
    assert store.has(entity_id=entity_1, component_type=Position)
    assert store.has(entity_id=entity_2, component_type=Position)
    assert store.has(entity_id=entity_3, component_type=Position)


def test_get_all_components_of_type() -> None:
    """Test getting all components of a specific type."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=10.0, y=10.0))
    store.add(entity_id=entity_2, component=Position(x=20.0, y=20.0))
    store.add(entity_id=entity_3, component=Health(current=100, maximum=100))
    all_positions = store.get_all(component_type=Position)
    assert len(all_positions) == 2
    assert entity_1 in all_positions
    assert entity_2 in all_positions
    assert entity_3 not in all_positions


def test_get_all_returns_empty_dict_for_non_existent_type() -> None:
    """Test get_all returns empty dict for component type that doesn't exist."""
    store = ComponentStore()
    all_positions = store.get_all(component_type=Position)
    assert len(all_positions) == 0
    assert isinstance(all_positions, dict)


def test_get_all_returns_copy() -> None:
    """Test get_all returns a copy, not the internal dict."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    store.add(entity_id=entity_id, component=Position(x=1.0, y=1.0))
    all_positions_1 = store.get_all(component_type=Position)
    all_positions_2 = store.get_all(component_type=Position)
    assert all_positions_1 is not all_positions_2


def test_iter_items_returns_pairs_in_insertion_order() -> None:
    """iter_items yields (entity, component) pairs matching insertion order."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    first_position = Position(x=1.0, y=2.0)
    second_position = Position(x=3.0, y=4.0)
    store.add(entity_id=entity_1, component=first_position)
    store.add(entity_id=entity_2, component=second_position)

    assert store.iter_items(component_type=Position) == [
        (entity_1, first_position),
        (entity_2, second_position),
    ]


def test_iter_items_returns_empty_list_for_non_existent_type() -> None:
    """iter_items returns an empty list for unknown component types."""
    store = ComponentStore()

    assert store.iter_items(component_type=Position) == []


def test_get_map_returns_live_view() -> None:
    """get_map exposes the live mapping reflecting later mutations."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    store.add(entity_id=entity_id, component=Position(x=1.0, y=1.0))

    live_map = store.get_map(component_type=Position)
    assert entity_id in live_map

    store.remove(entity_id=entity_id, component_type=Position)
    assert entity_id not in live_map


def test_get_map_returns_empty_for_non_existent_type() -> None:
    """get_map returns an empty mapping for unknown component types."""
    store = ComponentStore()

    assert store.get_map(component_type=Position) == {}


def test_remove_all_components_from_entity() -> None:
    """Test removing all components from an entity."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    store.add(entity_id=entity_id, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_id, component=Health(current=50, maximum=100))
    store.add(entity_id=entity_id, component=Velocity(dx=5.0, dy=5.0))
    store.remove_all(entity_id=entity_id)
    assert not store.has(entity_id=entity_id, component_type=Position)
    assert not store.has(entity_id=entity_id, component_type=Health)
    assert not store.has(entity_id=entity_id, component_type=Velocity)


def test_remove_all_does_not_affect_other_entities() -> None:
    """Test remove_all only removes components from specified entity."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.remove_all(entity_id=entity_1)
    assert not store.has(entity_id=entity_1, component_type=Position)
    assert store.has(entity_id=entity_2, component_type=Position)


def test_overwrite_component_on_same_entity() -> None:
    """Test adding same component type twice overwrites previous value."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    store.add(entity_id=entity_id, component=Position(x=10.0, y=10.0))
    store.add(entity_id=entity_id, component=Position(x=20.0, y=20.0))
    position = store.get(entity_id=entity_id, component_type=Position)
    assert position is not None
    assert position.x == 20.0
    assert position.y == 20.0


def test_data_locality_components_grouped_by_type() -> None:
    """Test components are stored grouped by type for data locality."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_3, component=Position(x=3.0, y=3.0))
    all_positions = store.get_all(component_type=Position)
    assert len(all_positions) == 3


def test_get_component_types() -> None:
    """Test getting all registered component types."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_2, component=Health(current=100, maximum=100))
    types = store.get_component_types()
    assert len(types) == 2
    assert Position in types
    assert Health in types


def test_get_component_types_empty_store() -> None:
    """Test getting component types from empty store."""
    store = ComponentStore()
    types = store.get_component_types()
    assert len(types) == 0


def test_count_components_of_type() -> None:
    """Test counting number of entities with a component type."""
    store = ComponentStore()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    entity_3 = EntityID(fake.uuid4())
    store.add(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    store.add(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    store.add(entity_id=entity_3, component=Health(current=100, maximum=100))
    assert store.count(component_type=Position) == 2
    assert store.count(component_type=Health) == 1


def test_count_returns_zero_for_non_existent_type() -> None:
    """Test count returns zero for component type that doesn't exist."""
    store = ComponentStore()
    assert store.count(component_type=Position) == 0


def test_remove_all_on_entity_without_components() -> None:
    """Test remove_all on entity that has no components is safe."""
    store = ComponentStore()
    entity_id = EntityID(fake.uuid4())
    store.remove_all(entity_id=entity_id)


def test_complex_scenario() -> None:
    """Test complex scenario with multiple entities and components."""
    store = ComponentStore()
    player = EntityID(fake.uuid4())
    enemy_1 = EntityID(fake.uuid4())
    enemy_2 = EntityID(fake.uuid4())
    store.add(entity_id=player, component=Position(x=0.0, y=0.0))
    store.add(entity_id=player, component=Health(current=100, maximum=100))
    store.add(entity_id=player, component=Velocity(dx=1.0, dy=0.0))
    store.add(entity_id=enemy_1, component=Position(x=50.0, y=50.0))
    store.add(entity_id=enemy_1, component=Health(current=50, maximum=50))
    store.add(entity_id=enemy_2, component=Position(x=100.0, y=100.0))
    assert store.count(component_type=Position) == 3
    assert store.count(component_type=Health) == 2
    assert store.count(component_type=Velocity) == 1
    store.remove(entity_id=enemy_1, component_type=Health)
    assert store.count(component_type=Health) == 1
    store.remove_all(entity_id=enemy_2)
    assert store.count(component_type=Position) == 2
    all_positions = store.get_all(component_type=Position)
    assert player in all_positions
    assert enemy_1 in all_positions
    assert enemy_2 not in all_positions
