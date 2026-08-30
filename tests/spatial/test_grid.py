"""Tests for spatial grid implementation."""

import math
from dataclasses import dataclass
from unittest.mock import patch

from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.world import ECSWorld
from yuna.spatial.collision import CollisionMode
from yuna.spatial.grid import SpatialGrid
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


@dataclass
class TestComponent(Component):
    """Test component for ECS integration tests."""

    value: int = 0


class RecordingNativeIndex:
    """Stand-in for the optional native spatial index extension."""

    def __init__(self, cell_size: float, grid_box_mode: bool) -> None:
        self.cell_size = cell_size
        self.grid_box_mode = grid_box_mode
        self.raycast_hits = [fake.uuid4()]
        self.calls: list[tuple] = []

    def add(self, entity_id: str, x: float, y: float) -> None:
        self.calls.append(("add", entity_id, x, y))

    def remove(self, entity_id: str) -> None:
        self.calls.append(("remove", entity_id))

    def move_entity(self, entity_id: str, new_x: float, new_y: float) -> None:
        self.calls.append(("move_entity", entity_id, new_x, new_y))

    def raycast(
        self,
        origin_x: float,
        origin_y: float,
        dir_x: float,
        dir_y: float,
        max_distance: float,
    ) -> list[str]:
        self.calls.append(("raycast", origin_x, origin_y, dir_x, dir_y, max_distance))
        return self.raycast_hits


@patch(
    target="yuna.spatial.grid.NativeSpatialIndex",
    new=RecordingNativeIndex,
)
def test_native_index_mirrors_mutations_and_serves_raycasts() -> None:
    """The native mirror receives add/move/remove and answers finite raycasts."""
    grid = SpatialGrid(cell_size=10, native_raycast=True)
    entity_id = EntityID(fake.uuid4())

    grid.add(entity_id=entity_id, position=Vector2(x=1.0, y=2.0))
    grid.move(entity_id=entity_id, new_position=Vector2(x=3.0, y=4.0))
    hits = grid.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=0.0),
        max_distance=5.0,
    )
    grid.remove(entity_id=entity_id)

    native_index = grid._native_index
    assert isinstance(native_index, RecordingNativeIndex)
    assert hits == native_index.raycast_hits
    assert native_index.calls == [
        ("add", str(entity_id), 1.0, 2.0),
        ("move_entity", str(entity_id), 3.0, 4.0),
        ("raycast", 0.0, 0.0, 1.0, 0.0, 5.0),
        ("remove", str(entity_id)),
    ]


def test_spatial_grid_creation() -> None:
    """Test SpatialGrid can be created with cell size."""
    cell_size = fake.random_int(min=1, max=100)
    grid = SpatialGrid(cell_size=cell_size)
    assert grid._cell_size == cell_size
    assert grid._grid == {}
    assert grid._entity_positions == {}


def test_add_entity_to_grid() -> None:
    """Test adding entity to spatial grid."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(
        x=fake.pyfloat(min_value=0, max_value=100),
        y=fake.pyfloat(min_value=0, max_value=100),
    )
    grid.add(entity_id=entity_id, position=position)
    assert entity_id in grid._entity_positions
    assert grid._entity_positions[entity_id] == position


def test_add_multiple_entities_same_cell() -> None:
    """Test adding multiple entities to same grid cell."""
    grid = SpatialGrid(cell_size=10)
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    position_1 = Vector2(x=5.0, y=5.0)
    position_2 = Vector2(x=6.0, y=6.0)
    grid.add(entity_id=entity_id_1, position=position_1)
    grid.add(entity_id=entity_id_2, position=position_2)
    cell = grid._get_cell(position=position_1)
    assert entity_id_1 in grid._grid[cell]
    assert entity_id_2 in grid._grid[cell]


def test_remove_entity_from_grid() -> None:
    """Test removing entity from spatial grid."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(
        x=fake.pyfloat(min_value=0, max_value=100),
        y=fake.pyfloat(min_value=0, max_value=100),
    )
    grid.add(entity_id=entity_id, position=position)
    grid.remove(entity_id=entity_id)
    assert entity_id not in grid._entity_positions
    cell = grid._get_cell(position=position)
    assert cell not in grid._grid or entity_id not in grid._grid[cell]


def test_remove_nonexistent_entity() -> None:
    """Test removing entity that doesn't exist does nothing."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    grid.remove(entity_id=entity_id)
    assert entity_id not in grid._entity_positions


def test_remove_entity_cleans_up_empty_cell() -> None:
    """Test removing last entity from cell removes cell from grid."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(x=5.0, y=5.0)
    grid.add(entity_id=entity_id, position=position)
    cell = grid._get_cell(position=position)
    grid.remove(entity_id=entity_id)
    assert cell not in grid._grid


def test_move_entity_same_cell() -> None:
    """Test moving entity within same grid cell."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    old_position = Vector2(x=5.0, y=5.0)
    new_position = Vector2(x=6.0, y=6.0)
    grid.add(entity_id=entity_id, position=old_position)
    grid.move(entity_id=entity_id, new_position=new_position)
    assert grid._entity_positions[entity_id] == new_position
    cell = grid._get_cell(position=new_position)
    assert entity_id in grid._grid[cell]


def test_move_entity_different_cell() -> None:
    """Test moving entity to different grid cell."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    old_position = Vector2(x=5.0, y=5.0)
    new_position = Vector2(x=25.0, y=25.0)
    grid.add(entity_id=entity_id, position=old_position)
    grid.move(entity_id=entity_id, new_position=new_position)
    assert grid._entity_positions[entity_id] == new_position
    old_cell = grid._get_cell(position=old_position)
    new_cell = grid._get_cell(position=new_position)
    assert old_cell not in grid._grid or entity_id not in grid._grid[old_cell]
    assert entity_id in grid._grid[new_cell]


def test_move_entity_cleans_up_old_cell() -> None:
    """Test moving entity removes empty old cell."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    old_position = Vector2(x=5.0, y=5.0)
    new_position = Vector2(x=25.0, y=25.0)
    grid.add(entity_id=entity_id, position=old_position)
    old_cell = grid._get_cell(position=old_position)
    grid.move(entity_id=entity_id, new_position=new_position)
    assert old_cell not in grid._grid


def test_move_to_equal_position_is_noop() -> None:
    """Moving to an equal position early-outs without grid changes."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(x=5.0, y=5.0)
    grid.add(entity_id=entity_id, position=position)

    grid.move(entity_id=entity_id, new_position=Vector2(x=5.0, y=5.0))

    assert grid._entity_positions[entity_id] is position
    assert entity_id in grid._grid[grid._get_cell(position=position)]


