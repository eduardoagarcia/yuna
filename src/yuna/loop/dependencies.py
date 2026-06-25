"""Dependency graph for managing system execution order."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yuna.exceptions import ValidationError

if TYPE_CHECKING:
    from yuna.ecs.system import System


class CyclicDependencyError(Exception):
    """Raised when circular dependencies detected in graph."""


class DependencyGraph:
    """Manages dependencies between systems for deterministic execution order.

    Responsibilities:
    - Track dependencies between systems (A depends on B = B runs before A)
    - Perform topological sort to determine valid execution order
    - Detect circular dependencies
    - Validate graph integrity

    Uses Kahn's algorithm for topological sort and cycle detection.
    Systems without dependencies can still be ordered by priority.

    Usage:
        graph = DependencyGraph()
        graph.add_node(system=physics_system)
        graph.add_node(system=render_system)
        graph.add_edge(from_system=physics_system, to_system=render_system)

        if graph.validate():
            ordered = graph.topological_sort()
        else:
            cycles = graph.detect_cycles()
    """

    def __init__(self) -> None:
        """Initialize empty dependency graph."""
        self._nodes: set[System] = set()
        self._edges: dict[System, set[System]] = {}
        self._reverse_edges: dict[System, set[System]] = {}

    def add_node(self, system: System) -> None:
        """Add system to graph.

        Args:
            system: System to add
        """
        if system not in self._nodes:
            self._nodes.add(system)
            self._edges[system] = set()
            self._reverse_edges[system] = set()

    def add_edge(self, from_system: System, to_system: System) -> None:
        """Declare dependency between systems.

        from_system depends on to_system, meaning to_system runs before from_system.

        Args:
            from_system: System that depends on to_system
            to_system: System that from_system depends on

        Raises:
            ValidationError: If either system not in graph
        """
        if from_system not in self._nodes:
            raise ValidationError(
                field="from_system",
                value=str(from_system),
                reason="System not in dependency graph",
            )
        if to_system not in self._nodes:
            raise ValidationError(
                field="to_system",
                value=str(to_system),
                reason="System not in dependency graph",
            )

        self._edges[to_system].add(from_system)
        self._reverse_edges[from_system].add(to_system)

    def topological_sort(self) -> list[System]:
        """Return systems in valid execution order using topological sort.

        Uses Kahn's algorithm. Systems with same dependency level are
        sorted by priority for deterministic ordering.

        Returns:
            List of systems in execution order

        Raises:
            CyclicDependencyError: If graph contains cycles
        """
        in_degree = {node: len(self._reverse_edges[node]) for node in self._nodes}

        queue = sorted(
            [node for node in self._nodes if in_degree[node] == 0],
            key=lambda s: s.priority,
        )

        result: list[System] = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            neighbors = sorted(self._edges[current], key=lambda s: s.priority)
            for neighbor in neighbors:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    queue.sort(key=lambda s: s.priority)

        if len(result) != len(self._nodes):
            raise CyclicDependencyError("Circular dependency detected in graph")

        return result

    def detect_cycles(self) -> list[list[System]]:
        """Detect circular dependencies in graph.

        Uses DFS to find all cycles.

        Returns:
            List of cycles, where each cycle is a list of systems
            Empty list if no cycles found
        """
        cycles: list[list[System]] = []
        visited: set[System] = set()
        rec_stack: set[System] = set()
        path: list[System] = []

        def dfs(node: System) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._edges[node]:
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        for node in self._nodes:
            if node not in visited:
                dfs(node)

        return cycles

    def validate(self) -> bool:
        """Check if graph is valid (no cycles).

        Returns:
            True if graph has no cycles, False otherwise
        """
        return len(self.detect_cycles()) == 0

    def get_dependencies(self, system: System) -> set[System]:
        """Get all systems that the given system depends on.

        Args:
            system: System to query

        Returns:
            Set of systems that must run before the given system

        Raises:
            ValidationError: If system not in graph
        """
        if system not in self._nodes:
            raise ValidationError(
                field="system",
                value=str(system),
                reason="System not in dependency graph",
            )
        return self._reverse_edges[system].copy()

    def get_dependents(self, system: System) -> set[System]:
        """Get all systems that depend on the given system.

        Args:
            system: System to query

        Returns:
            Set of systems that must run after the given system

        Raises:
            ValidationError: If system not in graph
        """
        if system not in self._nodes:
            raise ValidationError(
                field="system",
                value=str(system),
                reason="System not in dependency graph",
            )
        return self._edges[system].copy()

    def clear(self) -> None:
        """Remove all nodes and edges from graph."""
        self._nodes.clear()
        self._edges.clear()
        self._reverse_edges.clear()

    @property
    def node_count(self) -> int:
        """Get number of nodes in graph.

        Returns:
            Number of systems in graph
        """
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        """Get number of edges in graph.

        Returns:
            Number of dependencies in graph
        """
        return sum(len(edges) for edges in self._edges.values())
