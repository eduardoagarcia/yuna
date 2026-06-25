"""Tests for ECS world coordinator."""

from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.ecs.archetype_store import ArchetypeStore
from yuna.ecs.component import Component
from yuna.ecs.store import ComponentStore
from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.exceptions import (
    StateError,
    WorldWriteProtectionError,
)
from yuna.modifiers.config import ModifierConfig
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.spatial.grid import SpatialGrid
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


class TestSystem(System):
    """Test system for tracking updates."""

    def __init__(self, priority_value: int) -> None:
        self._priority = priority_value
        self.update_count = 0
        self.last_delta_time = 0.0

    @property
    def priority(self) -> int:
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:
        self.update_count += 1
        self.last_delta_time = delta_time


class RecordingSystem(System):
    """Test system that records execution order."""

    execution_order: list[int] = []

    def __init__(self, priority_value: int, system_id: int) -> None:
        self._priority = priority_value
        self._system_id = system_id

    @property
    def priority(self) -> int:
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:
        RecordingSystem.execution_order.append(self._system_id)


def test_world_can_be_created() -> None:
    """Test ECSWorld can be instantiated."""
    world = ECSWorld()
    assert world is not None


def test_create_entity() -> None:
    """Test creating an entity returns unique ID."""
    world = ECSWorld()
    entity_1 = world.create_entity()
    entity_2 = world.create_entity()
    assert entity_1 != entity_2


def test_add_component() -> None:
    """Test adding component to entity."""
    world = ECSWorld()
    entity_id = world.create_entity()
    position = Position(x=10.0, y=20.0)
    world.add_component(entity_id=entity_id, component=position)
    assert world.has_component(entity_id=entity_id, component_type=Position)


def test_get_component() -> None:
    """Test getting component from entity."""
    world = ECSWorld()
    entity_id = world.create_entity()
    position = Position(x=5.0, y=15.0)
    world.add_component(entity_id=entity_id, component=position)
    retrieved = world.get_component(entity_id=entity_id, component_type=Position)
    assert retrieved is not None
    assert isinstance(retrieved, Position)
    assert retrieved.x == 5.0
    assert retrieved.y == 15.0


def test_get_component_returns_none_when_not_found() -> None:
    """Test get_component returns None for missing component."""
    world = ECSWorld()
    entity_id = world.create_entity()
    result = world.get_component(entity_id=entity_id, component_type=Position)
    assert result is None


def test_has_component() -> None:
    """Test checking if entity has component."""
    world = ECSWorld()
    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=Position(x=0.0, y=0.0))
    assert world.has_component(entity_id=entity_id, component_type=Position)
    assert not world.has_component(entity_id=entity_id, component_type=Velocity)


def test_remove_component() -> None:
    """Test removing component from entity."""
    world = ECSWorld()
    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=Position(x=1.0, y=2.0))
    assert world.has_component(entity_id=entity_id, component_type=Position)
    world.remove_component(entity_id=entity_id, component_type=Position)
    assert not world.has_component(entity_id=entity_id, component_type=Position)


