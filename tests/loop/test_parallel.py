"""Tests for ParallelScheduler class."""

from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.loop.job import Job
from yuna.loop.parallel import ParallelScheduler

fake = Faker()


@dataclass
class TestComponent(Component):
    """Test component."""

    value: int


class TestSystem(System):
    """Test system for parallel execution."""

    execution_order: list[int] = []

    def __init__(self, priority_value: int, system_id: int) -> None:
        self._priority = priority_value
        self._system_id = system_id
        self.update_count = 0

    @property
    def priority(self) -> int:
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:
        TestSystem.execution_order.append(self._system_id)
        self.update_count += 1


@pytest.fixture(autouse=True)
def _reset_execution_order() -> None:
    """Reset execution order before each test."""
    TestSystem.execution_order.clear()


def test_create_job_graph_with_no_dependencies() -> None:
    """Test creating job graph with independent systems."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    systems = [system1, system2]

    jobs = scheduler.create_job_graph(systems=systems)

    assert len(jobs) == 2
    assert all(isinstance(job, Job) for job in jobs)
    assert all(len(job.dependencies) == 0 for job in jobs)


def test_create_job_graph_with_dependencies() -> None:
    """Test creating job graph with system dependencies."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    systems = [system1, system2]
    dependencies: dict[System, list[System]] = {system2: [system1]}

    jobs = scheduler.create_job_graph(systems=systems, dependencies=dependencies)

    assert len(jobs) == 2
    job1 = next(job for job in jobs if job.system is system1)
    job2 = next(job for job in jobs if job.system is system2)

    assert len(job1.dependencies) == 0
    assert len(job2.dependencies) == 1
    assert job2.dependencies[0] is job1


def test_create_job_graph_with_multiple_dependencies() -> None:
    """Test creating job graph with multiple dependencies per system."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    system3 = TestSystem(priority_value=300, system_id=3)
    systems = [system1, system2, system3]
    dependencies: dict[System, list[System]] = {system3: [system1, system2]}

    jobs = scheduler.create_job_graph(systems=systems, dependencies=dependencies)

    job3 = next(job for job in jobs if job.system is system3)
    assert len(job3.dependencies) == 2


def test_get_execution_layers_with_no_dependencies() -> None:
    """Test execution layers with independent jobs."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    job1 = Job(system=system1)
    job2 = Job(system=system2)

    layers = scheduler.get_execution_layers(jobs=[job1, job2])

    assert len(layers) == 1
    assert len(layers[0]) == 2
    assert job1 in layers[0]
    assert job2 in layers[0]


def test_get_execution_layers_with_dependencies() -> None:
    """Test execution layers respects dependencies."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    job1 = Job(system=system1)
    job2 = Job(system=system2, dependencies=[job1])

    layers = scheduler.get_execution_layers(jobs=[job1, job2])

    assert len(layers) == 2
    assert layers[0] == [job1]
    assert layers[1] == [job2]


def test_get_execution_layers_with_multiple_levels() -> None:
    """Test execution layers with multiple dependency levels."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    system3 = TestSystem(priority_value=300, system_id=3)
    job1 = Job(system=system1)
    job2 = Job(system=system2, dependencies=[job1])
    job3 = Job(system=system3, dependencies=[job2])

    layers = scheduler.get_execution_layers(jobs=[job1, job2, job3])

    assert len(layers) == 3
    assert layers[0] == [job1]
    assert layers[1] == [job2]
    assert layers[2] == [job3]


def test_get_execution_layers_with_parallel_jobs_in_same_layer() -> None:
    """Test multiple independent jobs in same layer."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    system3 = TestSystem(priority_value=300, system_id=3)
    system4 = TestSystem(priority_value=400, system_id=4)
    job1 = Job(system=system1)
    job2 = Job(system=system2)
    job3 = Job(system=system3, dependencies=[job1, job2])
    job4 = Job(system=system4, dependencies=[job1, job2])

    layers = scheduler.get_execution_layers(jobs=[job1, job2, job3, job4])

    assert len(layers) == 2
    assert set(layers[0]) == {job1, job2}
    assert set(layers[1]) == {job3, job4}


@pytest.mark.asyncio
async def test_execute_parallel_runs_all_jobs() -> None:
    """Test parallel execution runs all jobs."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    jobs = scheduler.create_job_graph(systems=[system1, system2])
    world = ECSWorld()

    await scheduler.execute_parallel(jobs=jobs, world=world, delta_time=0.016)

    assert system1.update_count == 1
    assert system2.update_count == 1


