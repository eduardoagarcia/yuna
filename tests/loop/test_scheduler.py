"""Tests for system scheduler implementation."""

import pytest
from faker import Faker

from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.loop.scheduler import SystemScheduler
from yuna.profiling.monitor import PerformanceMonitor

fake = Faker()


class TestSystem(System):
    """Test system implementation."""

    def __init__(self, priority_value: int, name: str = ""):
        self._priority = priority_value
        self.name = name
        self.update_count = 0

    @property
    def priority(self) -> int:
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:
        self.update_count += 1


def test_system_scheduler_creation() -> None:
    """Test SystemScheduler can be created."""
    scheduler = SystemScheduler()
    assert scheduler.count == 0


def test_register_single_system() -> None:
    """Test registering single system."""
    scheduler = SystemScheduler()
    system = TestSystem(priority_value=100)
    scheduler.register(system=system)
    assert scheduler.count == 1


def test_get_ordered_systems_single() -> None:
    """Test getting ordered systems with single system."""
    scheduler = SystemScheduler()
    system = TestSystem(priority_value=100)
    scheduler.register(system=system)
    systems = scheduler.get_ordered_systems()
    assert len(systems) == 1
    assert systems[0] is system


def test_register_multiple_systems() -> None:
    """Test registering multiple systems."""
    scheduler = SystemScheduler()
    system1 = TestSystem(priority_value=100)
    system2 = TestSystem(priority_value=200)
    scheduler.register(system=system1)
    scheduler.register(system=system2)
    assert scheduler.count == 2


def test_systems_ordered_by_priority() -> None:
    """Test systems are sorted by priority (lower first)."""
    scheduler = SystemScheduler()
    system_high = TestSystem(priority_value=300)
    system_low = TestSystem(priority_value=100)
    system_mid = TestSystem(priority_value=200)
    scheduler.register(system=system_high)
    scheduler.register(system=system_low)
    scheduler.register(system=system_mid)
    systems = scheduler.get_ordered_systems()
    assert systems[0] is system_low
    assert systems[1] is system_mid
    assert systems[2] is system_high


def test_same_priority_maintains_registration_order() -> None:
    """Test systems with same priority use registration order."""
    scheduler = SystemScheduler()
    system1 = TestSystem(priority_value=100, name="first")
    system2 = TestSystem(priority_value=100, name="second")
    system3 = TestSystem(priority_value=100, name="third")
    scheduler.register(system=system1)
    scheduler.register(system=system2)
    scheduler.register(system=system3)
    systems = scheduler.get_ordered_systems()
    assert isinstance(systems[0], TestSystem)
    assert isinstance(systems[1], TestSystem)
    assert isinstance(systems[2], TestSystem)
    assert systems[0].name == "first"
    assert systems[1].name == "second"
    assert systems[2].name == "third"


def test_clear_removes_all_systems() -> None:
    """Test clear removes all registered systems."""
    scheduler = SystemScheduler()
    for i in range(5):
        scheduler.register(system=TestSystem(priority_value=i * 100))
    scheduler.clear()
    assert scheduler.count == 0


def test_clear_on_empty_scheduler() -> None:
    """Test clear on empty scheduler does nothing."""
    scheduler = SystemScheduler()
    scheduler.clear()
    assert scheduler.count == 0


def test_get_ordered_systems_returns_copy() -> None:
    """Test get_ordered_systems returns copy not reference."""
    scheduler = SystemScheduler()
    scheduler.register(system=TestSystem(priority_value=100))
    systems1 = scheduler.get_ordered_systems()
    systems2 = scheduler.get_ordered_systems()
    assert systems1 is not systems2
    assert systems1 == systems2


def test_count_property() -> None:
    """Test count property returns correct number."""
    scheduler = SystemScheduler()
    assert scheduler.count == 0
    scheduler.register(system=TestSystem(priority_value=100))
    assert scheduler.count == 1
    scheduler.register(system=TestSystem(priority_value=200))
    assert scheduler.count == 2


def test_register_systems_with_negative_priority() -> None:
    """Test systems with negative priority sort correctly."""
    scheduler = SystemScheduler()
    system_negative = TestSystem(priority_value=-100)
    system_zero = TestSystem(priority_value=0)
    system_positive = TestSystem(priority_value=100)
    scheduler.register(system=system_positive)
    scheduler.register(system=system_negative)
    scheduler.register(system=system_zero)
    systems = scheduler.get_ordered_systems()
    assert systems[0] is system_negative
    assert systems[1] is system_zero
    assert systems[2] is system_positive


def test_register_many_systems() -> None:
    """Test registering large number of systems."""
    scheduler = SystemScheduler()
    num_systems = 100
    for i in range(num_systems):
        scheduler.register(system=TestSystem(priority_value=i))
    assert scheduler.count == num_systems
    systems = scheduler.get_ordered_systems()
    for i in range(num_systems - 1):
        assert systems[i].priority <= systems[i + 1].priority


