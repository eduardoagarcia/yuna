"""Pathfinding infrastructure for AI navigation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from yuna.ecs.component import Component
from yuna.types.vector import Vector2


class PathfindingProvider(Protocol):
    """Protocol for pathfinding implementations.

    Games implement this with A*, NavMesh, Dijkstra, or custom algorithms.
    CORE provides infrastructure, games choose pathfinding strategy.

    Responsibilities:
    - Find paths between positions
    - Validate walkability
    - Return waypoint lists

    Usage:
        class CustomPathfinding:
            def find_path(self, start, goal, context=None):
                # Custom pathfinding logic
                return waypoint_list

            def is_walkable(self, position, context=None):
                # Custom walkability check
                return True

        pathfinder = CustomPathfinding()
        path = pathfinder.find_path(
            start=Vector2(x=0.0, y=0.0),
            goal=Vector2(x=10.0, y=10.0),
        )
    """

    def find_path(
        self,
        start: Vector2,
        goal: Vector2,
        context: Any = None,
    ) -> list[Vector2] | None:  # pragma: no cover
        """Find path from start to goal.

        Args:
            start: Starting position in world coordinates
            goal: Goal position in world coordinates
            context: Optional context (world, entity_id, obstacles)

        Returns:
            List of waypoints (including start and goal) or None if no path
        """
        ...

    def is_walkable(
        self, position: Vector2, context: Any = None
    ) -> bool:  # pragma: no cover
        """Check if position is walkable.

        Args:
            position: Position to check
            context: Optional context

        Returns:
            True if position is walkable
        """
        ...


class GridPathfinding:
    """Grid-based A* pathfinding implementation.

    Included pathfinding for grid-based worlds. Implements PathfindingProvider  protocol
    using A* algorithm with 8-directional movement (N, NE, E, SE, S, SW, W, NW)

    Responsibilities:
    - A* pathfinding on integer grid
    - 8-directional movement support
    - Walkability validation
    - World-to-grid coordinate conversion

    Usage:
        pathfinder = GridPathfinding(
            grid_size=1.0,
            walkable_checker=lambda pos, ctx: is_valid_position(pos),
        )

        path = pathfinder.find_path(
            start=Vector2(x=0.0, y=0.0),
            goal=Vector2(x=10.0, y=10.0),
        )
    """

    def __init__(
        self,
        grid_size: float = 1.0,
        walkable_checker: Callable[[Vector2, Any], bool] | None = None,
        allow_diagonal: bool = True,
        heuristic: Callable[[Vector2, Vector2], float] | None = None,
    ) -> None:
        """Initialize grid pathfinding.

        Args:
            grid_size: Size of grid cells in world units
            walkable_checker: Function to check if position is walkable
            allow_diagonal: Enable 8-directional movement
            heuristic: Distance heuristic function
        """
        self.grid_size = grid_size
        self._walkable_checker = walkable_checker
        self.allow_diagonal = allow_diagonal
        self._heuristic = heuristic or self._euclidean_distance

    def find_path(
        self,
        start: Vector2,
        goal: Vector2,
        context: Any = None,
    ) -> list[Vector2] | None:
        """Find path using A* algorithm.

        Converts world coordinates to grid coordinates, runs A*,
        converts result back to world coordinates.

        Args:
            start: Starting position in world coordinates
            goal: Goal position in world coordinates
            context: Optional context (passed to walkable_checker)

        Returns:
            List of waypoints (world coordinates) or None if no path
        """
        start_grid = self._world_to_grid(position=start)
        goal_grid = self._world_to_grid(position=goal)

        if not self.is_walkable(
            position=self._grid_to_world(position=goal_grid),
            context=context,
        ):
            return None

        open_set: list[tuple[float, Vector2]] = [(0.0, start_grid)]
        closed_set: set[Vector2] = set()
        came_from: dict[Vector2, Vector2] = {}
        g_score: dict[Vector2, float] = {start_grid: 0.0}
        f_score: dict[Vector2, float] = {
            start_grid: self._heuristic(start_grid, goal_grid)
        }

        while open_set:
            open_set.sort(key=lambda x: x[0])
            _, current = open_set.pop(0)

            if current in closed_set:  # pragma: no cover
                continue

            if current == goal_grid:
                return self._reconstruct_path(
                    came_from=came_from,
                    current=current,
                )

            closed_set.add(current)

            for neighbor in self._get_neighbors(position=current):
                if neighbor in closed_set:
                    continue

                if not self.is_walkable(
                    position=self._grid_to_world(position=neighbor),
                    context=context,
                ):
                    continue

                tentative_g = g_score[current] + self._movement_cost(
                    from_pos=current,
                    to_pos=neighbor,
                )

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(
                        neighbor,
                        goal_grid,
                    )
                    open_set.append((f_score[neighbor], neighbor))

        return None

    def is_walkable(self, position: Vector2, context: Any = None) -> bool:
        """Check if position is walkable.

        Args:
            position: Position to check (world coordinates)
            context: Optional context passed to walkable_checker

        Returns:
            True if position is walkable
        """
        if self._walkable_checker is None:
            return True
        return self._walkable_checker(position, context)

    def _world_to_grid(self, position: Vector2) -> Vector2:
        """Convert world coordinates to grid coordinates.

        Args:
            position: World coordinates

        Returns:
            Grid coordinates
        """
        return Vector2(
            x=int(position.x / self.grid_size),
            y=int(position.y / self.grid_size),
        )

    def _grid_to_world(self, position: Vector2) -> Vector2:
        """Convert grid coordinates to world coordinates (cell center).

        Args:
            position: Grid coordinates

        Returns:
            World coordinates
        """
        return Vector2(
            x=(position.x + 0.5) * self.grid_size,
            y=(position.y + 0.5) * self.grid_size,
        )

    def _get_neighbors(self, position: Vector2) -> list[Vector2]:
        """Get valid neighbor positions (4 or 8 directional).

        Args:
            position: Current position

        Returns:
            List of neighbor positions
        """
        neighbors = [
            Vector2(x=position.x + 1, y=position.y),
            Vector2(x=position.x - 1, y=position.y),
            Vector2(x=position.x, y=position.y + 1),
            Vector2(x=position.x, y=position.y - 1),
        ]

        if self.allow_diagonal:
            neighbors.extend([
                Vector2(x=position.x + 1, y=position.y + 1),
                Vector2(x=position.x + 1, y=position.y - 1),
                Vector2(x=position.x - 1, y=position.y + 1),
                Vector2(x=position.x - 1, y=position.y - 1),
            ])

        return neighbors

    @staticmethod
    def _movement_cost(from_pos: Vector2, to_pos: Vector2) -> float:
        """Calculate movement cost between positions.

        Args:
            from_pos: Starting position
            to_pos: Ending position

        Returns:
            Movement cost (1.0 for cardinal, 1.414 for diagonal)
        """
        dx = abs(to_pos.x - from_pos.x)
        dy = abs(to_pos.y - from_pos.y)

        if dx == 1 and dy == 1:
            return 1.414
        return 1.0

    @staticmethod
    def _euclidean_distance(a: Vector2, b: Vector2) -> float:
        """Euclidean distance heuristic (admissible for diagonal movement).

        Args:
            a: First position
            b: Second position

        Returns:
            Euclidean distance
        """
        dx: float = abs(a.x - b.x)
        dy: float = abs(a.y - b.y)
        return float((dx * dx + dy * dy) ** 0.5)

    def _reconstruct_path(
        self,
        came_from: dict[Vector2, Vector2],
        current: Vector2,
    ) -> list[Vector2]:
        """Reconstruct path from came_from dict.

        Args:
            came_from: Parent map from A*
            current: Goal position

        Returns:
            List of waypoints in world coordinates
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)

        path.reverse()
        return [self._grid_to_world(position=pos) for pos in path]


