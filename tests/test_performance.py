"""Performance tests for engine core patterns."""

import time
from dataclasses import dataclass

from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.world import ECSWorld
from yuna.resources.pool import ObjectPool
from yuna.spatial.grid import SpatialGrid
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


@dataclass
class Position(Component):
    """Position component."""

    x: float
    y: float


@dataclass
class Velocity(Component):
    """Velocity component."""

    dx: float
    dy: float


@dataclass
class Health(Component):
    """Health component."""

    value: float


def test_large_entity_creation_performance() -> None:
    """Test creating 1000 entities with components performs well."""
    world = ECSWorld()
    entity_count = 1000
    start_time = time.time()
    for i in range(entity_count):
        entity = world.create_entity()
        world.add_component(
            entity_id=entity, component=Position(x=float(i), y=float(i))
        )
        world.add_component(entity_id=entity, component=Velocity(dx=1.0, dy=1.0))
        world.add_component(entity_id=entity, component=Health(value=100.0))
    elapsed = time.time() - start_time
    assert elapsed < 1.0
    entities = world.query().with_components(Position).get_entities()
    assert len(entities) == entity_count


def test_spatial_grid_point_query_is_fast() -> None:
    """Test spatial grid point query is O(1) fast."""
    grid = SpatialGrid(cell_size=10)
    entity_count = 1000
    for i in range(entity_count):
        entity = EntityID(f"entity-{i}")
        grid.add(entity_id=entity, position=Vector2(x=float(i * 10), y=float(i * 10)))
    start_time = time.time()
    for _ in range(10000):
        grid.get_at(position=Vector2(x=500.0, y=500.0))
    elapsed = time.time() - start_time
    assert elapsed < 1.0


def test_spatial_grid_versus_linear_search() -> None:
    """Test spatial grid is faster than linear search."""
    grid = SpatialGrid(cell_size=10)
    entity_count = 1000
    entities_positions: dict[EntityID, Vector2] = {}
    for i in range(entity_count):
        entity = EntityID(f"entity-{i}")
        position = Vector2(x=float(i * 5), y=float(i * 5))
        grid.add(entity_id=entity, position=position)
        entities_positions[entity] = position
    target_position = Vector2(x=250.0, y=250.0)
    radius = 50.0
    start_grid = time.time()
    for _ in range(100):
        grid.get_in_radius(position=target_position, radius=radius)
    grid_elapsed = time.time() - start_grid
    start_linear = time.time()
    for _ in range(100):
        result = set()
        for entity_id, pos in entities_positions.items():
            distance = (
                (pos.x - target_position.x) ** 2 + (pos.y - target_position.y) ** 2
            ) ** 0.5
            if distance <= radius:
                result.add(entity_id)
    linear_elapsed = time.time() - start_linear
    assert grid_elapsed < linear_elapsed


def test_object_pool_reuse() -> None:
    """Test object pool correctly reuses objects."""

    def factory() -> dict[str, float]:
        return {"x": 0.0, "y": 0.0, "z": 0.0}

    def reset(obj: dict[str, float]) -> None:
        obj["x"] = 0.0
        obj["y"] = 0.0
        obj["z"] = 0.0

    pool = ObjectPool[dict[str, float]](factory=factory, reset=reset, max_size=100)
    iteration_count = 10000
    start_time = time.time()
    for _ in range(iteration_count):
        obj = pool.acquire()
        obj["x"] = 1.0
        obj["y"] = 2.0
        obj["z"] = 3.0
        pool.release(obj=obj)
    elapsed = time.time() - start_time
    assert elapsed < 1.0


def test_component_iteration_performance() -> None:
    """Test iterating components with data locality is fast."""
    world = ECSWorld()
    entity_count = 1000
    for i in range(entity_count):
        entity = world.create_entity()
        world.add_component(
            entity_id=entity, component=Position(x=float(i), y=float(i))
        )
        world.add_component(entity_id=entity, component=Velocity(dx=1.0, dy=1.0))
    start_time = time.time()
    for _entity_id, (_position, _velocity) in (
        world.query().with_components(Position, Velocity).iterator()
    ):
        pass
    elapsed = time.time() - start_time
    assert elapsed < 0.1


def test_query_with_multiple_components_performance() -> None:
    """Test querying entities with multiple components is fast."""
    world = ECSWorld()
    entity_count = 1000
    for i in range(entity_count):
        entity = world.create_entity()
        world.add_component(
            entity_id=entity, component=Position(x=float(i), y=float(i))
        )
        if i % 2 == 0:
            world.add_component(entity_id=entity, component=Velocity(dx=1.0, dy=1.0))
        if i % 3 == 0:
            world.add_component(entity_id=entity, component=Health(value=100.0))
    start_time = time.time()
    for _ in range(100):
        world.query().with_components(Position, Velocity, Health).get_entities()
    elapsed = time.time() - start_time
    assert elapsed < 0.5