def test_move_nonexistent_entity() -> None:
    """Test moving entity that wasn't previously added."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    new_position = Vector2(
        x=fake.pyfloat(min_value=0, max_value=100),
        y=fake.pyfloat(min_value=0, max_value=100),
    )
    grid.move(entity_id=entity_id, new_position=new_position)
    assert grid._entity_positions[entity_id] == new_position
    cell = grid._get_cell(position=new_position)
    assert entity_id in grid._grid[cell]


def test_get_at_position() -> None:
    """Test getting entities at specific position."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(x=5.0, y=5.0)
    grid.add(entity_id=entity_id, position=position)
    entities = grid.get_at(position=position)
    assert entity_id in entities


def test_get_at_empty_position() -> None:
    """Test getting entities at position with no entities."""
    grid = SpatialGrid(cell_size=10)
    position = Vector2(
        x=fake.pyfloat(min_value=0, max_value=100),
        y=fake.pyfloat(min_value=0, max_value=100),
    )
    entities = grid.get_at(position=position)
    assert len(entities) == 0


def test_get_at_returns_copy() -> None:
    """Test get_at returns copy not reference."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(x=5.0, y=5.0)
    grid.add(entity_id=entity_id, position=position)
    entities_1 = grid.get_at(position=position)
    entities_2 = grid.get_at(position=position)
    assert entities_1 is not entities_2
    assert entities_1 == entities_2


def test_get_in_radius() -> None:
    """Test getting entities within radius."""
    grid = SpatialGrid(cell_size=10)
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    center = Vector2(x=50.0, y=50.0)
    position_1 = Vector2(x=51.0, y=50.0)
    position_2 = Vector2(x=60.0, y=50.0)
    grid.add(entity_id=entity_id_1, position=position_1)
    grid.add(entity_id=entity_id_2, position=position_2)
    entities = grid.get_in_radius(position=center, radius=5.0)
    assert entity_id_1 in entities
    assert entity_id_2 not in entities


def test_get_in_radius_empty() -> None:
    """Test getting entities in radius with no entities."""
    grid = SpatialGrid(cell_size=10)
    center = Vector2(
        x=fake.pyfloat(min_value=0, max_value=100),
        y=fake.pyfloat(min_value=0, max_value=100),
    )
    entities = grid.get_in_radius(position=center, radius=10.0)
    assert len(entities) == 0


def test_get_in_radius_exact_distance() -> None:
    """Test entity exactly at radius distance is included."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    center = Vector2(x=0.0, y=0.0)
    position = Vector2(x=3.0, y=4.0)
    grid.add(entity_id=entity_id, position=position)
    entities = grid.get_in_radius(position=center, radius=5.0)
    assert entity_id in entities


def test_get_in_radius_multiple_cells() -> None:
    """Test radius query spans multiple cells."""
    grid = SpatialGrid(cell_size=10)
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    entity_id_3 = EntityID(fake.uuid4())
    center = Vector2(x=15.0, y=15.0)
    position_1 = Vector2(x=10.0, y=10.0)
    position_2 = Vector2(x=20.0, y=20.0)
    position_3 = Vector2(x=40.0, y=40.0)
    grid.add(entity_id=entity_id_1, position=position_1)
    grid.add(entity_id=entity_id_2, position=position_2)
    grid.add(entity_id=entity_id_3, position=position_3)
    entities = grid.get_in_radius(position=center, radius=10.0)
    assert entity_id_1 in entities
    assert entity_id_2 in entities
    assert entity_id_3 not in entities


def test_get_cell_calculation() -> None:
    """Test grid cell calculation for various positions."""
    grid = SpatialGrid(cell_size=10)
    position_1 = Vector2(x=0.0, y=0.0)
    position_2 = Vector2(x=9.9, y=9.9)
    position_3 = Vector2(x=10.0, y=10.0)
    position_4 = Vector2(x=-5.0, y=-5.0)
    assert grid._get_cell(position=position_1) == (0, 0)
    assert grid._get_cell(position=position_2) == (0, 0)
    assert grid._get_cell(position=position_3) == (1, 1)
    assert grid._get_cell(position=position_4) == (-1, -1)


def test_get_cell_with_negative_coordinates() -> None:
    """Test cell calculation handles negative coordinates."""
    grid = SpatialGrid(cell_size=10)
    position = Vector2(x=-15.0, y=-25.0)
    cell = grid._get_cell(position=position)
    expected_x = math.floor(-15.0 / 10)
    expected_y = math.floor(-25.0 / 10)
    assert cell == (expected_x, expected_y)


def test_add_entity_at_negative_position() -> None:
    """Test adding entity at negative coordinates."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(
        x=-fake.pyfloat(min_value=0, max_value=100),
        y=-fake.pyfloat(min_value=0, max_value=100),
    )
    grid.add(entity_id=entity_id, position=position)
    assert entity_id in grid._entity_positions
    entities = grid.get_at(position=position)
    assert entity_id in entities


def test_radius_query_with_zero_radius() -> None:
    """Test radius query with zero radius."""
    grid = SpatialGrid(cell_size=10)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(x=5.0, y=5.0)
    grid.add(entity_id=entity_id, position=position)
    entities_exact = grid.get_in_radius(position=position, radius=0.0)
    entities_offset = grid.get_in_radius(position=Vector2(x=6.0, y=6.0), radius=0.0)
    assert entity_id in entities_exact
    assert entity_id not in entities_offset


def test_radius_query_with_large_radius() -> None:
    """Test radius query with very large radius."""
    grid = SpatialGrid(cell_size=10)
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    position_1 = Vector2(x=0.0, y=0.0)
    position_2 = Vector2(x=100.0, y=100.0)
    grid.add(entity_id=entity_id_1, position=position_1)
    grid.add(entity_id=entity_id_2, position=position_2)
    entities = grid.get_in_radius(position=Vector2(x=50.0, y=50.0), radius=1000.0)
    assert entity_id_1 in entities
    assert entity_id_2 in entities


def test_multiple_entities_at_same_position() -> None:
    """Test multiple entities can exist at exact same position."""
    grid = SpatialGrid(cell_size=10)
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    position = Vector2(
        x=fake.pyfloat(min_value=0, max_value=100),
        y=fake.pyfloat(min_value=0, max_value=100),
    )
    grid.add(entity_id=entity_id_1, position=position)
    grid.add(entity_id=entity_id_2, position=position)
    entities = grid.get_at(position=position)
    assert entity_id_1 in entities
    assert entity_id_2 in entities
    assert len(entities) == 2


def test_get_in_radius_filters_by_actual_distance() -> None:
    """Test radius query uses actual distance not just cell proximity."""
    grid = SpatialGrid(cell_size=10)
    entity_id_far = EntityID(fake.uuid4())
    entity_id_near = EntityID(fake.uuid4())
    center = Vector2(x=15.0, y=15.0)
    position_far = Vector2(x=10.0, y=10.0)
    position_near = Vector2(x=16.0, y=16.0)
    grid.add(entity_id=entity_id_far, position=position_far)
    grid.add(entity_id=entity_id_near, position=position_near)
    entities = grid.get_in_radius(position=center, radius=2.0)
    assert entity_id_near in entities
    assert entity_id_far not in entities


def test_get_in_bounds() -> None:
    """Test getting entities within rectangular bounds."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    grid.add(entity_id=entity2, position=Vector2(x=150.0, y=150.0))
    grid.add(entity_id=entity3, position=Vector2(x=300.0, y=300.0))

    result = grid.get_in_bounds(
        min_pos=Vector2(x=50.0, y=50.0),
        max_pos=Vector2(x=200.0, y=200.0),
    )

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result


