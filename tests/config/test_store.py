"""Tests for config store."""

from typing import cast

import pytest
from faker import Faker

from yuna.config.schema import ConfigKey, ConfigSchema
from yuna.config.store import ConfigStore
from yuna.config.types import (
    ConfigConstraints,
    ConfigResolver,
    DerivedConfigKey,
)
from yuna.exceptions import ConfigSchemaError, ConfigValidationError
from yuna.types.identifiers import EntityID

fake = Faker()


@pytest.fixture
def schema():
    """Create test config schema."""
    s = ConfigSchema()

    s.register(
        ConfigKey(
            name="cache.size",
            type=int,
            value=16,
            constraints=ConfigConstraints(min_value=1, max_value=256),
        )
    )

    s.register(
        ConfigKey(
            name="sensor.range",
            type=float,
            value=50.0,
            constraints=ConfigConstraints(min_value=10.0, max_value=100.0),
        )
    )

    return s


@pytest.fixture
def store(schema):
    """Create test config store."""
    return ConfigStore(schema=schema)


@pytest.fixture
def entity_id():
    """Create test entity ID."""
    return EntityID(fake.uuid4())


def test_config_store_initialization(store):
    """Test config store initialization."""
    assert store.schema is not None
    assert len(store._global_defaults) == 0
    assert len(store._entity_overrides) == 0


def test_get_returns_schema_default(store, entity_id):
    """Test that get returns schema default when no overrides exist."""
    value = store.get(entity_id=entity_id, key="cache.size")
    assert value == 16


def test_set_global_default(store, entity_id):
    """Test setting global default value."""
    new_value = fake.random_int(min=1, max=256)
    store.set(key="cache.size", value=new_value)

    value = store.get(entity_id=entity_id, key="cache.size")
    assert value == new_value


def test_set_global_default_invalid_value_raises_error(store):
    """Test that setting invalid global default raises error."""
    invalid_value = fake.random_int(min=-100, max=-1)

    with pytest.raises(ConfigValidationError):
        store.set(key="cache.size", value=invalid_value)


def test_set_global_default_nonexistent_key_raises_error(store):
    """Test that setting global default for nonexistent key raises error."""
    nonexistent_key = fake.word() + "." + fake.word()
    value = fake.random_int()

    with pytest.raises(ConfigSchemaError):
        store.set(key=nonexistent_key, value=value)


def test_get_global_default(store):
    """Test getting global default value."""
    assert store.get("cache.size") == 16

    new_value = fake.random_int(min=1, max=256)
    store.set(key="cache.size", value=new_value)
    assert store.get("cache.size") == new_value


def test_set_entity_override(store, entity_id):
    """Test setting entity-specific override."""
    override_value = fake.random_int(min=1, max=256)

    store.set(
        key="cache.size",
        value=override_value,
        entity_id=entity_id,
    )

    value = store.get(entity_id=entity_id, key="cache.size")
    assert value == override_value


def test_set_entity_override_invalid_value_raises_error(store, entity_id):
    """Test that setting invalid entity override raises error."""
    invalid_value = fake.random_int(min=257, max=1000)

    with pytest.raises(ConfigValidationError):
        store.set(
            key="cache.size",
            value=invalid_value,
            entity_id=entity_id,
        )


def test_get_entity_override(store, entity_id):
    """Test getting entity-specific override."""
    assert not store.has_entity_override(entity_id=entity_id, key="cache.size")

    override_value = fake.random_int(min=1, max=256)
    store.set(
        key="cache.size",
        value=override_value,
        entity_id=entity_id,
    )

    overrides = store.get_all_entity_overrides(entity_id=entity_id)
    assert overrides["cache.size"] == override_value


def test_fallback_chain(store, entity_id):
    """Test entity override → global default → schema default fallback."""
    assert store.get(entity_id=entity_id, key="cache.size") == 16

    global_value = fake.random_int(min=1, max=256)
    store.set(key="cache.size", value=global_value)
    assert store.get(entity_id=entity_id, key="cache.size") == global_value

    entity_value = fake.random_int(min=1, max=256)
    store.set(
        key="cache.size",
        value=entity_value,
        entity_id=entity_id,
    )
    assert store.get(entity_id=entity_id, key="cache.size") == entity_value