def test_systems_execute_in_priority_order() -> None:
    """Test systems can be executed in priority order."""
    scheduler = SystemScheduler()
    system1 = TestSystem(priority_value=100)
    system2 = TestSystem(priority_value=50)
    scheduler.register(system=system1)
    scheduler.register(system=system2)
    world = ECSWorld()
    for system in scheduler.get_ordered_systems():
        system.update(world=world, delta_time=0.016)
    assert system2.update_count == 1
    assert system1.update_count == 1


def test_register_after_clear() -> None:
    """Test registering systems after clearing."""
    scheduler = SystemScheduler()
    scheduler.register(system=TestSystem(priority_value=100))
    scheduler.clear()
    scheduler.register(system=TestSystem(priority_value=200))
    assert scheduler.count == 1


def test_get_ordered_systems_empty_scheduler() -> None:
    """Test get_ordered_systems returns empty list for empty scheduler."""
    scheduler = SystemScheduler()
    systems = scheduler.get_ordered_systems()
    assert systems == []


def test_priority_ordering_with_random_registration() -> None:
    """Test priority ordering works regardless of registration order."""
    scheduler = SystemScheduler()
    priorities = [500, 100, 300, 200, 400]
    for priority in priorities:
        scheduler.register(system=TestSystem(priority_value=priority))
    systems = scheduler.get_ordered_systems()
    sorted_priorities = [s.priority for s in systems]
    assert sorted_priorities == sorted(priorities)


def test_multiple_clears() -> None:
    """Test multiple clear operations."""
    scheduler = SystemScheduler()
    scheduler.register(system=TestSystem(priority_value=100))
    scheduler.clear()
    scheduler.clear()
    scheduler.clear()
    assert scheduler.count == 0


def test_count_after_multiple_operations() -> None:
    """Test count remains accurate after multiple operations."""
    scheduler = SystemScheduler()
    scheduler.register(system=TestSystem(priority_value=100))
    scheduler.register(system=TestSystem(priority_value=200))
    assert scheduler.count == 2
    scheduler.clear()
    assert scheduler.count == 0
    scheduler.register(system=TestSystem(priority_value=300))
    assert scheduler.count == 1


def test_scheduler_with_monitor() -> None:
    """Test SystemScheduler can be created with performance monitor."""
    monitor = PerformanceMonitor()
    scheduler = SystemScheduler(monitor=monitor)
    assert scheduler.count == 0


def test_scheduler_with_monitor_registers_systems() -> None:
    """Test scheduler with monitor can register and order systems."""
    monitor = PerformanceMonitor()
    scheduler = SystemScheduler(monitor=monitor)
    system1 = TestSystem(priority_value=200)
    system2 = TestSystem(priority_value=100)
    scheduler.register(system=system1)
    scheduler.register(system=system2)
    systems = scheduler.get_ordered_systems()
    assert len(systems) == 2
    assert systems[0] is system2
    assert systems[1] is system1


def test_get_parallel_jobs() -> None:
    """Test getting parallel jobs from registered systems."""
    scheduler = SystemScheduler()
    system1 = TestSystem(priority_value=100)
    system2 = TestSystem(priority_value=200)
    scheduler.register(system=system1)
    scheduler.register(system=system2)

    jobs = scheduler.get_parallel_jobs()

    assert len(jobs) == 2
    assert all(job.system in [system1, system2] for job in jobs)


def test_get_parallel_jobs_with_dependencies() -> None:
    """Test getting parallel jobs respects dependencies."""
    scheduler = SystemScheduler()
    system1 = TestSystem(priority_value=100)
    system2 = TestSystem(priority_value=200)
    scheduler.register(system=system1)
    scheduler.register(system=system2)
    scheduler.add_dependency(system=system2, depends_on=system1)

    jobs = scheduler.get_parallel_jobs()

    job1 = next(job for job in jobs if job.system is system1)
    job2 = next(job for job in jobs if job.system is system2)
    assert len(job1.dependencies) == 0
    assert len(job2.dependencies) == 1
    assert job2.dependencies[0] is job1


@pytest.mark.asyncio
async def test_execute_parallel() -> None:
    """Test parallel execution runs all systems."""
    scheduler = SystemScheduler()
    system1 = TestSystem(priority_value=100)
    system2 = TestSystem(priority_value=200)
    scheduler.register(system=system1)
    scheduler.register(system=system2)
    world = ECSWorld()

    await scheduler.execute_parallel(world=world, delta_time=0.016)

    assert system1.update_count == 1
    assert system2.update_count == 1


@pytest.mark.asyncio
async def test_execute_sequential() -> None:
    """Test sequential execution runs all systems."""
    scheduler = SystemScheduler()
    system1 = TestSystem(priority_value=100)
    system2 = TestSystem(priority_value=200)
    scheduler.register(system=system1)
    scheduler.register(system=system2)
    world = ECSWorld()

    await scheduler.execute_sequential(world=world, delta_time=0.016)

    assert system1.update_count == 1
    assert system2.update_count == 1