@dataclass
class PathComponent(Component):
    """Path following component for AI entities.

    Stores current path, progress, and pathfinding state.

    Responsibilities:
    - Store waypoint list
    - Track current waypoint index
    - Determine path completion
    - Support path recalculation

    Usage:
        path_component = PathComponent(
            waypoints=[Vector2(x=0.0, y=0.0), Vector2(x=5.0, y=5.0)],
            goal=Vector2(x=10.0, y=10.0),
        )

        world.add_component(
            entity_id=agent_id,
            component=path_component,
        )
    """

    waypoints: list[Vector2] = field(default_factory=list)
    current_waypoint_index: int = 0
    goal: Vector2 | None = None
    recalculate_on_blocked: bool = True
    waypoint_threshold: float = 1.0
    _last_recalculation_tick: int = 0

    def get_current_waypoint(self) -> Vector2 | None:
        """Get current waypoint to move toward.

        Returns:
            Current waypoint or None if path complete
        """
        if 0 <= self.current_waypoint_index < len(self.waypoints):
            return self.waypoints[self.current_waypoint_index]
        return None

    def advance_waypoint(self) -> None:
        """Move to next waypoint."""
        self.current_waypoint_index += 1

    def is_complete(self) -> bool:
        """Check if path is complete.

        Returns:
            True if all waypoints reached
        """
        return self.current_waypoint_index >= len(self.waypoints)

    def clear_path(self) -> None:
        """Clear current path."""
        self.waypoints.clear()
        self.current_waypoint_index = 0

    def set_path(self, waypoints: list[Vector2], goal: Vector2 | None = None) -> None:
        """Set new path.

        Args:
            waypoints: New path waypoints
            goal: Optional goal position
        """
        self.waypoints = waypoints
        self.current_waypoint_index = 0
        self.goal = goal


@dataclass
class PathRequest(Component):
    """Request pathfinding calculation.

    Add this component to request path. PathfindingSystem
    will calculate path and update PathComponent.

    Responsibilities:
    - Signal pathfinding request
    - Store goal position
    - Priority for request ordering

    Usage:
        world.add_component(
            entity_id=agent_id,
            component=PathRequest(
                goal=Vector2(x=10.0, y=10.0),
                priority=1,
            ),
        )
    """

    goal: Vector2
    priority: int = 0