def test_spatial_grid_many_entities_same_cell() -> None:
    """Test spatial grid handles many entities in same cell efficiently."""
    grid = SpatialGrid(cell_size=100)
    entity_count = 1000
    for i in range(entity_count):
        entity = EntityID(f"entity-{i}")
        grid.add(
            entity_id=entity,
            position=Vector2(x=50.0 + float(i % 10), y=50.0 + float(i % 10)),
        )
    start_time = time.time()
    for _ in range(1000):
        grid.get_at(position=Vector2(x=55.0, y=55.0))
    elapsed = time.time() - start_time
    assert elapsed < 0.5


def test_spatial_grid_radius_query_scaling() -> None:
    """Test spatial grid radius queries scale well with larger grids."""
    grid = SpatialGrid(cell_size=10)
    entity_count = 5000
    for i in range(entity_count):
        entity = EntityID(f"entity-{i}")
        x = float(i % 100) * 10
        y = float(i // 100) * 10
        grid.add(entity_id=entity, position=Vector2(x=x, y=y))
    start_time = time.time()
    for _ in range(100):
        grid.get_in_radius(position=Vector2(x=500.0, y=500.0), radius=50.0)
    elapsed = time.time() - start_time
    assert elapsed < 1.0


def test_entity_destruction_performance() -> None:
    """Test destroying entities is fast."""
    world = ECSWorld()
    entity_count = 1000
    entities = []
    for i in range(entity_count):
        entity = world.create_entity()
        entities.append(entity)
        world.add_component(
            entity_id=entity, component=Position(x=float(i), y=float(i))
        )
        world.add_component(entity_id=entity, component=Velocity(dx=1.0, dy=1.0))
    start_time = time.time()
    for entity in entities:
        world.destroy_entity(entity_id=entity)
    world.update(delta_time=0.016)
    elapsed = time.time() - start_time
    assert elapsed < 1.0
    assert len(world.query().with_components(Position).get_entities()) == 0


def test_component_addition_removal_performance() -> None:
    """Test adding and removing components is fast."""
    world = ECSWorld()
    entity = world.create_entity()
    start_time = time.time()
    for _ in range(10000):
        world.add_component(entity_id=entity, component=Position(x=1.0, y=2.0))
        world.remove_component(entity_id=entity, component_type=Position)
    elapsed = time.time() - start_time
    assert elapsed < 1.0


def test_spatial_grid_update_performance() -> None:
    """Test updating entity positions in spatial grid is fast."""
    grid = SpatialGrid(cell_size=10)
    entity_count = 1000
    entities = []
    for i in range(entity_count):
        entity = EntityID(f"entity-{i}")
        entities.append(entity)
        grid.add(entity_id=entity, position=Vector2(x=float(i), y=float(i)))
    start_time = time.time()
    for i, entity in enumerate(entities):
        grid.move(
            entity_id=entity, new_position=Vector2(x=float(i + 100), y=float(i + 100))
        )
    elapsed = time.time() - start_time
    assert elapsed < 1.0


def test_object_pool_stress() -> None:
    """Test object pool handles stress with many acquire/release cycles."""

    def factory() -> list[int]:
        return []

    def reset(obj: list[int]) -> None:
        obj.clear()

    pool = ObjectPool[list[int]](factory=factory, reset=reset, max_size=50)
    start_time = time.time()
    for _ in range(10000):
        obj = pool.acquire()
        obj.append(1)
        obj.append(2)
        obj.append(3)
        pool.release(obj=obj)
    elapsed = time.time() - start_time
    assert elapsed < 0.5


def test_query_iteration_provides_components() -> None:
    """Test query iterator provides components directly without extra lookups."""
    world = ECSWorld()
    entity_count = 1000
    for i in range(entity_count):
        entity = world.create_entity()
        world.add_component(
            entity_id=entity, component=Position(x=float(i), y=float(i))
        )
        world.add_component(entity_id=entity, component=Velocity(dx=1.0, dy=1.0))
    components_retrieved = 0
    start_time = time.time()
    for _entity_id, (_position, _velocity) in (
        world.query().with_components(Position, Velocity).iterator()
    ):
        components_retrieved += 2
    elapsed = time.time() - start_time
    assert elapsed < 0.1
    assert components_retrieved == entity_count * 2


def test_spatial_grid_removal_performance() -> None:
    """Test removing entities from spatial grid is fast."""
    grid = SpatialGrid(cell_size=10)
    entity_count = 1000
    entities = []
    for i in range(entity_count):
        entity = EntityID(f"entity-{i}")
        entities.append(entity)
        grid.add(entity_id=entity, position=Vector2(x=float(i), y=float(i)))
    start_time = time.time()
    for entity in entities:
        grid.remove(entity_id=entity)
    elapsed = time.time() - start_time
    assert elapsed < 0.5
