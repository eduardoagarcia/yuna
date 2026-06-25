"""Tests for TypeRegistry class."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from faker import Faker

from yuna.exceptions import StateError, ValidationError
from yuna.types.registry import TypeRegistry
from yuna.types.type_object import EntityType

fake = Faker()


def test_type_registry_creation() -> None:
    registry = TypeRegistry()

    assert registry is not None


def test_register_type() -> None:
    registry = TypeRegistry()
    entity_type = EntityType(name=fake.word())

    registry.register_type(entity_type=entity_type)

    assert registry.has_type(name=entity_type.name)


def test_register_duplicate_type_raises_error() -> None:
    registry = TypeRegistry()
    name = fake.word()
    entity_type1 = EntityType(name=name)
    entity_type2 = EntityType(name=name)

    registry.register_type(entity_type=entity_type1)

    with pytest.raises(StateError, match="already registered"):
        registry.register_type(entity_type=entity_type2)


def test_get_type() -> None:
    registry = TypeRegistry()
    entity_type = EntityType(name=fake.word(), components={"Position": {"x": 0.0}})

    registry.register_type(entity_type=entity_type)
    retrieved = registry.get_type(name=entity_type.name)

    assert retrieved == entity_type


def test_get_non_existent_type_raises_error() -> None:
    registry = TypeRegistry()

    with pytest.raises(ValidationError, match="not found"):
        registry.get_type(name=fake.word())


def test_has_type_returns_true_for_registered() -> None:
    registry = TypeRegistry()
    entity_type = EntityType(name=fake.word())

    registry.register_type(entity_type=entity_type)

    assert registry.has_type(name=entity_type.name)


def test_has_type_returns_false_for_non_existent() -> None:
    registry = TypeRegistry()

    assert not registry.has_type(name=fake.word())


def test_get_all_types() -> None:
    registry = TypeRegistry()
    type1 = EntityType(name=fake.unique.word())
    type2 = EntityType(name=fake.unique.word())

    registry.register_type(entity_type=type1)
    registry.register_type(entity_type=type2)

    all_types = registry.get_all_types()

    assert len(all_types) == 2
    assert type1.name in all_types
    assert type2.name in all_types


def test_get_all_types_returns_copy() -> None:
    registry = TypeRegistry()
    entity_type = EntityType(name=fake.word())

    registry.register_type(entity_type=entity_type)
    all_types = registry.get_all_types()
    all_types.clear()

    assert registry.has_type(name=entity_type.name)


def test_unregister_type() -> None:
    registry = TypeRegistry()
    entity_type = EntityType(name=fake.word())

    registry.register_type(entity_type=entity_type)
    registry.unregister_type(name=entity_type.name)

    assert not registry.has_type(name=entity_type.name)


def test_unregister_non_existent_type_raises_error() -> None:
    registry = TypeRegistry()

    with pytest.raises(ValidationError, match="not found"):
        registry.unregister_type(name=fake.word())


def test_clear() -> None:
    registry = TypeRegistry()
    type1 = EntityType(name=fake.unique.word())
    type2 = EntityType(name=fake.unique.word())

    registry.register_type(entity_type=type1)
    registry.register_type(entity_type=type2)
    registry.clear()

    assert len(registry.get_all_types()) == 0


def test_load_from_dict() -> None:
    registry = TypeRegistry()
    data = {
        "player": {"components": {"Position": {"x": 0.0}}, "behaviors": ["movement"]},
        "enemy": {"components": {"Health": {"current": 50}}, "behaviors": ["combat"]},
    }

    registry.load_from_dict(data=data)

    assert registry.has_type(name="player")
    assert registry.has_type(name="enemy")


def test_load_from_dict_with_invalid_data_raises_error() -> None:
    registry = TypeRegistry()

    with pytest.raises(ValidationError, match="must be a dictionary"):
        registry.load_from_dict(data="invalid")  # type: ignore[arg-type]


def test_load_from_dict_with_invalid_type_data_raises_error() -> None:
    registry = TypeRegistry()
    data = {"player": "invalid"}

    with pytest.raises(ValidationError, match="must be a dictionary"):
        registry.load_from_dict(data=data)


def test_load_from_dict_creates_entity_types() -> None:
    registry = TypeRegistry()
    data = {"player": {"components": {"Position": {"x": 0.0}}, "behaviors": []}}

    registry.load_from_dict(data=data)
    player_type = registry.get_type(name="player")

    assert player_type.name == "player"
    assert player_type.components == {"Position": {"x": 0.0}}


def test_load_from_json() -> None:
    registry = TypeRegistry()
    json_string = json.dumps({
        "player": {
            "components": {"Position": {"x": 0.0}},
            "behaviors": ["movement"],
        }
    })

    registry.load_from_json(json_string=json_string)

    assert registry.has_type(name="player")


def test_load_from_json_with_invalid_json_raises_error() -> None:
    registry = TypeRegistry()

    with pytest.raises(ValidationError, match="Invalid JSON"):
        registry.load_from_json(json_string="invalid json")


def test_load_from_yaml() -> None:
    registry = TypeRegistry()
    yaml_string = yaml.dump({
        "player": {
            "components": {"Position": {"x": 0.0}},
            "behaviors": ["movement"],
        }
    })

    registry.load_from_yaml(yaml_string=yaml_string)

    assert registry.has_type(name="player")


def test_load_from_yaml_with_invalid_yaml_raises_error() -> None:
    registry = TypeRegistry()

    with pytest.raises(ValidationError, match="Invalid YAML"):
        registry.load_from_yaml(yaml_string="invalid: yaml: :")


def test_load_from_yaml_with_empty_string() -> None:
    registry = TypeRegistry()

    registry.load_from_yaml(yaml_string="")

    assert len(registry.get_all_types()) == 0


def test_load_from_file_json() -> None:
    registry = TypeRegistry()
    data = {"player": {"components": {"Position": {"x": 0.0}}, "behaviors": []}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    try:
        registry.load_from_file(path=temp_path)
        assert registry.has_type(name="player")
    finally:
        Path(temp_path).unlink()


def test_load_from_file_yaml() -> None:
    registry = TypeRegistry()
    data = {"enemy": {"components": {"Health": {"current": 50}}, "behaviors": []}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        temp_path = f.name

    try:
        registry.load_from_file(path=temp_path)
        assert registry.has_type(name="enemy")
    finally:
        Path(temp_path).unlink()


def test_load_from_file_yml_extension() -> None:
    registry = TypeRegistry()
    data = {"npc": {"components": {"Sprite": {"texture": "npc.png"}}, "behaviors": []}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(data, f)
        temp_path = f.name

    try:
        registry.load_from_file(path=temp_path)
        assert registry.has_type(name="npc")
    finally:
        Path(temp_path).unlink()


def test_load_from_file_not_found_raises_error() -> None:
    registry = TypeRegistry()

    with pytest.raises(FileNotFoundError):
        registry.load_from_file(path="/nonexistent/path/types.json")


def test_load_from_file_unsupported_format_raises_error() -> None:
    registry = TypeRegistry()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("data")
        temp_path = f.name

    try:
        with pytest.raises(ValidationError, match="Unsupported file format"):
            registry.load_from_file(path=temp_path)
    finally:
        Path(temp_path).unlink()


def test_load_from_dict_without_components() -> None:
    registry = TypeRegistry()
    data: dict[str, dict[str, list[str]]] = {"item": {}}

    registry.load_from_dict(data=data)
    item_type = registry.get_type(name="item")

    assert item_type.components == {}
    assert item_type.behaviors == []


def test_load_from_dict_without_behaviors() -> None:
    registry = TypeRegistry()
    data = {"powerup": {"components": {"Effect": {"type": "speed"}}}}

    registry.load_from_dict(data=data)
    powerup_type = registry.get_type(name="powerup")

    assert powerup_type.components == {"Effect": {"type": "speed"}}
    assert powerup_type.behaviors == []


def test_multiple_registrations() -> None:
    registry = TypeRegistry()
    types = [EntityType(name=f"type_{i}_{fake.word()}") for i in range(10)]

    for entity_type in types:
        registry.register_type(entity_type=entity_type)

    assert len(registry.get_all_types()) == 10