def test_query_entities() -> None:
    """Test querying entities by component composition."""
    world = ECSWorld()
    entity_1 = world.create_entity()
    entity_2 = world.create_entity()
    entity_3 = world.create_entity()
    world.add_component(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    world.add_component(entity_id=entity_1, component=Velocity(dx=0.5, dy=0.5))
    world.add_component(entity_id=entity_2, component=Position(x=2.0, y=2.0))
    world.add_component(entity_id=entity_3, component=Velocity(dx=1.0, dy=1.0))
    query = world.query().with_components(Position, Velocity)
    entities = query.get_entities()
    assert len(entities) == 1
    assert entity_1 in entities


def test_register_system() -> None:
    """Test registering a system."""
    world = ECSWorld()
    system = TestSystem(priority_value=100)
    world.register_system(system=system)
    world.update(delta_time=0.016)
    assert system.update_count == 1


def test_update_calls_all_systems() -> None:
    """Test update calls all registered systems."""
    world = ECSWorld()
    system_1 = TestSystem(priority_value=100)
    system_2 = TestSystem(priority_value=200)
    world.register_system(system=system_1)
    world.register_system(system=system_2)
    world.update(delta_time=0.016)
    assert system_1.update_count == 1
    assert system_2.update_count == 1


def test_update_passes_delta_time_to_systems() -> None:
    """Test update passes delta_time to systems."""
    world = ECSWorld()
    system = TestSystem(priority_value=100)
    world.register_system(system=system)
    delta_time = 0.032
    world.update(delta_time=delta_time)
    assert system.last_delta_time == delta_time


def test_systems_execute_in_priority_order() -> None:
    """Test systems execute in priority order (lower first)."""
    RecordingSystem.execution_order = []
    world = ECSWorld()
    system_3 = RecordingSystem(priority_value=300, system_id=3)
    system_1 = RecordingSystem(priority_value=100, system_id=1)
    system_2 = RecordingSystem(priority_value=200, system_id=2)
    world.register_system(system=system_3)
    world.register_system(system=system_1)
    world.register_system(system=system_2)
    world.update(delta_time=0.016)
    assert RecordingSystem.execution_order == [1, 2, 3]


def test_destroy_entity() -> None:
    """Test destroying an entity marks it for destruction."""
    world = ECSWorld()
    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=Position(x=0.0, y=0.0))
    world.destroy_entity(entity_id=entity_id)
    world.update(delta_time=0.016)
    assert not world.has_component(entity_id=entity_id, component_type=Position)


def test_destroyed_entities_flushed_after_update() -> None:
    """Test destroyed entities are removed after systems update."""
    world = ECSWorld()
    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=Position(x=1.0, y=1.0))
    world.destroy_entity(entity_id=entity_id)
    world.update(delta_time=0.016)
    result = world.get_component(entity_id=entity_id, component_type=Position)
    assert result is None


def test_multiple_components_per_entity() -> None:
    """Test entity can have multiple components."""
    world = ECSWorld()
    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=Position(x=5.0, y=10.0))
    world.add_component(entity_id=entity_id, component=Velocity(dx=1.0, dy=2.0))
    world.add_component(entity_id=entity_id, component=Health(current=100, maximum=100))
    assert world.has_component(entity_id=entity_id, component_type=Position)
    assert world.has_component(entity_id=entity_id, component_type=Velocity)
    assert world.has_component(entity_id=entity_id, component_type=Health)


def test_query_returns_new_instance() -> None:
    """Test query method returns new Query instance."""
    world = ECSWorld()
    query_1 = world.query()
    query_2 = world.query()
    assert query_1 is not query_2


def test_update_with_no_systems() -> None:
    """Test update with no registered systems completes successfully."""
    world = ECSWorld()
    world.update(delta_time=0.016)


def test_update_with_zero_delta_time() -> None:
    """Test update with zero delta time."""
    world = ECSWorld()
    system = TestSystem(priority_value=100)
    world.register_system(system=system)
    world.update(delta_time=0.0)
    assert system.last_delta_time == 0.0


def test_update_multiple_times() -> None:
    """Test calling update multiple times."""
    world = ECSWorld()
    system = TestSystem(priority_value=100)
    world.register_system(system=system)
    world.update(delta_time=0.016)
    world.update(delta_time=0.016)
    world.update(delta_time=0.016)
    assert system.update_count == 3


def test_entity_with_no_components() -> None:
    """Test entity can exist with no components."""
    world = ECSWorld()
    entity_id = world.create_entity()
    assert not world.has_component(entity_id=entity_id, component_type=Position)


