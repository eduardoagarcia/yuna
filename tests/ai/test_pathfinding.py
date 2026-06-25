"""Tests for pathfinding infrastructure."""

from yuna.ai.pathfinding import (
    GridPathfinding,
    PathComponent,
    PathRequest,
)
from yuna.types.vector import Vector2


def test_grid_pathfinding_creation() -> None:
    """Test creating GridPathfinding with defaults."""
    pathfinder = GridPathfinding()

    assert pathfinder.grid_size == 1.0
    assert pathfinder.allow_diagonal is True


def test_grid_pathfinding_with_custom_grid_size() -> None:
    """Test GridPathfinding with custom grid size."""
    pathfinder = GridPathfinding(grid_size=2.0)

    assert pathfinder.grid_size == 2.0


def test_grid_pathfinding_simple_path() -> None:
    """Test finding simple straight path."""
    pathfinder = GridPathfinding(grid_size=1.0)

    path = pathfinder.find_path(
        start=Vector2(x=0.0, y=0.0),
        goal=Vector2(x=3.0, y=0.0),
    )

    assert path is not None
    assert len(path) == 4
    assert path[0] == Vector2(x=0.5, y=0.5)
    assert path[-1] == Vector2(x=3.5, y=0.5)


def test_grid_pathfinding_diagonal_path() -> None:
    """Test finding diagonal path."""
    pathfinder = GridPathfinding(grid_size=1.0, allow_diagonal=True)

    path = pathfinder.find_path(
        start=Vector2(x=0.0, y=0.0),
        goal=Vector2(x=3.0, y=3.0),
    )

    assert path is not None
    assert len(path) == 4


def test_grid_pathfinding_no_diagonal_movement() -> None:
    """Test pathfinding with diagonal movement disabled."""
    pathfinder = GridPathfinding(grid_size=1.0, allow_diagonal=False)

    path = pathfinder.find_path(
        start=Vector2(x=0.0, y=0.0),
        goal=Vector2(x=2.0, y=2.0),
    )

    assert path is not None
    assert len(path) == 5


def test_grid_pathfinding_with_obstacles() -> None:
    """Test pathfinding around obstacles."""
    obstacles = {Vector2(x=1.5, y=0.5), Vector2(x=1.5, y=1.5)}

    def walkable_checker(position: Vector2, context=None) -> bool:
        grid_x = int(position.x)
        grid_y = int(position.y)
        check_pos = Vector2(x=grid_x + 0.5, y=grid_y + 0.5)
        return check_pos not in obstacles

    pathfinder = GridPathfinding(
        grid_size=1.0,
        walkable_checker=walkable_checker,
    )

    path = pathfinder.find_path(
        start=Vector2(x=0.0, y=0.0),
        goal=Vector2(x=2.0, y=0.0),
    )

    assert path is not None
    assert len(path) > 3


def test_grid_pathfinding_no_path_found() -> None:
    """Test pathfinding when goal is blocked."""
    obstacles = {
        Vector2(x=1.5, y=0.5),
        Vector2(x=1.5, y=1.5),
        Vector2(x=1.5, y=2.5),
        Vector2(x=2.5, y=0.5),
        Vector2(x=2.5, y=1.5),
        Vector2(x=2.5, y=2.5),
    }

    def walkable_checker(position: Vector2, context=None) -> bool:
        grid_x = int(position.x)
        grid_y = int(position.y)
        check_pos = Vector2(x=grid_x + 0.5, y=grid_y + 0.5)
        return check_pos not in obstacles

    pathfinder = GridPathfinding(
        grid_size=1.0,
        walkable_checker=walkable_checker,
    )

    path = pathfinder.find_path(
        start=Vector2(x=0.0, y=0.0),
        goal=Vector2(x=2.0, y=1.0),
    )

    assert path is None


def test_grid_pathfinding_unwalkable_goal() -> None:
    """Test pathfinding when goal is unwalkable."""

    def walkable_checker(position: Vector2, context=None) -> bool:
        return position != Vector2(x=5.5, y=5.5)

    pathfinder = GridPathfinding(
        grid_size=1.0,
        walkable_checker=walkable_checker,
    )

    path = pathfinder.find_path(
        start=Vector2(x=0.0, y=0.0),
        goal=Vector2(x=5.0, y=5.0),
    )

    assert path is None


def test_grid_pathfinding_is_walkable_with_checker() -> None:
    """Test is_walkable with custom checker."""

    def walkable_checker(position: Vector2, context=None) -> bool:
        return position.x >= 0.0

    pathfinder = GridPathfinding(walkable_checker=walkable_checker)

    assert pathfinder.is_walkable(position=Vector2(x=1.0, y=0.0)) is True
    assert pathfinder.is_walkable(position=Vector2(x=-1.0, y=0.0)) is False


