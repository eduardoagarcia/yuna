"""Tests for service locator dependency injection."""

import pytest
from faker import Faker

from yuna.services.lifetime import ServiceLifetime
from yuna.services.locator import (
    ServiceLocator,
    ServiceNotFoundError,
)

fake = Faker()


class DummyService:
    """Test service for dependency injection testing."""

    def __init__(self, value: str | None = None) -> None:
        self.value = value or fake.word()


class AnotherService:
    """Another test service for testing multiple registrations."""

    def __init__(self) -> None:
        self.id = fake.uuid4()


def test_service_locator_creation() -> None:
    """Test ServiceLocator can be instantiated."""
    locator = ServiceLocator()
    assert locator is not None


def test_register_and_resolve_service() -> None:
    """Test registering and resolving a service."""
    locator = ServiceLocator()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.TRANSIENT,
    )
    service = locator.resolve(interface=DummyService)
    assert isinstance(service, DummyService)


def test_singleton_lifetime_returns_same_instance() -> None:
    """Test SINGLETON lifetime returns the same instance on every resolve."""
    locator = ServiceLocator()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.SINGLETON,
    )
    instance1 = locator.resolve(interface=DummyService)
    instance2 = locator.resolve(interface=DummyService)
    assert instance1 is instance2


def test_transient_lifetime_returns_new_instance() -> None:
    """Test TRANSIENT lifetime returns new instance on every resolve."""
    locator = ServiceLocator()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.TRANSIENT,
    )
    instance1 = locator.resolve(interface=DummyService)
    instance2 = locator.resolve(interface=DummyService)
    assert instance1 is not instance2


def test_per_world_lifetime_returns_same_instance_per_world() -> None:
    """Test PER_WORLD lifetime returns same instance for same world."""
    locator = ServiceLocator()
    world_id = fake.uuid4()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.PER_WORLD,
    )
    instance1 = locator.resolve(interface=DummyService, world_id=world_id)
    instance2 = locator.resolve(interface=DummyService, world_id=world_id)
    assert instance1 is instance2


def test_per_world_lifetime_returns_different_instance_per_world() -> None:
    """Test PER_WORLD lifetime returns different instance for different worlds."""
    locator = ServiceLocator()
    world_id_1 = fake.uuid4()
    world_id_2 = fake.uuid4()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.PER_WORLD,
    )
    instance1 = locator.resolve(interface=DummyService, world_id=world_id_1)
    instance2 = locator.resolve(interface=DummyService, world_id=world_id_2)
    assert instance1 is not instance2


def test_per_world_lifetime_requires_world_id() -> None:
    """Test PER_WORLD lifetime raises error without world_id."""
    locator = ServiceLocator()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.PER_WORLD,
    )
    with pytest.raises(ValueError, match="world_id required for PER_WORLD service"):
        locator.resolve(interface=DummyService)


def test_resolve_unregistered_service_raises_error() -> None:
    """Test resolving unregistered service raises ServiceNotFoundError."""
    locator = ServiceLocator()
    with pytest.raises(
        ServiceNotFoundError, match="Service DummyService is not registered"
    ):
        locator.resolve(interface=DummyService)


def test_clear_removes_all_registrations() -> None:
    """Test clear removes all service registrations."""
    locator = ServiceLocator()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.SINGLETON,
    )
    locator.clear()
    with pytest.raises(ServiceNotFoundError):
        locator.resolve(interface=DummyService)


def test_clear_removes_singleton_instances() -> None:
    """Test clear removes cached singleton instances."""
    locator = ServiceLocator()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.SINGLETON,
    )
    instance1 = locator.resolve(interface=DummyService)
    locator.clear()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.SINGLETON,
    )
    instance2 = locator.resolve(interface=DummyService)
    assert instance1 is not instance2


def test_clear_removes_per_world_instances() -> None:
    """Test clear removes cached per-world instances."""
    locator = ServiceLocator()
    world_id = fake.uuid4()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.PER_WORLD,
    )
    instance1 = locator.resolve(interface=DummyService, world_id=world_id)
    locator.clear()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.PER_WORLD,
    )
    instance2 = locator.resolve(interface=DummyService, world_id=world_id)
    assert instance1 is not instance2


def test_has_returns_true_for_registered_service() -> None:
    """Test has returns True for registered service."""
    locator = ServiceLocator()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.TRANSIENT,
    )
    assert locator.has(interface=DummyService) is True