def test_complex_world_scenario() -> None:
    """Test complex scenario with multiple entities, components, and systems."""
    world = ECSWorld()
    player = world.create_entity()
    enemy_1 = world.create_entity()
    enemy_2 = world.create_entity()
    world.add_component(entity_id=player, component=Position(x=0.0, y=0.0))
    world.add_component(entity_id=player, component=Velocity(dx=1.0, dy=0.0))
    world.add_component(entity_id=player, component=Health(current=100, maximum=100))
    world.add_component(entity_id=enemy_1, component=Position(x=50.0, y=50.0))
    world.add_component(entity_id=enemy_1, component=Health(current=50, maximum=50))
    world.add_component(entity_id=enemy_2, component=Position(x=100.0, y=100.0))
    world.add_component(entity_id=enemy_2, component=Velocity(dx=0.5, dy=0.5))
    system = TestSystem(priority_value=100)
    world.register_system(system=system)
    world.update(delta_time=0.016)
    query = world.query().with_components(Position, Velocity)
    movers = query.get_entities()
    assert len(movers) == 2
    assert player in movers
    assert enemy_2 in movers


def test_remove_nonexistent_component() -> None:
    """Test removing component that doesn't exist completes without error."""
    world = ECSWorld()
    entity_id = world.create_entity()
    world.remove_component(entity_id=entity_id, component_type=Position)


def test_systems_maintain_order_after_multiple_registrations() -> None:
    """Test system priority order maintained with multiple registrations."""
    RecordingSystem.execution_order = []
    world = ECSWorld()
    world.register_system(system=RecordingSystem(priority_value=200, system_id=2))
    world.register_system(system=RecordingSystem(priority_value=100, system_id=1))
    world.register_system(system=RecordingSystem(priority_value=300, system_id=3))
    world.register_system(system=RecordingSystem(priority_value=50, system_id=0))
    world.update(delta_time=0.016)
    assert RecordingSystem.execution_order == [0, 1, 2, 3]


def test_get_all_entities() -> None:
    """Test getting all active entities."""
    world = ECSWorld()
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    entity3 = world.create_entity()

    all_entities = world.get_all_entities()

    assert len(all_entities) == 3
    assert entity1 in all_entities
    assert entity2 in all_entities
    assert entity3 in all_entities


def test_get_all_entities_excludes_destroyed() -> None:
    """Test get_all_entities excludes destroyed entities."""
    world = ECSWorld()
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    entity3 = world.create_entity()

    world.destroy_entity(entity_id=entity2)

    all_entities = world.get_all_entities()

    assert len(all_entities) == 2
    assert entity1 in all_entities
    assert entity2 not in all_entities
    assert entity3 in all_entities


def test_get_component_types() -> None:
    """Test getting all component types."""
    world = ECSWorld()
    entity = world.create_entity()

    world.add_component(entity_id=entity, component=Position(x=1.0, y=2.0))
    world.add_component(entity_id=entity, component=Health(current=100, maximum=100))

    component_types = world.get_component_types()

    assert len(component_types) == 2
    assert Position in component_types
    assert Health in component_types


def test_get_all_components() -> None:
    """Test getting all components of a specific type."""
    world = ECSWorld()
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    entity3 = world.create_entity()

    world.add_component(entity_id=entity1, component=Position(x=1.0, y=2.0))
    world.add_component(entity_id=entity2, component=Position(x=3.0, y=4.0))
    world.add_component(entity_id=entity3, component=Health(current=100, maximum=100))

    positions = world.get_all_components(component_type=Position)

    assert len(positions) == 2
    assert entity1 in positions
    assert entity2 in positions
    assert entity3 not in positions

    pos1 = positions[entity1]
    assert isinstance(pos1, Position)
    assert pos1.x == 1.0

    pos2 = positions[entity2]
    assert isinstance(pos2, Position)
    assert pos2.x == 3.0


def test_derive_entity_id_is_deterministic() -> None:
    """derive_entity_id returns a stable ID without registering it."""
    world = ECSWorld(seed=42)
    derivation_name = fake.word()

    derived = world.derive_entity_id(name=derivation_name)

    assert world.derive_entity_id(name=derivation_name) == derived
    assert derived not in world.get_all_entities()


def test_iter_components_returns_pairs() -> None:
    """iter_components yields (entity, component) pairs for the type."""
    world = ECSWorld()
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    first_position = Position(x=1.0, y=2.0)
    second_position = Position(x=3.0, y=4.0)
    world.add_component(entity_id=entity1, component=first_position)
    world.add_component(entity_id=entity2, component=second_position)

    assert world.iter_components(component_type=Position) == [
        (entity1, first_position),
        (entity2, second_position),
    ]
    assert world.iter_components(component_type=Health) == []


