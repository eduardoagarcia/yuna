"""Tests for PrefabManager."""

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml
from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.world import ECSWorld
from yuna.exceptions import StateError, ValidationError
from yuna.prefabs.manager import PrefabManager
from yuna.prefabs.prefab import Prefab

fake = Faker()


@dataclass
class Position(Component):
    """Test position component."""

    x: float
    y: float


@dataclass
class Health(Component):
    """Test health component."""

    max_hp: float
    current_hp: float


@dataclass
class Sprite(Component):
    """Test sprite component."""

    texture: str


def test_manager_initialization() -> None:
    """Test PrefabManager initialization."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    assert manager.prefab_count == 0
    assert manager.component_type_count == 0


def test_register_component_type() -> None:
    """Test registering component types."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    manager.register_component_type(name="Position", component_class=Position)

    assert manager.component_type_count == 1


def test_register_component_type_duplicate_same_class() -> None:
    """Test registering same component type twice with same class."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    manager.register_component_type(name="Position", component_class=Position)
    manager.register_component_type(name="Position", component_class=Position)

    assert manager.component_type_count == 1


def test_register_component_type_duplicate_different_class() -> None:
    """Test registering same component type with different class raises error."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    manager.register_component_type(name="Position", component_class=Position)

    with pytest.raises(StateError, match="already registered"):
        manager.register_component_type(name="Position", component_class=Health)


def test_register_prefab() -> None:
    """Test registering prefab."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    prefab = Prefab(name="player")
    manager.register_prefab(prefab=prefab)

    assert manager.prefab_count == 1
    assert manager.has_prefab(name="player")


def test_register_prefab_duplicate_raises_error() -> None:
    """Test registering duplicate prefab raises error."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    prefab = Prefab(name="player")
    manager.register_prefab(prefab=prefab)

    with pytest.raises(StateError, match="already registered"):
        manager.register_prefab(prefab=prefab)


def test_instantiate_simple_prefab() -> None:
    """Test instantiating entity from prefab."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    manager.register_component_type(name="Position", component_class=Position)

    prefab = Prefab(
        name="player",
        components={"Position": {"x": 10.0, "y": 20.0}},
    )
    manager.register_prefab(prefab=prefab)

    entity_id = manager.instantiate(prefab_name="player")

    assert entity_id is not None
    position_component = world.get_component(
        entity_id=entity_id, component_type=Position
    )
    assert position_component is not None
    assert isinstance(position_component, Position)
    assert position_component.x == 10.0
    assert position_component.y == 20.0


def test_instantiate_with_multiple_components() -> None:
    """Test instantiating entity with multiple components."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    manager.register_component_type(name="Position", component_class=Position)
    manager.register_component_type(name="Health", component_class=Health)

    prefab = Prefab(
        name="player",
        components={
            "Position": {"x": 0.0, "y": 0.0},
            "Health": {"max_hp": 100.0, "current_hp": 100.0},
        },
    )
    manager.register_prefab(prefab=prefab)

    entity_id = manager.instantiate(prefab_name="player")

    position_component = world.get_component(
        entity_id=entity_id, component_type=Position
    )
    health_component = world.get_component(entity_id=entity_id, component_type=Health)

    assert position_component is not None
    assert isinstance(position_component, Position)
    assert health_component is not None
    assert isinstance(health_component, Health)
    assert position_component.x == 0.0
    assert health_component.max_hp == 100.0


def test_instantiate_with_overrides() -> None:
    """Test instantiating with property overrides."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    manager.register_component_type(name="Position", component_class=Position)

    prefab = Prefab(
        name="player",
        components={"Position": {"x": 0.0, "y": 0.0}},
    )
    manager.register_prefab(prefab=prefab)

    entity_id = manager.instantiate(
        prefab_name="player",
        overrides={"Position": {"x": 100.0}},
    )

    position_component = world.get_component(
        entity_id=entity_id, component_type=Position
    )
    assert position_component is not None
    assert isinstance(position_component, Position)
    assert position_component.x == 100.0
    assert position_component.y == 0.0


def test_instantiate_not_found_raises_error() -> None:
    """Test instantiating unknown prefab raises error."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    with pytest.raises(ValidationError, match="not found"):
        manager.instantiate(prefab_name="nonexistent")


