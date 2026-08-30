"""Tests for spatial system integration."""

import pytest
from faker import Faker

from yuna.ecs.markers import StaticComponent
from yuna.ecs.world import ECSWorld
from yuna.spatial.collision import CollisionMode
from yuna.spatial.integration import Position, SpatialSystem
from yuna.types.vector import Vector2

fake = Faker()


def test_position_component_creation() -> None:
    """Test Position component can be created."""
    position = Vector2(x=fake.pyfloat(), y=fake.pyfloat())
    component = Position(position=position)
    assert component.position == position


def test_position_component_is_immutable() -> None:
    """Test Position component is frozen."""
    position = Vector2(x=fake.pyfloat(), y=fake.pyfloat())
    component = Position(position=position)
    with pytest.raises(AttributeError):
        component.position = Vector2(x=0.0, y=0.0)  # type: ignore[misc]


def test_spatial_system_creation() -> None:
    """Test SpatialSystem can be created."""
    cell_size = fake.random_int(min=1, max=100)
    spatial_system = SpatialSystem(cell_size=cell_size)
    assert spatial_system._grid._cell_size == cell_size


def test_spatial_system_priority() -> None:
    """Test SpatialSystem has correct priority."""
    spatial_system = SpatialSystem(cell_size=10)
    assert spatial_system.priority == 75


def test_spatial_system_wires_grid_to_world_on_first_update() -> None:
    """Test SpatialSystem wires its grid to world on first update."""
    spatial_system = SpatialSystem(cell_size=10)
    world = ECSWorld()

    assert spatial_system._initialized is False
    assert world._spatial_grid is None

    spatial_system.update(world=world, delta_time=0.016)

    assert spatial_system._initialized is True
    assert world._spatial_grid is spatial_system._grid  # type: ignore[unreachable]


def test_spatial_system_only_initializes_once() -> None:
    """Test SpatialSystem only wires to world once."""
    spatial_system = SpatialSystem(cell_size=10)
    world = ECSWorld()

    spatial_system.update(world=world, delta_time=0.016)
    grid_reference = world._spatial_grid

    spatial_system.update(world=world, delta_time=0.016)

    assert world._spatial_grid is grid_reference


def test_spatial_system_initializes_with_existing_entities() -> None:
    """Test SpatialSystem adds existing entities to grid on first update."""
    world = ECSWorld()
    entity_id = world.create_entity()
    position = Vector2(x=10.0, y=20.0)
    world.add_component(entity_id=entity_id, component=Position(position=position))

    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)

    entities = spatial_system.get_at(position=position)
    assert entity_id in entities


def test_spatial_system_syncs_dynamic_entities_on_update() -> None:
    """Test SpatialSystem synchronizes dynamic entity positions each tick."""
    world = ECSWorld()
    entity_id = world.create_entity()
    old_position = Vector2(x=10.0, y=20.0)
    world.add_component(entity_id=entity_id, component=Position(position=old_position))

    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)

    entities_at_old = spatial_system.get_at(position=old_position)
    assert entity_id in entities_at_old

    new_position = Vector2(x=30.0, y=40.0)
    world.add_component(entity_id=entity_id, component=Position(position=new_position))

    spatial_system.update(world=world, delta_time=0.016)

    entities_at_old = spatial_system.get_at(position=old_position)
    entities_at_new = spatial_system.get_at(position=new_position)
    assert entity_id not in entities_at_old
    assert entity_id in entities_at_new


def test_spatial_system_skips_static_entities() -> None:
    """Test SpatialSystem does not re-sync static entities."""
    world = ECSWorld()
    entity_id = world.create_entity()
    position = Vector2(x=10.0, y=20.0)
    world.add_component(entity_id=entity_id, component=Position(position=position))
    world.add_component(entity_id=entity_id, component=StaticComponent())

    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)

    assert entity_id in spatial_system._static_entities
    entities = spatial_system.get_at(position=position)
    assert entity_id in entities

    new_position = Vector2(x=30.0, y=40.0)
    world.add_component(entity_id=entity_id, component=Position(position=new_position))

    spatial_system.update(world=world, delta_time=0.016)

    entities_at_old = spatial_system.get_at(position=position)
    entities_at_new = spatial_system.get_at(position=new_position)
    assert entity_id in entities_at_old
    assert entity_id not in entities_at_new


def test_spatial_system_removes_destroyed_entities() -> None:
    """Test SpatialSystem removes destroyed entities from grid."""
    world = ECSWorld()
    entity_id = world.create_entity()
    position = Vector2(x=10.0, y=20.0)
    world.add_component(entity_id=entity_id, component=Position(position=position))

    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)

    entities = spatial_system.get_at(position=position)
    assert entity_id in entities

    world.remove_component(entity_id=entity_id, component_type=Position)

    spatial_system.update(world=world, delta_time=0.016)

    entities = spatial_system.get_at(position=position)
    assert entity_id not in entities


def test_a_destroyed_static_entity_invalidates_the_static_cache() -> None:
    """A static entity that dies must stop showing up in the static caches.

    Static positions are cached without expiry because static entities never
    move, but they can still be destroyed, and callers pathing around them
    would otherwise route around a cell that is now empty.
    """
    world = ECSWorld()
    entity_id = world.create_entity()
    position = Vector2(x=10.0, y=20.0)
    world.add_component(entity_id=entity_id, component=Position(position=position))
    world.add_component(entity_id=entity_id, component=StaticComponent())

    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)

    assert spatial_system._grid.get_static_positions_by_component(
        component_type=StaticComponent,
    ) == {position}
    version = spatial_system._grid.static_version

    world.remove_component(entity_id=entity_id, component_type=Position)
    spatial_system.update(world=world, delta_time=0.016)

    assert (
        spatial_system._grid.get_static_positions_by_component(
            component_type=StaticComponent,
        )
        == set()
    )
    assert spatial_system._grid.static_version != version
    assert entity_id not in spatial_system._static_entities