def test_get_in_bounds_empty() -> None:
    """Test bounds query with no entities."""
    grid = SpatialGrid(cell_size=10)

    result = grid.get_in_bounds(
        min_pos=Vector2(x=0.0, y=0.0),
        max_pos=Vector2(x=100.0, y=100.0),
    )

    assert len(result) == 0


def test_get_in_bounds_edge_cases() -> None:
    """Test entities exactly on bounds edges are included."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    grid.add(entity_id=entity2, position=Vector2(x=200.0, y=200.0))

    result = grid.get_in_bounds(
        min_pos=Vector2(x=100.0, y=100.0),
        max_pos=Vector2(x=200.0, y=200.0),
    )

    assert entity1 in result
    assert entity2 in result


def test_raycast() -> None:
    """Test raycast query returns entities along ray path."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    grid.add(entity_id=entity2, position=Vector2(x=200.0, y=200.0))
    grid.add(entity_id=entity3, position=Vector2(x=500.0, y=100.0))

    result = grid.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=500.0,
    )

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result


def test_raycast_empty() -> None:
    """Test raycast with no entities."""
    grid = SpatialGrid(cell_size=10)

    result = grid.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=0.0),
        max_distance=100.0,
    )

    assert len(result) == 0


def test_raycast_ordering() -> None:
    """Test raycast returns entities in distance order."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=300.0, y=300.0))
    grid.add(entity_id=entity2, position=Vector2(x=100.0, y=100.0))
    grid.add(entity_id=entity3, position=Vector2(x=200.0, y=200.0))

    result = grid.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=500.0,
    )

    assert result[0] == entity2
    assert result[1] == entity3
    assert result[2] == entity1


def test_get_nearest() -> None:
    """Test k-nearest neighbors query."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())
    entity4 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    grid.add(entity_id=entity2, position=Vector2(x=105.0, y=105.0))
    grid.add(entity_id=entity3, position=Vector2(x=200.0, y=200.0))
    grid.add(entity_id=entity4, position=Vector2(x=500.0, y=500.0))

    result = grid.get_nearest(position=Vector2(x=100.0, y=100.0), count=2)

    assert len(result) == 2
    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result
    assert entity4 not in result


def test_get_nearest_empty() -> None:
    """Test get_nearest with no entities."""
    grid = SpatialGrid(cell_size=10)

    result = grid.get_nearest(position=Vector2(x=100.0, y=100.0), count=5)

    assert len(result) == 0


def test_get_nearest_ordering() -> None:
    """Test get_nearest returns entities in distance order."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=300.0, y=300.0))
    grid.add(entity_id=entity2, position=Vector2(x=105.0, y=105.0))
    grid.add(entity_id=entity3, position=Vector2(x=110.0, y=110.0))

    result = grid.get_nearest(position=Vector2(x=100.0, y=100.0), count=3)

    assert result[0] == entity2
    assert result[1] == entity3
    assert result[2] == entity1


def test_get_nearest_less_than_count() -> None:
    """Test get_nearest when fewer entities exist than count requested."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    grid.add(entity_id=entity2, position=Vector2(x=105.0, y=105.0))

    result = grid.get_nearest(position=Vector2(x=100.0, y=100.0), count=10)

    assert len(result) == 2
    assert entity1 in result
    assert entity2 in result


def test_spatial_grid_creation_with_collision_mode() -> None:
    """Test SpatialGrid can be created with collision mode."""
    cell_size = fake.random_int(min=1, max=100)
    grid = SpatialGrid(cell_size=cell_size, collision_mode=CollisionMode.GRID_BOX)
    assert grid._cell_size == cell_size
    assert grid._collision_mode == CollisionMode.GRID_BOX


def test_spatial_grid_default_collision_mode() -> None:
    """Test SpatialGrid defaults to CIRCLE collision mode."""
    grid = SpatialGrid(cell_size=10)
    assert grid._collision_mode == CollisionMode.CIRCLE


def test_raycast_grid_box_mode() -> None:
    """Test raycast with GRID_BOX collision mode."""
    grid = SpatialGrid(cell_size=10, collision_mode=CollisionMode.GRID_BOX)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=5.0, y=5.0))
    grid.add(entity_id=entity2, position=Vector2(x=10.0, y=10.0))
    grid.add(entity_id=entity3, position=Vector2(x=50.0, y=5.0))

    result = grid.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=20.0,
    )

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result


def test_raycast_grid_box_mode_ordering() -> None:
    """Test raycast with GRID_BOX mode returns entities in distance order."""
    grid = SpatialGrid(cell_size=10, collision_mode=CollisionMode.GRID_BOX)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=20.0, y=20.0))
    grid.add(entity_id=entity2, position=Vector2(x=5.0, y=5.0))
    grid.add(entity_id=entity3, position=Vector2(x=10.0, y=10.0))

    result = grid.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=30.0,
    )

    assert result[0] == entity2
    assert result[1] == entity3
    assert result[2] == entity1


def test_ray_box_intersection_hit() -> None:
    """Test ray-box intersection detects hit."""
    origin = Vector2(x=0.0, y=0.5)
    direction_x = 1.0
    direction_y = 0.0
    box_x = 5.0
    box_y = 0.0

    distance = SpatialGrid._ray_box_intersection(
        ray_origin=origin,
        ray_dir_x=direction_x,
        ray_dir_y=direction_y,
        box_x=box_x,
        box_y=box_y,
        max_distance=10.0,
    )

    assert distance is not None
    assert distance == 4.5