def test_fallback_chain_different_entities(store):
    """Test that different entities have independent overrides."""
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    value1 = fake.random_int(min=1, max=256)
    value2 = fake.random_int(min=1, max=256)

    store.set(key="cache.size", value=value1, entity_id=entity1)
    store.set(key="cache.size", value=value2, entity_id=entity2)

    assert store.get(entity_id=entity1, key="cache.size") == value1
    assert store.get(entity_id=entity2, key="cache.size") == value2


def test_clear_entity_override(store, entity_id):
    """Test clearing entity-specific override."""
    override_value = fake.random_int(min=1, max=256)

    store.set(
        key="cache.size",
        value=override_value,
        entity_id=entity_id,
    )

    assert store.get(entity_id=entity_id, key="cache.size") == override_value

    store.clear_entity_override(entity_id=entity_id, key="cache.size")
    assert store.get(entity_id=entity_id, key="cache.size") == 16


def test_clear_all_entity_overrides(store, entity_id):
    """Test clearing all overrides for an entity."""
    cache_value = fake.random_int(min=1, max=256)
    sensor_value = fake.pyfloat(min_value=10.0, max_value=100.0)

    store.set(key="cache.size", value=cache_value, entity_id=entity_id)
    store.set(key="sensor.range", value=sensor_value, entity_id=entity_id)

    assert store.get(entity_id=entity_id, key="cache.size") == cache_value
    assert store.get(entity_id=entity_id, key="sensor.range") == sensor_value

    store.clear_all_entity_overrides(entity_id=entity_id)

    assert store.get(entity_id=entity_id, key="cache.size") == 16
    assert store.get(entity_id=entity_id, key="sensor.range") == 50.0


def test_get_all_entity_overrides(store, entity_id):
    """Test getting all overrides for an entity."""
    assert store.get_all_entity_overrides(entity_id=entity_id) == {}

    cache_value = fake.random_int(min=1, max=256)
    sensor_value = fake.pyfloat(min_value=10.0, max_value=100.0)

    store.set(key="cache.size", value=cache_value, entity_id=entity_id)
    store.set(key="sensor.range", value=sensor_value, entity_id=entity_id)

    overrides = store.get_all_entity_overrides(entity_id=entity_id)
    assert len(overrides) == 2
    assert overrides["cache.size"] == cache_value
    assert overrides["sensor.range"] == sensor_value


def test_has_entity_override(store, entity_id):
    """Test checking if entity has override for key."""
    assert not store.has_entity_override(entity_id=entity_id, key="cache.size")

    override_value = fake.random_int(min=1, max=256)
    store.set(key="cache.size", value=override_value, entity_id=entity_id)
    assert store.has_entity_override(entity_id=entity_id, key="cache.size")

    assert not store.has_entity_override(entity_id=entity_id, key="sensor.range")


def test_multiple_entities_with_global_default(store):
    """Test multiple entities sharing global default."""
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    global_value = fake.random_int(min=1, max=256)
    store.set(key="cache.size", value=global_value)

    assert store.get(entity_id=entity1, key="cache.size") == global_value
    assert store.get(entity_id=entity2, key="cache.size") == global_value
    assert store.get(entity_id=entity3, key="cache.size") == global_value

    entity2_value = fake.random_int(min=1, max=256)
    store.set(key="cache.size", value=entity2_value, entity_id=entity2)

    assert store.get(entity_id=entity1, key="cache.size") == global_value
    assert store.get(entity_id=entity2, key="cache.size") == entity2_value
    assert store.get(entity_id=entity3, key="cache.size") == global_value


def test_float_config_values(store, entity_id):
    """Test float configuration values."""
    assert store.get(entity_id=entity_id, key="sensor.range") == 50.0

    global_value = fake.pyfloat(min_value=10.0, max_value=100.0)
    store.set(key="sensor.range", value=global_value)
    assert store.get(entity_id=entity_id, key="sensor.range") == global_value

    entity_value = fake.pyfloat(min_value=10.0, max_value=100.0)
    store.set(key="sensor.range", value=entity_value, entity_id=entity_id)
    assert store.get(entity_id=entity_id, key="sensor.range") == entity_value


def test_get_min_with_constraints(store):
    """Test get_min returns minimum value from constraints."""
    min_value = store.get_min(key="cache.size")
    assert min_value == 1

    min_range = store.get_min(key="sensor.range")
    assert min_range == 10.0


