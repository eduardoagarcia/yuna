"""Tests for spatial query protocol."""

from faker import Faker

from yuna.spatial.grid import SpatialGrid
from yuna.spatial.queries import SpatialQuery
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


def test_spatial_grid_implements_protocol() -> None:
    """Test SpatialGrid implements SpatialQuery protocol."""
    grid = SpatialGrid(cell_size=10)
    assert isinstance(grid, SpatialQuery)


def test_spatial_query_get_at_method() -> None:
    """Test SpatialQuery protocol defines get_at method."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(
        x=fake.pyfloat(min_value=0, max_value=100),
        y=fake.pyfloat(min_value=0, max_value=100),
    )
    grid.add(entity_id=entity_id, position=position)
    result = grid.get_at(position=position)
    assert isinstance(result, set)
    assert entity_id in result
    assert hasattr(SpatialQuery, "get_at")


def test_spatial_query_get_in_radius_method() -> None:
    """Test SpatialQuery protocol defines get_in_radius method."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(x=50.0, y=50.0)
    grid.add(entity_id=entity_id, position=position)
    result = grid.get_in_radius(position=position, radius=10.0)
    assert isinstance(result, set)
    assert entity_id in result
    assert hasattr(SpatialQuery, "get_in_radius")


def test_protocol_method_signatures() -> None:
    """Test protocol method signatures are properly defined."""
    assert hasattr(SpatialQuery, "get_at")
    assert hasattr(SpatialQuery, "get_in_radius")
    grid = SpatialGrid(cell_size=10)
    assert callable(grid.get_at)
    assert callable(grid.get_in_radius)