def test_ray_box_intersection_miss() -> None:
    """Test ray-box intersection detects miss."""
    origin = Vector2(x=0.0, y=0.0)
    direction = Vector2(x=1.0, y=1.0).normalize()
    box_x = 10.0
    box_y = 0.0

    distance = SpatialGrid._ray_box_intersection(
        ray_origin=origin,
        ray_dir_x=direction.x,
        ray_dir_y=direction.y,
        box_x=box_x,
        box_y=box_y,
        max_distance=10.0,
    )

    assert distance is None


def test_ray_box_intersection_ray_parallel_to_x_axis() -> None:
    """Test ray-box intersection when ray is parallel to X axis."""
    origin = Vector2(x=0.0, y=0.5)
    direction_x = 1.0
    direction_y = 0.0
    box_x = 3.0
    box_y = 0.0

    distance = SpatialGrid._ray_box_intersection(
        ray_origin=origin,
        ray_dir_x=direction_x,
        ray_dir_y=direction_y,
        box_x=box_x,
        box_y=box_y,
        max_distance=10.0,
    )

    assert distance is not None
    assert distance == 2.5


def test_ray_box_intersection_ray_parallel_to_y_axis() -> None:
    """Test ray-box intersection when ray is parallel to Y axis."""
    origin = Vector2(x=0.5, y=0.0)
    direction_x = 0.0
    direction_y = 1.0
    box_x = 0.0
    box_y = 3.0

    distance = SpatialGrid._ray_box_intersection(
        ray_origin=origin,
        ray_dir_x=direction_x,
        ray_dir_y=direction_y,
        box_x=box_x,
        box_y=box_y,
        max_distance=10.0,
    )

    assert distance is not None
    assert distance == 2.5


def test_ray_box_intersection_ray_starting_inside_box() -> None:
    """Test ray-box intersection when ray starts inside box."""
    origin = Vector2(x=5.5, y=5.5)
    direction_x = 1.0
    direction_y = 0.0
    box_x = 5.0
    box_y = 5.0

    distance = SpatialGrid._ray_box_intersection(
        ray_origin=origin,
        ray_dir_x=direction_x,
        ray_dir_y=direction_y,
        box_x=box_x,
        box_y=box_y,
        max_distance=10.0,
    )

    assert distance is not None
    assert distance == 0.0


def test_ray_box_intersection_max_distance_boundary() -> None:
    """Test ray-box intersection respects max_distance."""
    origin = Vector2(x=0.0, y=0.5)
    direction_x = 1.0
    direction_y = 0.0
    box_x = 15.0
    box_y = 0.0

    distance = SpatialGrid._ray_box_intersection(
        ray_origin=origin,
        ray_dir_x=direction_x,
        ray_dir_y=direction_y,
        box_x=box_x,
        box_y=box_y,
        max_distance=10.0,
    )

    assert distance is None


def test_ray_box_intersection_diagonal_ray() -> None:
    """Test ray-box intersection with diagonal ray."""
    origin = Vector2(x=0.0, y=0.0)
    direction = Vector2(x=1.0, y=1.0).normalize()
    box_x = 5.0
    box_y = 5.0

    distance = SpatialGrid._ray_box_intersection(
        ray_origin=origin,
        ray_dir_x=direction.x,
        ray_dir_y=direction.y,
        box_x=box_x,
        box_y=box_y,
        max_distance=20.0,
    )

    assert distance is not None
    assert distance > 0


def test_ray_box_intersection_negative_direction() -> None:
    """Test ray-box intersection with ray pointing backwards."""
    origin = Vector2(x=10.0, y=0.5)
    direction_x = -1.0
    direction_y = 0.0
    box_x = 15.0
    box_y = 0.0

    distance = SpatialGrid._ray_box_intersection(
        ray_origin=origin,
        ray_dir_x=direction_x,
        ray_dir_y=direction_y,
        box_x=box_x,
        box_y=box_y,
        max_distance=10.0,
    )

    assert distance is None


def test_ray_box_intersection_box_behind_ray() -> None:
    """Test ray-box intersection when box is behind ray origin."""
    origin = Vector2(x=10.0, y=0.5)
    direction_x = 1.0
    direction_y = 0.0
    box_x = 5.0
    box_y = 0.0

    distance = SpatialGrid._ray_box_intersection(
        ray_origin=origin,
        ray_dir_x=direction_x,
        ray_dir_y=direction_y,
        box_x=box_x,
        box_y=box_y,
        max_distance=10.0,
    )

    assert distance is None


def test_ray_box_entry_point_returns_intersection() -> None:
    """ray_box_entry_point returns Vector2 intersection point."""
    origin = Vector2(x=0.0, y=0.5)
    direction = Vector2(x=1.0, y=0.0)
    box_position = Vector2(x=5.0, y=0.0)

    result = SpatialGrid.ray_box_entry_point(
        ray_origin=origin,
        ray_direction=direction,
        box_position=box_position,
        max_distance=20.0,
    )

    assert result is not None
    assert abs(result.x - 4.5) < 0.001
    assert abs(result.y - 0.5) < 0.001


def test_ray_box_entry_point_returns_none_on_miss() -> None:
    """ray_box_entry_point returns None when ray misses box."""
    origin = Vector2(x=0.0, y=0.5)
    direction = Vector2(x=1.0, y=0.0)
    box_position = Vector2(x=25.0, y=0.0)

    result = SpatialGrid.ray_box_entry_point(
        ray_origin=origin,
        ray_direction=direction,
        box_position=box_position,
        max_distance=10.0,
    )

    assert result is None


def test_ray_box_entry_point_axis_aligned() -> None:
    """ray_box_entry_point with axis-aligned ray along Y axis."""
    origin = Vector2(x=0.5, y=0.0)
    direction = Vector2(x=0.0, y=1.0)
    box_position = Vector2(x=0.0, y=3.0)

    result = SpatialGrid.ray_box_entry_point(
        ray_origin=origin,
        ray_direction=direction,
        box_position=box_position,
        max_distance=10.0,
    )

    assert result is not None
    assert abs(result.x - 0.5) < 0.001
    assert abs(result.y - 2.5) < 0.001


def test_ray_box_entry_point_diagonal() -> None:
    """ray_box_entry_point with diagonal ray."""
    sqrt2_half = math.sqrt(2) / 2
    origin = Vector2(x=0.0, y=0.0)
    direction = Vector2(x=sqrt2_half, y=sqrt2_half)
    box_position = Vector2(x=3.0, y=3.0)

    result = SpatialGrid.ray_box_entry_point(
        ray_origin=origin,
        ray_direction=direction,
        box_position=box_position,
        max_distance=20.0,
    )

    assert result is not None
    assert abs(result.x - 2.5) < 0.001
    assert abs(result.y - 2.5) < 0.001


