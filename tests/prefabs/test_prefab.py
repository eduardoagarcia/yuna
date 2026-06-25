"""Tests for Prefab dataclass."""

import pytest
from faker import Faker

from yuna.exceptions import ValidationError
from yuna.prefabs.prefab import Prefab

fake = Faker()


def test_prefab_initialization() -> None:
    """Test Prefab initialization with all fields."""
    name = fake.word()
    components = {"Position": {"x": 0.0, "y": 0.0}}
    behaviors = ["PlayerController"]
    children = ["child1"]
    metadata = {"tags": ["player"]}

    prefab = Prefab(
        name=name,
        components=components,
        behaviors=behaviors,
        children=children,
        metadata=metadata,
    )

    assert prefab.name == name
    assert prefab.components == components
    assert prefab.behaviors == behaviors
    assert prefab.children == children
    assert prefab.metadata == metadata


def test_prefab_initialization_minimal() -> None:
    """Test Prefab initialization with minimal fields."""
    name = fake.word()

    prefab = Prefab(name=name)

    assert prefab.name == name
    assert prefab.components == {}
    assert prefab.behaviors == []
    assert prefab.children == []
    assert prefab.metadata == {}


def test_prefab_empty_name_raises_error() -> None:
    """Test Prefab raises error with empty name."""
    with pytest.raises(ValidationError, match="name cannot be empty"):
        Prefab(name="")


def test_prefab_with_multiple_components() -> None:
    """Test Prefab with multiple components."""
    prefab = Prefab(
        name=fake.word(),
        components={
            "Position": {"x": 10.0, "y": 20.0},
            "Health": {"max_hp": 100.0, "current_hp": 100.0},
            "Sprite": {"texture": "player.png"},
        },
    )

    assert len(prefab.components) == 3
    assert "Position" in prefab.components
    assert "Health" in prefab.components
    assert "Sprite" in prefab.components


def test_prefab_with_multiple_behaviors() -> None:
    """Test Prefab with multiple behaviors."""
    behaviors = ["PlayerController", "CameraFollow", "InputHandler"]
    prefab = Prefab(name=fake.word(), behaviors=behaviors)

    assert prefab.behaviors == behaviors
    assert len(prefab.behaviors) == 3


def test_prefab_with_children() -> None:
    """Test Prefab with child prefabs."""
    children = ["weapon", "shield", "armor"]
    prefab = Prefab(name=fake.word(), children=children)

    assert prefab.children == children
    assert len(prefab.children) == 3


def test_prefab_with_metadata() -> None:
    """Test Prefab with custom metadata."""
    metadata = {
        "tags": ["player", "controllable"],
        "layer": 1,
        "description": "Main player character",
    }
    prefab = Prefab(name=fake.word(), metadata=metadata)

    assert prefab.metadata == metadata
    assert "tags" in prefab.metadata
    assert "layer" in prefab.metadata


def test_prefab_components_mutable() -> None:
    """Test Prefab components dict is mutable."""
    prefab = Prefab(name=fake.word())

    prefab.components["Position"] = {"x": 0.0, "y": 0.0}
    assert "Position" in prefab.components


def test_prefab_behaviors_mutable() -> None:
    """Test Prefab behaviors list is mutable."""
    prefab = Prefab(name=fake.word())

    prefab.behaviors.append("NewBehavior")
    assert "NewBehavior" in prefab.behaviors


def test_prefab_children_mutable() -> None:
    """Test Prefab children list is mutable."""
    prefab = Prefab(name=fake.word())

    prefab.children.append("child_prefab")
    assert "child_prefab" in prefab.children


def test_prefab_metadata_mutable() -> None:
    """Test Prefab metadata dict is mutable."""
    prefab = Prefab(name=fake.word())

    prefab.metadata["custom_key"] = "custom_value"
    assert prefab.metadata["custom_key"] == "custom_value"
