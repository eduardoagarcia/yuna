"""Tests for service provider protocol."""

from dataclasses import dataclass

from faker import Faker

from yuna.services.provider import ServiceFactory, ServiceProvider

fake = Faker()


@dataclass
class DummyService:
    """Test service for provider testing."""

    value: str


def test_service_factory_type_alias() -> None:
    """Test ServiceFactory type alias can be used."""
    value = fake.word()

    def factory() -> DummyService:
        return DummyService(value=value)

    typed_factory: ServiceFactory[DummyService] = factory
    service = typed_factory()
    assert isinstance(service, DummyService)
    assert service.value == value


def test_service_provider_protocol_with_inline_factory() -> None:
    """Test ServiceProvider protocol works with inline factory function."""
    value = fake.word()

    def provider() -> DummyService:
        return DummyService(value=value)

    typed_provider: ServiceProvider = provider
    service = typed_provider()
    assert isinstance(service, DummyService)
    assert service.value == value


def test_service_provider_protocol_with_function() -> None:
    """Test ServiceProvider protocol works with function."""
    value = fake.word()

    def create_service() -> DummyService:
        return DummyService(value=value)

    provider: ServiceProvider = create_service
    service = provider()
    assert isinstance(service, DummyService)
    assert service.value == value


def test_service_provider_protocol_with_callable_class() -> None:
    """Test ServiceProvider protocol works with callable class."""

    class ServiceFactory:
        def __init__(self, value: str) -> None:
            self.value = value

        def __call__(self) -> DummyService:
            return DummyService(value=self.value)

    value = fake.word()
    provider: ServiceProvider = ServiceFactory(value=value)
    service = provider()
    assert isinstance(service, DummyService)
    assert service.value == value