def test_get_nearest_with_profiling() -> None:
    """Test get_nearest with profiling enabled."""
    grid = SpatialGrid(cell_size=10, profiling_enabled=True)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    grid.add(entity_id=entity2, position=Vector2(x=105.0, y=105.0))

    result = grid.get_nearest(position=Vector2(x=100.0, y=100.0), count=2)

    assert len(result) == 2
    assert entity1 in result
    assert entity2 in result


def test_get_nearest_zero_count() -> None:
    """Test get_nearest with count of zero."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    grid.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))

    result = grid.get_nearest(position=Vector2(x=100.0, y=100.0), count=0)

    assert len(result) == 0


def test_get_in_radius_with_predicate() -> None:
    """Test get_in_radius with predicate filter."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=50.0, y=50.0))
    grid.add(entity_id=entity2, position=Vector2(x=51.0, y=50.0))
    grid.add(entity_id=entity3, position=Vector2(x=52.0, y=50.0))

    allowed_entities = {entity1, entity2}
    result = grid.get_in_radius(
        position=Vector2(x=50.0, y=50.0),
        radius=5.0,
        predicate=lambda e: e in allowed_entities,
    )

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result


def test_get_in_radius_along_ray() -> None:
    """Test get entities within radius of ray path."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=10.0, y=10.0))
    grid.add(entity_id=entity2, position=Vector2(x=20.0, y=20.0))
    grid.add(entity_id=entity3, position=Vector2(x=30.0, y=30.0))

    result = grid.get_in_radius_along_ray(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=50.0,
        radius=2.0,
    )

    assert entity1 in result
    assert entity2 in result
    assert entity3 in result


def test_get_in_radius_along_ray_empty() -> None:
    """Test get_in_radius_along_ray with no entities."""
    grid = SpatialGrid(cell_size=10)

    result = grid.get_in_radius_along_ray(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=0.0),
        max_distance=100.0,
        radius=5.0,
    )

    assert len(result) == 0


def test_get_in_radius_along_ray_ordering() -> None:
    """Test get_in_radius_along_ray returns entities ordered near to far."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=200.0, y=200.0))
    grid.add(entity_id=entity2, position=Vector2(x=50.0, y=50.0))
    grid.add(entity_id=entity3, position=Vector2(x=100.0, y=100.0))

    result = grid.get_in_radius_along_ray(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=300.0,
        radius=2.0,
    )

    assert result[0] == entity2
    assert result[1] == entity3
    assert result[2] == entity1


def test_get_in_radius_along_ray_entity_before_origin() -> None:
    """Test get_in_radius_along_ray with entity before ray origin."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=48.0, y=50.0))
    grid.add(entity_id=entity2, position=Vector2(x=100.0, y=100.0))

    result = grid.get_in_radius_along_ray(
        origin=Vector2(x=50.0, y=50.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=100.0,
        radius=3.0,
    )

    assert entity1 in result
    assert entity2 in result


def test_get_in_radius_along_ray_entity_after_max_distance() -> None:
    """Test get_in_radius_along_ray with entity near endpoint."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=50.0, y=50.0))
    grid.add(entity_id=entity2, position=Vector2(x=72.0, y=72.0))

    result = grid.get_in_radius_along_ray(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=100.0,
        radius=3.0,
    )

    assert entity1 in result
    assert entity2 in result


def test_get_in_radius_along_ray_entity_outside_radius() -> None:
    """Test get_in_radius_along_ray excludes entities outside radius."""
    grid = SpatialGrid(cell_size=10)
    entity_near = EntityID(fake.uuid4())
    entity_far = EntityID(fake.uuid4())

    grid.add(entity_id=entity_near, position=Vector2(x=100.0, y=2.0))
    grid.add(entity_id=entity_far, position=Vector2(x=100.0, y=20.0))

    result = grid.get_in_radius_along_ray(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=0.0),
        max_distance=200.0,
        radius=5.0,
    )

    assert entity_near in result
    assert entity_far not in result


def test_get_in_radius_along_ray_uses_closest_point_on_segment() -> None:
    """Test get_in_radius_along_ray calculates distance to closest point."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=50.0, y=51.0))

    result = grid.get_in_radius_along_ray(
        origin=Vector2(x=0.0, y=50.0),
        direction=Vector2(x=1.0, y=0.0),
        max_distance=100.0,
        radius=2.0,
    )

    assert entity1 in result


def test_get_grid_cells_along_ray() -> None:
    """Test get grid cells ray passes through using DDA algorithm."""
    grid = SpatialGrid(cell_size=1)

    cells = grid.get_grid_cells_along_ray(
        origin=Vector2(x=0.5, y=0.5),
        direction=Vector2(x=1.0, y=0.0),
        max_distance=5.0,
    )

    assert len(cells) > 0
    assert Vector2(x=0.0, y=0.0) in cells
    assert Vector2(x=1.0, y=0.0) in cells
    assert Vector2(x=2.0, y=0.0) in cells


def test_get_grid_cells_along_ray_diagonal() -> None:
    """Test get_grid_cells_along_ray with diagonal ray."""
    grid = SpatialGrid(cell_size=1)

    cells = grid.get_grid_cells_along_ray(
        origin=Vector2(x=0.5, y=0.5),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=5.0,
    )

    assert len(cells) > 0
    assert Vector2(x=0.0, y=0.0) in cells


def test_get_grid_cells_along_ray_negative_direction_x() -> None:
    """Test get_grid_cells_along_ray with negative X direction."""
    grid = SpatialGrid(cell_size=1)

    cells = grid.get_grid_cells_along_ray(
        origin=Vector2(x=5.5, y=0.5),
        direction=Vector2(x=-1.0, y=0.0),
        max_distance=5.0,
    )

    assert len(cells) > 0
    assert Vector2(x=5.0, y=0.0) in cells
    assert Vector2(x=4.0, y=0.0) in cells


def test_get_grid_cells_along_ray_negative_direction_y() -> None:
    """Test get_grid_cells_along_ray with negative Y direction."""
    grid = SpatialGrid(cell_size=1)

    cells = grid.get_grid_cells_along_ray(
        origin=Vector2(x=0.5, y=5.5),
        direction=Vector2(x=0.0, y=-1.0),
        max_distance=5.0,
    )

    assert len(cells) > 0
    assert Vector2(x=0.0, y=5.0) in cells
    assert Vector2(x=0.0, y=4.0) in cells


def test_get_grid_cells_along_ray_zero_x_direction() -> None:
    """Test get_grid_cells_along_ray with zero X direction."""
    grid = SpatialGrid(cell_size=1)

    cells = grid.get_grid_cells_along_ray(
        origin=Vector2(x=0.5, y=0.5),
        direction=Vector2(x=0.0, y=1.0),
        max_distance=3.0,
    )

    assert len(cells) > 0
    assert Vector2(x=0.0, y=0.0) in cells


def test_get_grid_cells_along_ray_zero_y_direction() -> None:
    """Test get_grid_cells_along_ray with zero Y direction."""
    grid = SpatialGrid(cell_size=1)

    cells = grid.get_grid_cells_along_ray(
        origin=Vector2(x=0.5, y=0.5),
        direction=Vector2(x=1.0, y=0.0),
        max_distance=3.0,
    )

    assert len(cells) > 0
    assert Vector2(x=0.0, y=0.0) in cells


def test_get_grid_cells_along_ray_short_distance() -> None:
    """Test get_grid_cells_along_ray with very short distance."""
    grid = SpatialGrid(cell_size=1)

    cells = grid.get_grid_cells_along_ray(
        origin=Vector2(x=0.5, y=0.5),
        direction=Vector2(x=1.0, y=0.0),
        max_distance=0.1,
    )

    assert len(cells) == 1
    assert Vector2(x=0.0, y=0.0) in cells


def test_get_grid_cells_along_ray_traverses_cells_correctly() -> None:
    """Test get_grid_cells_along_ray traverses multiple cells."""
    grid = SpatialGrid(cell_size=1)

    cells = grid.get_grid_cells_along_ray(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=3.0,
    )

    assert len(cells) >= 3


def test_get_nearest_negative_count() -> None:
    """Test get_nearest with negative count returns empty list."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    grid.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))

    result = grid.get_nearest(position=Vector2(x=100.0, y=100.0), count=-1)

    assert len(result) == 0