def test_add_existing_entity() -> None:
    """Test adding an existing entity ID."""
    world = ECSWorld()

    custom_id = EntityID("custom-entity-id")
    world.add_existing_entity(entity_id=custom_id)

    all_entities = world.get_all_entities()

    assert custom_id in all_entities


def test_clear_all_entities() -> None:
    """Test clearing all entities."""
    world = ECSWorld()
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    world.add_component(entity_id=entity1, component=Position(x=1.0, y=2.0))
    world.add_component(entity_id=entity2, component=Health(current=100, maximum=100))

    world.clear_all_entities()

    all_entities = world.get_all_entities()
    assert len(all_entities) == 0


def test_world_with_archetype_store() -> None:
    """Test creating world with archetype-based storage."""
    world = ECSWorld(use_archetypes=True)

    assert isinstance(world._components, ArchetypeStore)
    assert world._use_archetypes is True


def test_world_with_component_store_default() -> None:
    """Test world uses ComponentStore by default."""
    world = ECSWorld()

    assert isinstance(world._components, ComponentStore)
    assert world._use_archetypes is False


def test_archetype_world_basic_operations() -> None:
    """Test basic ECS operations work with archetype storage."""
    world = ECSWorld(use_archetypes=True)
    entity_id = world.create_entity()

    world.add_component(entity_id=entity_id, component=Position(x=10.0, y=20.0))

    assert world.has_component(entity_id=entity_id, component_type=Position)

    position = world.get_component(entity_id=entity_id, component_type=Position)
    assert position is not None
    assert isinstance(position, Position)
    assert position.x == 10.0

    world.remove_component(entity_id=entity_id, component_type=Position)
    assert not world.has_component(entity_id=entity_id, component_type=Position)


def test_archetype_world_query() -> None:
    """Test querying works with archetype storage."""
    world = ECSWorld(use_archetypes=True)

    entity_1 = world.create_entity()
    world.add_component(entity_id=entity_1, component=Position(x=1.0, y=1.0))
    world.add_component(entity_id=entity_1, component=Velocity(dx=0.5, dy=0.5))

    entity_2 = world.create_entity()
    world.add_component(entity_id=entity_2, component=Position(x=2.0, y=2.0))

    query = world.query().with_components(Position, Velocity)
    results = list(query.iterator())

    assert len(results) == 1
    result_entity_id, (position, velocity) = results[0]
    assert result_entity_id == entity_1
    assert isinstance(position, Position)
    assert isinstance(velocity, Velocity)


@pytest.mark.asyncio
async def test_add_component_async_with_lock() -> None:
    """Test async component addition with thread safety."""
    world = ECSWorld(thread_safe=True)
    entity_id = world.create_entity()

    await world.add_component_async(
        entity_id=entity_id, component=Position(x=10.0, y=20.0)
    )

    assert world.has_component(entity_id=entity_id, component_type=Position)
    position = world.get_component(entity_id=entity_id, component_type=Position)
    assert position is not None
    assert isinstance(position, Position)
    assert position.x == 10.0


@pytest.mark.asyncio
async def test_add_component_async_without_lock() -> None:
    """Test async component addition without thread safety."""
    world = ECSWorld(thread_safe=False)
    entity_id = world.create_entity()

    await world.add_component_async(
        entity_id=entity_id, component=Position(x=5.0, y=15.0)
    )

    assert world.has_component(entity_id=entity_id, component_type=Position)


@pytest.mark.asyncio
async def test_remove_component_async_with_lock() -> None:
    """Test async component removal with thread safety."""
    world = ECSWorld(thread_safe=True)
    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=Position(x=10.0, y=20.0))

    await world.remove_component_async(entity_id=entity_id, component_type=Position)

    assert not world.has_component(entity_id=entity_id, component_type=Position)