def test_a_destroyed_dynamic_entity_leaves_the_static_cache_alone() -> None:
    """Only static removals pay for invalidation, so ordinary deaths cost nothing."""
    world = ECSWorld()
    entity_id = world.create_entity()
    world.add_component(
        entity_id=entity_id,
        component=Position(position=Vector2(x=10.0, y=20.0)),
    )

    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)
    version = spatial_system._grid.static_version

    world.remove_component(entity_id=entity_id, component_type=Position)
    spatial_system.update(world=world, delta_time=0.016)

    assert spatial_system._grid.static_version == version


def test_spatial_system_get_in_radius() -> None:
    """Test SpatialSystem radius queries."""
    world = ECSWorld()
    entity_id_1 = world.create_entity()
    entity_id_2 = world.create_entity()
    position_1 = Vector2(x=50.0, y=50.0)
    position_2 = Vector2(x=60.0, y=50.0)

    world.add_component(entity_id=entity_id_1, component=Position(position=position_1))
    world.add_component(entity_id=entity_id_2, component=Position(position=position_2))

    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)

    nearby = spatial_system.get_in_radius(
        position=Vector2(x=50.0, y=50.0),
        radius=5.0,
    )
    assert entity_id_1 in nearby
    assert entity_id_2 not in nearby


def test_spatial_system_get_in_bounds() -> None:
    """Test SpatialSystem rectangular bounds queries."""
    world = ECSWorld()
    entity_id_1 = world.create_entity()
    entity_id_2 = world.create_entity()
    position_1 = Vector2(x=50.0, y=50.0)
    position_2 = Vector2(x=60.0, y=50.0)

    world.add_component(entity_id=entity_id_1, component=Position(position=position_1))
    world.add_component(entity_id=entity_id_2, component=Position(position=position_2))

    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)

    inside = spatial_system.get_in_bounds(
        min_pos=Vector2(x=45.0, y=45.0),
        max_pos=Vector2(x=55.0, y=55.0),
    )
    assert entity_id_1 in inside
    assert entity_id_2 not in inside


def test_spatial_system_multiple_entities_same_position() -> None:
    """Test SpatialSystem handles multiple entities at same position."""
    world = ECSWorld()
    entity_id_1 = world.create_entity()
    entity_id_2 = world.create_entity()
    position = Vector2(x=50.0, y=50.0)

    world.add_component(entity_id=entity_id_1, component=Position(position=position))
    world.add_component(entity_id=entity_id_2, component=Position(position=position))

    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)

    entities = spatial_system.get_at(position=position)
    assert entity_id_1 in entities
    assert entity_id_2 in entities


def test_spatial_system_integration_with_world() -> None:
    """Test SpatialSystem can be registered with ECSWorld."""
    spatial_system = SpatialSystem(cell_size=10)
    world = ECSWorld()
    world.register_system(system=spatial_system)
    world.update(delta_time=0.016)


def test_spatial_system_with_collision_mode() -> None:
    """Test SpatialSystem can be created with collision mode."""
    spatial_system = SpatialSystem(
        cell_size=10,
        collision_mode=CollisionMode.GRID_BOX,
    )
    assert spatial_system._grid._collision_mode == CollisionMode.GRID_BOX


def test_spatial_system_default_collision_mode() -> None:
    """Test SpatialSystem defaults to CIRCLE collision mode."""
    spatial_system = SpatialSystem(cell_size=10)
    assert spatial_system._grid._collision_mode == CollisionMode.CIRCLE


def test_spatial_system_handles_entity_created_mid_tick() -> None:
    """Test entities created mid-tick appear in grid on next update."""
    world = ECSWorld()
    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)

    entity_id = world.create_entity()
    position = Vector2(x=10.0, y=20.0)
    world.add_component(entity_id=entity_id, component=Position(position=position))

    entities = spatial_system.get_at(position=position)
    assert entity_id not in entities

    spatial_system.update(world=world, delta_time=0.016)

    entities = spatial_system.get_at(position=position)
    assert entity_id in entities


def test_spatial_system_tracks_multiple_static_entities() -> None:
    """Test SpatialSystem tracks multiple static entities."""
    world = ECSWorld()
    entity_id_1 = world.create_entity()
    entity_id_2 = world.create_entity()

    world.add_component(
        entity_id=entity_id_1,
        component=Position(position=Vector2(x=10.0, y=10.0)),
    )
    world.add_component(entity_id=entity_id_1, component=StaticComponent())

    world.add_component(
        entity_id=entity_id_2,
        component=Position(position=Vector2(x=20.0, y=20.0)),
    )
    world.add_component(entity_id=entity_id_2, component=StaticComponent())

    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)

    assert entity_id_1 in spatial_system._static_entities
    assert entity_id_2 in spatial_system._static_entities
    assert len(spatial_system._static_entities) == 2


def test_spatial_system_cleans_up_static_entity_on_destruction() -> None:
    """Test SpatialSystem removes static entity from tracking on destruction."""
    world = ECSWorld()
    entity_id = world.create_entity()
    position = Vector2(x=10.0, y=20.0)

    world.add_component(entity_id=entity_id, component=Position(position=position))
    world.add_component(entity_id=entity_id, component=StaticComponent())

    spatial_system = SpatialSystem(cell_size=10)
    spatial_system.update(world=world, delta_time=0.016)

    assert entity_id in spatial_system._static_entities

    world.remove_component(entity_id=entity_id, component_type=Position)

    spatial_system.update(world=world, delta_time=0.016)

    assert entity_id not in spatial_system._static_entities
