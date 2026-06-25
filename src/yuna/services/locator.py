"""Service locator for dependency injection and service resolution."""

from __future__ import annotations

from typing import Any, TypeVar, cast

from yuna.exceptions import ServiceNotFoundError
from yuna.services.lifetime import ServiceLifetime
from yuna.services.provider import ServiceFactory

T = TypeVar("T")


class ServiceLocator:
    """Central registry for dependency injection.

    Responsibilities:
    - Register services with their lifetime scope
    - Resolve service instances by interface type
    - Manage singleton instances
    - Support testing through clear mechanism

    Usage:
        locator = ServiceLocator()
        locator.register(
            interface=LoggerInterface,
            factory=lambda: ConcreteLogger(),
            lifetime=ServiceLifetime.SINGLETON
        )
        logger = locator.resolve(interface=LoggerInterface)
    """

    def __init__(self) -> None:
        self._registrations: dict[
            type[Any], tuple[ServiceFactory[Any], ServiceLifetime]
        ] = {}
        self._singletons: dict[type[Any], Any] = {}
        self._per_world_instances: dict[str, dict[type[Any], Any]] = {}

    def register(
        self,
        interface: type[T],
        factory: ServiceFactory[T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> None:
        """Register a service with its factory and lifetime.

        Args:
            interface: Interface or base class type
            factory: Factory function that creates service instances
            lifetime: Lifetime scope for the service
        """
        if interface in self._singletons:
            del self._singletons[interface]
        for world_instances in self._per_world_instances.values():
            if interface in world_instances:
                del world_instances[interface]
        self._registrations[interface] = (factory, lifetime)

    def resolve(self, interface: type[T], world_id: str | None = None) -> T:
        """Resolve a service instance by its interface type.

        Args:
            interface: Interface or base class type to resolve
            world_id: World identifier for PER_WORLD lifetime (optional)

        Returns:
            Service instance of the requested type

        Raises:
            ServiceNotFoundError: If service is not registered
        """
        if interface not in self._registrations:
            raise ServiceNotFoundError(
                f"Service {interface.__name__} is not registered"
            )

        factory, lifetime = self._registrations[interface]

        if lifetime == ServiceLifetime.SINGLETON:
            if interface not in self._singletons:
                self._singletons[interface] = factory()
            return cast(T, self._singletons[interface])

        elif lifetime == ServiceLifetime.PER_WORLD:
            if world_id is None:
                raise ValueError(
                    f"world_id required for PER_WORLD service {interface.__name__}"
                )
            if world_id not in self._per_world_instances:
                self._per_world_instances[world_id] = {}
            if interface not in self._per_world_instances[world_id]:
                self._per_world_instances[world_id][interface] = factory()
            return cast(T, self._per_world_instances[world_id][interface])

        else:
            return cast(T, factory())

    def clear(self) -> None:
        """Clear all registrations and cached instances.

        Used primarily for testing to ensure clean state between tests.
        """
        self._registrations.clear()
        self._singletons.clear()
        self._per_world_instances.clear()

    def has(self, interface: type[Any]) -> bool:
        """Check if a service is registered.

        Args:
            interface: Interface or base class type to check

        Returns:
            True if service is registered, False otherwise
        """
        return interface in self._registrations
