"""Tests for object pool management."""

from typing import cast

from faker import Faker

from yuna.events.queue import QueuedEvent
from yuna.modifiers.modifier import Modifier
from yuna.resources.pool import ObjectPool
from yuna.resources.pools import (
    GlobalPools,
    PoolStatistics,
    TrackedPool,
    get_global_pools,
    reset_global_pools,
)
from yuna.types.identifiers import EntityID

fake = Faker()


def test_pool_statistics_initial_state() -> None:
    """Test PoolStatistics starts with zero counts."""
    stats = PoolStatistics()
    assert stats.acquire_count == 0
    assert stats.release_count == 0
    assert stats.reuse_ratio == 0.0


def test_pool_statistics_record_acquire() -> None:
    """Test PoolStatistics records acquire operations."""
    stats = PoolStatistics()
    count = fake.random_int(min=1, max=10)
    for _ in range(count):
        stats.record_acquire()
    assert stats.acquire_count == count


def test_pool_statistics_record_release() -> None:
    """Test PoolStatistics records release operations."""
    stats = PoolStatistics()
    count = fake.random_int(min=1, max=10)
    for _ in range(count):
        stats.record_release()
    assert stats.release_count == count


def test_pool_statistics_reuse_ratio_perfect() -> None:
    """Test PoolStatistics calculates perfect reuse ratio."""
    stats = PoolStatistics()
    count = fake.random_int(min=1, max=10)
    for _ in range(count):
        stats.record_acquire()
        stats.record_release()
    assert stats.reuse_ratio == 1.0


def test_pool_statistics_reuse_ratio_partial() -> None:
    """Test PoolStatistics calculates partial reuse ratio."""
    stats = PoolStatistics()
    acquire_count = 10
    release_count = 5
    for _ in range(acquire_count):
        stats.record_acquire()
    for _ in range(release_count):
        stats.record_release()
    assert stats.reuse_ratio == 0.5


def test_pool_statistics_reuse_ratio_over_100_percent() -> None:
    """Test PoolStatistics caps reuse ratio at 100%."""
    stats = PoolStatistics()
    stats.record_acquire()
    for _ in range(5):
        stats.record_release()
    assert stats.reuse_ratio == 1.0


def test_pool_statistics_reset() -> None:
    """Test PoolStatistics reset clears all counts."""
    stats = PoolStatistics()
    stats.record_acquire()
    stats.record_release()
    stats.reset()
    assert stats.acquire_count == 0
    assert stats.release_count == 0
    assert stats.reuse_ratio == 0.0


def test_tracked_pool_acquire() -> None:
    """Test TrackedPool tracks acquire operations."""
    pool: TrackedPool[list] = TrackedPool(
        underlying=ObjectPool(
            factory=lambda: [],
            reset=lambda x: x.clear(),
            initial_size=0,
            max_size=10,
        )
    )
    obj = pool.acquire()
    assert isinstance(obj, list)
    assert pool.statistics.acquire_count == 1


def test_tracked_pool_release() -> None:
    """Test TrackedPool tracks release operations."""
    pool: TrackedPool[list] = TrackedPool(
        underlying=ObjectPool(
            factory=lambda: [],
            reset=lambda x: x.clear(),
            initial_size=0,
            max_size=10,
        )
    )
    obj = pool.acquire()
    pool.release(obj=obj)
    assert pool.statistics.release_count == 1


def test_tracked_pool_size() -> None:
    """Test TrackedPool reports correct size."""
    initial_size = fake.random_int(min=1, max=10)
    pool: TrackedPool[list] = TrackedPool(
        underlying=ObjectPool(
            factory=lambda: [],
            reset=lambda x: x.clear(),
            initial_size=initial_size,
            max_size=20,
        )
    )
    assert pool.size == initial_size


def test_tracked_pool_clear() -> None:
    """Test TrackedPool clear resets pool and statistics."""
    pool: TrackedPool[list] = TrackedPool(
        underlying=ObjectPool(
            factory=lambda: [],
            reset=lambda x: x.clear(),
            initial_size=5,
            max_size=10,
        )
    )
    pool.acquire()
    pool.clear()
    assert pool.size == 0
    assert pool.statistics.acquire_count == 0


def test_global_pools_event_list_pool() -> None:
    """Test GlobalPools provides event list pool."""
    pools = GlobalPools()
    event_list = pools.event_list.acquire()
    assert isinstance(event_list, list)
    assert len(event_list) == 0


def test_global_pools_entity_set_pool() -> None:
    """Test GlobalPools provides entity set pool."""
    pools = GlobalPools()
    entity_set = pools.entity_set.acquire()
    assert isinstance(entity_set, set)
    assert len(entity_set) == 0


