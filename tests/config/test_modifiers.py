"""Tests for config modifiers."""

import pytest
from faker import Faker

from yuna.config.modifiers import (
    ConfigModificationType,
    ConfigModifier,
    ConfigModifierProcessor,
)
from yuna.modifiers.types import ModifierPriority

fake = Faker()


def test_config_modification_type_enum():
    """Test ConfigModificationType enum values."""
    assert ConfigModificationType.SET.value == "set"
    assert ConfigModificationType.ADD.value == "add"
    assert ConfigModificationType.MULTIPLY.value == "multiply"
    assert ConfigModificationType.MAX.value == "max"
    assert ConfigModificationType.MIN.value == "min"


def test_config_modifier_creation():
    """Test ConfigModifier creation."""
    key_name = f"{fake.word()}.{fake.word()}"
    value = fake.random_int(min=1, max=100)

    modifier = ConfigModifier(
        key=key_name,
        value=value,
        modification_type=ConfigModificationType.SET,
        duration_ticks=fake.random_int(min=1, max=1000),
        priority=ModifierPriority.HIGH,
        source=fake.word(),
    )

    assert modifier.key == key_name
    assert modifier.value == value
    assert modifier.modification_type == ConfigModificationType.SET


def test_config_modifier_defaults():
    """Test ConfigModifier default values."""
    modifier = ConfigModifier(
        key=fake.word(),
        value=fake.random_int(),
        modification_type=ConfigModificationType.SET,
    )

    assert modifier.duration_ticks is None
    assert modifier.priority == ModifierPriority.NORMAL
    assert modifier.source == "config_modifier"


def test_config_modifier_frozen():
    """Test ConfigModifier is immutable."""
    modifier = ConfigModifier(
        key=fake.word(),
        value=fake.random_int(),
        modification_type=ConfigModificationType.SET,
    )

    with pytest.raises((AttributeError, TypeError)):
        modifier.value = fake.random_int()  # type: ignore[misc]


def test_config_modifier_apply_set():
    """Test ConfigModifier.apply with SET type."""
    base_value = fake.random_int(min=1, max=100)
    new_value = fake.random_int(min=101, max=200)

    modifier = ConfigModifier(
        key=fake.word(),
        value=new_value,
        modification_type=ConfigModificationType.SET,
    )

    result = modifier.apply(base_value)
    assert result == new_value


def test_config_modifier_apply_add_int():
    """Test ConfigModifier.apply with ADD type for integers."""
    base_value = fake.random_int(min=10, max=50)
    add_value = fake.random_int(min=1, max=20)

    modifier = ConfigModifier(
        key=fake.word(),
        value=add_value,
        modification_type=ConfigModificationType.ADD,
    )

    result = modifier.apply(base_value)
    assert result == base_value + add_value


def test_config_modifier_apply_add_float():
    """Test ConfigModifier.apply with ADD type for floats."""
    base_value = fake.pyfloat(min_value=10.0, max_value=50.0)
    add_value = fake.pyfloat(min_value=1.0, max_value=20.0)

    modifier = ConfigModifier(
        key=fake.word(),
        value=add_value,
        modification_type=ConfigModificationType.ADD,
    )

    result = modifier.apply(base_value)
    assert result == pytest.approx(base_value + add_value)


def test_config_modifier_apply_multiply_int():
    """Test ConfigModifier.apply with MULTIPLY type for integers."""
    base_value = fake.random_int(min=10, max=50)
    multiplier = fake.random_int(min=2, max=5)

    modifier = ConfigModifier(
        key=fake.word(),
        value=multiplier,
        modification_type=ConfigModificationType.MULTIPLY,
    )

    result = modifier.apply(base_value)
    assert result == base_value * multiplier


def test_config_modifier_apply_multiply_float():
    """Test ConfigModifier.apply with MULTIPLY type for floats."""
    base_value = fake.pyfloat(min_value=10.0, max_value=50.0)
    multiplier = fake.pyfloat(min_value=1.1, max_value=3.0)

    modifier = ConfigModifier(
        key=fake.word(),
        value=multiplier,
        modification_type=ConfigModificationType.MULTIPLY,
    )

    result = modifier.apply(base_value)
    assert result == pytest.approx(base_value * multiplier)