@pytest.mark.asyncio
async def test_remove_component_async_without_lock() -> None:
    """Test async component removal without thread safety."""
    world = ECSWorld(thread_safe=False)
    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=Position(x=10.0, y=20.0))

    await world.remove_component_async(entity_id=entity_id, component_type=Position)

    assert not world.has_component(entity_id=entity_id, component_type=Position)


def test_add_relationship() -> None:
    """Test adding relationship between entities."""
    world = ECSWorld()
    entity_a = world.create_entity()
    entity_b = world.create_entity()
    relationship_type = fake.word()

    world.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )

    assert world.has_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )


def test_get_relationships() -> None:
    """Test getting relationships from world."""
    world = ECSWorld()
    entity_a = world.create_entity()
    entity_b = world.create_entity()
    entity_c = world.create_entity()
    relationship_type = fake.word()

    world.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )
    world.add_relationship(
        from_entity=entity_a,
        to_entity=entity_c,
        relationship_type=relationship_type,
    )

    relationships = world.get_relationships(
        entity_id=entity_a,
        relationship_type=relationship_type,
    )

    assert relationships == {entity_b, entity_c}


def test_remove_relationship() -> None:
    """Test removing relationship between entities."""
    world = ECSWorld()
    entity_a = world.create_entity()
    entity_b = world.create_entity()
    relationship_type = fake.word()

    world.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )
    world.remove_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )

    assert not world.has_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )


def test_relationships_cleaned_up_on_entity_destruction() -> None:
    """Test relationships are removed when entity is destroyed."""
    world = ECSWorld()
    entity_a = world.create_entity()
    entity_b = world.create_entity()
    relationship_type = fake.word()

    world.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )
    world.destroy_entity(entity_id=entity_a)
    world.update(delta_time=0.016)

    assert not world.has_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )


def test_set_parent() -> None:
    """Test setting parent-child relationship."""
    world = ECSWorld()
    parent = world.create_entity()
    child = world.create_entity()

    world.set_parent(child_id=child, parent_id=parent)

    assert world.get_parent(entity_id=child) == parent
    assert child in world.get_children(entity_id=parent)


def test_remove_parent() -> None:
    """Test removing parent from child."""
    world = ECSWorld()
    parent = world.create_entity()
    child = world.create_entity()

    world.set_parent(child_id=child, parent_id=parent)
    world.remove_parent(child_id=child)

    assert world.get_parent(entity_id=child) is None
    assert child not in world.get_children(entity_id=parent)


def test_get_descendants() -> None:
    """Test getting descendants from hierarchy."""
    world = ECSWorld()
    root = world.create_entity()
    child = world.create_entity()
    grandchild = world.create_entity()

    world.set_parent(child_id=child, parent_id=root)
    world.set_parent(child_id=grandchild, parent_id=child)

    descendants = world.get_descendants(entity_id=root)

    assert set(descendants) == {child, grandchild}


def test_get_ancestors() -> None:
    """Test getting ancestors from hierarchy."""
    world = ECSWorld()
    root = world.create_entity()
    middle = world.create_entity()
    leaf = world.create_entity()

    world.set_parent(child_id=middle, parent_id=root)
    world.set_parent(child_id=leaf, parent_id=middle)

    ancestors = world.get_ancestors(entity_id=leaf)

    assert ancestors == [middle, root]


def test_get_root() -> None:
    """Test getting root of hierarchy."""
    world = ECSWorld()
    root = world.create_entity()
    middle = world.create_entity()
    leaf = world.create_entity()

    world.set_parent(child_id=middle, parent_id=root)
    world.set_parent(child_id=leaf, parent_id=middle)

    assert world.get_root(entity_id=leaf) == root
    assert world.get_root(entity_id=middle) == root
    assert world.get_root(entity_id=root) == root


def test_destroy_recursive() -> None:
    """Test recursive destruction of entity and descendants."""
    world = ECSWorld()
    root = world.create_entity()
    child_1 = world.create_entity()
    child_2 = world.create_entity()
    grandchild = world.create_entity()

    world.set_parent(child_id=child_1, parent_id=root)
    world.set_parent(child_id=child_2, parent_id=root)
    world.set_parent(child_id=grandchild, parent_id=child_1)

    world.destroy_recursive(entity_id=root)
    world.update(delta_time=0.016)

    all_entities = world.get_all_entities()
    assert root not in all_entities
    assert child_1 not in all_entities
    assert child_2 not in all_entities
    assert grandchild not in all_entities