def test_grid_pathfinding_is_walkable_without_checker() -> None:
    """Test is_walkable without custom checker returns True."""
    pathfinder = GridPathfinding()

    assert pathfinder.is_walkable(position=Vector2(x=1.0, y=0.0)) is True
    assert pathfinder.is_walkable(position=Vector2(x=-1.0, y=0.0)) is True


def test_grid_pathfinding_custom_heuristic() -> None:
    """Test pathfinding with custom heuristic."""

    def manhattan_distance(a: Vector2, b: Vector2) -> float:
        return abs(a.x - b.x) + abs(a.y - b.y)

    pathfinder = GridPathfinding(
        grid_size=1.0,
        heuristic=manhattan_distance,
    )

    path = pathfinder.find_path(
        start=Vector2(x=0.0, y=0.0),
        goal=Vector2(x=3.0, y=3.0),
    )

    assert path is not None
    assert len(path) >= 4


def test_path_component_creation() -> None:
    """Test creating PathComponent with defaults."""
    component = PathComponent()

    assert component.waypoints == []
    assert component.current_waypoint_index == 0
    assert component.goal is None
    assert component.recalculate_on_blocked is True
    assert component.waypoint_threshold == 1.0


def test_path_component_with_waypoints() -> None:
    """Test creating PathComponent with waypoints."""
    waypoints = [
        Vector2(x=0.0, y=0.0),
        Vector2(x=5.0, y=5.0),
        Vector2(x=10.0, y=10.0),
    ]
    component = PathComponent(waypoints=waypoints)

    assert component.waypoints == waypoints
    assert len(component.waypoints) == 3


def test_path_component_get_current_waypoint() -> None:
    """Test getting current waypoint."""
    waypoints = [
        Vector2(x=0.0, y=0.0),
        Vector2(x=5.0, y=5.0),
        Vector2(x=10.0, y=10.0),
    ]
    component = PathComponent(waypoints=waypoints)

    current = component.get_current_waypoint()

    assert current == Vector2(x=0.0, y=0.0)


def test_path_component_get_current_waypoint_empty() -> None:
    """Test getting current waypoint with empty path."""
    component = PathComponent()

    current = component.get_current_waypoint()

    assert current is None


def test_path_component_advance_waypoint() -> None:
    """Test advancing to next waypoint."""
    waypoints = [
        Vector2(x=0.0, y=0.0),
        Vector2(x=5.0, y=5.0),
        Vector2(x=10.0, y=10.0),
    ]
    component = PathComponent(waypoints=waypoints)

    component.advance_waypoint()

    assert component.current_waypoint_index == 1
    assert component.get_current_waypoint() == Vector2(x=5.0, y=5.0)


def test_path_component_is_complete() -> None:
    """Test checking if path is complete."""
    waypoints = [Vector2(x=0.0, y=0.0), Vector2(x=5.0, y=5.0)]
    component = PathComponent(waypoints=waypoints)

    assert component.is_complete() is False

    component.current_waypoint_index = 2

    assert component.is_complete() is True


def test_path_component_is_complete_empty_path() -> None:
    """Test is_complete with empty path."""
    component = PathComponent()

    assert component.is_complete() is True


def test_path_component_clear_path() -> None:
    """Test clearing path."""
    waypoints = [Vector2(x=0.0, y=0.0), Vector2(x=5.0, y=5.0)]
    component = PathComponent(waypoints=waypoints, current_waypoint_index=1)

    component.clear_path()

    assert component.waypoints == []
    assert component.current_waypoint_index == 0


def test_path_component_set_path() -> None:
    """Test setting new path."""
    component = PathComponent()
    new_waypoints = [
        Vector2(x=1.0, y=1.0),
        Vector2(x=2.0, y=2.0),
    ]
    goal = Vector2(x=10.0, y=10.0)

    component.set_path(waypoints=new_waypoints, goal=goal)

    assert component.waypoints == new_waypoints
    assert component.current_waypoint_index == 0
    assert component.goal == goal


def test_path_component_set_path_without_goal() -> None:
    """Test setting path without goal."""
    component = PathComponent()
    new_waypoints = [Vector2(x=1.0, y=1.0)]

    component.set_path(waypoints=new_waypoints)

    assert component.waypoints == new_waypoints
    assert component.goal is None


def test_path_request_creation() -> None:
    """Test creating PathRequest."""
    goal = Vector2(x=10.0, y=10.0)
    request = PathRequest(goal=goal)

    assert request.goal == goal
    assert request.priority == 0


def test_path_request_with_priority() -> None:
    """Test creating PathRequest with priority."""
    goal = Vector2(x=10.0, y=10.0)
    request = PathRequest(goal=goal, priority=5)

    assert request.goal == goal
    assert request.priority == 5