def test_config_modifier_apply_max():
    """Test ConfigModifier.apply with MAX type."""
    base_value = fake.random_int(min=10, max=50)
    max_value = fake.random_int(min=51, max=100)

    modifier = ConfigModifier(
        key=fake.word(),
        value=max_value,
        modification_type=ConfigModificationType.MAX,
    )

    result = modifier.apply(base_value)
    assert result == max_value

    lower_value = fake.random_int(min=1, max=9)
    modifier_lower = ConfigModifier(
        key=fake.word(),
        value=lower_value,
        modification_type=ConfigModificationType.MAX,
    )

    result_lower = modifier_lower.apply(base_value)
    assert result_lower == base_value


def test_config_modifier_apply_min():
    """Test ConfigModifier.apply with MIN type."""
    base_value = fake.random_int(min=50, max=100)
    min_value = fake.random_int(min=1, max=49)

    modifier = ConfigModifier(
        key=fake.word(),
        value=min_value,
        modification_type=ConfigModificationType.MIN,
    )

    result = modifier.apply(base_value)
    assert result == min_value

    higher_value = fake.random_int(min=101, max=200)
    modifier_higher = ConfigModifier(
        key=fake.word(),
        value=higher_value,
        modification_type=ConfigModificationType.MIN,
    )

    result_higher = modifier_higher.apply(base_value)
    assert result_higher == base_value


def test_config_modifier_processor_creation():
    """Test ConfigModifierProcessor creation."""
    processor = ConfigModifierProcessor()
    assert processor is not None


def test_config_modifier_processor_empty_modifiers():
    """Test ConfigModifierProcessor with empty modifiers list."""
    processor = ConfigModifierProcessor()
    base_value = fake.random_int(min=1, max=100)

    result = processor.apply_modifiers(base_value=base_value, modifiers=[])

    assert result == base_value


def test_config_modifier_processor_single_modifier():
    """Test ConfigModifierProcessor with single modifier."""
    processor = ConfigModifierProcessor()
    base_value = fake.random_int(min=10, max=50)
    add_value = fake.random_int(min=1, max=20)

    modifier = ConfigModifier(
        key=fake.word(),
        value=add_value,
        modification_type=ConfigModificationType.ADD,
    )

    result = processor.apply_modifiers(base_value=base_value, modifiers=[modifier])

    assert result == base_value + add_value


def test_config_modifier_processor_multiple_modifiers():
    """Test ConfigModifierProcessor with multiple modifiers."""
    processor = ConfigModifierProcessor()
    base_value = 100

    modifier1 = ConfigModifier(
        key=fake.word(),
        value=20,
        modification_type=ConfigModificationType.ADD,
        priority=ModifierPriority.NORMAL,
    )

    modifier2 = ConfigModifier(
        key=fake.word(),
        value=2,
        modification_type=ConfigModificationType.MULTIPLY,
        priority=ModifierPriority.NORMAL,
    )

    result = processor.apply_modifiers(
        base_value=base_value, modifiers=[modifier1, modifier2]
    )

    assert result == (100 + 20) * 2


def test_config_modifier_processor_priority_order():
    """Test ConfigModifierProcessor applies modifiers in priority order."""
    processor = ConfigModifierProcessor()
    base_value = 10

    low_priority = ConfigModifier(
        key=fake.word(),
        value=5,
        modification_type=ConfigModificationType.ADD,
        priority=ModifierPriority.LOW,
    )

    high_priority = ConfigModifier(
        key=fake.word(),
        value=2,
        modification_type=ConfigModificationType.MULTIPLY,
        priority=ModifierPriority.HIGH,
    )

    normal_priority = ConfigModifier(
        key=fake.word(),
        value=3,
        modification_type=ConfigModificationType.ADD,
        priority=ModifierPriority.NORMAL,
    )

    result = processor.apply_modifiers(
        base_value=base_value,
        modifiers=[low_priority, high_priority, normal_priority],
    )

    assert result == ((10 * 2) + 3) + 5