def test_get_nearest_exceeds_max_radius() -> None:
    """Test get_nearest when entities are very far apart."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=50000.0, y=50000.0))

    result = grid.get_nearest(position=Vector2(x=0.0, y=0.0), count=1)

    assert len(result) == 1
    assert entity1 in result


def test_get_positions_filtered() -> None:
    """Test get_positions_filtered with predicate function."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    position1 = Vector2(x=10.0, y=10.0)
    position2 = Vector2(x=20.0, y=20.0)
    position3 = Vector2(x=30.0, y=30.0)

    grid.add(entity_id=entity1, position=position1)
    grid.add(entity_id=entity2, position=position2)
    grid.add(entity_id=entity3, position=position3)

    allowed_entities = {entity1, entity3}
    result = grid.get_positions_filtered(predicate=lambda e: e in allowed_entities)

    assert len(result) == 2
    assert entity1 in result
    assert result[entity1] == position1
    assert entity3 in result
    assert result[entity3] == position3
    assert entity2 not in result


def test_get_positions_filtered_empty() -> None:
    """Test get_positions_filtered with no matching entities."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=10.0, y=10.0))

    result = grid.get_positions_filtered(predicate=lambda e: False)

    assert len(result) == 0


def test_get_positions_filtered_all_match() -> None:
    """Test get_positions_filtered when all entities match predicate."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    position1 = Vector2(x=10.0, y=10.0)
    position2 = Vector2(x=20.0, y=20.0)

    grid.add(entity_id=entity1, position=position1)
    grid.add(entity_id=entity2, position=position2)

    result = grid.get_positions_filtered(predicate=lambda e: True)

    assert len(result) == 2
    assert entity1 in result
    assert entity2 in result


def test_get_positions_by_component_no_world() -> None:
    """Test get_positions_by_component returns empty when no world is set."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=10.0, y=10.0))

    result = grid.get_positions_by_component(component_type=TestComponent)

    assert len(result) == 0


def test_get_positions_by_component_with_world() -> None:
    """Test get_positions_by_component retrieves entity positions."""
    world = ECSWorld()
    grid = SpatialGrid(cell_size=10)
    grid.set_world(world=world)

    entity1 = world.create_entity()
    entity2 = world.create_entity()
    entity3 = world.create_entity()

    position1 = Vector2(x=10.0, y=10.0)
    position2 = Vector2(x=20.0, y=20.0)
    position3 = Vector2(x=30.0, y=30.0)

    grid.add(entity_id=entity1, position=position1)
    grid.add(entity_id=entity2, position=position2)
    grid.add(entity_id=entity3, position=position3)

    world.add_component(entity_id=entity1, component=TestComponent(value=1))
    world.add_component(entity_id=entity2, component=TestComponent(value=2))

    result = grid.get_positions_by_component(component_type=TestComponent)

    assert len(result) == 2
    assert entity1 in result
    assert result[entity1] == position1
    assert entity2 in result
    assert result[entity2] == position2
    assert entity3 not in result


def test_get_positions_by_component_excludes_entity() -> None:
    """Test get_positions_by_component can exclude specific entity."""
    world = ECSWorld()
    grid = SpatialGrid(cell_size=10)
    grid.set_world(world=world)

    entity1 = world.create_entity()
    entity2 = world.create_entity()

    position1 = Vector2(x=10.0, y=10.0)
    position2 = Vector2(x=20.0, y=20.0)

    grid.add(entity_id=entity1, position=position1)
    grid.add(entity_id=entity2, position=position2)

    world.add_component(entity_id=entity1, component=TestComponent(value=1))
    world.add_component(entity_id=entity2, component=TestComponent(value=2))

    result = grid.get_positions_by_component(
        component_type=TestComponent,
        exclude_entity=entity1,
    )

    assert len(result) == 1
    assert entity1 not in result
    assert entity2 in result
    assert result[entity2] == position2


def test_get_positions_by_component_caches_results() -> None:
    """Test get_positions_by_component caches results per tick."""
    world = ECSWorld()
    grid = SpatialGrid(cell_size=10)
    grid.set_world(world=world)

    entity1 = world.create_entity()
    position1 = Vector2(x=10.0, y=10.0)
    grid.add(entity_id=entity1, position=position1)
    world.add_component(entity_id=entity1, component=TestComponent(value=1))

    result1 = grid.get_positions_by_component(component_type=TestComponent)
    assert len(result1) == 1

    entity2 = world.create_entity()
    position2 = Vector2(x=20.0, y=20.0)
    grid.add(entity_id=entity2, position=position2)
    world.add_component(entity_id=entity2, component=TestComponent(value=2))

    result2 = grid.get_positions_by_component(component_type=TestComponent)
    assert len(result2) == 1

    world.increment_tick()

    result3 = grid.get_positions_by_component(component_type=TestComponent)
    assert len(result3) == 2


def test_get_positions_by_component_exclude_entity_not_in_results() -> None:
    """Test get_positions_by_component with exclude_entity that doesn't match."""
    world = ECSWorld()
    grid = SpatialGrid(cell_size=10)
    grid.set_world(world=world)

    entity1 = world.create_entity()
    entity2 = world.create_entity()

    position1 = Vector2(x=10.0, y=10.0)
    grid.add(entity_id=entity1, position=position1)
    world.add_component(entity_id=entity1, component=TestComponent(value=1))

    result = grid.get_positions_by_component(
        component_type=TestComponent,
        exclude_entity=entity2,
    )

    assert len(result) == 1
    assert entity1 in result


