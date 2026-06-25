"""Tests for profiling decorators."""

import asyncio
import time

import pytest
from faker import Faker

from yuna.profiling.decorators import profile, profile_async
from yuna.profiling.monitor import (
    get_performance_monitor,
    reset_performance_monitor,
)

fake = Faker()


def test_profile_decorator_records_timing() -> None:
    """Test profile decorator records function timing."""
    reset_performance_monitor()
    monitor = get_performance_monitor()

    category = fake.word()
    metric_name = fake.word()

    @profile(category=category, name=metric_name)
    def test_function() -> str:
        time.sleep(0.01)
        return fake.word()

    result = test_function()

    assert isinstance(result, str)
    stats = monitor.get_timing_stats(category=category, name=metric_name)
    assert stats is not None
    assert stats.count == 1
    assert stats.avg_time > 0.0


def test_profile_decorator_uses_function_name_by_default() -> None:
    """Test profile decorator uses function name when name not provided."""
    reset_performance_monitor()
    monitor = get_performance_monitor()

    category = fake.word()

    @profile(category=category)
    def my_test_function() -> None:
        pass

    my_test_function()

    stats = monitor.get_timing_stats(category=category, name="my_test_function")
    assert stats is not None
    assert stats.count == 1


def test_profile_decorator_multiple_calls() -> None:
    """Test profile decorator records multiple function calls."""
    reset_performance_monitor()
    monitor = get_performance_monitor()

    category = fake.word()
    metric_name = fake.word()

    @profile(category=category, name=metric_name)
    def test_function() -> None:
        time.sleep(0.001)

    test_function()
    test_function()
    test_function()

    stats = monitor.get_timing_stats(category=category, name=metric_name)
    assert stats is not None
    assert stats.count == 3


def test_profile_decorator_preserves_return_value() -> None:
    """Test profile decorator preserves function return value."""
    reset_performance_monitor()

    category = fake.word()
    expected_value = fake.random_int()

    @profile(category=category)
    def test_function() -> int:
        return expected_value

    result = test_function()

    assert result == expected_value


def test_profile_decorator_preserves_exceptions() -> None:
    """Test profile decorator preserves function exceptions."""
    reset_performance_monitor()
    monitor = get_performance_monitor()

    category = fake.word()
    metric_name = fake.word()
    error_message = fake.sentence()

    @profile(category=category, name=metric_name)
    def test_function() -> None:
        raise ValueError(error_message)

    try:
        test_function()
        pytest.fail("Expected ValueError to be raised")
    except ValueError as e:
        assert str(e) == error_message

    stats = monitor.get_timing_stats(category=category, name=metric_name)
    assert stats is not None
    assert stats.count == 1


def test_profile_decorator_disabled_has_zero_overhead() -> None:
    """Test profile decorator with enabled=False does not record."""
    reset_performance_monitor()
    monitor = get_performance_monitor()

    category = fake.word()
    metric_name = fake.word()

    @profile(category=category, name=metric_name, enabled=False)
    def test_function() -> None:
        time.sleep(0.001)

    test_function()

    stats = monitor.get_timing_stats(category=category, name=metric_name)
    assert stats is None


def test_profile_decorator_preserves_function_metadata() -> None:
    """Test profile decorator preserves function name and docstring."""
    category = fake.word()

    @profile(category=category)
    def test_function_with_docs() -> None:
        """Test docstring."""
        pass

    assert test_function_with_docs.__name__ == "test_function_with_docs"
    assert test_function_with_docs.__doc__ == "Test docstring."


def test_profile_async_decorator_records_timing() -> None:
    """Test profile_async decorator records async function timing."""
    reset_performance_monitor()
    monitor = get_performance_monitor()

    category = fake.word()
    metric_name = fake.word()

    @profile_async(category=category, name=metric_name)
    async def test_function() -> str:
        await asyncio.sleep(0.01)
        return fake.word()

    result = asyncio.run(test_function())

    assert isinstance(result, str)
    stats = monitor.get_timing_stats(category=category, name=metric_name)
    assert stats is not None
    assert stats.count == 1
    assert stats.avg_time > 0.0


def test_profile_async_decorator_uses_function_name_by_default() -> None:
    """Test profile_async decorator uses function name when name not provided."""
    reset_performance_monitor()
    monitor = get_performance_monitor()

    category = fake.word()

    @profile_async(category=category)
    async def my_async_function() -> None:
        pass

    asyncio.run(my_async_function())

    stats = monitor.get_timing_stats(category=category, name="my_async_function")
    assert stats is not None
    assert stats.count == 1


def test_profile_async_decorator_multiple_calls() -> None:
    """Test profile_async decorator records multiple async calls."""
    reset_performance_monitor()
    monitor = get_performance_monitor()

    category = fake.word()
    metric_name = fake.word()

    @profile_async(category=category, name=metric_name)
    async def test_function() -> None:
        await asyncio.sleep(0.001)

    async def run_multiple() -> None:
        await test_function()
        await test_function()
        await test_function()

    asyncio.run(run_multiple())

    stats = monitor.get_timing_stats(category=category, name=metric_name)
    assert stats is not None
    assert stats.count == 3


def test_profile_async_decorator_preserves_return_value() -> None:
    """Test profile_async decorator preserves return value."""
    reset_performance_monitor()

    category = fake.word()
    expected_value = fake.random_int()

    @profile_async(category=category)
    async def test_function() -> int:
        return expected_value

    result = asyncio.run(test_function())

    assert result == expected_value


def test_profile_async_decorator_preserves_exceptions() -> None:
    """Test profile_async decorator preserves exceptions."""
    reset_performance_monitor()
    monitor = get_performance_monitor()

    category = fake.word()
    metric_name = fake.word()
    error_message = fake.sentence()

    @profile_async(category=category, name=metric_name)
    async def test_function() -> None:
        raise ValueError(error_message)

    try:
        asyncio.run(test_function())
        pytest.fail("Expected ValueError to be raised")
    except ValueError as e:
        assert str(e) == error_message

    stats = monitor.get_timing_stats(category=category, name=metric_name)
    assert stats is not None
    assert stats.count == 1


def test_profile_async_decorator_disabled_has_zero_overhead() -> None:
    """Test profile_async decorator with enabled=False does not record."""
    reset_performance_monitor()
    monitor = get_performance_monitor()

    category = fake.word()
    metric_name = fake.word()

    @profile_async(category=category, name=metric_name, enabled=False)
    async def test_function() -> None:
        await asyncio.sleep(0.001)

    asyncio.run(test_function())

    stats = monitor.get_timing_stats(category=category, name=metric_name)
    assert stats is None


def test_profile_async_decorator_preserves_function_metadata() -> None:
    """Test profile_async decorator preserves function metadata."""
    category = fake.word()

    @profile_async(category=category)
    async def async_function_with_docs() -> None:
        """Async docstring."""
        pass

    assert async_function_with_docs.__name__ == "async_function_with_docs"
    assert async_function_with_docs.__doc__ == "Async docstring."
