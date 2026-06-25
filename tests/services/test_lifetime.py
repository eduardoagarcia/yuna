"""Tests for service lifetime enumerations."""

from yuna.services.lifetime import ServiceLifetime


def test_service_lifetime_singleton_value() -> None:
    """Test SINGLETON lifetime has correct value."""
    assert ServiceLifetime.SINGLETON.value == "singleton"


def test_service_lifetime_per_world_value() -> None:
    """Test PER_WORLD lifetime has correct value."""
    assert ServiceLifetime.PER_WORLD.value == "per_world"


def test_service_lifetime_transient_value() -> None:
    """Test TRANSIENT lifetime has correct value."""
    assert ServiceLifetime.TRANSIENT.value == "transient"


def test_service_lifetime_members() -> None:
    """Test all service lifetime members exist."""
    assert hasattr(ServiceLifetime, "SINGLETON")
    assert hasattr(ServiceLifetime, "PER_WORLD")
    assert hasattr(ServiceLifetime, "TRANSIENT")


def test_service_lifetime_equality() -> None:
    """Test service lifetime equality comparison."""
    assert ServiceLifetime.SINGLETON == ServiceLifetime.SINGLETON
    assert ServiceLifetime.SINGLETON != ServiceLifetime.TRANSIENT  # type: ignore[comparison-overlap]
    assert ServiceLifetime.PER_WORLD != ServiceLifetime.SINGLETON  # type: ignore[comparison-overlap]


def test_service_lifetime_count() -> None:
    """Test correct number of service lifetime options."""
    assert len(ServiceLifetime) == 3
