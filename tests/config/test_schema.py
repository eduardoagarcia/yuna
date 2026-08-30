"""Tests for config schema."""

from collections.abc import Callable
from typing import cast

import pytest
from faker import Faker

from yuna.config.schema import ConfigKey, ConfigSchema
from yuna.config.types import (
    ConfigConstraints,
    ConfigResolver,
    ConfigValue,
    DerivedConfigKey,
)
from yuna.config.validators import must_be_power_of_two
from yuna.exceptions import ConfigSchemaError

fake = Faker()


def test_config_key_basic():
    """Test basic config key creation."""
    key_name = f"{fake.word()}.{fake.word()}"
    default_value = fake.random_int(min=1, max=100)

    key = ConfigKey(
        name=key_name,
        type=int,
        value=default_value,
    )

    assert key.name == key_name
    assert key.type is int
    assert key.value == default_value
    assert key.constraints is None
    assert not key.description


def test_config_key_with_constraints():
    """Test config key with min/max constraints."""
    min_value = fake.random_int(min=1, max=10)
    max_value = fake.random_int(min=100, max=1000)
    default_value = fake.random_int(min=min_value, max=max_value)
    description = fake.sentence()

    key = ConfigKey(
        name=f"{fake.word()}.{fake.word()}",
        type=int,
        value=default_value,
        constraints=ConfigConstraints(min_value=min_value, max_value=max_value),
        description=description,
    )

    assert key.constraints is not None
    assert key.constraints.min_value == min_value
    assert key.constraints.max_value == max_value
    assert key.description == description


def test_config_key_default_below_min_raises_error():
    """Test that default value below minimum raises error."""
    min_value = fake.random_int(min=10, max=100)
    default_value = fake.random_int(min=1, max=min_value - 1)

    with pytest.raises(ConfigSchemaError):
        ConfigKey(
            name=f"{fake.word()}.{fake.word()}",
            type=int,
            value=default_value,
            constraints=ConfigConstraints(min_value=min_value),
        )


def test_config_key_default_above_max_raises_error():
    """Test that default value above maximum raises error."""
    max_value = fake.random_int(min=10, max=100)
    default_value = fake.random_int(min=max_value + 1, max=max_value + 100)

    with pytest.raises(ConfigSchemaError):
        ConfigKey(
            name=f"{fake.word()}.{fake.word()}",
            type=int,
            value=default_value,
            constraints=ConfigConstraints(max_value=max_value),
        )


def test_config_key_validate_type():
    """Test type validation."""
    default_value = fake.random_int(min=1, max=100)
    valid_value = fake.random_int(min=1, max=100)
    invalid_value = fake.word()

    key = ConfigKey(
        name=f"{fake.word()}.{fake.word()}",
        type=int,
        value=default_value,
    )

    valid, reason = key.validate(valid_value)
    assert valid is True
    assert not reason

    valid, reason = key.validate(cast(int, invalid_value))
    assert valid is False
    assert "Expected int" in reason


def test_config_key_validate_min_value():
    """Test minimum value validation."""
    min_value = fake.random_int(min=5, max=20)
    default_value = fake.random_int(min=min_value, max=100)
    valid_value = fake.random_int(min=min_value, max=100)
    invalid_value = fake.random_int(min=1, max=min_value - 1)

    key = ConfigKey(
        name=f"{fake.word()}.{fake.word()}",
        type=int,
        value=default_value,
        constraints=ConfigConstraints(min_value=min_value),
    )

    valid, _ = key.validate(valid_value)
    assert valid is True

    valid, _ = key.validate(min_value)
    assert valid is True

    valid, reason = key.validate(invalid_value)
    assert valid is False
    assert "< min" in reason


def test_config_key_validate_max_value():
    """Test maximum value validation."""
    max_value = fake.random_int(min=50, max=100)
    default_value = fake.random_int(min=1, max=max_value)
    valid_value = fake.random_int(min=1, max=max_value)
    invalid_value = fake.random_int(min=max_value + 1, max=max_value + 100)

    key = ConfigKey(
        name=f"{fake.word()}.{fake.word()}",
        type=int,
        value=default_value,
        constraints=ConfigConstraints(max_value=max_value),
    )

    valid, _ = key.validate(valid_value)
    assert valid is True

    valid, _ = key.validate(max_value)
    assert valid is True

    valid, reason = key.validate(invalid_value)
    assert valid is False
    assert "> max" in reason


