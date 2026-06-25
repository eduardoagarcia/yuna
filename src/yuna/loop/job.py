"""Job representation for parallel system execution."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from yuna.exceptions import StateError

if TYPE_CHECKING:
    from yuna.ecs.system import System
    from yuna.ecs.world import ECSWorld


class Job:
    """Represents a system execution job with dependencies.

    Responsibilities:
    - Wrap a system for async execution
    - Track dependencies on other jobs
    - Manage execution state via asyncio.Future
    - Check if ready to execute (all dependencies complete)
    - Execute system and update future

    Usage:
        job1 = Job(system=physics_system)
        job2 = Job(system=render_system, dependencies=[job1])

        if job1.is_ready():
            await job1.execute(world=world, delta_time=dt)

        if job2.is_ready():
            await job2.execute(world=world, delta_time=dt)
    """

    def __init__(
        self,
        system: System,
        dependencies: list[Job] | None = None,
    ) -> None:
        """Initialize job with system and dependencies.

        Args:
            system: System to execute
            dependencies: Jobs that must complete before this job can run
        """
        self._system = system
        self._dependencies = dependencies if dependencies is not None else []
        self._future: asyncio.Future[None] | None = None

    def is_ready(self) -> bool:
        """Check if all dependencies have completed.

        Returns:
            True if job can execute (no dependencies or all done)
        """
        return all(
            dep._future is not None and dep._future.done() for dep in self._dependencies
        )

    async def execute(self, world: ECSWorld, delta_time: float) -> None:
        """Execute the system and mark future as done.

        Args:
            world: ECS world to pass to system
            delta_time: Time elapsed since last update

        Raises:
            StateError: If job is not ready to execute
        """
        if not self.is_ready():
            raise StateError(
                operation="execute",
                state="dependencies_incomplete",
                reason=f"Job for {self._system} has incomplete dependencies",
            )

        if self._future is None:
            self._future = asyncio.Future()

        try:
            self._system.update(world=world, delta_time=delta_time)
            self._future.set_result(None)
        except Exception as e:
            self._future.set_exception(e)
            raise

    @property
    def system(self) -> System:
        """Get the system this job executes.

        Returns:
            System instance
        """
        return self._system

    @property
    def dependencies(self) -> list[Job]:
        """Get list of dependency jobs.

        Returns:
            List of jobs this job depends on
        """
        return self._dependencies.copy()

    @property
    def future(self) -> asyncio.Future[None] | None:
        """Get execution future.

        Returns:
            Future representing execution state, or None if not started
        """
        return self._future

    @property
    def is_complete(self) -> bool:
        """Check if job has completed execution.

        Returns:
            True if future is done
        """
        return self._future is not None and self._future.done()

    def reset(self) -> None:
        """Reset job state for re-execution."""
        self._future = None
