"""Integration tests for config system with ECS."""

import pytest
from faker import Faker

from yuna.config.component import ConfigComponent
from yuna.config.schema import ConfigKey, ConfigSchema
from yuna.config.types import ConfigConstraints
from yuna.ecs.world import ECSWorld
from yuna.exceptions import StateError

fake = Faker()


@pytest.fixture
def schema():
    """Create test config schema."""
    schema = ConfigSchema()

    schema.register(
        ConfigKey(
            name="cache.size",
            type=int,
            value=16,
            constraints=ConfigConstraints(min_value=1, max_value=256),
        )
    )

    schema.register(
        ConfigKey(
            name="sensor.range",
            type=float,
            value=50.0,
            constraints=ConfigConstraints(min_value=10.0, max_value=100.0),
        )
    )

    return schema


@pytest.fixture
def world(schema):
    """Create ECS world with config schema."""
    return ECSWorld(config_schema=schema)


def test_config_component_creation():
    """Test ConfigComponent creation."""
    overrides = {
        fake.word(): fake.random_int(),
        fake.word(): fake.pyfloat(),
    }

    component = ConfigComponent(overrides=overrides)

    assert component.overrides == overrides


def test_config_component_get_override():
    """Test ConfigComponent.get_override."""
    key = fake.word()
    value = fake.random_int()

    component = ConfigComponent(overrides={key: value})

    assert component.get_override(key) == value
    assert component.get_override(f"{key}_nonexistent") is None


def test_config_component_has_override():
    """Test ConfigComponent.has_override."""
    key = fake.word()
    value = fake.random_int()

    component = ConfigComponent(overrides={key: value})

    assert component.has_override(key) is True
    assert component.has_override(f"{key}_nonexistent") is False


def test_config_component_with_override():
    """Test ConfigComponent.with_override returns new instance."""
    key1 = fake.unique.word()
    value1 = fake.random_int()
    key2 = fake.unique.word()
    value2 = fake.random_int()

    component = ConfigComponent(overrides={key1: value1})
    new_component = component.with_override(key=key2, value=value2)

    assert component.overrides == {key1: value1}
    assert new_component.overrides == {key1: value1, key2: value2}


def test_config_component_without_override():
    """Test ConfigComponent.without_override returns new instance."""
    key1 = fake.unique.word()
    value1 = fake.random_int()
    key2 = fake.unique.word()
    value2 = fake.random_int()

    component = ConfigComponent(overrides={key1: value1, key2: value2})
    new_component = component.without_override(key=key2)

    assert component.overrides == {key1: value1, key2: value2}
    assert new_component.overrides == {key1: value1}


def test_config_component_frozen():
    """Test ConfigComponent is immutable."""
    component = ConfigComponent(overrides={fake.word(): fake.random_int()})

    with pytest.raises((AttributeError, TypeError)):
        component.overrides = {}  # type: ignore[misc]


def test_ecs_world_with_config_schema(schema):
    """Test ECSWorld initialization with config schema."""
    world = ECSWorld(config_schema=schema)

    assert world._config_schema is schema
    assert world._config_store is not None


def test_ecs_world_without_config_schema():
    """Test ECSWorld initialization without config schema."""
    world = ECSWorld()

    assert world._config_schema is None
    assert world._config_store is None


def test_ecs_world_config_property(world):
    """Test ECSWorld.config property access."""
    config_store = world.config

    assert config_store is not None
    assert config_store.schema is world._config_schema


def test_ecs_world_config_property_raises_without_schema():
    """Test ECSWorld.config raises StateError without schema."""
    world = ECSWorld()

    with pytest.raises(StateError) as exc_info:
        _ = world.config

    assert "no config schema" in str(exc_info.value).lower()


def test_ecs_world_config_fallback_chain(world):
    """Test config fallback chain with ECS world."""
    entity_id = world.create_entity()

    assert world.config.get(entity_id=entity_id, key="cache.size") == 16

    world.config.set(key="cache.size", value=32)
    assert world.config.get(entity_id=entity_id, key="cache.size") == 32

    world.config.set(key="cache.size", value=64, entity_id=entity_id)
    assert world.config.get(entity_id=entity_id, key="cache.size") == 64


