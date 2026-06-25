"""Deprecation utilities for API stability and migration support."""

import functools
import warnings
from collections.abc import Callable
from enum import Enum, auto
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class DeprecationLevel(Enum):
    """Level of deprecation severity."""

    WARNING = auto()
    ERROR = auto()
    REMOVED = auto()


class DeprecationConfig:
    """Configuration for deprecation behavior."""

    def __init__(self) -> None:
        self.enabled: bool = True
        self.warnings_as_errors: bool = False
        self._warned: set[str] = set()

    def should_warn(self, identifier: str) -> bool:
        """Check if warning should be emitted for identifier.

        Args:
            identifier: Unique identifier for deprecated API

        Returns:
            True if warning should be emitted
        """
        if not self.enabled:
            return False
        if identifier in self._warned:
            return False
        self._warned.add(identifier)
        return True

    def reset(self) -> None:
        """Reset warning tracking (useful for tests)."""
        self._warned.clear()


_config = DeprecationConfig()


def get_deprecation_config() -> DeprecationConfig:
    """Get global deprecation configuration.

    Returns:
        Global deprecation configuration instance
    """
    return _config


def deprecation_warning(
    message: str,
    deprecated_in: str,
    removed_in: str | None = None,
    migration_guide: str | None = None,
    level: DeprecationLevel = DeprecationLevel.WARNING,
) -> None:
    """Emit deprecation warning.

    Args:
        message: Deprecation message
        deprecated_in: Version when deprecated
        removed_in: Version when will be removed (optional)
        migration_guide: Migration instructions (optional)
        level: Deprecation severity level

    Raises:
        DeprecationError: If level is ERROR or REMOVED
    """
    full_message = f"{message} (deprecated in {deprecated_in}"
    if removed_in:
        full_message += f", will be removed in {removed_in}"
    full_message += ")"

    if migration_guide:
        full_message += f"\nMigration: {migration_guide}"

    if level == DeprecationLevel.REMOVED:
        raise DeprecationError(full_message)

    if level == DeprecationLevel.ERROR or _config.warnings_as_errors:
        raise DeprecationError(full_message)

    warnings.warn(message=full_message, category=DeprecationWarning, stacklevel=3)


def deprecated(
    deprecated_in: str,
    removed_in: str | None = None,
    reason: str | None = None,
    migration_guide: str | None = None,
    level: DeprecationLevel = DeprecationLevel.WARNING,
) -> Callable[[F], F]:
    """Decorator to mark functions/methods as deprecated.

    Args:
        deprecated_in: Version when deprecated
        removed_in: Version when will be removed (optional)
        reason: Reason for deprecation (optional)
        migration_guide: Migration instructions (optional)
        level: Deprecation severity level

    Returns:
        Decorator function

    Usage:
        @deprecated(
            deprecated_in="3.1.0",
            removed_in="4.0.0",
            reason="Use new_function() instead",
            migration_guide="Replace old_function(x) with new_function(x)",
        )
        def old_function(x: int) -> int:
            return x * 2
    """

    def decorator(func: F) -> F:
        identifier = f"{func.__module__}.{func.__qualname__}"
        message = f"{func.__qualname__}() is deprecated"
        if reason:
            message += f": {reason}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if _config.should_warn(identifier=identifier):
                deprecation_warning(
                    message=message,
                    deprecated_in=deprecated_in,
                    removed_in=removed_in,
                    migration_guide=migration_guide,
                    level=level,
                )
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


class DeprecationError(Exception):
    """Raised when deprecated API is used with ERROR or REMOVED level."""

    pass