def test_get_min_without_constraints(schema):
    """Test get_min returns None when no constraints defined."""
    schema.define(key="no_constraints", value_type=int, value=42)
    store = ConfigStore(schema=schema)

    min_value = store.get_min(key="no_constraints")
    assert min_value is None


def test_get_max_with_constraints(store):
    """Test get_max returns maximum value from constraints."""
    max_value = store.get_max(key="cache.size")
    assert max_value == 256

    max_range = store.get_max(key="sensor.range")
    assert max_range == 100.0


def test_get_max_without_constraints(schema):
    """Test get_max returns None when no constraints defined."""
    schema.define(key="no_constraints", value_type=int, value=42)
    store = ConfigStore(schema=schema)

    max_value = store.get_max(key="no_constraints")
    assert max_value is None


def test_merge_config_stores():
    """Test merging two config stores."""
    schema1 = ConfigSchema()
    schema1.register(
        ConfigKey(
            name="board.width",
            type=int,
            value=32,
            constraints=ConfigConstraints(min_value=1, max_value=100),
        )
    )
    store1 = ConfigStore(schema=schema1)
    custom_width = fake.random_int(min=1, max=100)
    store1.set(key="board.width", value=custom_width)

    schema2 = ConfigSchema()
    schema2.register(
        ConfigKey(
            name="game.speed",
            type=float,
            value=1.0,
            constraints=ConfigConstraints(min_value=0.5, max_value=2.0),
        )
    )
    store2 = ConfigStore(schema=schema2)

    store2.merge(other=store1)

    assert store2.get(key="board.width") == custom_width
    assert store2.get(key="game.speed") == 1.0


def test_invalidate_cache_specific_key():
    """Test invalidating specific derived key cache."""
    schema = ConfigSchema()
    base_key = f"{fake.unique.word()}.{fake.unique.word()}"
    derived_key = f"{fake.unique.word()}.{fake.unique.word()}"
    base_value = fake.random_int(min=100, max=1000)

    schema.register(ConfigKey(name=base_key, type=int, value=base_value))

    def formula(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(base_key)) * 0.5

    schema.register(
        DerivedConfigKey(
            name=derived_key,
            type=float,
            value=None,
            formula=formula,
            dependencies=(base_key,),
        )
    )

    store = ConfigStore(schema=schema)

    result1 = store.get(key=derived_key)
    assert derived_key in store._resolved_globals

    store.invalidate_cache(key=derived_key)
    assert derived_key not in store._resolved_globals

    result2 = store.get(key=derived_key)
    assert result1 == result2


def test_get_derived_config_key_evaluates_formula():
    """Test that getting derived key evaluates formula."""
    schema = ConfigSchema()
    base_key = f"{fake.unique.word()}.{fake.unique.word()}"
    derived_key = f"{fake.unique.word()}.{fake.unique.word()}"
    base_value = fake.random_int(min=100, max=1000)
    multiplier = fake.pyfloat(min_value=0.1, max_value=2.0)

    schema.register(ConfigKey(name=base_key, type=int, value=base_value))

    def formula(cfg: ConfigResolver) -> float:
        value = cast(float, cfg.get(base_key))
        result: float = value * multiplier
        return result

    schema.register(
        DerivedConfigKey(
            name=derived_key,
            type=float,
            value=None,
            formula=formula,
            dependencies=(base_key,),
        )
    )

    store = ConfigStore(schema=schema)

    result = store.get(key=derived_key)
    expected = base_value * multiplier
    assert abs(result - expected) < 0.0001


def test_get_derived_config_key_caches_result():
    """Test that derived key result is cached."""
    schema = ConfigSchema()
    base_key = f"{fake.unique.word()}.{fake.unique.word()}"
    derived_key = f"{fake.unique.word()}.{fake.unique.word()}"
    base_value = fake.random_int(min=100, max=1000)

    schema.register(ConfigKey(name=base_key, type=int, value=base_value))

    call_count = {"count": 0}

    def formula(cfg: ConfigResolver) -> float:
        call_count["count"] += 1
        return cast(float, cfg.get(base_key)) * 0.5

    schema.register(
        DerivedConfigKey(
            name=derived_key,
            type=float,
            value=None,
            formula=formula,
            dependencies=(base_key,),
        )
    )

    store = ConfigStore(schema=schema)

    result1 = store.get(key=derived_key)
    assert call_count["count"] == 1
    assert derived_key in store._resolved_globals

    result2 = store.get(key=derived_key)
    assert call_count["count"] == 1
    assert result1 == result2


