"""Tests for object pool implementation."""

from dataclasses import dataclass

from faker import Faker

from yuna.resources.pool import ObjectPool

fake = Faker()


@dataclass
class TestObject:
    """Test object for pool testing."""

    value: int = 0
    name: str = ""


def test_object_pool_creation() -> None:
    """Test ObjectPool can be created with factory and reset."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
    )
    assert pool.size == 0


def test_object_pool_with_initial_size() -> None:
    """Test ObjectPool pre-creates objects with initial_size."""
    initial_size = fake.random_int(min=1, max=10)
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        initial_size=initial_size,
    )
    assert pool.size == initial_size


def test_acquire_from_empty_pool_creates_new_object() -> None:
    """Test acquire creates new object when pool is empty."""
    pool = ObjectPool(
        factory=lambda: TestObject(value=fake.random_int()),
        reset=lambda obj: None,
    )
    obj = pool.acquire()
    assert isinstance(obj, TestObject)


def test_acquire_from_pool_with_objects() -> None:
    """Test acquire returns object from pool when available."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        initial_size=1,
    )
    initial_size = pool.size
    obj = pool.acquire()
    assert pool.size == initial_size - 1
    assert isinstance(obj, TestObject)


def test_release_adds_object_to_pool() -> None:
    """Test release returns object to pool."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: setattr(obj, "value", 0),
    )
    obj = pool.acquire()
    obj.value = fake.random_int()
    initial_size = pool.size
    pool.release(obj=obj)
    assert pool.size == initial_size + 1


def test_release_calls_reset_function() -> None:
    """Test release resets object state."""
    reset_value = fake.random_int()
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: setattr(obj, "value", reset_value),
    )
    obj = pool.acquire()
    obj.value = fake.random_int(min=reset_value + 1, max=reset_value + 100)
    pool.release(obj=obj)
    assert obj.value == reset_value


def test_release_when_pool_at_max_size_discards_object() -> None:
    """Test release discards object when pool is full."""
    max_size = fake.random_int(min=1, max=5)
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        initial_size=max_size,
        max_size=max_size,
    )
    obj = pool.acquire()
    pool.release(obj=obj)
    assert pool.size == max_size


def test_acquire_and_release_cycle() -> None:
    """Test acquiring and releasing objects maintains pool."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: setattr(obj, "value", 0),
        initial_size=5,
    )
    obj1 = pool.acquire()
    obj2 = pool.acquire()
    pool.release(obj=obj1)
    pool.release(obj=obj2)
    assert pool.size == 5


def test_clear_removes_all_objects() -> None:
    """Test clear empties the pool."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        initial_size=fake.random_int(min=1, max=10),
    )
    pool.clear()
    assert pool.size == 0


def test_clear_on_empty_pool() -> None:
    """Test clear on empty pool does nothing."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
    )
    pool.clear()
    assert pool.size == 0


def test_size_property() -> None:
    """Test size property returns correct count."""
    initial_size = fake.random_int(min=1, max=10)
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        initial_size=initial_size,
    )
    assert pool.size == initial_size
    pool.acquire()
    assert pool.size == initial_size - 1


def test_multiple_acquire_depletes_pool() -> None:
    """Test multiple acquires reduce pool size correctly."""
    initial_size = 5
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        initial_size=initial_size,
    )
    for i in range(initial_size):
        pool.acquire()
        assert pool.size == initial_size - i - 1


def test_acquire_beyond_initial_size_creates_new() -> None:
    """Test acquiring more objects than initial size creates new ones."""
    initial_size = 2
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        initial_size=initial_size,
    )
    objects = [pool.acquire() for _ in range(initial_size + 5)]
    assert len(objects) == initial_size + 5
    assert pool.size == 0


def test_pool_with_zero_initial_size() -> None:
    """Test pool works with zero initial size."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        initial_size=0,
    )
    assert pool.size == 0
    obj = pool.acquire()
    assert isinstance(obj, TestObject)


def test_pool_with_zero_max_size_discards_all_releases() -> None:
    """Test pool with max_size=0 never stores objects."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        max_size=0,
    )
    obj = pool.acquire()
    pool.release(obj=obj)
    assert pool.size == 0


def test_reset_function_can_modify_multiple_fields() -> None:
    """Test reset function can reset multiple object fields."""
    reset_value = fake.random_int()
    reset_name = fake.word()

    def reset_obj(obj: TestObject) -> None:
        obj.value = reset_value
        obj.name = reset_name

    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=reset_obj,
    )
    obj = pool.acquire()
    obj.value = fake.random_int()
    obj.name = fake.word()
    pool.release(obj=obj)
    assert obj.value == reset_value
    assert obj.name == reset_name


def test_factory_creates_different_instances() -> None:
    """Test factory creates unique instances."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
    )
    obj1 = pool.acquire()
    obj2 = pool.acquire()
    assert obj1 is not obj2


def test_pool_reuses_released_objects() -> None:
    """Test pool returns same object instance after release."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
    )
    obj1 = pool.acquire()
    pool.release(obj=obj1)
    obj2 = pool.acquire()
    assert obj1 is obj2


def test_pool_with_large_max_size() -> None:
    """Test pool with very large max size."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        max_size=10000,
    )
    objects = [pool.acquire() for _ in range(100)]
    for obj in objects:
        pool.release(obj=obj)
    assert pool.size == 100


def test_release_multiple_times_does_not_exceed_max_size() -> None:
    """Test releasing more objects than max_size discards excess."""
    max_size = 3
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        max_size=max_size,
    )
    objects = [pool.acquire() for _ in range(10)]
    for obj in objects:
        pool.release(obj=obj)
    assert pool.size == max_size


def test_pool_with_custom_factory() -> None:
    """Test pool works with custom factory function."""
    custom_value = fake.random_int()

    def custom_factory() -> TestObject:
        return TestObject(value=custom_value)

    pool = ObjectPool(
        factory=custom_factory,
        reset=lambda obj: None,
    )
    obj = pool.acquire()
    assert obj.value == custom_value


def test_pool_with_complex_reset_logic() -> None:
    """Test pool with complex reset function."""
    call_count = 0

    def complex_reset(obj: TestObject) -> None:
        nonlocal call_count
        call_count += 1
        obj.value = 0
        obj.name = ""

    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=complex_reset,
    )
    obj = pool.acquire()
    pool.release(obj=obj)
    assert call_count == 1


def test_acquire_release_cycle_maintains_count() -> None:
    """Test repeated acquire/release cycles maintain correct count."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        initial_size=5,
    )
    for _ in range(10):
        obj = pool.acquire()
        pool.release(obj=obj)
    assert pool.size == 5


def test_clear_after_acquires() -> None:
    """Test clear works after acquiring objects."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        initial_size=10,
    )
    for _ in range(5):
        pool.acquire()
    pool.clear()
    assert pool.size == 0


def test_initial_size_greater_than_max_size() -> None:
    """Test initial_size can be greater than max_size."""
    pool = ObjectPool(
        factory=lambda: TestObject(),
        reset=lambda obj: None,
        initial_size=10,
        max_size=5,
    )
    assert pool.size == 10
