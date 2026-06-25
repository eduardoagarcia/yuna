"""Object pool for reusing instances and reducing allocations."""

from __future__ import annotations

from collections.abc import Callable


class ObjectPool[T]:
    """Generic object pool for reusing instances.

    Responsibilities:
    - Create objects using factory function
    - Maintain pool of reusable instances
    - Reset objects when returned to pool
    - Limit pool size to prevent unbounded growth

    Usage:
        def create_vector() -> Vector2:
            return Vector2(x=0.0, y=0.0)

        def reset_vector(vec: Vector2) -> None:
            vec.x = 0.0
            vec.y = 0.0

        pool = ObjectPool(
            factory=create_vector,
            reset=reset_vector,
            initial_size=10,
            max_size=100,
        )

        vec = pool.acquire()
        vec.x = 5.0
        pool.release(obj=vec)
    """

    def __init__(
        self,
        factory: Callable[[], T],
        reset: Callable[[T], None],
        initial_size: int = 0,
        max_size: int = 100,
    ):
        """Initialize object pool.

        Args:
            factory: Function to create new instances
            reset: Function to reset instance state
            initial_size: Number of objects to pre-create
            max_size: Maximum pool size (objects beyond this are discarded)
        """
        self._factory = factory
        self._reset = reset
        self._max_size = max_size
        self._pool: list[T] = []

        for _ in range(initial_size):
            self._pool.append(self._factory())

    def acquire(self) -> T:
        """Get object from pool or create new one if pool is empty.

        Returns:
            Object instance ready for use
        """
        if self._pool:
            return self._pool.pop()
        return self._factory()

    def release(self, obj: T) -> None:
        """Return object to pool after resetting its state.

        If pool is at max size, object is discarded.

        Args:
            obj: Object to return to pool
        """
        self._reset(obj)
        if len(self._pool) < self._max_size:
            self._pool.append(obj)

    def clear(self) -> None:
        """Clear all objects from pool."""
        self._pool.clear()

    @property
    def size(self) -> int:
        """Get current number of objects in pool.

        Returns:
            Number of available objects
        """
        return len(self._pool)
