"""Performance and correctness tests for SpatialGrid optimizations."""

import time

from faker import Faker

from yuna.spatial.grid import SpatialGrid
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


def test_get_nearest_returns_correct_entities_small_world() -> None:
    """Test get_nearest returns correct entities in small world."""
    grid = SpatialGrid(cell_size=10)

    entities = []
    for i in range(10):
        entity_id = EntityID(f"entity_{i}")
        position = Vector2(x=float(i * 10), y=float(i * 10))
        grid.add(entity_id=entity_id, position=position)
        entities.append((entity_id, position))

    query_pos = Vector2(x=25.0, y=25.0)
    nearest = grid.get_nearest(position=query_pos, count=3)

    assert len(nearest) == 3
    assert EntityID("entity_2") in nearest
    assert EntityID("entity_3") in nearest


def test_get_nearest_returns_all_when_count_exceeds_total() -> None:
    """Test get_nearest returns all entities when k > total."""
    grid = SpatialGrid(cell_size=10)

    for i in range(5):
        entity_id = EntityID(f"entity_{i}")
        grid.add(entity_id=entity_id, position=Vector2(x=float(i), y=float(i)))

    nearest = grid.get_nearest(position=Vector2(x=0.0, y=0.0), count=10)

    assert len(nearest) == 5


def test_get_nearest_empty_world() -> None:
    """Test get_nearest returns empty list for empty world."""
    grid = SpatialGrid(cell_size=10)
    nearest = grid.get_nearest(position=Vector2(x=0.0, y=0.0), count=5)
    assert nearest == []


def test_get_nearest_zero_count() -> None:
    """Test get_nearest returns empty list for count=0."""
    grid = SpatialGrid(cell_size=10)
    grid.add(entity_id=EntityID("entity_1"), position=Vector2(x=1.0, y=1.0))
    nearest = grid.get_nearest(position=Vector2(x=0.0, y=0.0), count=0)
    assert nearest == []


def test_get_nearest_single_entity() -> None:
    """Test get_nearest with single entity."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID("entity_1")
    grid.add(entity_id=entity_id, position=Vector2(x=50.0, y=50.0))

    nearest = grid.get_nearest(position=Vector2(x=0.0, y=0.0), count=5)

    assert len(nearest) == 1
    assert nearest[0] == entity_id


def test_get_nearest_returns_sorted_by_distance() -> None:
    """Test get_nearest returns entities sorted by distance."""
    grid = SpatialGrid(cell_size=10)

    grid.add(entity_id=EntityID("far"), position=Vector2(x=100.0, y=100.0))
    grid.add(entity_id=EntityID("close"), position=Vector2(x=10.0, y=10.0))
    grid.add(entity_id=EntityID("closest"), position=Vector2(x=5.0, y=5.0))
    grid.add(entity_id=EntityID("medium"), position=Vector2(x=50.0, y=50.0))

    query_pos = Vector2(x=0.0, y=0.0)
    nearest = grid.get_nearest(position=query_pos, count=4)

    assert nearest[0] == EntityID("closest")
    assert nearest[1] == EntityID("close")
    assert nearest[2] == EntityID("medium")
    assert nearest[3] == EntityID("far")


def test_get_nearest_performance_large_world() -> None:
    """Test get_nearest performance with 10,000 entities."""
    grid = SpatialGrid(cell_size=50)

    for i in range(10000):
        entity_id = EntityID(f"entity_{i}")
        position = Vector2(
            x=fake.pyfloat(min_value=0, max_value=10000),
            y=fake.pyfloat(min_value=0, max_value=10000),
        )
        grid.add(entity_id=entity_id, position=position)

    query_pos = Vector2(x=5000.0, y=5000.0)

    start_time = time.perf_counter()
    nearest = grid.get_nearest(position=query_pos, count=10)
    elapsed_time = time.perf_counter() - start_time

    assert len(nearest) == 10
    assert elapsed_time < 0.01


def test_get_nearest_progressive_expansion_correctness() -> None:
    """Test progressive expansion finds same results as exhaustive search."""
    grid = SpatialGrid(cell_size=50)

    entities_data = []
    for i in range(100):
        entity_id = EntityID(f"entity_{i}")
        position = Vector2(
            x=fake.pyfloat(min_value=0, max_value=1000),
            y=fake.pyfloat(min_value=0, max_value=1000),
        )
        grid.add(entity_id=entity_id, position=position)
        entities_data.append((entity_id, position))

    query_pos = Vector2(x=500.0, y=500.0)
    nearest = grid.get_nearest(position=query_pos, count=10)

    distances = []
    for entity_id, position in entities_data:
        distance = position.distance(other=query_pos)
        distances.append((distance, entity_id))
    distances.sort(key=lambda x: x[0])
    expected = [entity_id for _, entity_id in distances[:10]]

    assert len(nearest) == 10
    assert set(nearest) == set(expected)


def test_get_nearest_clustered_entities() -> None:
    """Test get_nearest with clustered entity distribution."""
    grid = SpatialGrid(cell_size=10)

    for i in range(50):
        grid.add(
            entity_id=EntityID(f"cluster_1_{i}"),
            position=Vector2(
                x=100.0 + fake.pyfloat(min_value=-10, max_value=10),
                y=100.0 + fake.pyfloat(min_value=-10, max_value=10),
            ),
        )

    for i in range(50):
        grid.add(
            entity_id=EntityID(f"cluster_2_{i}"),
            position=Vector2(
                x=900.0 + fake.pyfloat(min_value=-10, max_value=10),
                y=900.0 + fake.pyfloat(min_value=-10, max_value=10),
            ),
        )

    query_pos = Vector2(x=100.0, y=100.0)
    nearest = grid.get_nearest(position=query_pos, count=10)

    assert len(nearest) == 10
    for entity_id in nearest:
        assert "cluster_1" in entity_id


def test_get_nearest_sparse_world() -> None:
    """Test get_nearest in sparse world with few entities."""
    grid = SpatialGrid(cell_size=100)

    grid.add(entity_id=EntityID("entity_1"), position=Vector2(x=1000.0, y=1000.0))
    grid.add(entity_id=EntityID("entity_2"), position=Vector2(x=50000.0, y=50000.0))
    grid.add(entity_id=EntityID("entity_3"), position=Vector2(x=99000.0, y=99000.0))

    query_pos = Vector2(x=0.0, y=0.0)
    nearest = grid.get_nearest(position=query_pos, count=2)

    assert len(nearest) == 2
    assert EntityID("entity_1") in nearest
    assert EntityID("entity_2") in nearest


def test_get_nearest_uses_cell_size_for_initial_radius() -> None:
    """Test get_nearest uses cell_size for initial radius."""
    grid = SpatialGrid(cell_size=100)

    for i in range(20):
        entity_id = EntityID(f"entity_{i}")
        position = Vector2(x=float(i * 50), y=float(i * 50))
        grid.add(entity_id=entity_id, position=position)

    nearest = grid.get_nearest(position=Vector2(x=0.0, y=0.0), count=5)

    assert len(nearest) == 5
    assert EntityID("entity_0") in nearest
