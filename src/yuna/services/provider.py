"""Service provider protocol for dependency injection."""

from collections.abc import Callable
from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class ServiceProvider(Protocol):
    """Protocol for service factory functions.

    Responsibilities:
    - Define interface for creating service instances
    - Support type-safe service creation

    Usage:
        def create_logger() -> Logger:
            return Logger()

        provider: ServiceProvider = create_logger
    """

    def __call__(self) -> Any:
        """Create and return service instance.

        Returns:
            Service instance of any type
        """
        ...  # pragma: no cover


ServiceFactory = Callable[[], T]