def test_global_pools_modifier_list_pool() -> None:
    """Test GlobalPools provides modifier list pool."""
    pools = GlobalPools()
    modifier_list = pools.modifier_list.acquire()
    assert isinstance(modifier_list, list)
    assert len(modifier_list) == 0


def test_global_pools_event_list_reuse() -> None:
    """Test GlobalPools event list pool reuses objects."""
    pools = GlobalPools()
    list1 = pools.event_list.acquire()
    list1.append(cast(QueuedEvent, fake.pyint()))
    pools.event_list.release(obj=list1)
    list2 = pools.event_list.acquire()
    assert list2 is list1
    assert len(list2) == 0


def test_global_pools_entity_set_reuse() -> None:
    """Test GlobalPools entity set pool reuses objects."""
    pools = GlobalPools()
    set1 = pools.entity_set.acquire()
    set1.add(EntityID(fake.uuid4()))
    pools.entity_set.release(obj=set1)
    set2 = pools.entity_set.acquire()
    assert set2 is set1
    assert len(set2) == 0


def test_global_pools_modifier_list_reuse() -> None:
    """Test GlobalPools modifier list pool reuses objects."""
    pools = GlobalPools()
    list1 = pools.modifier_list.acquire()
    list1.append(cast(Modifier, fake.pyint()))
    pools.modifier_list.release(obj=list1)
    list2 = pools.modifier_list.acquire()
    assert list2 is list1
    assert len(list2) == 0


def test_global_pools_clear_all() -> None:
    """Test GlobalPools clear_all clears all pools."""
    pools = GlobalPools()
    pools.event_list.acquire()
    pools.entity_set.acquire()
    pools.modifier_list.acquire()
    pools.clear_all()
    assert pools.event_list.size == 0
    assert pools.entity_set.size == 0
    assert pools.modifier_list.size == 0


def test_get_global_pools_singleton() -> None:
    """Test get_global_pools returns same instance."""
    reset_global_pools()
    pools1 = get_global_pools()
    pools2 = get_global_pools()
    assert pools1 is pools2


def test_reset_global_pools() -> None:
    """Test reset_global_pools clears singleton."""
    pools1 = get_global_pools()
    reset_global_pools()
    pools2 = get_global_pools()
    assert pools1 is not pools2


def test_reset_global_pools_clears_pools() -> None:
    """Test reset_global_pools creates fresh pools with initial sizes."""
    pools = get_global_pools()
    pools.event_list.acquire()
    pools.entity_set.acquire()
    pools.modifier_list.acquire()
    reset_global_pools()
    new_pools = get_global_pools()
    assert new_pools.event_list.size == 10
    assert new_pools.entity_set.size == 20
    assert new_pools.modifier_list.size == 10


def test_global_pools_event_list_statistics() -> None:
    """Test GlobalPools tracks event list pool statistics."""
    reset_global_pools()
    pools = get_global_pools()
    event_list = pools.event_list.acquire()
    pools.event_list.release(obj=event_list)
    assert pools.event_list.statistics.acquire_count == 1
    assert pools.event_list.statistics.release_count == 1
    assert pools.event_list.statistics.reuse_ratio == 1.0


def test_global_pools_entity_set_statistics() -> None:
    """Test GlobalPools tracks entity set pool statistics."""
    reset_global_pools()
    pools = get_global_pools()
    entity_set = pools.entity_set.acquire()
    pools.entity_set.release(obj=entity_set)
    assert pools.entity_set.statistics.acquire_count == 1
    assert pools.entity_set.statistics.release_count == 1
    assert pools.entity_set.statistics.reuse_ratio == 1.0


def test_global_pools_modifier_list_statistics() -> None:
    """Test GlobalPools tracks modifier list pool statistics."""
    reset_global_pools()
    pools = get_global_pools()
    modifier_list = pools.modifier_list.acquire()
    pools.modifier_list.release(obj=modifier_list)
    assert pools.modifier_list.statistics.acquire_count == 1
    assert pools.modifier_list.statistics.release_count == 1
    assert pools.modifier_list.statistics.reuse_ratio == 1.0


def test_global_pools_multiple_acquires_exceeds_pool() -> None:
    """Test GlobalPools creates new objects when pool exhausted."""
    reset_global_pools()
    pools = get_global_pools()
    acquired_lists = []
    for _ in range(15):
        acquired_lists.append(pools.event_list.acquire())
    assert pools.event_list.statistics.acquire_count == 15
    assert all(isinstance(lst, list) for lst in acquired_lists)


def test_global_pools_release_respects_max_size() -> None:
    """Test GlobalPools respects max_size when releasing."""
    reset_global_pools()
    pools = get_global_pools()
    acquired = [pools.event_list.acquire() for _ in range(150)]
    for lst in acquired:
        pools.event_list.release(obj=lst)
    assert pools.event_list.size == 100