def test_get_derived_config_key_with_global_default():
    """Test that derived key respects global default fallback."""
    schema = ConfigSchema()
    base_key = f"{fake.unique.word()}.{fake.unique.word()}"
    derived_key = f"{fake.unique.word()}.{fake.unique.word()}"
    base_value = fake.random_int(min=100, max=1000)
    override_base = fake.random_int(min=100, max=1000)

    schema.register(ConfigKey(name=base_key, type=int, value=base_value))

    def formula(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(base_key)) * 2.0

    schema.register(
        DerivedConfigKey(
            name=derived_key,
            type=float,
            value=None,
            formula=formula,
            dependencies=(base_key,),
        )
    )

    store = ConfigStore(schema=schema)

    result1 = store.get(key=derived_key)
    expected1 = base_value * 2.0
    assert abs(result1 - expected1) < 0.0001

    store.set(key=base_key, value=override_base)

    result2 = store.get(key=derived_key)
    expected2 = override_base * 2.0
    assert abs(result2 - expected2) < 0.0001


def test_invalidate_cache_clears_all_when_global_default_changes():
    """Test that setting global default invalidates all cached derived values."""
    schema = ConfigSchema()
    base_key = f"{fake.word()}.{fake.word()}"
    derived1 = f"{fake.word()}.derived1"
    derived2 = f"{fake.word()}.derived2"
    base_value = fake.random_int(min=100, max=1000)

    schema.register(ConfigKey(name=base_key, type=int, value=base_value))

    def formula1(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(base_key)) * 0.5

    def formula2(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(base_key)) * 2.0

    schema.register(
        DerivedConfigKey(
            name=derived1,
            type=float,
            value=None,
            formula=formula1,
            dependencies=(base_key,),
        )
    )

    schema.register(
        DerivedConfigKey(
            name=derived2,
            type=float,
            value=None,
            formula=formula2,
            dependencies=(base_key,),
        )
    )

    store = ConfigStore(schema=schema)

    store.get(key=derived1)
    store.get(key=derived2)
    assert derived1 in store._resolved_globals
    assert derived2 in store._resolved_globals

    new_base = fake.random_int(min=100, max=1000)
    store.set(key=base_key, value=new_base)

    assert len(store._resolved_globals) == 0


def test_resolved_cache_serves_repeat_reads(store):
    """Repeat global reads are served from the resolved cache."""
    first = store.get(key="cache.size")

    assert store._resolved_globals["cache.size"] == first
    assert store.get(key="cache.size") == first


def test_set_invalidates_resolved_cache(store):
    """Setting a global default clears resolved values."""
    assert store.get(key="cache.size") == 16

    store.set(key="cache.size", value=64)

    assert store._resolved_globals == {}
    assert store.get(key="cache.size") == 64


def test_selective_invalidate_clears_resolved_key(store):
    """invalidate_cache(key=...) drops only that resolved entry."""
    store.get(key="cache.size")
    store.get(key="sensor.range")

    store.invalidate_cache(key="cache.size")

    assert "cache.size" not in store._resolved_globals
    assert "sensor.range" in store._resolved_globals


def test_merge_invalidates_resolved_cache():
    """Merging another store clears previously resolved values."""
    base_schema = ConfigSchema()
    base_schema.register(
        ConfigKey(name="board.width", type=int, value=16, constraints=None)
    )
    store = ConfigStore(schema=base_schema)
    assert store.get(key="board.width") == 16

    incoming_schema = ConfigSchema()
    incoming_schema.register(
        ConfigKey(name="board.width", type=int, value=16, constraints=None)
    )
    incoming = ConfigStore(schema=incoming_schema)
    incoming._global_defaults["board.width"] = 32

    store.schema._keys.pop("board.width")
    store.merge(other=incoming)

    assert store.get(key="board.width") == 32


def test_entity_get_falls_back_to_resolved_global(store, entity_id):
    """Entity reads without overrides reuse the resolved global value."""
    assert store.get(key="cache.size", entity_id=entity_id) == 16
    assert store.get(key="cache.size") == 16
    assert store.get(key="cache.size", entity_id=entity_id) == 16