def test_has_returns_false_for_unregistered_service() -> None:
    """Test has returns False for unregistered service."""
    locator = ServiceLocator()
    assert locator.has(interface=DummyService) is False


def test_multiple_service_registrations() -> None:
    """Test registering and resolving multiple different services."""
    locator = ServiceLocator()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(),
        lifetime=ServiceLifetime.SINGLETON,
    )
    locator.register(
        interface=AnotherService,
        factory=lambda: AnotherService(),
        lifetime=ServiceLifetime.TRANSIENT,
    )
    service1 = locator.resolve(interface=DummyService)
    service2 = locator.resolve(interface=AnotherService)
    assert isinstance(service1, DummyService)
    assert isinstance(service2, AnotherService)


def test_register_overwrites_existing_registration() -> None:
    """Test registering same interface twice overwrites first registration."""
    locator = ServiceLocator()
    value1 = fake.word()
    value2 = fake.word()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(value=value1),
        lifetime=ServiceLifetime.SINGLETON,
    )
    instance1 = locator.resolve(interface=DummyService)
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(value=value2),
        lifetime=ServiceLifetime.SINGLETON,
    )
    instance2 = locator.resolve(interface=DummyService)
    assert instance1.value == value1
    assert instance2.value == value2
    assert instance1 is not instance2


def test_default_lifetime_is_transient() -> None:
    """Test default lifetime is TRANSIENT when not specified."""
    locator = ServiceLocator()
    locator.register(interface=DummyService, factory=lambda: DummyService())
    instance1 = locator.resolve(interface=DummyService)
    instance2 = locator.resolve(interface=DummyService)
    assert instance1 is not instance2


def test_factory_is_called_on_transient_resolve() -> None:
    """Test factory function is called each time for TRANSIENT lifetime."""
    locator = ServiceLocator()
    call_count = 0

    def factory() -> DummyService:
        nonlocal call_count
        call_count += 1
        return DummyService()

    locator.register(
        interface=DummyService, factory=factory, lifetime=ServiceLifetime.TRANSIENT
    )
    locator.resolve(interface=DummyService)
    locator.resolve(interface=DummyService)
    locator.resolve(interface=DummyService)
    assert call_count == 3


def test_factory_is_called_once_on_singleton_resolve() -> None:
    """Test factory function is called only once for SINGLETON lifetime."""
    locator = ServiceLocator()
    call_count = 0

    def factory() -> DummyService:
        nonlocal call_count
        call_count += 1
        return DummyService()

    locator.register(
        interface=DummyService, factory=factory, lifetime=ServiceLifetime.SINGLETON
    )
    locator.resolve(interface=DummyService)
    locator.resolve(interface=DummyService)
    locator.resolve(interface=DummyService)
    assert call_count == 1


def test_factory_is_called_once_per_world_on_per_world_resolve() -> None:
    """Test factory is called once per world for PER_WORLD lifetime."""
    locator = ServiceLocator()
    call_count = 0
    world_id_1 = fake.uuid4()
    world_id_2 = fake.uuid4()

    def factory() -> DummyService:
        nonlocal call_count
        call_count += 1
        return DummyService()

    locator.register(
        interface=DummyService, factory=factory, lifetime=ServiceLifetime.PER_WORLD
    )
    locator.resolve(interface=DummyService, world_id=world_id_1)
    locator.resolve(interface=DummyService, world_id=world_id_1)
    locator.resolve(interface=DummyService, world_id=world_id_2)
    locator.resolve(interface=DummyService, world_id=world_id_2)
    assert call_count == 2


def test_register_per_world_clears_cached_instances() -> None:
    """Test re-registering PER_WORLD service clears cached instances."""
    locator = ServiceLocator()
    world_id = fake.uuid4()
    value1 = fake.word()
    value2 = fake.word()
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(value=value1),
        lifetime=ServiceLifetime.PER_WORLD,
    )
    instance1 = locator.resolve(interface=DummyService, world_id=world_id)
    locator.register(
        interface=DummyService,
        factory=lambda: DummyService(value=value2),
        lifetime=ServiceLifetime.PER_WORLD,
    )
    instance2 = locator.resolve(interface=DummyService, world_id=world_id)
    assert instance1.value == value1
    assert instance2.value == value2
    assert instance1 is not instance2
