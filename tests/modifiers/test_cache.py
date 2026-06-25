"""Tests for ModifierCache."""

from unittest.mock import Mock, patch

from faker import Faker

from yuna.modifiers.cache import CacheEntry, ModifierCache

fake = Faker()


def test_cache_entry_is_not_expired_when_no_ttl() -> None:
    """Test cache entry never expires when ttl_ticks is None."""
    entry = CacheEntry(value=fake.pyint(), created_tick=0, ttl_ticks=None)
    assert not entry.is_expired(current_tick=1000)


def test_cache_entry_is_not_expired_when_within_ttl() -> None:
    """Test cache entry is not expired when within TTL."""
    entry = CacheEntry(value=fake.pyint(), created_tick=100, ttl_ticks=50)
    assert not entry.is_expired(current_tick=149)


def test_cache_entry_is_expired_when_past_ttl() -> None:
    """Test cache entry is expired when past TTL."""
    entry = CacheEntry(value=fake.pyint(), created_tick=100, ttl_ticks=50)
    assert entry.is_expired(current_tick=150)


def test_cache_entry_is_expired_at_exact_ttl_boundary() -> None:
    """Test cache entry is expired at exact TTL boundary."""
    entry = CacheEntry(value=fake.pyint(), created_tick=100, ttl_ticks=50)
    assert entry.is_expired(current_tick=150)


def test_cache_initializes_with_defaults() -> None:
    """Test cache initializes with default values."""
    cache = ModifierCache()
    assert cache.get_size() == 0
    assert cache.get_hit_rate() == 0.0


def test_cache_initializes_with_custom_max_size() -> None:
    """Test cache initializes with custom max size."""
    max_size = fake.pyint(min_value=100, max_value=1000)
    cache = ModifierCache(max_size=max_size)
    assert cache._max_size == max_size


def test_cache_set_current_tick_updates_tick() -> None:
    """Test set_current_tick updates internal tick counter."""
    cache = ModifierCache()
    tick = fake.pyint(min_value=0, max_value=1000)
    cache.set_current_tick(tick=tick)
    assert cache._current_tick == tick


def test_get_or_compute_returns_computed_value_on_miss() -> None:
    """Test get_or_compute computes and caches value on cache miss."""
    cache = ModifierCache()
    key = fake.word()
    expected_value = fake.pyint()
    compute_fn = Mock(return_value=expected_value)

    result = cache.get_or_compute(key=key, compute_fn=compute_fn)

    assert result == expected_value
    compute_fn.assert_called_once()
    assert cache.get_size() == 1


def test_get_or_compute_returns_cached_value_on_hit() -> None:
    """Test get_or_compute returns cached value without recomputing."""
    cache = ModifierCache()
    key = fake.word()
    expected_value = fake.pyint()
    compute_fn = Mock(return_value=expected_value)

    cache.get_or_compute(key=key, compute_fn=compute_fn)
    result = cache.get_or_compute(key=key, compute_fn=compute_fn)

    assert result == expected_value
    compute_fn.assert_called_once()


def test_get_or_compute_increments_hit_counter_on_cache_hit() -> None:
    """Test get_or_compute increments hit counter on cache hit."""
    cache = ModifierCache()
    key = fake.word()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key, compute_fn=compute_fn)
    cache.get_or_compute(key=key, compute_fn=compute_fn)

    assert cache._hits == 1
    assert cache._misses == 1


def test_get_or_compute_increments_miss_counter_on_cache_miss() -> None:
    """Test get_or_compute increments miss counter on cache miss."""
    cache = ModifierCache()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=fake.unique.word(), compute_fn=compute_fn)
    cache.get_or_compute(key=fake.unique.word(), compute_fn=compute_fn)

    assert cache._hits == 0
    assert cache._misses == 2


def test_get_or_compute_recomputes_when_entry_expired() -> None:
    """Test get_or_compute recomputes value when cached entry expired."""
    cache = ModifierCache()
    cache.set_current_tick(tick=100)
    key = fake.word()
    first_value = fake.pyint()
    second_value = fake.pyint()
    compute_fn = Mock(side_effect=[first_value, second_value])

    cache.get_or_compute(key=key, compute_fn=compute_fn, ttl_ticks=50)
    cache.set_current_tick(tick=200)
    result = cache.get_or_compute(key=key, compute_fn=compute_fn, ttl_ticks=50)

    assert result == second_value
    assert compute_fn.call_count == 2


def test_get_or_compute_removes_expired_entry_from_access_order() -> None:
    """Test get_or_compute removes expired entry from LRU access order."""
    cache = ModifierCache()
    cache.set_current_tick(tick=100)
    key = fake.word()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key, compute_fn=compute_fn, ttl_ticks=50)
    assert key in cache._access_order

    cache.set_current_tick(tick=200)
    cache.get_or_compute(key=key, compute_fn=compute_fn, ttl_ticks=50)

    assert cache._access_order.count(key) == 1


def test_get_or_compute_updates_lru_order_on_hit() -> None:
    """Test get_or_compute updates LRU access order on cache hit."""
    cache = ModifierCache()
    key1 = fake.unique.word()
    key2 = fake.unique.word()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key1, compute_fn=compute_fn)
    cache.get_or_compute(key=key2, compute_fn=compute_fn)
    cache.get_or_compute(key=key1, compute_fn=compute_fn)

    assert cache._access_order == [key2, key1]