def test_get_static_positions_by_component_no_world() -> None:
    """Test get_static_positions_by_component returns empty when no world is set."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=10.0, y=10.0))

    result = grid.get_static_positions_by_component(component_type=TestComponent)

    assert len(result) == 0


def test_get_static_positions_by_component_with_world() -> None:
    """Test get_static_positions_by_component retrieves static positions."""
    world = ECSWorld()
    grid = SpatialGrid(cell_size=10)
    grid.set_world(world=world)

    entity1 = world.create_entity()
    entity2 = world.create_entity()
    entity3 = world.create_entity()

    position1 = Vector2(x=10.0, y=10.0)
    position2 = Vector2(x=20.0, y=20.0)
    position3 = Vector2(x=30.0, y=30.0)

    grid.add(entity_id=entity1, position=position1)
    grid.add(entity_id=entity2, position=position2)
    grid.add(entity_id=entity3, position=position3)

    world.add_component(entity_id=entity1, component=TestComponent(value=1))
    world.add_component(entity_id=entity2, component=TestComponent(value=2))

    result = grid.get_static_positions_by_component(component_type=TestComponent)

    assert len(result) == 2
    assert position1 in result
    assert position2 in result
    assert position3 not in result


def test_get_static_positions_by_component_caches_permanently() -> None:
    """Test get_static_positions_by_component caches results permanently."""
    world = ECSWorld()
    grid = SpatialGrid(cell_size=10)
    grid.set_world(world=world)

    entity1 = world.create_entity()
    position1 = Vector2(x=10.0, y=10.0)
    grid.add(entity_id=entity1, position=position1)
    world.add_component(entity_id=entity1, component=TestComponent(value=1))

    result1 = grid.get_static_positions_by_component(component_type=TestComponent)
    assert len(result1) == 1

    entity2 = world.create_entity()
    position2 = Vector2(x=20.0, y=20.0)
    grid.add(entity_id=entity2, position=position2)
    world.add_component(entity_id=entity2, component=TestComponent(value=2))

    world.increment_tick()

    result2 = grid.get_static_positions_by_component(component_type=TestComponent)
    assert len(result2) == 1


def test_invalidate_static_cache_drops_a_removed_entity() -> None:
    """A destroyed static entity stops being reported as occupying its cell."""
    world = ECSWorld()
    grid = SpatialGrid(cell_size=10)
    grid.set_world(world=world)

    entity1 = world.create_entity()
    entity2 = world.create_entity()
    position1 = Vector2(x=10.0, y=10.0)
    position2 = Vector2(x=20.0, y=20.0)
    grid.add(entity_id=entity1, position=position1)
    grid.add(entity_id=entity2, position=position2)
    world.add_component(entity_id=entity1, component=TestComponent(value=1))
    world.add_component(entity_id=entity2, component=TestComponent(value=2))

    assert (
        len(grid.get_static_positions_by_component(component_type=TestComponent)) == 2
    )

    world.destroy_entity(entity_id=entity1)
    world.update(delta_time=0.0)
    grid.remove(entity_id=entity1)
    grid.invalidate_static_cache()

    result = grid.get_static_positions_by_component(component_type=TestComponent)

    assert result == {position2}


def test_invalidate_static_cache_advances_the_static_version() -> None:
    """The revision is what lets a caller cache statics without a timer."""
    grid = SpatialGrid(cell_size=10)
    before = grid.static_version

    grid.invalidate_static_cache()

    assert grid.static_version != before


def test_get_static_positions_by_component_returns_copy() -> None:
    """Test get_static_positions_by_component returns copy of cached data."""
    world = ECSWorld()
    grid = SpatialGrid(cell_size=10)
    grid.set_world(world=world)

    entity1 = world.create_entity()
    position1 = Vector2(x=10.0, y=10.0)
    grid.add(entity_id=entity1, position=position1)
    world.add_component(entity_id=entity1, component=TestComponent(value=1))

    result1 = grid.get_static_positions_by_component(component_type=TestComponent)
    result2 = grid.get_static_positions_by_component(component_type=TestComponent)

    assert result1 is not result2
    assert result1 == result2


def test_set_world() -> None:
    """Test set_world wires grid to ECS world."""
    world = ECSWorld()
    grid = SpatialGrid(cell_size=10)

    assert grid._world is None

    grid.set_world(world=world)

    assert grid._world is world


def test_query_component_positions_no_world() -> None:
    """Test _query_component_positions returns empty dict when no world set."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID(fake.uuid4())

    grid.add(entity_id=entity1, position=Vector2(x=10.0, y=10.0))

    result = grid._query_component_positions(component_type=TestComponent)

    assert len(result) == 0
    assert result == {}


def test_raycast_equal_distance_resolves_by_entity_id() -> None:
    """Equal-distance raycast hits resolve in canonical entity_id order.

    Regression for a determinism bug where equal-distance ties resolved via
    non-deterministic set iteration order rather than a stable entity_id key.
    """
    position = Vector2(x=100.0, y=100.0)
    forward_grid = SpatialGrid(cell_size=10)
    reverse_grid = SpatialGrid(cell_size=10)
    for entity_id in ("aaaa", "bbbb", "cccc"):
        forward_grid.add(entity_id=EntityID(entity_id), position=position)
    for entity_id in ("cccc", "bbbb", "aaaa"):
        reverse_grid.add(entity_id=EntityID(entity_id), position=position)

    origin = Vector2(x=0.0, y=0.0)
    direction = Vector2(x=1.0, y=1.0).normalize()
    forward = forward_grid.raycast(
        origin=origin, direction=direction, max_distance=500.0
    )
    reverse = reverse_grid.raycast(
        origin=origin, direction=direction, max_distance=500.0
    )

    assert forward == reverse
    assert forward == [EntityID("aaaa"), EntityID("bbbb"), EntityID("cccc")]


