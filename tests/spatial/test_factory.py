"""Tests for SpatialIndexFactory."""

from faker import Faker

from yuna.spatial.bvh import BoundingVolumeHierarchy
from yuna.spatial.factory import SpatialIndexFactory
from yuna.spatial.grid import SpatialGrid
from yuna.spatial.quadtree import Bounds, QuadTree
from yuna.types.vector import Vector2

fake = Faker()


def test_create_grid() -> None:
    """Test creating grid with default cell size."""
    factory = SpatialIndexFactory()
    grid = factory.create_grid()

    assert isinstance(grid, SpatialGrid)


def test_create_grid_with_custom_cell_size() -> None:
    """Test creating grid with custom cell size."""
    factory = SpatialIndexFactory()
    cell_size = fake.random_int(min=5, max=50)
    grid = factory.create_grid(cell_size=cell_size)

    assert isinstance(grid, SpatialGrid)


def test_create_quadtree() -> None:
    """Test creating quadtree with bounds."""
    factory = SpatialIndexFactory()
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = factory.create_quadtree(bounds=bounds)

    assert isinstance(tree, QuadTree)


def test_create_quadtree_with_custom_parameters() -> None:
    """Test creating quadtree with custom parameters."""
    factory = SpatialIndexFactory()
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    max_objects = fake.random_int(min=5, max=20)
    max_depth = fake.random_int(min=4, max=12)

    tree = factory.create_quadtree(
        bounds=bounds,
        max_objects=max_objects,
        max_depth=max_depth,
    )

    assert isinstance(tree, QuadTree)


def test_create_bvh() -> None:
    """Test creating BVH."""
    factory = SpatialIndexFactory()
    bvh = factory.create_bvh()

    assert isinstance(bvh, BoundingVolumeHierarchy)


def test_create_auto_small_dense_world() -> None:
    """Test auto-selection creates grid for small dense worlds."""
    factory = SpatialIndexFactory()

    index = factory.create_auto(
        entity_count=500,
        world_size=Vector2(x=400.0, y=400.0),
    )

    assert isinstance(index, SpatialGrid)


def test_create_auto_large_sparse_world() -> None:
    """Test auto-selection creates quadtree for large sparse worlds."""
    factory = SpatialIndexFactory()

    index = factory.create_auto(
        entity_count=2000,
        world_size=Vector2(x=1000.0, y=1000.0),
    )

    assert isinstance(index, QuadTree)


def test_create_auto_very_large_world() -> None:
    """Test auto-selection creates quadtree for very large worlds."""
    factory = SpatialIndexFactory()

    index = factory.create_auto(
        entity_count=1000,
        world_size=Vector2(x=600.0, y=600.0),
    )

    assert isinstance(index, QuadTree)


def test_create_auto_very_sparse_world() -> None:
    """Test auto-selection creates quadtree for very sparse worlds."""
    factory = SpatialIndexFactory()

    index = factory.create_auto(
        entity_count=100,
        world_size=Vector2(x=1000.0, y=1000.0),
    )

    assert isinstance(index, QuadTree)


def test_create_auto_with_custom_min_pos() -> None:
    """Test auto-selection with custom minimum position."""
    factory = SpatialIndexFactory()

    index = factory.create_auto(
        entity_count=100,
        world_size=Vector2(x=500.0, y=500.0),
        min_pos=Vector2(x=-250.0, y=-250.0),
    )

    assert index is not None


def test_create_auto_zero_area_world() -> None:
    """Test auto-selection with zero area world."""
    factory = SpatialIndexFactory()

    index = factory.create_auto(
        entity_count=100,
        world_size=Vector2(x=0.0, y=0.0),
    )

    assert isinstance(index, SpatialGrid)


def test_create_auto_medium_density_world() -> None:
    """Test auto-selection for medium density world uses grid."""
    factory = SpatialIndexFactory()

    index = factory.create_auto(
        entity_count=800,
        world_size=Vector2(x=450.0, y=450.0),
    )

    assert isinstance(index, SpatialGrid)


def test_factory_is_static() -> None:
    """Test factory methods can be called without instantiation."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)

    grid = SpatialIndexFactory.create_grid()
    quadtree = SpatialIndexFactory.create_quadtree(bounds=bounds)
    bvh = SpatialIndexFactory.create_bvh()
    auto = SpatialIndexFactory.create_auto(
        entity_count=100,
        world_size=Vector2(x=100.0, y=100.0),
    )

    assert isinstance(grid, SpatialGrid)
    assert isinstance(quadtree, QuadTree)
    assert isinstance(bvh, BoundingVolumeHierarchy)
    assert auto is not None


def test_create_auto_medium_world_fallback() -> None:
    """Test auto-selection fallback to grid for medium worlds."""
    factory = SpatialIndexFactory()

    index = factory.create_auto(
        entity_count=2000,
        world_size=Vector2(x=400.0, y=400.0),
    )

    assert isinstance(index, SpatialGrid)