def test_config_key_validate_custom_validator():
    """Test custom validator."""
    valid_power = 2 ** fake.random_int(min=1, max=10)
    invalid_value = fake.random_int(min=1, max=100)
    while invalid_value & (invalid_value - 1) == 0:
        invalid_value = fake.random_int(min=1, max=100)

    key = ConfigKey(
        name=f"{fake.word()}.{fake.word()}",
        type=int,
        value=valid_power,
        constraints=ConfigConstraints(validator=must_be_power_of_two),
    )

    valid, _ = key.validate(valid_power)
    assert valid is True

    valid, reason = key.validate(invalid_value)
    assert valid is False
    assert "power of 2" in reason


def test_config_key_clamp():
    """Test clamping values to min/max."""
    min_value = fake.random_int(min=5, max=20)
    max_value = fake.random_int(min=50, max=100)
    default_value = fake.random_int(min=min_value, max=max_value)
    below_min = fake.random_int(min=1, max=min_value - 1)
    above_max = fake.random_int(min=max_value + 1, max=max_value + 100)
    within_range = fake.random_int(min=min_value, max=max_value)

    key = ConfigKey(
        name=f"{fake.word()}.{fake.word()}",
        type=int,
        value=default_value,
        constraints=ConfigConstraints(min_value=min_value, max_value=max_value),
    )

    assert key.clamp(below_min) == min_value
    assert key.clamp(within_range) == within_range
    assert key.clamp(above_max) == max_value


def test_config_schema_register():
    """Test registering config keys."""
    schema = ConfigSchema()
    key_name = f"{fake.word()}.{fake.word()}"

    key = ConfigKey(
        name=key_name,
        type=int,
        value=fake.random_int(min=1, max=100),
    )

    schema.register(key)
    assert schema.has_key(key_name)


def test_config_schema_register_duplicate_raises_error():
    """Test that registering duplicate key raises error."""
    schema = ConfigSchema()
    key_name = f"{fake.word()}.{fake.word()}"

    key = ConfigKey(
        name=key_name,
        type=int,
        value=fake.random_int(min=1, max=100),
    )

    schema.register(key)

    with pytest.raises(ConfigSchemaError):
        schema.register(key)


def test_config_schema_get_key():
    """Test getting config key by name."""
    schema = ConfigSchema()
    key_name = f"{fake.word()}.{fake.word()}"
    default_value = fake.random_int(min=1, max=100)

    key = ConfigKey(
        name=key_name,
        type=int,
        value=default_value,
    )

    schema.register(key)
    retrieved = schema.get_key(key_name)

    assert retrieved.name == key_name
    assert retrieved.value == default_value


def test_config_schema_get_nonexistent_key_raises_error():
    """Test that getting non-existent key raises error."""
    schema = ConfigSchema()
    nonexistent_key = f"{fake.word()}.{fake.word()}"

    with pytest.raises(ConfigSchemaError):
        schema.get_key(nonexistent_key)


def test_config_schema_has_key():
    """Test checking if key exists."""
    schema = ConfigSchema()
    key_name = f"{fake.word()}.{fake.word()}"

    key = ConfigKey(
        name=key_name,
        type=int,
        value=fake.random_int(min=1, max=100),
    )

    assert not schema.has_key(key_name)

    schema.register(key)
    assert schema.has_key(key_name)


def test_config_schema_get_all_keys():
    """Test getting all registered keys."""
    schema = ConfigSchema()

    key1_name = f"{fake.unique.word()}.{fake.unique.word()}"
    key2_name = f"{fake.unique.word()}.{fake.unique.word()}"

    key1 = ConfigKey(name=key1_name, type=int, value=fake.random_int(min=1, max=100))
    key2 = ConfigKey(name=key2_name, type=int, value=fake.random_int(min=1, max=100))

    schema.register(key1)
    schema.register(key2)

    all_keys = schema.get_all_keys()
    assert len(all_keys) == 2
    assert key1_name in all_keys
    assert key2_name in all_keys


def test_config_schema_validate_value():
    """Test validating value for a key."""
    schema = ConfigSchema()
    key_name = f"{fake.word()}.{fake.word()}"
    min_value = fake.random_int(min=5, max=20)
    max_value = fake.random_int(min=50, max=100)
    default_value = fake.random_int(min=min_value, max=max_value)

    key = ConfigKey(
        name=key_name,
        type=int,
        value=default_value,
        constraints=ConfigConstraints(min_value=min_value, max_value=max_value),
    )

    schema.register(key)

    valid_value = fake.random_int(min=min_value, max=max_value)
    invalid_low = fake.random_int(min=1, max=min_value - 1)
    invalid_high = fake.random_int(min=max_value + 1, max=max_value + 100)

    valid, _ = schema.validate_value(key_name, valid_value)
    assert valid is True

    valid, _ = schema.validate_value(key_name, invalid_low)
    assert valid is False

    valid, _ = schema.validate_value(key_name, invalid_high)
    assert valid is False


