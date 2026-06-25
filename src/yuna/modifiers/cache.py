"""Caching layer for expensive modifier calculations."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from yuna.profiling.monitor import get_performance_monitor


@dataclass
class CacheEntry:
    """Cache entry with value and TTL tracking.

    Attributes:
        value: Cached value
        created_tick: Tick when entry was created
        ttl_ticks: Time to live in ticks (None = no expiration)
    """

    value: Any
    created_tick: int
    ttl_ticks: int | None = None

    def is_expired(self, current_tick: int) -> bool:
        """Check if entry has expired.

        Args:
            current_tick: Current game tick

        Returns:
            True if expired, False otherwise
        """
        if self.ttl_ticks is None:
            return False
        return current_tick >= self.created_tick + self.ttl_ticks


class ModifierCache:
    """Cache for expensive modifier calculations.

    Provides caching with TTL support and LRU eviction when size limit reached.

    Usage:
        cache = ModifierCache(max_size=1000)
        result = cache.get_or_compute(
            key="stat_calculation_entity_123",
            compute_fn=lambda: expensive_calculation(),
            ttl_ticks=100,
        )
        cache.invalidate(key="stat_calculation_entity_123")
    """

    def __init__(self, max_size: int = 1000, profiling_enabled: bool = False) -> None:
        """Initialize cache.

        Args:
            max_size: Maximum number of entries to cache
            profiling_enabled: Whether to track cache metrics
        """
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._access_order: list[str] = []
        self._current_tick = 0
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    def set_current_tick(self, tick: int) -> None:
        """Update current tick for TTL tracking.

        Args:
            tick: Current game tick
        """
        self._current_tick = tick

    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        ttl_ticks: int | None = None,
    ) -> Any:
        """Get cached value or compute if missing.

        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached
            ttl_ticks: Time to live in ticks (None = no expiration)

        Returns:
            Cached or computed value
        """
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired(current_tick=self._current_tick):
                self._hits += 1
                if self._profiling_enabled and self._monitor:
                    self._monitor.record_count(
                        category="modifier_cache", name="hits", count=1
                    )
                self._update_access_order(key=key)
                return entry.value
            else:
                del self._cache[key]
                self._access_order.remove(key)

        self._misses += 1
        if self._profiling_enabled and self._monitor:
            self._monitor.record_count(
                category="modifier_cache", name="misses", count=1
            )
        value = compute_fn()

        self._evict_if_needed()

        self._cache[key] = CacheEntry(
            value=value, created_tick=self._current_tick, ttl_ticks=ttl_ticks
        )
        self._access_order.append(key)

        return value

    def invalidate(self, key: str) -> None:
        """Invalidate specific cache entry.

        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
            self._access_order.remove(key)

    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all entries matching pattern.

        Args:
            pattern: Pattern to match (substring match)
        """
        keys_to_remove = [key for key in self._cache if pattern in key]
        for key in keys_to_remove:
            del self._cache[key]
            self._access_order.remove(key)

    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
        self._access_order.clear()

    def get_hit_rate(self) -> float:
        """Get cache hit rate [0, 1].

        Returns:
            Hit rate as float between 0 and 1
        """
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def get_size(self) -> int:
        """Get current cache size.

        Returns:
            Number of entries in cache
        """
        return len(self._cache)

    def get_stats(self) -> dict[str, int | float]:
        """Get cache statistics.

        Returns:
            Dictionary with hits, misses, size, and hit_rate
        """
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "hit_rate": self.get_hit_rate(),
        }

    def _update_access_order(self, key: str) -> None:
        """Update LRU access order.

        Args:
            key: Key that was accessed
        """
        self._access_order.remove(key)
        self._access_order.append(key)

    def _evict_if_needed(self) -> None:
        """Evict least recently used entry if cache is full."""
        if len(self._cache) >= self._max_size and self._access_order:
            lru_key = self._access_order.pop(0)
            del self._cache[lru_key]