def test_hierarchy_cleaned_up_on_entity_destruction() -> None:
    """Test hierarchy is updated when entity is destroyed."""
    world = ECSWorld()
    parent = world.create_entity()
    child = world.create_entity()
    grandchild = world.create_entity()

    world.set_parent(child_id=child, parent_id=parent)
    world.set_parent(child_id=grandchild, parent_id=child)

    world.destroy_entity(entity_id=child)
    world.update(delta_time=0.016)

    assert child not in world.get_children(entity_id=parent)
    assert world.get_parent(entity_id=grandchild) is None


def test_modifiers_property_raises_error_when_not_configured() -> None:
    """Test modifiers property raises StateError when no pipeline configured."""
    world = ECSWorld()

    with pytest.raises(StateError) as exc_info:
        _ = world.modifiers

    assert exc_info.value.operation == "modifiers_access"
    assert "no modifier pipeline" in exc_info.value.reason.lower()


def test_modifiers_property_returns_pipeline_when_configured() -> None:
    """Test modifiers property returns pipeline when configured."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    world = ECSWorld(modifier_pipeline=pipeline)

    assert world.modifiers is pipeline


def test_tick_property_returns_current_tick() -> None:
    """Test tick property returns current tick counter."""
    world = ECSWorld()

    assert world.tick == 0


def test_increment_tick_increments_counter() -> None:
    """Test increment_tick increments the tick counter."""
    world = ECSWorld()

    assert world.tick == 0

    world.increment_tick()
    assert world.tick == 1

    world.increment_tick()
    assert world.tick == 2

    world.increment_tick()
    assert world.tick == 3


def test_world_spatial_property_returns_none_when_not_configured() -> None:
    """Test that spatial property returns None when no spatial grid configured."""
    world = ECSWorld()

    assert world.spatial is None


def test_world_spatial_property_returns_grid_when_configured() -> None:
    """Test that spatial property returns spatial grid when configured."""
    grid = SpatialGrid(cell_size=fake.pyfloat(min_value=1.0, max_value=100.0))
    world = ECSWorld(spatial_grid=grid)

    assert world.spatial is grid


def test_set_metadata_stores_value() -> None:
    """Test set_metadata stores arbitrary metadata in world context."""
    world = ECSWorld()
    key = fake.word()
    value = fake.sentence()

    world.set_metadata(key=key, value=value)

    assert world._metadata[key] == value


def test_get_metadata_returns_stored_value() -> None:
    """Test get_metadata retrieves stored metadata value."""
    world = ECSWorld()
    key = fake.word()
    value = fake.pyint()

    world.set_metadata(key=key, value=value)
    retrieved_value = world.get_metadata(key=key)

    assert retrieved_value == value


def test_get_metadata_returns_default_for_missing_key() -> None:
    """Test get_metadata returns default value when key not found."""
    world = ECSWorld()
    key = fake.word()
    default_value = fake.sentence()

    retrieved_value = world.get_metadata(key=key, default=default_value)

    assert retrieved_value == default_value


def test_get_metadata_returns_none_for_missing_key_without_default() -> None:
    """Test get_metadata returns None when key not found and no default."""
    world = ECSWorld()
    key = fake.word()

    retrieved_value = world.get_metadata(key=key)

    assert retrieved_value is None


def test_metadata_supports_multiple_types() -> None:
    """Test metadata can store different types of values."""
    world = ECSWorld()

    string_key = fake.unique.word()
    string_value = fake.sentence()
    int_key = fake.unique.word()
    int_value = fake.pyint()
    list_key = fake.unique.word()
    list_value = [fake.word(), fake.word(), fake.word()]

    world.set_metadata(key=string_key, value=string_value)
    world.set_metadata(key=int_key, value=int_value)
    world.set_metadata(key=list_key, value=list_value)

    assert world.get_metadata(key=string_key) == string_value
    assert world.get_metadata(key=int_key) == int_value
    assert world.get_metadata(key=list_key) == list_value


def test_set_metadata_overwrites_existing_value() -> None:
    """Test set_metadata overwrites existing value for same key."""
    world = ECSWorld()
    key = fake.word()
    first_value = fake.sentence()
    second_value = fake.sentence()

    world.set_metadata(key=key, value=first_value)
    world.set_metadata(key=key, value=second_value)

    assert world.get_metadata(key=key) == second_value


def test_create_entity_with_explicit_entity_id() -> None:
    """Test creating entity with explicit entity_id uses that ID."""
    world = ECSWorld()
    explicit_id = EntityID(fake.uuid4())
    result = world.create_entity(entity_id=explicit_id)
    assert result == explicit_id
    assert explicit_id in world.get_all_entities()


def test_create_entity_without_explicit_id_generates_id() -> None:
    """Test creating entity without explicit ID generates one."""
    world = ECSWorld()
    result = world.create_entity(entity_id=None)
    assert isinstance(result, str)
    assert result in world.get_all_entities()


def test_create_entity_with_explicit_id_supports_components() -> None:
    """Test entity created with explicit ID works with components."""
    world = ECSWorld()
    explicit_id = EntityID(fake.uuid4())
    world.create_entity(entity_id=explicit_id)
    world.add_component(
        entity_id=explicit_id,
        component=Position(x=1.0, y=2.0),
    )
    assert world.has_component(
        entity_id=explicit_id,
        component_type=Position,
    )


def _protected_world() -> tuple[ECSWorld, EntityID, EntityID]:
    world = ECSWorld()
    world.enable_write_protection(enabled=True)
    owner = world.create_entity()
    other = world.create_entity()
    world.set_write_owner(entity_id=owner)
    return world, owner, other


def test_write_protection_disabled_allows_any_write() -> None:
    """With protection off, writes to any entity are permitted."""
    world = ECSWorld()
    owner = world.create_entity()
    other = world.create_entity()
    world.set_write_owner(entity_id=owner)

    world.add_component(entity_id=other, component=Position(x=1.0, y=2.0))

    assert world.has_component(entity_id=other, component_type=Position)


def test_write_protection_without_owner_allows_write() -> None:
    """A thread with no owner set is unprotected."""
    world = ECSWorld()
    world.enable_write_protection(enabled=True)
    entity_id = world.create_entity()

    world.add_component(entity_id=entity_id, component=Position(x=1.0, y=2.0))

    assert world.has_component(entity_id=entity_id, component_type=Position)


def test_write_protection_allows_owner_entity_write() -> None:
    """The owner entity may be written during a protected section."""
    world, owner, _ = _protected_world()

    world.add_component(entity_id=owner, component=Position(x=1.0, y=2.0))

    assert world.has_component(entity_id=owner, component_type=Position)


def test_write_protection_blocks_non_owner_entity_write() -> None:
    """Writing a different entity during a protected section raises."""
    world, _, other = _protected_world()

    with pytest.raises(expected_exception=WorldWriteProtectionError):
        world.add_component(entity_id=other, component=Position(x=1.0, y=2.0))


def test_write_protection_blocks_entityless_write() -> None:
    """Entity-less structural writes are blocked during a protected section."""
    world, _, _ = _protected_world()

    with pytest.raises(expected_exception=WorldWriteProtectionError):
        world.set_metadata(key=fake.word(), value=fake.word())


def test_write_protection_blocks_entity_creation() -> None:
    """Creating an entity during a protected section raises."""
    world, _, _ = _protected_world()

    with pytest.raises(expected_exception=WorldWriteProtectionError):
        world.create_entity()


def test_write_protection_clearing_owner_restores_writes() -> None:
    """Clearing the owner re-enables unrestricted writes on the thread."""
    world, _, other = _protected_world()

    world.set_write_owner(entity_id=None)
    world.add_component(entity_id=other, component=Position(x=1.0, y=2.0))

    assert world.has_component(entity_id=other, component_type=Position)