def test_config_key_clamp_without_constraints():
    """Test clamping when key has no constraints."""
    value = fake.random_int(min=1, max=100)
    key = ConfigKey(
        name=f"{fake.word()}.{fake.word()}",
        type=int,
        value=50,
    )

    assert key.clamp(value) == value


def test_config_schema_define():
    """Test defining config keys with automatic namespace prefixing."""
    namespace = fake.word()
    schema = ConfigSchema(namespace=namespace)

    key = fake.word()
    default_value = fake.random_int(min=1, max=100)
    description = fake.sentence()

    schema.define(
        key=key,
        value_type=int,
        value=default_value,
        description=description,
    )

    full_key = f"{namespace}.{key}"
    assert schema.has_key(full_key)

    retrieved = schema.get_key(full_key)
    assert retrieved.name == full_key
    assert retrieved.value == default_value
    assert retrieved.description == description


def test_config_schema_define_with_constraints():
    """Test defining config keys with constraints."""
    namespace = fake.word()
    schema = ConfigSchema(namespace=namespace)

    key = fake.word()
    min_value = fake.random_int(min=1, max=10)
    max_value = fake.random_int(min=50, max=100)
    default_value = fake.random_int(min=min_value, max=max_value)

    schema.define(
        key=key,
        value_type=int,
        value=default_value,
        constraints=ConfigConstraints(min_value=min_value, max_value=max_value),
    )

    full_key = f"{namespace}.{key}"
    retrieved = schema.get_key(full_key)
    assert retrieved.constraints is not None
    assert retrieved.constraints.min_value == min_value
    assert retrieved.constraints.max_value == max_value


def test_config_schema_define_no_namespace():
    """Test defining config keys without namespace."""
    schema = ConfigSchema()

    key = f"{fake.word()}.{fake.word()}"
    default_value = fake.random_int(min=1, max=100)

    schema.define(
        key=key,
        value_type=int,
        value=default_value,
    )

    assert schema.has_key(key)
    retrieved = schema.get_key(key)
    assert retrieved.name == key


def test_config_schema_merge():
    """Test merging schemas with namespace prefixing."""
    child_namespace = fake.word()
    child_schema = ConfigSchema(namespace=child_namespace)
    child_key = fake.word()
    child_default = fake.random_int(min=1, max=100)

    child_schema.define(
        key=child_key,
        value_type=int,
        value=child_default,
    )

    parent_namespace = fake.word()
    parent_schema = ConfigSchema(namespace=parent_namespace)
    parent_schema.merge(child_schema)

    merged_key = f"{parent_namespace}.{child_namespace}.{child_key}"
    assert parent_schema.has_key(merged_key)

    retrieved = parent_schema.get_key(merged_key)
    assert retrieved.value == child_default


def test_config_schema_merge_preserves_constraints():
    """Test that merge preserves constraints."""
    child_schema = ConfigSchema(namespace="child")
    min_value = fake.random_int(min=1, max=10)
    max_value = fake.random_int(min=50, max=100)
    default_value = fake.random_int(min=min_value, max=max_value)

    child_schema.define(
        key="size",
        value_type=int,
        value=default_value,
        constraints=ConfigConstraints(min_value=min_value, max_value=max_value),
    )

    parent_schema = ConfigSchema(namespace="parent")
    parent_schema.merge(child_schema)

    merged_key = "parent.child.size"
    retrieved = parent_schema.get_key(merged_key)
    assert retrieved.constraints is not None
    assert retrieved.constraints.min_value == min_value
    assert retrieved.constraints.max_value == max_value