def test_grid_pathfinding_same_start_and_goal() -> None:
    """Test pathfinding when start equals goal."""
    pathfinder = GridPathfinding(grid_size=1.0)

    path = pathfinder.find_path(
        start=Vector2(x=5.0, y=5.0),
        goal=Vector2(x=5.0, y=5.0),
    )

    assert path is not None
    assert len(path) == 1
    assert path[0] == Vector2(x=5.5, y=5.5)


def test_grid_pathfinding_negative_coordinates() -> None:
    """Test pathfinding with negative coordinates."""
    pathfinder = GridPathfinding(grid_size=1.0)

    path = pathfinder.find_path(
        start=Vector2(x=-3.0, y=-3.0),
        goal=Vector2(x=3.0, y=3.0),
    )

    assert path is not None
    assert len(path) > 0


def test_path_component_advance_past_end() -> None:
    """Test advancing waypoint past end of path."""
    waypoints = [Vector2(x=0.0, y=0.0)]
    component = PathComponent(waypoints=waypoints)

    component.advance_waypoint()
    component.advance_waypoint()

    assert component.current_waypoint_index == 2
    assert component.get_current_waypoint() is None
    assert component.is_complete() is True


def test_grid_pathfinding_goal_separated_by_wall() -> None:
    """Test pathfinding when goal is separated by impassable wall."""
    min_coord = -5.0
    max_coord = 10.0
    wall_y = 2.0

    def walkable_checker(position: Vector2, context=None) -> bool:
        if position.x < min_coord or position.x > max_coord:
            return False
        if position.y < min_coord or position.y > max_coord:
            return False
        return position.y < wall_y or position.y >= wall_y + 1.0

    pathfinder = GridPathfinding(
        grid_size=1.0,
        walkable_checker=walkable_checker,
        allow_diagonal=False,
    )

    path = pathfinder.find_path(
        start=Vector2(x=0.0, y=0.0),
        goal=Vector2(x=0.0, y=5.0),
    )

    assert path is None


def test_grid_pathfinding_duplicate_nodes_in_open_set() -> None:
    """Test pathfinding handles duplicate nodes in open set correctly."""
    obstacles = {
        Vector2(x=2.5, y=1.5),
        Vector2(x=1.5, y=2.5),
        Vector2(x=3.5, y=3.5),
        Vector2(x=4.5, y=2.5),
        Vector2(x=2.5, y=4.5),
    }

    def walkable_checker(position: Vector2, context=None) -> bool:
        grid_x = int(position.x)
        grid_y = int(position.y)
        check_pos = Vector2(x=grid_x + 0.5, y=grid_y + 0.5)
        return check_pos not in obstacles

    pathfinder = GridPathfinding(
        grid_size=1.0,
        walkable_checker=walkable_checker,
        allow_diagonal=True,
    )

    path = pathfinder.find_path(
        start=Vector2(x=0.0, y=0.0),
        goal=Vector2(x=6.0, y=6.0),
    )

    assert path is not None
    assert len(path) > 0


def test_grid_pathfinding_complex_maze() -> None:
    """Test pathfinding through complex maze with many alternate paths."""
    obstacles = {
        Vector2(x=1.5, y=0.5),
        Vector2(x=1.5, y=1.5),
        Vector2(x=3.5, y=1.5),
        Vector2(x=3.5, y=2.5),
        Vector2(x=1.5, y=3.5),
        Vector2(x=2.5, y=3.5),
        Vector2(x=4.5, y=3.5),
        Vector2(x=4.5, y=4.5),
    }

    def walkable_checker(position: Vector2, context=None) -> bool:
        grid_x = int(position.x)
        grid_y = int(position.y)
        check_pos = Vector2(x=grid_x + 0.5, y=grid_y + 0.5)
        return check_pos not in obstacles

    pathfinder = GridPathfinding(
        grid_size=1.0,
        walkable_checker=walkable_checker,
        allow_diagonal=True,
    )

    path = pathfinder.find_path(
        start=Vector2(x=0.0, y=0.0),
        goal=Vector2(x=5.0, y=5.0),
    )

    assert path is not None
    assert len(path) > 0


def test_grid_pathfinding_large_search_space() -> None:
    """Test pathfinding with large search space and Dijkstra's algorithm."""

    def zero_heuristic(a: Vector2, b: Vector2) -> float:
        return 0.0

    pathfinder = GridPathfinding(
        grid_size=1.0,
        allow_diagonal=False,
        heuristic=zero_heuristic,
    )

    path = pathfinder.find_path(
        start=Vector2(x=0.0, y=0.0),
        goal=Vector2(x=10.0, y=10.0),
    )

    assert path is not None
    assert len(path) == 21
