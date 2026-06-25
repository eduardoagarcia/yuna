"""Tests for flyweight factory implementation."""

from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.resources.flyweight import FlyweightFactory

fake = Faker()


@dataclass(frozen=True)
class ImmutableObject:
    """Test immutable object for flyweight testing."""

    value: int
    name: str


def test_flyweight_factory_creation() -> None:
    """Test FlyweightFactory can be created."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    assert factory.count() == 0


def test_get_creates_instance_for_new_key() -> None:
    """Test get creates new instance for first access."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    value = fake.random_int()
    name = fake.word()
    obj = factory.get(
        key="test",
        factory=lambda: ImmutableObject(value=value, name=name),
    )
    assert obj.value == value
    assert obj.name == name


def test_get_returns_same_instance_for_same_key() -> None:
    """Test get returns cached instance for same key."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    obj1 = factory.get(
        key="test",
        factory=lambda: ImmutableObject(value=1, name="test"),
    )
    obj2 = factory.get(
        key="test",
        factory=lambda: ImmutableObject(value=2, name="other"),
    )
    assert obj1 is obj2
    assert obj1.value == 1
    assert obj2.value == 1


def test_get_with_different_keys_creates_different_instances() -> None:
    """Test get creates different instances for different keys."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    obj1 = factory.get(
        key="key1",
        factory=lambda: ImmutableObject(value=1, name="obj1"),
    )
    obj2 = factory.get(
        key="key2",
        factory=lambda: ImmutableObject(value=2, name="obj2"),
    )
    assert obj1 is not obj2
    assert obj1.value == 1
    assert obj2.value == 2


def test_count_returns_zero_initially() -> None:
    """Test count returns zero for empty factory."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    assert factory.count() == 0


def test_count_increases_with_new_keys() -> None:
    """Test count increases as new keys are added."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    factory.get(key="key1", factory=lambda: ImmutableObject(value=1, name="a"))
    assert factory.count() == 1
    factory.get(key="key2", factory=lambda: ImmutableObject(value=2, name="b"))
    assert factory.count() == 2


def test_count_does_not_increase_for_existing_keys() -> None:
    """Test count stays same when getting cached instances."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    factory.get(key="test", factory=lambda: ImmutableObject(value=1, name="a"))
    count_before = factory.count()
    factory.get(key="test", factory=lambda: ImmutableObject(value=2, name="b"))
    assert factory.count() == count_before


def test_clear_removes_all_instances() -> None:
    """Test clear empties the cache."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    for i in range(5):
        factory.get(
            key=f"key{i}",
            factory=lambda i=i: ImmutableObject(value=i, name=f"obj{i}"),  # type: ignore[misc]
        )
    factory.clear()
    assert factory.count() == 0


def test_has_returns_false_for_new_key() -> None:
    """Test has returns False for uncached key."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    assert factory.has(key="nonexistent") is False


def test_has_returns_true_for_cached_key() -> None:
    """Test has returns True for cached key."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    factory.get(key="test", factory=lambda: ImmutableObject(value=1, name="a"))
    assert factory.has(key="test") is True


def test_has_returns_false_after_clear() -> None:
    """Test has returns False after clearing cache."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    factory.get(key="test", factory=lambda: ImmutableObject(value=1, name="a"))
    factory.clear()
    assert factory.has(key="test") is False


def test_factory_function_called_once_per_key() -> None:
    """Test factory function only called once for same key."""
    call_count = 0

    def counting_factory() -> ImmutableObject:
        nonlocal call_count
        call_count += 1
        return ImmutableObject(value=1, name="test")

    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    factory.get(key="test", factory=counting_factory)
    factory.get(key="test", factory=counting_factory)
    factory.get(key="test", factory=counting_factory)
    assert call_count == 1


def test_factory_function_called_for_each_unique_key() -> None:
    """Test factory function called for each different key."""
    call_count = 0

    def counting_factory() -> ImmutableObject:
        nonlocal call_count
        call_count += 1
        return ImmutableObject(value=call_count, name="test")

    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    factory.get(key="key1", factory=counting_factory)
    factory.get(key="key2", factory=counting_factory)
    factory.get(key="key3", factory=counting_factory)
    assert call_count == 3


def test_get_with_string_keys() -> None:
    """Test get works with string keys."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    key = fake.word()
    factory.get(key=key, factory=lambda: ImmutableObject(value=1, name="a"))
    assert factory.has(key=key)
    assert factory.count() == 1