def test_config_schema_merge_derived_key():
    """Test that merge handles DerivedConfigKey correctly."""
    child_schema = ConfigSchema(namespace="child")
    base_key = "core.baseline"
    derived_key_name = "computed"
    multiplier = fake.pyfloat(min_value=1.0, max_value=5.0)

    def formula(cfg: ConfigResolver) -> float:
        value = cast(float, cfg.get(base_key))
        result: float = value * multiplier
        return result

    child_schema.define_derived(
        key=derived_key_name,
        value_type=float,
        formula=formula,
        dependencies=(base_key,),
        description="Computed value",
    )

    parent_schema = ConfigSchema(namespace="parent")
    parent_schema.merge(child_schema)

    merged_key = f"parent.child.{derived_key_name}"
    assert parent_schema.has_key(merged_key)

    retrieved = parent_schema.get_key(merged_key)
    assert isinstance(retrieved, DerivedConfigKey)
    assert retrieved.dependencies == (base_key,)
    assert retrieved.description == "Computed value"


def test_define_derived() -> None:
    """Test defining derived config key with formula."""
    schema = ConfigSchema(namespace="bot")
    base_value = fake.random_int(min=100, max=1000)

    schema.define(key="base_ticks", value_type=int, value=base_value)

    def drain_formula(cfg: ConfigResolver) -> float:
        return 1.0 / float(cfg.get("bot.base_ticks"))

    min_drain = fake.pyfloat(min_value=0.0, max_value=0.001)
    max_drain = fake.pyfloat(min_value=0.01, max_value=0.1)

    schema.define_derived(
        key="drain_per_tick",
        value_type=float,
        formula=drain_formula,
        dependencies=("bot.base_ticks",),
        constraints=ConfigConstraints(min_value=min_drain, max_value=max_drain),
        description="Battery drain per tick",
    )

    assert schema.has_key("bot.drain_per_tick")
    derived = schema.get_key("bot.drain_per_tick")
    assert isinstance(derived, DerivedConfigKey)
    assert derived.type is float
    assert derived.formula is drain_formula
    assert derived.dependencies == ("bot.base_ticks",)
    assert derived.constraints is not None
    assert derived.constraints.min_value == min_drain
    assert derived.constraints.max_value == max_drain
    assert derived.description == "Battery drain per tick"


def test_define_derived_no_namespace() -> None:
    """Test defining derived key without namespace."""
    schema = ConfigSchema()
    base_key = f"{fake.word()}.{fake.word()}"
    derived_key = f"{fake.word()}.{fake.word()}"

    def formula(cfg: ConfigResolver) -> int:
        return int(cfg.get(base_key)) * 2

    schema.define_derived(
        key=derived_key,
        value_type=int,
        formula=formula,
        dependencies=(base_key,),
    )

    assert schema.has_key(derived_key)
    derived = schema.get_key(derived_key)
    assert isinstance(derived, DerivedConfigKey)


def test_register_formula_pattern() -> None:
    """Test registering formula pattern at class level."""
    pattern_name = f"{fake.word()}_pattern"
    dep1 = f"{fake.word()}.{fake.word()}"
    dep2 = f"{fake.word()}.{fake.word()}"

    def factory(mult: float) -> Callable[[ConfigResolver], ConfigValue]:
        def formula(cfg: ConfigResolver) -> float:
            return mult * float(cfg.get(dep1)) / float(cfg.get(dep2))

        return formula

    ConfigSchema.register_formula_pattern(
        name=pattern_name,
        dependencies=(dep1, dep2),
        factory=factory,
    )

    assert ConfigSchema._formula_patterns.has_pattern(pattern_name)


def test_define_derived_from_pattern() -> None:
    """Test defining derived key using registered pattern."""
    pattern_name = f"{fake.word()}_cost_pattern"
    baseline_key = "core.baseline"
    ticks_key = "core.ticks"

    def cost_factory(multiplier: float) -> Callable[[ConfigResolver], ConfigValue]:
        def formula(cfg: ConfigResolver) -> float:
            base = float(cfg.get(baseline_key))
            ticks = float(cfg.get(ticks_key))
            return (multiplier * base) / ticks

        return formula

    ConfigSchema.register_formula_pattern(
        name=pattern_name,
        dependencies=(baseline_key, ticks_key),
        factory=cost_factory,
    )

    schema = ConfigSchema(namespace="bot")
    multiplier = fake.pyfloat(min_value=0.1, max_value=1.0)
    min_cost = fake.pyfloat(min_value=0.0, max_value=0.01)

    schema.define_derived_from_pattern(
        key="battery_cost",
        value_type=float,
        pattern=pattern_name,
        pattern_params={"multiplier": multiplier},
        constraints=ConfigConstraints(min_value=min_cost),
        description="Battery cost per action",
    )

    assert schema.has_key("bot.battery_cost")
    derived = schema.get_key("bot.battery_cost")
    assert isinstance(derived, DerivedConfigKey)
    assert derived.dependencies == (baseline_key, ticks_key)
    assert derived.constraints is not None
    assert derived.constraints.min_value == min_cost
    assert derived.description == "Battery cost per action"