def test_config_modifier_processor_critical_priority():
    """Test ConfigModifierProcessor with CRITICAL priority."""
    processor = ConfigModifierProcessor()
    base_value = 100

    critical = ConfigModifier(
        key=fake.word(),
        value=50,
        modification_type=ConfigModificationType.SET,
        priority=ModifierPriority.CRITICAL,
    )

    normal = ConfigModifier(
        key=fake.word(),
        value=2,
        modification_type=ConfigModificationType.MULTIPLY,
        priority=ModifierPriority.NORMAL,
    )

    result = processor.apply_modifiers(
        base_value=base_value, modifiers=[normal, critical]
    )

    assert result == 50 * 2


def test_config_modifier_processor_same_priority_preserves_order():
    """Test ConfigModifierProcessor preserves order for same priority."""
    processor = ConfigModifierProcessor()
    base_value = 10

    modifier1 = ConfigModifier(
        key=fake.word(),
        value=5,
        modification_type=ConfigModificationType.ADD,
        priority=ModifierPriority.NORMAL,
    )

    modifier2 = ConfigModifier(
        key=fake.word(),
        value=3,
        modification_type=ConfigModificationType.ADD,
        priority=ModifierPriority.NORMAL,
    )

    result = processor.apply_modifiers(
        base_value=base_value, modifiers=[modifier1, modifier2]
    )

    assert result == 10 + 5 + 3


def test_config_modifier_buff_pattern():
    """Test config modifier for buff pattern."""
    processor = ConfigModifierProcessor()
    base_speed = 5.0

    speed_boost = ConfigModifier(
        key="movement.speed",
        value=1.5,
        modification_type=ConfigModificationType.MULTIPLY,
        duration_ticks=300,
        priority=ModifierPriority.HIGH,
        source="speed_potion",
    )

    boosted_speed = processor.apply_modifiers(
        base_value=base_speed, modifiers=[speed_boost]
    )

    assert boosted_speed == 7.5


def test_config_modifier_debuff_pattern():
    """Test config modifier for debuff pattern."""
    processor = ConfigModifierProcessor()
    base_range = 50.0

    sensor_damage = ConfigModifier(
        key="sensor.range",
        value=0.7,
        modification_type=ConfigModificationType.MULTIPLY,
        duration_ticks=None,
        priority=ModifierPriority.HIGH,
        source="sensor_damage",
    )

    damaged_range = processor.apply_modifiers(
        base_value=base_range, modifiers=[sensor_damage]
    )

    assert damaged_range == pytest.approx(35.0)


def test_config_modifier_stacking_pattern():
    """Test multiple modifiers stacking."""
    processor = ConfigModifierProcessor()
    base_damage = 100

    equipment_bonus = ConfigModifier(
        key="stats.damage",
        value=50,
        modification_type=ConfigModificationType.ADD,
        priority=ModifierPriority.NORMAL,
        source="legendary_sword",
    )

    buff_multiplier = ConfigModifier(
        key="stats.damage",
        value=1.2,
        modification_type=ConfigModificationType.MULTIPLY,
        priority=ModifierPriority.HIGH,
        source="damage_buff",
    )

    critical_bonus = ConfigModifier(
        key="stats.damage",
        value=2.0,
        modification_type=ConfigModificationType.MULTIPLY,
        priority=ModifierPriority.CRITICAL,
        source="critical_hit",
    )

    final_damage = processor.apply_modifiers(
        base_value=base_damage,
        modifiers=[equipment_bonus, buff_multiplier, critical_bonus],
    )

    assert final_damage == ((100 * 2.0) * 1.2) + 50


def test_config_modifier_cap_pattern():
    """Test using MAX modifier to cap values."""
    processor = ConfigModifierProcessor()
    base_value = 10

    minimum_cap = ConfigModifier(
        key="cache.size",
        value=16,
        modification_type=ConfigModificationType.MAX,
        priority=ModifierPriority.HIGH,
        source="minimum_requirement",
    )

    result = processor.apply_modifiers(base_value=base_value, modifiers=[minimum_cap])

    assert result == 16