def test_get_with_integer_keys() -> None:
    """Test get works with integer keys."""
    factory: FlyweightFactory[int, ImmutableObject] = FlyweightFactory()
    key = fake.random_int()
    factory.get(key=key, factory=lambda: ImmutableObject(value=1, name="a"))
    assert factory.has(key=key)


def test_get_with_tuple_keys() -> None:
    """Test get works with tuple keys."""
    factory: FlyweightFactory[tuple[str, int], ImmutableObject] = FlyweightFactory()
    key = (fake.word(), fake.random_int())
    factory.get(key=key, factory=lambda: ImmutableObject(value=1, name="a"))
    assert factory.has(key=key)


def test_multiple_factories_are_independent() -> None:
    """Test multiple factory instances have separate caches."""
    factory1: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    factory2: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    obj1 = factory1.get(
        key="test",
        factory=lambda: ImmutableObject(value=1, name="a"),
    )
    obj2 = factory2.get(
        key="test",
        factory=lambda: ImmutableObject(value=2, name="b"),
    )
    assert obj1 is not obj2
    assert obj1.value == 1
    assert obj2.value == 2


def test_clear_on_empty_factory() -> None:
    """Test clear on empty factory does nothing."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    factory.clear()
    assert factory.count() == 0


def test_has_with_none_key() -> None:
    """Test has works with None as key."""
    factory: FlyweightFactory[None, ImmutableObject] = FlyweightFactory()
    assert factory.has(key=None) is False
    factory.get(key=None, factory=lambda: ImmutableObject(value=1, name="a"))
    assert factory.has(key=None) is True


def test_get_after_clear_creates_new_instance() -> None:
    """Test get creates new instance after clearing cache."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    obj1 = factory.get(key="test", factory=lambda: ImmutableObject(value=1, name="a"))
    factory.clear()
    obj2 = factory.get(key="test", factory=lambda: ImmutableObject(value=2, name="b"))
    assert obj1 is not obj2
    assert obj2.value == 2


def test_count_with_many_keys() -> None:
    """Test count works with large number of keys."""
    factory: FlyweightFactory[int, ImmutableObject] = FlyweightFactory()
    num_keys = 100
    for i in range(num_keys):
        factory.get(
            key=i,
            factory=lambda i=i: ImmutableObject(value=i, name=f"obj{i}"),  # type: ignore[misc]
        )
    assert factory.count() == num_keys


def test_get_preserves_instance_identity() -> None:
    """Test get returns exact same instance across calls."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()
    obj = ImmutableObject(value=fake.random_int(), name=fake.word())
    result1 = factory.get(key="test", factory=lambda: obj)
    result2 = factory.get(key="test", factory=lambda: obj)
    result3 = factory.get(key="test", factory=lambda: obj)
    assert result1 is result2
    assert result2 is result3


def test_factory_with_complex_key_types() -> None:
    """Test factory works with complex hashable key types."""
    factory: FlyweightFactory[frozenset[int], ImmutableObject] = FlyweightFactory()
    key1 = frozenset([1, 2, 3])
    key2 = frozenset([4, 5, 6])
    obj1 = factory.get(key=key1, factory=lambda: ImmutableObject(value=1, name="a"))
    obj2 = factory.get(key=key2, factory=lambda: ImmutableObject(value=2, name="b"))
    obj1_again = factory.get(
        key=key1,
        factory=lambda: ImmutableObject(value=3, name="c"),
    )
    assert obj1 is obj1_again
    assert obj1 is not obj2


def test_get_with_callable_that_raises() -> None:
    """Test get propagates exceptions from factory function."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()

    def failing_factory() -> ImmutableObject:
        raise ValueError("Factory failed")

    with pytest.raises(ValueError, match="Factory failed"):
        factory.get(key="test", factory=failing_factory)


def test_count_after_failed_factory() -> None:
    """Test count unchanged if factory function raises."""
    factory: FlyweightFactory[str, ImmutableObject] = FlyweightFactory()

    def failing_factory() -> ImmutableObject:
        raise ValueError("Factory failed")

    with pytest.raises(ValueError):
        factory.get(key="test", factory=failing_factory)

    assert factory.count() == 0
    assert factory.has(key="test") is False