def test_define_derived_from_pattern_no_params() -> None:
    """Test defining derived key from pattern without params."""
    pattern_name = f"{fake.word()}_simple_pattern"
    dep_key = f"{fake.word()}.{fake.word()}"

    def simple_factory() -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: float(cfg.get(dep_key)) * 2.0

    ConfigSchema.register_formula_pattern(
        name=pattern_name,
        dependencies=(dep_key,),
        factory=simple_factory,
    )

    schema = ConfigSchema()
    derived_key = f"{fake.word()}.{fake.word()}"

    schema.define_derived_from_pattern(
        key=derived_key,
        value_type=float,
        pattern=pattern_name,
    )

    assert schema.has_key(derived_key)


def test_validate_dependencies_success() -> None:
    """Test validate_dependencies succeeds with valid dependencies."""
    schema = ConfigSchema()
    base_key = f"{fake.unique.word()}.{fake.unique.word()}"
    derived_key = f"{fake.unique.word()}.{fake.unique.word()}"

    schema.define(key=base_key, value_type=int, value=100)

    def formula(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(base_key)) * 0.5

    schema.define_derived(
        key=derived_key,
        value_type=float,
        formula=formula,
        dependencies=(base_key,),
    )

    schema.validate_dependencies()


def test_validate_dependencies_missing_dependency_raises_error() -> None:
    """Test validate_dependencies raises error for missing dependency."""
    schema = ConfigSchema()
    missing_key = f"{fake.unique.word()}.{fake.unique.word()}"
    derived_key = f"{fake.unique.word()}.{fake.unique.word()}"

    def formula(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(missing_key)) * 2.0

    schema.define_derived(
        key=derived_key,
        value_type=float,
        formula=formula,
        dependencies=(missing_key,),
    )

    with pytest.raises(
        expected_exception=ConfigSchemaError,
        match=f"{derived_key} depends on unknown key: {missing_key}",
    ):
        schema.validate_dependencies()


def test_validate_dependencies_circular_dependency_raises_error() -> None:
    """Test validate_dependencies raises error for circular dependencies."""
    schema = ConfigSchema()
    key1 = f"{fake.word()}.a"
    key2 = f"{fake.word()}.b"
    key3 = f"{fake.word()}.c"

    def formula1(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(key2))

    def formula2(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(key3))

    def formula3(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(key1))

    schema.define_derived(
        key=key1,
        value_type=float,
        formula=formula1,
        dependencies=(key2,),
    )

    schema.define_derived(
        key=key2,
        value_type=float,
        formula=formula2,
        dependencies=(key3,),
    )

    schema.define_derived(
        key=key3,
        value_type=float,
        formula=formula3,
        dependencies=(key1,),
    )

    with pytest.raises(
        expected_exception=ConfigSchemaError,
        match="Circular dependency detected involving",
    ):
        schema.validate_dependencies()


def test_validate_dependencies_self_dependency_raises_error() -> None:
    """Test validate_dependencies raises error for self-dependency."""
    schema = ConfigSchema()
    key = f"{fake.word()}.{fake.word()}"

    def formula(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(key)) * 2.0

    schema.define_derived(
        key=key,
        value_type=float,
        formula=formula,
        dependencies=(key,),
    )

    with pytest.raises(
        expected_exception=ConfigSchemaError,
        match="Circular dependency detected involving",
    ):
        schema.validate_dependencies()


def test_validate_dependencies_multiple_derived_keys() -> None:
    """Test validate_dependencies with multiple derived keys."""
    schema = ConfigSchema()
    base1 = f"{fake.word()}.base1"
    base2 = f"{fake.word()}.base2"
    derived1 = f"{fake.word()}.derived1"
    derived2 = f"{fake.word()}.derived2"

    schema.define(key=base1, value_type=int, value=100)
    schema.define(key=base2, value_type=int, value=200)

    def formula1(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(base1)) * 0.5

    def formula2(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(base2)) + float(cfg.get(derived1))

    schema.define_derived(
        key=derived1,
        value_type=float,
        formula=formula1,
        dependencies=(base1,),
    )

    schema.define_derived(
        key=derived2,
        value_type=float,
        formula=formula2,
        dependencies=(base2, derived1),
    )

    schema.validate_dependencies()
