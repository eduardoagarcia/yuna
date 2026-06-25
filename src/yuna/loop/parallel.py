"""Parallel execution scheduler for systems."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from yuna.loop.job import Job

if TYPE_CHECKING:
    from yuna.ecs.system import System
    from yuna.ecs.world import ECSWorld


class ParallelScheduler:
    """Manages parallel execution of independent systems.

    Responsibilities:
    - Build job dependency graph from systems
    - Group jobs into execution layers by dependency level
    - Execute independent jobs concurrently using asyncio
    - Respect dependencies between systems
    - Maximize parallelism while maintaining correctness

    Execution layers:
    - Layer 0: Jobs with no dependencies (execute first, in parallel)
    - Layer 1: Jobs depending only on Layer 0 (execute after Layer 0, in parallel)
    - Layer N: Jobs depending on previous layers (execute after N-1, in parallel)

    Usage:
        scheduler = ParallelScheduler()
        jobs = scheduler.create_job_graph(
            systems=[physics, render, audio],
            dependencies={(render, physics)}  # render depends on physics
        )
        await scheduler.execute_parallel(jobs=jobs, world=world, delta_time=dt)
    """

    @staticmethod
    def create_job_graph(
        systems: Sequence[System],
        dependencies: Mapping[System, Sequence[System]] | None = None,
    ) -> list[Job]:
        """Create job graph from systems and dependencies.

        Args:
            systems: Sequence of systems to execute
            dependencies: Mapping of system -> sequence of systems it depends on

        Returns:
            List of Job instances with dependency relationships
        """
        deps = dependencies if dependencies is not None else {}
        system_to_job: dict[System, Job] = {}

        for system in systems:
            system_to_job[system] = Job(system=system)

        for system, deps_list in deps.items():
            if system in system_to_job:
                job = system_to_job[system]
                dep_jobs = [
                    system_to_job[dep] for dep in deps_list if dep in system_to_job
                ]
                job._dependencies = dep_jobs

        return list(system_to_job.values())

    @staticmethod
    def get_execution_layers(jobs: list[Job]) -> list[list[Job]]:
        """Group jobs into layers by dependency level.

        Layer 0: No dependencies
        Layer 1: Depends only on Layer 0
        Layer N: Depends only on layers 0 through N-1

        Args:
            jobs: List of jobs to group

        Returns:
            List of layers, each containing jobs that can run in parallel
        """
        layers: list[list[Job]] = []
        remaining_jobs = jobs.copy()
        completed_jobs: set[Job] = set()

        while remaining_jobs:
            current_layer: list[Job] = []

            for job in remaining_jobs:
                deps_complete = all(dep in completed_jobs for dep in job.dependencies)
                if deps_complete:
                    current_layer.append(job)

            if not current_layer:
                break

            layers.append(current_layer)
            for job in current_layer:
                remaining_jobs.remove(job)
                completed_jobs.add(job)

        return layers

    async def execute_parallel(
        self,
        jobs: list[Job],
        world: ECSWorld,
        delta_time: float,
    ) -> None:
        """Execute jobs in parallel by layers.

        Each layer executes concurrently, layers execute sequentially.

        Args:
            jobs: Jobs to execute
            world: ECS world to pass to systems
            delta_time: Time elapsed since last update
        """
        layers = self.get_execution_layers(jobs=jobs)

        for layer in layers:
            tasks = [job.execute(world=world, delta_time=delta_time) for job in layer]
            await asyncio.gather(*tasks)

    async def execute_sequential(
        self,
        jobs: list[Job],
        world: ECSWorld,
        delta_time: float,
    ) -> None:
        """Execute jobs sequentially in dependency order.

        Args:
            jobs: Jobs to execute
            world: ECS world to pass to systems
            delta_time: Time elapsed since last update
        """
        layers = self.get_execution_layers(jobs=jobs)

        for layer in layers:
            for job in layer:
                await job.execute(world=world, delta_time=delta_time)