def test_get_or_compute_evicts_lru_when_cache_full() -> None:
    """Test get_or_compute evicts least recently used entry when cache full."""
    cache = ModifierCache(max_size=2)
    key1 = fake.unique.word()
    key2 = fake.unique.word()
    key3 = fake.unique.word()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key1, compute_fn=compute_fn)
    cache.get_or_compute(key=key2, compute_fn=compute_fn)
    cache.get_or_compute(key=key3, compute_fn=compute_fn)

    assert key1 not in cache._cache
    assert key2 in cache._cache
    assert key3 in cache._cache
    assert cache.get_size() == 2


def test_invalidate_removes_entry_from_cache() -> None:
    """Test invalidate removes specific entry from cache."""
    cache = ModifierCache()
    key = fake.word()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key, compute_fn=compute_fn)
    cache.invalidate(key=key)

    assert key not in cache._cache
    assert cache.get_size() == 0


def test_invalidate_removes_entry_from_access_order() -> None:
    """Test invalidate removes entry from LRU access order."""
    cache = ModifierCache()
    key = fake.word()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key, compute_fn=compute_fn)
    cache.invalidate(key=key)

    assert key not in cache._access_order


def test_invalidate_does_nothing_when_key_not_found() -> None:
    """Test invalidate does nothing when key doesn't exist."""
    cache = ModifierCache()
    cache.invalidate(key=fake.word())
    assert cache.get_size() == 0


def test_invalidate_pattern_removes_matching_entries() -> None:
    """Test invalidate_pattern removes all entries matching pattern."""
    cache = ModifierCache()
    pattern = fake.pystr(min_chars=10, max_chars=15)
    key1 = f"{pattern}_test1"
    key2 = f"{pattern}_test2"
    key3 = f"unrelated_{fake.pystr(min_chars=10, max_chars=15)}"
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key1, compute_fn=compute_fn)
    cache.get_or_compute(key=key2, compute_fn=compute_fn)
    cache.get_or_compute(key=key3, compute_fn=compute_fn)

    cache.invalidate_pattern(pattern=pattern)

    assert key1 not in cache._cache
    assert key2 not in cache._cache
    assert key3 in cache._cache
    assert cache.get_size() == 1


def test_invalidate_pattern_removes_entries_from_access_order() -> None:
    """Test invalidate_pattern removes matching entries from access order."""
    cache = ModifierCache()
    pattern = fake.unique.word()
    key1 = f"{pattern}_test"
    key2 = fake.unique.word()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key1, compute_fn=compute_fn)
    cache.get_or_compute(key=key2, compute_fn=compute_fn)

    cache.invalidate_pattern(pattern=pattern)

    assert key1 not in cache._access_order
    assert key2 in cache._access_order


def test_clear_removes_all_entries() -> None:
    """Test clear removes all cached entries."""
    cache = ModifierCache()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=fake.word(), compute_fn=compute_fn)
    cache.get_or_compute(key=fake.word(), compute_fn=compute_fn)

    cache.clear()

    assert cache.get_size() == 0
    assert len(cache._access_order) == 0


def test_get_hit_rate_returns_zero_when_no_accesses() -> None:
    """Test get_hit_rate returns 0.0 when no cache accesses."""
    cache = ModifierCache()
    assert cache.get_hit_rate() == 0.0


def test_get_hit_rate_calculates_correct_ratio() -> None:
    """Test get_hit_rate calculates correct hit/miss ratio."""
    cache = ModifierCache()
    key = fake.unique.word()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key, compute_fn=compute_fn)
    cache.get_or_compute(key=key, compute_fn=compute_fn)
    cache.get_or_compute(key=key, compute_fn=compute_fn)
    cache.get_or_compute(key=fake.unique.word(), compute_fn=compute_fn)

    assert cache.get_hit_rate() == 0.5


def test_get_stats_returns_complete_statistics() -> None:
    """Test get_stats returns dictionary with all statistics."""
    cache = ModifierCache()
    key = fake.word()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key, compute_fn=compute_fn)
    cache.get_or_compute(key=key, compute_fn=compute_fn)

    stats = cache.get_stats()

    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["size"] == 1
    assert stats["hit_rate"] == 0.5


@patch("yuna.modifiers.cache.get_performance_monitor")
def test_cache_with_profiling_enabled_tracks_hits(mock_get_monitor: Mock) -> None:
    """Test cache tracks hit metrics when profiling enabled."""
    mock_monitor = Mock()
    mock_get_monitor.return_value = mock_monitor
    cache = ModifierCache(profiling_enabled=True)
    key = fake.word()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key, compute_fn=compute_fn)
    cache.get_or_compute(key=key, compute_fn=compute_fn)

    mock_monitor.record_count.assert_called_with(
        category="modifier_cache", name="hits", count=1
    )


@patch("yuna.modifiers.cache.get_performance_monitor")
def test_cache_with_profiling_enabled_tracks_misses(mock_get_monitor: Mock) -> None:
    """Test cache tracks miss metrics when profiling enabled."""
    mock_monitor = Mock()
    mock_get_monitor.return_value = mock_monitor
    cache = ModifierCache(profiling_enabled=True)
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=fake.word(), compute_fn=compute_fn)

    mock_monitor.record_count.assert_called_with(
        category="modifier_cache", name="misses", count=1
    )


@patch("yuna.modifiers.cache.get_performance_monitor")
def test_cache_with_profiling_disabled_does_not_track_metrics(
    mock_get_monitor: Mock,
) -> None:
    """Test cache does not track metrics when profiling disabled."""
    cache = ModifierCache(profiling_enabled=False)
    key = fake.word()
    compute_fn = Mock(return_value=fake.pyint())

    cache.get_or_compute(key=key, compute_fn=compute_fn)
    cache.get_or_compute(key=key, compute_fn=compute_fn)

    mock_get_monitor.assert_not_called()
