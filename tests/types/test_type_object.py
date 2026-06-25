"""Tests for EntityType dataclass."""

import pytest
from faker import Faker

from yuna.exceptions import ValidationError
from yuna.types.type_object import EntityType

fake = Faker()


def test_entity_type_creation() -> None:
    entity_type = EntityType(name=fake.word())

    assert entity_type is not None


def test_entity_type_with_name() -> None:
    name = fake.word()

    entity_type = EntityType(name=name)

    assert entity_type.name == name


def test_entity_type_with_components() -> None:
    components = {"Position": {"x": 0.0, "y": 0.0}, "Health": {"current": 100}}

    entity_type = EntityType(name=fake.word(), components=components)

    assert entity_type.components == components


def test_entity_type_with_behaviors() -> None:
    behaviors = ["movement", "combat", "inventory"]

    entity_type = EntityType(name=fake.word(), behaviors=behaviors)

    assert entity_type.behaviors == behaviors


def test_entity_type_components_default_to_empty_dict() -> None:
    entity_type = EntityType(name=fake.word())

    assert entity_type.components == {}


def test_entity_type_behaviors_default_to_empty_list() -> None:
    entity_type = EntityType(name=fake.word())

    assert entity_type.behaviors == []


def test_entity_type_with_empty_name_raises_error() -> None:
    with pytest.raises(ValidationError, match="name cannot be empty"):
        EntityType(name="")


def test_entity_type_components_must_be_dict() -> None:
    with pytest.raises(ValidationError, match="components must be a dictionary"):
        EntityType(name=fake.word(), components="invalid")  # type: ignore[arg-type]


def test_entity_type_behaviors_must_be_list() -> None:
    with pytest.raises(ValidationError, match="behaviors must be a list"):
        EntityType(name=fake.word(), behaviors="invalid")  # type: ignore[arg-type]


def test_entity_type_with_nested_component_data() -> None:
    components = {
        "Inventory": {
            "items": [{"id": 1, "name": "sword"}, {"id": 2, "name": "shield"}],
            "capacity": 20,
        }
    }

    entity_type = EntityType(name=fake.word(), components=components)

    assert entity_type.components == components


def test_entity_type_with_multiple_behaviors() -> None:
    behaviors = [fake.word() for _ in range(5)]

    entity_type = EntityType(name=fake.word(), behaviors=behaviors)

    assert len(entity_type.behaviors) == 5
    assert entity_type.behaviors == behaviors


def test_entity_type_immutability_with_dataclass() -> None:
    entity_type = EntityType(
        name=fake.word(),
        components={"Position": {"x": 0.0, "y": 0.0}},
        behaviors=["movement"],
    )

    assert entity_type.name is not None
    assert entity_type.components is not None
    assert entity_type.behaviors is not None
