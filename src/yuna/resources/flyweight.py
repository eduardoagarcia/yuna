"""Flyweight factory for sharing immutable instances."""

from __future__ import annotations

from collections.abc import Callable


class FlyweightFactory[K, T]:
    """Factory for managing shared flyweight instances.

    Responsibilities:
    - Create instances using factory function
    - Cache and reuse instances by key
    - Ensure same key returns same instance
    - Reduce memory usage for immutable objects

    Usage:
        factory = FlyweightFactory()

        texture1 = factory.get(
            key="grass.png",
            factory=lambda: load_texture("grass.png"),
        )
        texture2 = factory.get(
            key="grass.png",
            factory=lambda: load_texture("grass.png"),
        )

        assert texture1 is texture2
    """

    def __init__(self) -> None:
        """Initialize flyweight factory with empty cache."""
        self._cache: dict[K, T] = {}

    def get(self, key: K, factory: Callable[[], T]) -> T:
        """Get shared instance for key, creating if needed.

        Factory function is only called once per unique key.
        Subsequent calls with same key return cached instance.

        Args:
            key: Unique identifier for this instance
            factory: Function to create instance if not cached

        Returns:
            Shared instance for this key
        """
        if key not in self._cache:
            self._cache[key] = factory()
        return self._cache[key]

    def count(self) -> int:
        """Get number of cached instances.

        Returns:
            Number of unique instances in cache
        """
        return len(self._cache)

    def clear(self) -> None:
        """Clear all cached instances."""
        self._cache.clear()

    def has(self, key: K) -> bool:
        """Check if key exists in cache.

        Args:
            key: Key to check

        Returns:
            True if instance cached for this key
        """
        return key in self._cache
