"""Pre-configured object pools for frequently allocated types."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yuna.resources.pool import ObjectPool

if TYPE_CHECKING:
    from yuna.events.queue import QueuedEvent
    from yuna.modifiers.modifier import Modifier
    from yuna.types.identifiers import EntityID


class PoolStatistics:
    """Statistics tracker for object pool usage.

    Responsibilities:
    - Track acquire and release counts
    - Calculate reuse ratio
    - Provide performance metrics

    Usage:
        stats = PoolStatistics()
        stats.record_acquire()
        stats.record_release()
        ratio = stats.reuse_ratio
    """

    def __init__(self) -> None:
        self._acquire_count = 0
        self._release_count = 0

    def record_acquire(self) -> None:
        """Record object acquisition."""
        self._acquire_count += 1

    def record_release(self) -> None:
        """Record object release."""
        self._release_count += 1

    def reset(self) -> None:
        """Reset all statistics."""
        self._acquire_count = 0
        self._release_count = 0

    @property
    def acquire_count(self) -> int:
        """Get total number of acquires.

        Returns:
            Number of times acquire was called
        """
        return self._acquire_count

    @property
    def release_count(self) -> int:
        """Get total number of releases.

        Returns:
            Number of times release was called
        """
        return self._release_count

    @property
    def reuse_ratio(self) -> float:
        """Calculate object reuse ratio.

        Returns:
            Ratio of releases to acquires (0-1), or 0 if no acquires
        """
        if self._acquire_count == 0:
            return 0.0
        return min(1.0, self._release_count / self._acquire_count)


class TrackedPool[T]:
    """Object pool wrapper with statistics tracking.

    Responsibilities:
    - Delegate to underlying ObjectPool
    - Track acquire/release statistics
    - Provide performance metrics

    Usage:
        pool = TrackedPool(underlying=ObjectPool(...))
        obj = pool.acquire()
        pool.release(obj=obj)
        print(f"Reuse ratio: {pool.statistics.reuse_ratio}")
    """

    def __init__(self, underlying: ObjectPool[T]) -> None:
        self._pool = underlying
        self._stats = PoolStatistics()

    def acquire(self) -> T:
        """Acquire object from pool.

        Returns:
            Object instance
        """
        self._stats.record_acquire()
        return self._pool.acquire()

    def release(self, obj: T) -> None:
        """Release object back to pool.

        Args:
            obj: Object to release
        """
        self._stats.record_release()
        self._pool.release(obj=obj)

    def clear(self) -> None:
        """Clear pool and reset statistics."""
        self._pool.clear()
        self._stats.reset()

    @property
    def size(self) -> int:
        """Get current pool size.

        Returns:
            Number of available objects
        """
        return self._pool.size

    @property
    def statistics(self) -> PoolStatistics:
        """Get pool statistics.

        Returns:
            PoolStatistics instance
        """
        return self._stats


def _create_event_list() -> list[QueuedEvent]:
    """Factory for event lists.

    Returns:
        Empty list for QueuedEvent instances
    """
    return []


def _reset_event_list(lst: list[QueuedEvent]) -> None:
    """Reset event list to empty state.

    Args:
        lst: List to reset
    """
    lst.clear()


def _create_entity_set() -> set[EntityID]:
    """Factory for entity sets.

    Returns:
        Empty set for EntityID instances
    """
    return set()


def _reset_entity_set(s: set[EntityID]) -> None:
    """Reset entity set to empty state.

    Args:
        s: Set to reset
    """
    s.clear()


def _create_modifier_list() -> list[Modifier]:
    """Factory for modifier lists.

    Returns:
        Empty list for Modifier instances
    """
    return []


def _reset_modifier_list(lst: list[Modifier]) -> None:
    """Reset modifier list to empty state.

    Args:
        lst: List to reset
    """
    lst.clear()


class GlobalPools:
    """Global object pools for frequently allocated types.

    Responsibilities:
    - Provide pre-configured pools for common types
    - Reduce GC pressure through object reuse
    - Track pool usage statistics

    Usage:
        pools = GlobalPools()
        event_list = pools.event_list.acquire()
        pools.event_list.release(obj=event_list)
    """

    def __init__(self) -> None:
        self._event_list_pool = TrackedPool(
            underlying=ObjectPool(
                factory=_create_event_list,
                reset=_reset_event_list,
                initial_size=10,
                max_size=100,
            )
        )

        self._entity_set_pool = TrackedPool(
            underlying=ObjectPool(
                factory=_create_entity_set,
                reset=_reset_entity_set,
                initial_size=20,
                max_size=200,
            )
        )

        self._modifier_list_pool = TrackedPool(
            underlying=ObjectPool(
                factory=_create_modifier_list,
                reset=_reset_modifier_list,
                initial_size=10,
                max_size=100,
            )
        )

    @property
    def event_list(self) -> TrackedPool[list[QueuedEvent]]:
        """Get event list pool.

        Returns:
            Pool for event list instances
        """
        return self._event_list_pool

    @property
    def entity_set(self) -> TrackedPool[set[EntityID]]:
        """Get entity set pool.

        Returns:
            Pool for entity set instances
        """
        return self._entity_set_pool

    @property
    def modifier_list(self) -> TrackedPool[list[Modifier]]:
        """Get modifier list pool.

        Returns:
            Pool for modifier list instances
        """
        return self._modifier_list_pool

    def clear_all(self) -> None:
        """Clear all pools and reset statistics."""
        self._event_list_pool.clear()
        self._entity_set_pool.clear()
        self._modifier_list_pool.clear()


_global_pools_instance: GlobalPools | None = None


def get_global_pools() -> GlobalPools:
    """Get singleton global pools instance.

    Returns:
        GlobalPools singleton
    """
    global _global_pools_instance
    if _global_pools_instance is None:
        _global_pools_instance = GlobalPools()
    return _global_pools_instance


def reset_global_pools() -> None:
    """Reset global pools singleton (mainly for testing)."""
    global _global_pools_instance
    if _global_pools_instance is not None:
        _global_pools_instance.clear_all()
    _global_pools_instance = None