@pytest.mark.asyncio
async def test_execute_parallel_respects_dependencies() -> None:
    """Test parallel execution respects dependency order."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    systems = [system1, system2]
    dependencies: dict[System, list[System]] = {system2: [system1]}
    jobs = scheduler.create_job_graph(systems=systems, dependencies=dependencies)
    world = ECSWorld()

    await scheduler.execute_parallel(jobs=jobs, world=world, delta_time=0.016)

    assert TestSystem.execution_order == [1, 2]


@pytest.mark.asyncio
async def test_execute_parallel_with_multiple_layers() -> None:
    """Test parallel execution with multiple dependency layers."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    system3 = TestSystem(priority_value=300, system_id=3)
    systems = [system1, system2, system3]
    dependencies: dict[System, list[System]] = {system2: [system1], system3: [system2]}
    jobs = scheduler.create_job_graph(systems=systems, dependencies=dependencies)
    world = ECSWorld()

    await scheduler.execute_parallel(jobs=jobs, world=world, delta_time=0.016)

    assert TestSystem.execution_order == [1, 2, 3]


@pytest.mark.asyncio
async def test_execute_sequential_runs_all_jobs() -> None:
    """Test sequential execution runs all jobs."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    jobs = scheduler.create_job_graph(systems=[system1, system2])
    world = ECSWorld()

    await scheduler.execute_sequential(jobs=jobs, world=world, delta_time=0.016)

    assert system1.update_count == 1
    assert system2.update_count == 1


@pytest.mark.asyncio
async def test_execute_sequential_respects_dependencies() -> None:
    """Test sequential execution respects dependency order."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    systems = [system1, system2]
    dependencies: dict[System, list[System]] = {system2: [system1]}
    jobs = scheduler.create_job_graph(systems=systems, dependencies=dependencies)
    world = ECSWorld()

    await scheduler.execute_sequential(jobs=jobs, world=world, delta_time=0.016)

    assert TestSystem.execution_order == [1, 2]


def test_get_execution_layers_empty_jobs() -> None:
    """Test execution layers with empty job list."""
    scheduler = ParallelScheduler()

    layers = scheduler.get_execution_layers(jobs=[])

    assert layers == []


def test_get_execution_layers_with_orphaned_jobs() -> None:
    """Test execution layers stops when jobs have unsatisfiable dependencies."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    job1 = Job(system=system1)
    job2 = Job(system=system2)
    job2._dependencies = [job1]

    layers = scheduler.get_execution_layers(jobs=[job2])

    assert len(layers) == 0


def test_create_job_graph_empty_systems() -> None:
    """Test creating job graph with empty systems list."""
    scheduler = ParallelScheduler()

    jobs = scheduler.create_job_graph(systems=[])

    assert jobs == []


def test_create_job_graph_ignores_unknown_dependencies() -> None:
    """Test creating job graph ignores dependencies on unregistered systems."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    unknown_system = TestSystem(priority_value=300, system_id=99)
    dependencies: dict[System, list[System]] = {system2: [system1, unknown_system]}

    jobs = scheduler.create_job_graph(
        systems=[system1, system2], dependencies=dependencies
    )

    job2 = next(job for job in jobs if job.system is system2)
    assert len(job2.dependencies) == 1


@pytest.mark.asyncio
async def test_execute_parallel_jobs_complete_with_futures() -> None:
    """Test parallel execution completes all job futures."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    jobs = scheduler.create_job_graph(systems=[system1, system2])
    world = ECSWorld()

    await scheduler.execute_parallel(jobs=jobs, world=world, delta_time=0.016)

    assert all(job.is_complete for job in jobs)


@pytest.mark.asyncio
async def test_execute_parallel_with_diamond_dependency() -> None:
    """Test parallel execution handles diamond dependency pattern."""
    scheduler = ParallelScheduler()
    system1 = TestSystem(priority_value=100, system_id=1)
    system2 = TestSystem(priority_value=200, system_id=2)
    system3 = TestSystem(priority_value=300, system_id=3)
    system4 = TestSystem(priority_value=400, system_id=4)
    systems = [system1, system2, system3, system4]
    dependencies: dict[System, list[System]] = {
        system2: [system1],
        system3: [system1],
        system4: [system2, system3],
    }
    jobs = scheduler.create_job_graph(systems=systems, dependencies=dependencies)
    world = ECSWorld()

    await scheduler.execute_parallel(jobs=jobs, world=world, delta_time=0.016)

    execution = TestSystem.execution_order
    assert execution[0] == 1
    assert set(execution[1:3]) == {2, 3}
    assert execution[3] == 4
