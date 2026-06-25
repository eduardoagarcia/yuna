"""Tests for type-safe identifiers."""

from faker import Faker

from yuna.types.identifiers import (
    ComponentID,
    EntityID,
    SystemID,
)

fake = Faker()


def test_entity_id_creation() -> None:
    """Test EntityID can be created from string."""
    entity_id = EntityID(fake.uuid4())
    assert isinstance(entity_id, str)


def test_component_id_creation() -> None:
    """Test ComponentID can be created from string."""
    component_id = ComponentID(fake.uuid4())
    assert isinstance(component_id, str)


def test_system_id_creation() -> None:
    """Test SystemID can be created from string."""
    system_id = SystemID(fake.uuid4())
    assert isinstance(system_id, str)


def test_entity_id_equality() -> None:
    """Test EntityID equality comparison."""
    id_value = fake.uuid4()
    entity_id_1 = EntityID(id_value)
    entity_id_2 = EntityID(id_value)
    assert entity_id_1 == entity_id_2


def test_component_id_equality() -> None:
    """Test ComponentID equality comparison."""
    id_value = fake.uuid4()
    component_id_1 = ComponentID(id_value)
    component_id_2 = ComponentID(id_value)
    assert component_id_1 == component_id_2


def test_system_id_equality() -> None:
    """Test SystemID equality comparison."""
    id_value = fake.uuid4()
    system_id_1 = SystemID(id_value)
    system_id_2 = SystemID(id_value)
    assert system_id_1 == system_id_2


def test_different_entity_ids_not_equal() -> None:
    """Test different EntityID values are not equal."""
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    assert entity_id_1 != entity_id_2


def test_different_component_ids_not_equal() -> None:
    """Test different ComponentID values are not equal."""
    component_id_1 = ComponentID(fake.uuid4())
    component_id_2 = ComponentID(fake.uuid4())
    assert component_id_1 != component_id_2


def test_different_system_ids_not_equal() -> None:
    """Test different SystemID values are not equal."""
    system_id_1 = SystemID(fake.uuid4())
    system_id_2 = SystemID(fake.uuid4())
    assert system_id_1 != system_id_2


def test_entity_id_with_empty_string() -> None:
    """Test EntityID can be created with empty string."""
    entity_id = EntityID("")
    assert entity_id == ""


def test_component_id_with_empty_string() -> None:
    """Test ComponentID can be created with empty string."""
    component_id = ComponentID("")
    assert component_id == ""


def test_system_id_with_empty_string() -> None:
    """Test SystemID can be created with empty string."""
    system_id = SystemID("")
    assert system_id == ""