def test_ecs_world_config_multiple_entities(world):
    """Test config with multiple entities."""
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    entity3 = world.create_entity()

    global_value = fake.random_int(min=1, max=256)
    world.config.set(key="cache.size", value=global_value)

    assert world.config.get(entity_id=entity1, key="cache.size") == global_value
    assert world.config.get(entity_id=entity2, key="cache.size") == global_value
    assert world.config.get(entity_id=entity3, key="cache.size") == global_value

    entity2_value = fake.random_int(min=1, max=256)
    world.config.set(key="cache.size", value=entity2_value, entity_id=entity2)

    assert world.config.get(entity_id=entity1, key="cache.size") == global_value
    assert world.config.get(entity_id=entity2, key="cache.size") == entity2_value
    assert world.config.get(entity_id=entity3, key="cache.size") == global_value


def test_config_component_with_ecs_world(world):
    """Test ConfigComponent attached to entity."""
    entity_id = world.create_entity()

    cache_value = fake.random_int(min=1, max=256)
    sensor_value = fake.pyfloat(min_value=10.0, max_value=100.0)

    world.add_component(
        entity_id=entity_id,
        component=ConfigComponent(
            overrides={
                "cache.size": cache_value,
                "sensor.range": sensor_value,
            }
        ),
    )

    component = world.get_component(entity_id, ConfigComponent)
    assert component is not None
    assert component.get_override("cache.size") == cache_value
    assert component.get_override("sensor.range") == sensor_value


def test_config_component_sync_to_store(world):
    """Test syncing ConfigComponent overrides to ConfigStore."""
    entity_id = world.create_entity()

    cache_value = fake.random_int(min=1, max=256)
    sensor_value = fake.pyfloat(min_value=10.0, max_value=100.0)

    world.add_component(
        entity_id=entity_id,
        component=ConfigComponent(
            overrides={
                "cache.size": cache_value,
                "sensor.range": sensor_value,
            }
        ),
    )

    component = world.get_component(entity_id, ConfigComponent)

    for key_name, value in component.overrides.items():
        world.config.set(key=key_name, value=value, entity_id=entity_id)

    assert world.config.get(entity_id=entity_id, key="cache.size") == cache_value
    assert world.config.get(entity_id=entity_id, key="sensor.range") == sensor_value


def test_config_component_immutability_pattern(world):
    """Test ConfigComponent immutability pattern for updates."""
    entity_id = world.create_entity()

    key1 = "cache.size"
    value1 = fake.random_int(min=1, max=256)

    component = ConfigComponent(overrides={key1: value1})
    world.add_component(entity_id=entity_id, component=component)

    key2 = "sensor.range"
    value2 = fake.pyfloat(min_value=10.0, max_value=100.0)

    old_component = world.get_component(entity_id, ConfigComponent)
    new_component = old_component.with_override(key=key2, value=value2)

    world.add_component(entity_id=entity_id, component=new_component)

    updated_component = world.get_component(entity_id, ConfigComponent)
    assert updated_component.get_override(key1) == value1
    assert updated_component.get_override(key2) == value2


def test_config_upgrade_pattern(world):
    """Test upgrade pattern using config overrides."""
    entity_id = world.create_entity()

    current = world.config.get(entity_id=entity_id, key="cache.size")
    assert current == 16

    new_size = current * 2
    key = world.config.schema.get_key("cache.size")
    new_size = key.clamp(new_size)

    world.config.set(key="cache.size", value=new_size, entity_id=entity_id)

    upgraded = world.config.get(entity_id=entity_id, key="cache.size")
    assert upgraded == 32


def test_config_reset_pattern(world):
    """Test reset pattern by clearing overrides."""
    entity_id = world.create_entity()

    world.config.set(key="cache.size", value=32)

    world.config.set(key="cache.size", value=64, entity_id=entity_id)
    assert world.config.get(entity_id=entity_id, key="cache.size") == 64

    world.config.clear_all_entity_overrides(entity_id=entity_id)
    assert world.config.get(entity_id=entity_id, key="cache.size") == 32