def test_instantiate_unregistered_component_type_raises_error() -> None:
    """Test instantiating with unregistered component type raises error."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    prefab = Prefab(
        name="player",
        components={"Position": {"x": 0.0, "y": 0.0}},
    )
    manager.register_prefab(prefab=prefab)

    with pytest.raises(ValidationError, match="not registered"):
        manager.instantiate(prefab_name="player")


def test_instantiate_hierarchy_simple() -> None:
    """Test instantiating hierarchy with children."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    manager.register_component_type(name="Position", component_class=Position)

    child_prefab = Prefab(
        name="weapon",
        components={"Position": {"x": 1.0, "y": 0.0}},
    )
    parent_prefab = Prefab(
        name="player",
        components={"Position": {"x": 0.0, "y": 0.0}},
        children=["weapon"],
    )

    manager.register_prefab(prefab=child_prefab)
    manager.register_prefab(prefab=parent_prefab)

    root_id = manager.instantiate_hierarchy(prefab_name="player")

    assert root_id is not None


def test_instantiate_hierarchy_not_found_raises_error() -> None:
    """Test instantiating hierarchy with unknown prefab raises error."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    with pytest.raises(ValidationError, match="not found"):
        manager.instantiate_hierarchy(prefab_name="nonexistent")


def test_load_from_dict() -> None:
    """Test loading prefabs from dictionary."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    data = {
        "prefabs": [
            {
                "name": "player",
                "components": {"Position": {"x": 0.0, "y": 0.0}},
                "behaviors": ["PlayerController"],
                "children": [],
                "metadata": {"tags": ["player"]},
            },
            {
                "name": "enemy",
                "components": {"Position": {"x": 10.0, "y": 10.0}},
            },
        ]
    }

    loaded = manager.load_from_dict(data=data)

    assert len(loaded) == 2
    assert "player" in loaded
    assert "enemy" in loaded
    assert manager.has_prefab(name="player")
    assert manager.has_prefab(name="enemy")


def test_load_from_json_file() -> None:
    """Test loading prefabs from JSON file."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    data = {
        "prefabs": [
            {
                "name": "player",
                "components": {"Position": {"x": 0.0, "y": 0.0}},
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    try:
        loaded = manager.load_from_file(path=temp_path)
        assert len(loaded) == 1
        assert manager.has_prefab(name="player")
    finally:
        Path(temp_path).unlink()


def test_load_from_yaml_file() -> None:
    """Test loading prefabs from YAML file."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    data = {
        "prefabs": [
            {
                "name": "player",
                "components": {"Position": {"x": 0.0, "y": 0.0}},
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        temp_path = f.name

    try:
        loaded = manager.load_from_file(path=temp_path)
        assert len(loaded) == 1
        assert manager.has_prefab(name="player")
    finally:
        Path(temp_path).unlink()


def test_load_from_file_not_found_raises_error() -> None:
    """Test loading from nonexistent file raises error."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    with pytest.raises(FileNotFoundError):
        manager.load_from_file(path="/nonexistent/path.json")


def test_load_from_file_unsupported_format_raises_error() -> None:
    """Test loading from unsupported file format raises error."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test")
        temp_path = f.name

    try:
        with pytest.raises(ValidationError, match="Unsupported file format"):
            manager.load_from_file(path=temp_path)
    finally:
        Path(temp_path).unlink()


def test_get_prefab() -> None:
    """Test retrieving prefab definition."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    prefab = Prefab(name="player")
    manager.register_prefab(prefab=prefab)

    retrieved = manager.get_prefab(name="player")
    assert retrieved == prefab


def test_get_prefab_not_found_raises_error() -> None:
    """Test retrieving unknown prefab raises error."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    with pytest.raises(ValidationError, match="not found"):
        manager.get_prefab(name="nonexistent")


def test_has_prefab() -> None:
    """Test checking if prefab exists."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    assert not manager.has_prefab(name="player")

    prefab = Prefab(name="player")
    manager.register_prefab(prefab=prefab)

    assert manager.has_prefab(name="player")


def test_clear() -> None:
    """Test clearing all prefabs."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    prefab1 = Prefab(name="player")
    prefab2 = Prefab(name="enemy")
    manager.register_prefab(prefab=prefab1)
    manager.register_prefab(prefab=prefab2)

    assert manager.prefab_count == 2

    manager.clear()

    assert manager.prefab_count == 0
    assert not manager.has_prefab(name="player")
    assert not manager.has_prefab(name="enemy")


def test_prefab_count() -> None:
    """Test getting prefab count."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    assert manager.prefab_count == 0

    manager.register_prefab(prefab=Prefab(name="prefab1"))
    assert manager.prefab_count == 1

    manager.register_prefab(prefab=Prefab(name="prefab2"))
    assert manager.prefab_count == 2


def test_component_type_count() -> None:
    """Test getting component type count."""
    world = ECSWorld()
    manager = PrefabManager(world=world)

    assert manager.component_type_count == 0

    manager.register_component_type(name="Position", component_class=Position)
    assert manager.component_type_count == 1

    manager.register_component_type(name="Health", component_class=Health)
    assert manager.component_type_count == 2
