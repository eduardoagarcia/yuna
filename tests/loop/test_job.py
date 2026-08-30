"""Tests for Job class."""

import asyncio
from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.exceptions import StateError
from yuna.loop.job import Job

fake = Faker()


@dataclass
class TestComponent(Component):
    """Test component."""

    value: int


class TestSystem(System):
    """Test system for job execution."""

    def __init__(self, priority_value: int = 100) -> None:
        self._priority = priority_value
        self.update_count = 0

    @property
    def priority(self) -> int:
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:
        self.update_count += 1


def test_job_initialization() -> None:
    """Test Job can be initialized with system."""
    system = TestSystem()
    job = Job(system=system)

    assert job.system is system
    assert job.dependencies == []
    assert job.future is None
    assert not job.is_complete


def test_job_with_dependencies() -> None:
    """Test Job can be initialized with dependencies."""
    system1 = TestSystem(priority_value=100)
    system2 = TestSystem(priority_value=200)
    job1 = Job(system=system1)
    job2 = Job(system=system2, dependencies=[job1])

    assert job2.dependencies == [job1]
    assert len(job2.dependencies) == 1


def test_job_is_ready_with_no_dependencies() -> None:
    """Test job is ready when it has no dependencies."""
    system = TestSystem()
    job = Job(system=system)

    assert job.is_ready()


def test_job_is_not_ready_with_incomplete_dependencies() -> None:
    """Test job is not ready when dependencies are incomplete."""
    system1 = TestSystem()
    system2 = TestSystem()
    job1 = Job(system=system1)
    job2 = Job(system=system2, dependencies=[job1])

    assert not job2.is_ready()


@pytest.mark.asyncio
async def test_job_is_ready_with_complete_dependencies() -> None:
    """Test job is ready when all dependencies are complete."""
    system1 = TestSystem()
    system2 = TestSystem()
    job1 = Job(system=system1)
    job2 = Job(system=system2, dependencies=[job1])

    world = ECSWorld()
    await job1.execute(world=world, delta_time=0.016)

    assert job2.is_ready()


@pytest.mark.asyncio
async def test_job_execute_calls_system_update() -> None:
    """Test job execution calls system update method."""
    system = TestSystem()
    job = Job(system=system)
    world = ECSWorld()

    await job.execute(world=world, delta_time=0.016)

    assert system.update_count == 1


@pytest.mark.asyncio
async def test_job_execute_creates_future() -> None:
    """Test job execution creates and completes future."""
    system = TestSystem()
    job = Job(system=system)
    world = ECSWorld()

    await job.execute(world=world, delta_time=0.016)

    assert job.future is not None
    assert job.future.done()


@pytest.mark.asyncio
async def test_job_execute_sets_future_result() -> None:
    """Test job execution sets future result to None on success."""
    system = TestSystem()
    job = Job(system=system)
    world = ECSWorld()

    await job.execute(world=world, delta_time=0.016)

    assert job.future is not None
    assert job.future.result() is None


@pytest.mark.asyncio
async def test_job_execute_raises_when_not_ready() -> None:
    """Test job execution raises error when dependencies incomplete."""
    system1 = TestSystem()
    system2 = TestSystem()
    job1 = Job(system=system1)
    job2 = Job(system=system2, dependencies=[job1])
    world = ECSWorld()

    with pytest.raises(StateError, match="incomplete dependencies"):
        await job2.execute(world=world, delta_time=0.016)


class FailingSystem(System):
    """Test system that raises exception."""

    @property
    def priority(self) -> int:
        return 100

    def update(self, world: ECSWorld, delta_time: float) -> None:
        raise ValueError("System failed")


@pytest.mark.asyncio
async def test_job_execute_sets_exception_on_failure() -> None:
    """Test job execution sets exception in future on system failure."""
    system = FailingSystem()
    job = Job(system=system)
    world = ECSWorld()

    with pytest.raises(ValueError, match="System failed"):
        await job.execute(world=world, delta_time=0.016)

    assert job.future is not None
    assert job.future.done()
    with pytest.raises(ValueError):
        job.future.result()


async def test_job_is_complete_property() -> None:
    """Test is_complete property reflects future state."""
    system = TestSystem()
    job = Job(system=system)

    assert not job.is_complete

    job._future = asyncio.Future()
    assert not job.is_complete

    job._future.set_result(None)
    assert job.is_complete


async def test_job_reset() -> None:
    """Test job reset clears future."""
    system = TestSystem()
    job = Job(system=system)
    job._future = asyncio.Future()
    job._future.set_result(None)

    assert job.is_complete

    job.reset()

    assert job.future is None
    assert not job.is_complete


def test_job_dependencies_returns_copy() -> None:
    """Test dependencies property returns copy not reference."""
    system1 = TestSystem()
    system2 = TestSystem()
    job1 = Job(system=system1)
    job2 = Job(system=system2, dependencies=[job1])

    deps1 = job2.dependencies
    deps2 = job2.dependencies

    assert deps1 is not deps2
    assert deps1 == deps2


@pytest.mark.asyncio
async def test_multiple_dependencies_all_must_complete() -> None:
    """Test job with multiple dependencies requires all to complete."""
    system1 = TestSystem()
    system2 = TestSystem()
    system3 = TestSystem()
    job1 = Job(system=system1)
    job2 = Job(system=system2)
    job3 = Job(system=system3, dependencies=[job1, job2])
    world = ECSWorld()

    assert not job3.is_ready()

    await job1.execute(world=world, delta_time=0.016)
    assert not job3.is_ready()

    await job2.execute(world=world, delta_time=0.016)
    assert job3.is_ready()

    await job3.execute(world=world, delta_time=0.016)
    assert job3.is_complete


@pytest.mark.asyncio
async def test_job_can_be_executed_multiple_times_after_reset() -> None:
    """Test job can be reset and re-executed."""
    system = TestSystem()
    job = Job(system=system)
    world = ECSWorld()

    await job.execute(world=world, delta_time=0.016)
    assert system.update_count == 1
    assert job.is_complete

    job.reset()
    assert job.future is None

    await job.execute(world=world, delta_time=0.016)
    assert system.update_count == 2
    assert job.is_complete
