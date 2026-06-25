"""Profiling decorators for performance monitoring."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from yuna.profiling.monitor import get_performance_monitor

F = TypeVar("F", bound=Callable[..., Any])


def profile(
    category: str,
    name: str | None = None,
    enabled: bool = True,
) -> Callable[[F], F]:
    """Decorator for profiling synchronous function calls.

    Args:
        category: Metric category for organization
        name: Custom metric name (defaults to function name)
        enabled: Whether profiling is active (zero overhead when False)

    Returns:
        Decorated function that records timing metrics

    Usage:
        @profile(category="systems", name="physics_update")
        def update_physics():
            pass
    """
    if not enabled:
        return lambda func: func

    def decorator(func: F) -> F:
        metric_name = name or func.__name__
        monitor = get_performance_monitor()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with monitor.sample(category=category, name=metric_name):
                return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def profile_async(
    category: str,
    name: str | None = None,
    enabled: bool = True,
) -> Callable[[F], F]:
    """Decorator for profiling async function calls.

    Args:
        category: Metric category for organization
        name: Custom metric name (defaults to function name)
        enabled: Whether profiling is active (zero overhead when False)

    Returns:
        Decorated async function that records timing metrics

    Usage:
        @profile_async(category="systems", name="async_query")
        async def query_entities():
            pass
    """
    if not enabled:
        return lambda func: func

    def decorator(func: F) -> F:
        metric_name = name or func.__name__
        monitor = get_performance_monitor()

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            with monitor.sample(category=category, name=metric_name):
                return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