def test_get_nearest_equal_distance_resolves_by_entity_id() -> None:
    """Equal-distance get_nearest results resolve in canonical entity_id order."""
    position = Vector2(x=50.0, y=50.0)
    forward_grid = SpatialGrid(cell_size=10)
    reverse_grid = SpatialGrid(cell_size=10)
    for entity_id in ("aaaa", "bbbb", "cccc"):
        forward_grid.add(entity_id=EntityID(entity_id), position=position)
    for entity_id in ("cccc", "bbbb", "aaaa"):
        reverse_grid.add(entity_id=EntityID(entity_id), position=position)

    query = Vector2(x=0.0, y=0.0)
    forward = forward_grid.get_nearest(position=query, count=2)
    reverse = reverse_grid.get_nearest(position=query, count=2)

    assert forward == reverse
    assert forward == [EntityID("aaaa"), EntityID("bbbb")]


def test_raycast_hits_target_flush_against_wall() -> None:
    """A ray aimed at a target's position strikes it, not an adjacent wall.

    Regression: positions are cell centers, so a ray aimed at a target that is
    flush against a wall must hit the target's centered box instead of grazing
    the shared cell corner and striking the neighbouring wall. The shooter at
    (4, 5) aiming at the target at (1, 9) forms a clean 3-4-5 diagonal that
    previously grazed the corner shared with the wall at (0, 8).
    """
    grid = SpatialGrid(cell_size=1, collision_mode=CollisionMode.GRID_BOX)
    shooter = EntityID("shooter")
    target = EntityID("target")
    wall = EntityID("wall")
    grid.add(entity_id=shooter, position=Vector2(x=4.0, y=5.0))
    grid.add(entity_id=target, position=Vector2(x=1.0, y=9.0))
    grid.add(entity_id=wall, position=Vector2(x=0.0, y=8.0))

    direction = Vector2(x=1.0 - 4.0, y=9.0 - 5.0).normalize()
    hits = [
        hit
        for hit in grid.raycast(
            origin=Vector2(x=4.0, y=5.0),
            direction=direction,
            max_distance=25.0,
        )
        if hit != shooter
    ]

    assert hits
    assert hits[0] == target
    assert wall not in hits


def test_collect_cell_candidates_occupied_scan_branch() -> None:
    """Occupied-cell scan fires when the bounding box exceeds occupied cells."""
    grid = SpatialGrid(cell_size=1)
    inside_id = EntityID(fake.uuid4())
    outside_id = EntityID(fake.uuid4())
    grid.add(entity_id=inside_id, position=Vector2(x=2.0, y=3.0))
    grid.add(entity_id=outside_id, position=Vector2(x=90.0, y=90.0))
    candidates = grid._collect_cell_candidates(
        min_cell_x=0, max_cell_x=50, min_cell_y=0, max_cell_y=50
    )
    assert candidates == {inside_id}


def test_collect_cell_candidates_bbox_scan_branch() -> None:
    """Bounding-box scan fires when occupied cells exceed the box size."""
    grid = SpatialGrid(cell_size=1)
    inside_id_1 = EntityID(fake.uuid4())
    inside_id_2 = EntityID(fake.uuid4())
    outside_id = EntityID(fake.uuid4())
    grid.add(entity_id=inside_id_1, position=Vector2(x=0.0, y=0.0))
    grid.add(entity_id=inside_id_2, position=Vector2(x=1.0, y=0.0))
    grid.add(entity_id=outside_id, position=Vector2(x=5.0, y=5.0))
    candidates = grid._collect_cell_candidates(
        min_cell_x=0, max_cell_x=1, min_cell_y=0, max_cell_y=0
    )
    assert candidates == {inside_id_1, inside_id_2}


def test_collect_cell_candidates_branches_agree() -> None:
    """Both branches produce identical candidates for the same box."""
    grid = SpatialGrid(cell_size=1)
    inside_ids = [EntityID(fake.uuid4()) for _ in range(4)]
    inside_positions = [
        Vector2(x=-1.0, y=-1.0),
        Vector2(x=0.0, y=0.0),
        Vector2(x=1.0, y=0.0),
        Vector2(x=0.0, y=1.0),
    ]
    for entity_id, position in zip(inside_ids, inside_positions, strict=True):
        grid.add(entity_id=entity_id, position=position)
    for offset in range(20):
        grid.add(
            entity_id=EntityID(fake.uuid4()),
            position=Vector2(x=float(10 + offset), y=10.0),
        )
    bbox_scan = grid._collect_cell_candidates(
        min_cell_x=-1, max_cell_x=1, min_cell_y=-1, max_cell_y=1
    )
    occupied_scan = grid._collect_cell_candidates(
        min_cell_x=-30, max_cell_x=1, min_cell_y=-30, max_cell_y=1
    )
    assert bbox_scan == occupied_scan == set(inside_ids)


def test_collect_cell_candidates_occupied_scan_preserves_iteration_order() -> None:
    """The occupied-cell scan builds candidates in bbox scan order.

    The sorted() visit over occupied cells is load-bearing: downstream
    consumers iterate the returned sets unsorted and sum floats, so the
    set insertion sequence (and therefore iteration order) must match
    what the bounding-box scan produces.
    """
    grid = SpatialGrid(cell_size=1)
    for index in range(120):
        grid.add(
            entity_id=EntityID(fake.uuid4()),
            position=Vector2(x=float(index % 15 - 7), y=float(index // 15 - 4)),
        )
    min_cell_x, max_cell_x, min_cell_y, max_cell_y = -20, 20, -20, 20
    bbox_oracle: set[EntityID] = set()
    for cell_x in range(min_cell_x, max_cell_x + 1):
        for cell_y in range(min_cell_y, max_cell_y + 1):
            cell_entities = grid._grid.get((cell_x, cell_y))
            if cell_entities:
                bbox_oracle.update(cell_entities)
    occupied_scan = grid._collect_cell_candidates(
        min_cell_x=min_cell_x,
        max_cell_x=max_cell_x,
        min_cell_y=min_cell_y,
        max_cell_y=max_cell_y,
    )
    assert list(occupied_scan) == list(bbox_oracle)


def test_get_in_radius_large_radius_over_sparse_grid() -> None:
    """Radius query over a sparse grid still applies the exact distance test."""
    grid = SpatialGrid(cell_size=1)
    near_id = EntityID(fake.uuid4())
    far_id = EntityID(fake.uuid4())
    grid.add(entity_id=near_id, position=Vector2(x=3.0, y=4.0))
    grid.add(entity_id=far_id, position=Vector2(x=200.0, y=0.0))
    entities = grid.get_in_radius(position=Vector2(x=0.0, y=0.0), radius=100.0)
    assert entities == {near_id}
