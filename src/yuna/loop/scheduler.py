"""System scheduler for managing execution order."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yuna.exceptions import ValidationError
from yuna.loop.dependencies import (
    CyclicDependencyError,
    DependencyGraph,
)
from yuna.loop.job import Job
from yuna.loop.parallel import ParallelScheduler

if TYPE_CHECKING:
    from yuna.ecs.system import System
    from yuna.ecs.world import ECSWorld
    from yuna.profiling.monitor import PerformanceMonitor


class SystemScheduler:
    """Manages system registration and execution ordering.

    Responsibilities:
    - Register systems for execution
    - Sort systems by priority (lower = earlier)
    - Support explicit dependencies between systems
    - Maintain deterministic execution order
    - Detect and reject circular dependencies
    - Provide ordered system list for game loop

    Systems with dependencies use topological sort for ordering.
    Systems without dependencies execute in priority order.
    Mixed mode: dependencies respected, then priority used for tie-breaking.

    Usage:
        scheduler = SystemScheduler()
        scheduler.register(system=physics_system)  # priority: 100
        scheduler.register(system=render_system)   # priority: 200
        scheduler.add_dependency(system=render_system, depends_on=physics_system)

        for system in scheduler.get_ordered_systems():
            system.update(world=world, delta_time=dt)
    """

    def __init__(
        self,
        monitor: PerformanceMonitor | None = None,
        parallel_execution: bool = False,
    ) -> None:
        """Initialize empty scheduler.

        Args:
            monitor: Optional performance monitor for profiling system execution
            parallel_execution: Enable parallel execution of independent systems
        """
        self._systems: list[System] = []
        self._dependency_graph = DependencyGraph()
        self._monitor = monitor
        self._parallel_execution = parallel_execution
        self._parallel_scheduler = ParallelScheduler() if parallel_execution else None

    def register(self, system: System) -> None:
        """Register system for execution.

        Systems are automatically sorted by priority.
        Same priority maintains registration order.

        Args:
            system: System to register
        """
        self._systems.append(system)
        self._systems.sort(key=lambda s: s.priority)
        self._dependency_graph.add_node(system=system)

    def add_dependency(self, system: System, depends_on: System) -> None:
        """Declare that system depends on another system.

        This means depends_on must execute before system.

        Args:
            system: System that has a dependency
            depends_on: System that must execute before system

        Raises:
            ValidationError: If either system not registered
            CyclicDependencyError: If dependency creates a cycle
        """
        if system not in self._systems:
            raise ValidationError(
                field="system",
                value=str(system),
                reason="System not registered",
            )
        if depends_on not in self._systems:
            raise ValidationError(
                field="depends_on",
                value=str(depends_on),
                reason="Dependency system not registered",
            )

        self._dependency_graph.add_edge(from_system=system, to_system=depends_on)

        if not self._dependency_graph.validate():
            cycles = self._dependency_graph.detect_cycles()
            cycle_repr = " -> ".join(str(s) for s in cycles[0])
            raise CyclicDependencyError(f"Circular dependency detected: {cycle_repr}")

    def get_ordered_systems(self) -> list[System]:
        """Get systems in execution order.

        Uses topological sort if dependencies exist, otherwise priority order.
        Priority is used for tie-breaking in topological sort.

        Returns:
            List of systems in execution order

        Raises:
            CyclicDependencyError: If circular dependencies exist
        """
        if self._dependency_graph.edge_count > 0:
            return self._dependency_graph.topological_sort()
        return self._systems.copy()

    def clear(self) -> None:
        """Remove all systems from scheduler."""
        self._systems.clear()
        self._dependency_graph.clear()

    @property
    def count(self) -> int:
        """Get number of registered systems.

        Returns:
            Number of systems in scheduler
        """
        return len(self._systems)

    def get_parallel_jobs(self) -> list[Job]:
        """Create jobs from registered systems with dependencies.

        Returns:
            List of Job instances with dependency relationships
        """
        systems = self.get_ordered_systems()
        dependencies: dict[System, list[System]] = {}

        for system in systems:
            deps = self._dependency_graph.get_dependencies(system=system)
            if deps:
                dependencies[system] = list(deps)

        return ParallelScheduler.create_job_graph(
            systems=systems,
            dependencies=dependencies,
        )

    async def execute_parallel(
        self,
        world: ECSWorld,
        delta_time: float,
    ) -> None:
        """Execute systems in parallel by dependency layers.

        Args:
            world: ECS world to pass to systems
            delta_time: Time elapsed since last update
        """
        jobs = self.get_parallel_jobs()

        await ParallelScheduler().execute_parallel(
            jobs=jobs,
            world=world,
            delta_time=delta_time,
        )

    async def execute_sequential(
        self,
        world: ECSWorld,
        delta_time: float,
    ) -> None:
        """Execute systems sequentially in priority/dependency order.

        Args:
            world: ECS world to pass to systems
            delta_time: Time elapsed since last update
        """
        systems = self.get_ordered_systems()

        for system in systems:
            system.update(world=world, delta_time=delta_time)
