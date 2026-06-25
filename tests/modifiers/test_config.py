"""Tests for modifier config."""

from dataclasses import FrozenInstanceError

import pytest
from faker import Faker

from yuna.exceptions import ValidationError
from yuna.modifiers.applicator import StatApplicator
from yuna.modifiers.config import (
    CategoryStackingConfig,
    ModifierConfig,
    StackingRule,
    StatConfig,
)
from yuna.modifiers.reader import StatValueReader
from yuna.types.identifiers import EntityID

fake = Faker()


def test_stat_config_creation() -> None:
    """Test StatConfig can be instantiated."""
    config = StatConfig(
        name=fake.word(),
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    assert config is not None


def test_stat_config_has_name() -> None:
    """Test stat config has name."""
    name = fake.word()
    config = StatConfig(
        name=name,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    assert config.name == name


def test_stat_config_has_min_value() -> None:
    """Test stat config has min value."""
    config = StatConfig(
        name=fake.word(),
        min_value=10.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    assert config.min_value == 10.0


def test_stat_config_has_max_value() -> None:
    """Test stat config has max value."""
    config = StatConfig(
        name=fake.word(),
        min_value=0.0,
        max_value=75.0,
        stacking_rule=StackingRule.ADD,
    )
    assert config.max_value == 75.0


def test_stat_config_has_stacking_rule() -> None:
    """Test stat config has stacking rule."""
    config = StatConfig(
        name=fake.word(),
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.MULTIPLY,
    )
    assert config.stacking_rule == StackingRule.MULTIPLY


def test_stat_config_is_immutable() -> None:
    """Test stat config cannot be modified."""
    config = StatConfig(
        name=fake.word(),
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    try:
        config.min_value = 50.0  # type: ignore[misc]
        msg = "Expected FrozenInstanceError"
        raise AssertionError(msg)
    except FrozenInstanceError:
        pass


def test_stat_config_has_precision() -> None:
    """Test stat config has precision."""
    config = StatConfig(
        name=fake.word(),
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
        precision=3,
    )
    assert config.precision == 3


def test_stat_config_precision_defaults_none() -> None:
    """Test stat config precision defaults to None."""
    config = StatConfig(
        name=fake.word(),
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    assert config.precision is None


def test_stacking_rule_has_all_rules() -> None:
    """Test all stacking rules are defined."""
    rules = {r.name for r in StackingRule}
    assert "ADD" in rules
    assert "MULTIPLY" in rules
    assert "MAX" in rules
    assert "MIN" in rules


def test_modifier_config_creation() -> None:
    """Test ModifierConfig can be instantiated."""
    config = ModifierConfig()
    assert config is not None


def test_register_stat() -> None:
    """Test registering a stat."""
    config = ModifierConfig()
    name = fake.word()
    config.register_stat(
        name=name,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    assert config.has_stat(name=name)


def test_get_stat_config() -> None:
    """Test getting registered stat config."""
    config = ModifierConfig()
    name = fake.word()
    config.register_stat(
        name=name,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    stat_config = config.get_stat_config(name=name)
    assert stat_config.name == name


def test_get_nonexistent_stat_raises_error() -> None:
    """Test getting non-existent stat raises KeyError."""
    config = ModifierConfig()
    name = fake.word()

    with pytest.raises(ValidationError, match="not registered"):
        config.get_stat_config(name=name)


def test_has_stat_returns_false_for_missing() -> None:
    """Test has_stat returns False for unregistered stat."""
    config = ModifierConfig()
    assert config.has_stat(name=fake.word()) is False


def test_register_multiple_stats() -> None:
    """Test registering multiple stats."""
    config = ModifierConfig()
    name_1 = fake.unique.word()
    name_2 = fake.unique.word()
    config.register_stat(
        name=name_1,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_stat(
        name=name_2,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.MULTIPLY,
    )
    assert len(config.get_all_stat_names()) == 2


def test_register_overwrites_existing() -> None:
    """Test registering same stat overwrites."""
    config = ModifierConfig()
    name = fake.word()
    config.register_stat(
        name=name,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_stat(
        name=name,
        min_value=10.0,
        max_value=50.0,
        stacking_rule=StackingRule.MULTIPLY,
    )
    stat_config = config.get_stat_config(name=name)
    assert stat_config.min_value == 10.0


def test_clear_config() -> None:
    """Test clearing all stats."""
    config = ModifierConfig()
    config.register_stat(
        name=fake.word(),
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.clear()
    assert len(config.get_all_stat_names()) == 0


def test_get_all_stat_names() -> None:
    """Test getting all registered stat names."""
    config = ModifierConfig()
    name_1 = fake.word()
    name_2 = fake.word()
    config.register_stat(
        name=name_1,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_stat(
        name=name_2,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    names = config.get_all_stat_names()
    assert set(names) == {name_1, name_2}


def test_get_all_stat_names_empty() -> None:
    """Test getting names from empty config."""
    config = ModifierConfig()
    names = config.get_all_stat_names()
    assert names == []


def test_stat_config_with_negative_bounds() -> None:
    """Test stat config with negative bounds."""
    config = StatConfig(
        name=fake.word(),
        min_value=-100.0,
        max_value=-10.0,
        stacking_rule=StackingRule.ADD,
    )
    assert config.min_value == -100.0
    assert config.max_value == -10.0


def test_stat_config_with_zero_bounds() -> None:
    """Test stat config with zero bounds."""
    config = StatConfig(
        name=fake.word(),
        min_value=0.0,
        max_value=0.0,
        stacking_rule=StackingRule.ADD,
    )
    assert config.min_value == 0.0
    assert config.max_value == 0.0


def test_category_stacking_config_creation() -> None:
    """Test CategoryStackingConfig can be instantiated."""
    config = CategoryStackingConfig(
        category=fake.word(),
        stacking_rule=StackingRule.ADD,
    )
    assert config is not None


def test_category_stacking_config_has_category() -> None:
    """Test category stacking config has category."""
    category = fake.word()
    config = CategoryStackingConfig(
        category=category,
        stacking_rule=StackingRule.ADD,
    )
    assert config.category == category


def test_category_stacking_config_has_stacking_rule() -> None:
    """Test category stacking config has stacking rule."""
    config = CategoryStackingConfig(
        category=fake.word(),
        stacking_rule=StackingRule.MULTIPLY,
    )
    assert config.stacking_rule == StackingRule.MULTIPLY


def test_category_stacking_config_has_max_stack_count() -> None:
    """Test category stacking config has max stack count."""
    config = CategoryStackingConfig(
        category=fake.word(),
        stacking_rule=StackingRule.ADD,
        max_stack_count=5,
    )
    assert config.max_stack_count == 5


def test_category_stacking_config_max_stack_count_defaults_none() -> None:
    """Test category stacking config max_stack_count defaults to None."""
    config = CategoryStackingConfig(
        category=fake.word(),
        stacking_rule=StackingRule.ADD,
    )
    assert config.max_stack_count is None


def test_category_stacking_config_has_stack_merge_strategy() -> None:
    """Test category stacking config has stack merge strategy."""
    config = CategoryStackingConfig(
        category=fake.word(),
        stacking_rule=StackingRule.ADD,
        stack_merge_strategy="strongest",
    )
    assert config.stack_merge_strategy == "strongest"


def test_category_stacking_config_stack_merge_strategy_defaults() -> None:
    """Test category stacking config stack_merge_strategy defaults to newest."""
    config = CategoryStackingConfig(
        category=fake.word(),
        stacking_rule=StackingRule.ADD,
    )
    assert config.stack_merge_strategy == "newest"


def test_category_stacking_config_is_immutable() -> None:
    """Test category stacking config cannot be modified."""
    config = CategoryStackingConfig(
        category=fake.word(),
        stacking_rule=StackingRule.ADD,
    )
    try:
        config.max_stack_count = 10  # type: ignore[misc]
        msg = "Expected FrozenInstanceError"
        raise AssertionError(msg)
    except FrozenInstanceError:
        pass


def test_register_category_stacking() -> None:
    """Test registering category stacking config."""
    config = ModifierConfig()
    category = fake.word()
    config.register_category_stacking(
        category=category,
        stacking_rule=StackingRule.ADD,
    )
    assert config.has_category_stacking(category=category)


def test_get_category_stacking() -> None:
    """Test getting category stacking config."""
    config = ModifierConfig()
    category = fake.word()
    config.register_category_stacking(
        category=category,
        stacking_rule=StackingRule.MULTIPLY,
        max_stack_count=3,
    )
    category_config = config.get_category_stacking(category=category)
    assert category_config is not None
    assert category_config.category == category
    assert category_config.stacking_rule == StackingRule.MULTIPLY
    assert category_config.max_stack_count == 3


def test_get_category_stacking_nonexistent_returns_none() -> None:
    """Test get_category_stacking returns None for unregistered category."""
    config = ModifierConfig()
    category_config = config.get_category_stacking(category=fake.word())
    assert category_config is None


def test_has_category_stacking_returns_false_for_missing() -> None:
    """Test has_category_stacking returns False for unregistered category."""
    config = ModifierConfig()
    assert config.has_category_stacking(category=fake.word()) is False


def test_register_category_stacking_overwrites_existing() -> None:
    """Test registering same category overwrites config."""
    config = ModifierConfig()
    category = fake.word()
    config.register_category_stacking(
        category=category,
        stacking_rule=StackingRule.ADD,
        max_stack_count=3,
    )
    config.register_category_stacking(
        category=category,
        stacking_rule=StackingRule.MULTIPLY,
        max_stack_count=5,
    )
    category_config = config.get_category_stacking(category=category)
    assert category_config is not None
    assert category_config.stacking_rule == StackingRule.MULTIPLY
    assert category_config.max_stack_count == 5


def test_register_category_stacking_with_all_fields() -> None:
    """Test registering category stacking with all fields."""
    config = ModifierConfig()
    category = fake.word()
    config.register_category_stacking(
        category=category,
        stacking_rule=StackingRule.MAX,
        max_stack_count=10,
        stack_merge_strategy="sum",
    )
    category_config = config.get_category_stacking(category=category)
    assert category_config is not None
    assert category_config.category == category
    assert category_config.stacking_rule == StackingRule.MAX
    assert category_config.max_stack_count == 10
    assert category_config.stack_merge_strategy == "sum"


def test_category_stacking_independent_of_stats() -> None:
    """Test category stacking config is independent of stat config."""
    config = ModifierConfig()
    stat_name = fake.word()
    category = fake.word()
    config.register_stat(
        name=stat_name,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_category_stacking(
        category=category,
        stacking_rule=StackingRule.MULTIPLY,
    )
    assert config.has_stat(name=stat_name)
    assert config.has_category_stacking(category=category)
    stat_config = config.get_stat_config(name=stat_name)
    category_config = config.get_category_stacking(category=category)
    assert stat_config.stacking_rule == StackingRule.ADD
    assert category_config is not None
    assert category_config.stacking_rule == StackingRule.MULTIPLY


def test_register_applicator() -> None:
    """Test registering stat applicator."""
    config = ModifierConfig()
    stat = fake.word()

    def test_applicator(
        entity_id: EntityID, stat: str, value: float, world: object
    ) -> None:
        pass

    config.register_applicator(stat=stat, applicator=test_applicator)
    assert config.has_applicator(stat=stat)


def test_get_applicator() -> None:
    """Test getting registered applicator."""
    config = ModifierConfig()
    stat = fake.word()

    def test_applicator(
        entity_id: EntityID, stat: str, value: float, world: object
    ) -> None:
        pass

    config.register_applicator(stat=stat, applicator=test_applicator)
    applicator = config.get_applicator(stat=stat)
    assert applicator is test_applicator


def test_get_applicator_nonexistent_returns_none() -> None:
    """Test get_applicator returns None for unregistered stat."""
    config = ModifierConfig()
    applicator = config.get_applicator(stat=fake.word())
    assert applicator is None


def test_has_applicator_returns_false_for_missing() -> None:
    """Test has_applicator returns False for unregistered stat."""
    config = ModifierConfig()
    assert config.has_applicator(stat=fake.word()) is False


def test_register_applicator_overwrites_existing() -> None:
    """Test registering same stat applicator overwrites."""
    config = ModifierConfig()
    stat = fake.word()

    def applicator1(
        entity_id: EntityID, stat: str, value: float, world: object
    ) -> None:
        pass

    def applicator2(
        entity_id: EntityID, stat: str, value: float, world: object
    ) -> None:
        pass

    config.register_applicator(stat=stat, applicator=applicator1)
    config.register_applicator(stat=stat, applicator=applicator2)
    applicator = config.get_applicator(stat=stat)
    assert applicator is applicator2


def test_stat_applicator_protocol_compliance() -> None:
    """Test custom applicator implements StatApplicator protocol."""

    def test_applicator(
        entity_id: EntityID, stat: str, value: float, world: object
    ) -> None:
        pass

    applicator: StatApplicator = test_applicator
    assert callable(applicator)


def test_register_value_reader() -> None:
    """Test registering stat value reader."""
    config = ModifierConfig()
    stat = fake.word()

    def test_reader(entity_id: EntityID, stat: str, world: object) -> float:
        return 0.0

    config.register_value_reader(stat=stat, reader=test_reader)
    assert config.has_value_reader(stat=stat)


def test_get_value_reader() -> None:
    """Test getting registered value reader."""
    config = ModifierConfig()
    stat = fake.word()

    def test_reader(entity_id: EntityID, stat: str, world: object) -> float:
        return 0.0

    config.register_value_reader(stat=stat, reader=test_reader)
    reader = config.get_value_reader(stat=stat)
    assert reader is test_reader


def test_get_value_reader_nonexistent_returns_none() -> None:
    """Test get_value_reader returns None for unregistered stat."""
    config = ModifierConfig()
    reader = config.get_value_reader(stat=fake.word())
    assert reader is None


def test_has_value_reader_returns_false_for_missing() -> None:
    """Test has_value_reader returns False for unregistered stat."""
    config = ModifierConfig()
    assert config.has_value_reader(stat=fake.word()) is False


def test_register_value_reader_overwrites_existing() -> None:
    """Test registering same stat value reader overwrites."""
    config = ModifierConfig()
    stat = fake.word()

    def reader1(entity_id: EntityID, stat: str, world: object) -> float:
        return 1.0

    def reader2(entity_id: EntityID, stat: str, world: object) -> float:
        return 2.0

    config.register_value_reader(stat=stat, reader=reader1)
    config.register_value_reader(stat=stat, reader=reader2)
    reader = config.get_value_reader(stat=stat)
    assert reader is reader2


def test_stat_value_reader_protocol_compliance() -> None:
    """Test custom reader implements StatValueReader protocol."""

    def test_reader(entity_id: EntityID, stat: str, world: object) -> float:
        return 42.0

    reader: StatValueReader = test_reader
    assert callable(reader)


def test_register_interceptor() -> None:
    """Test registering stat interceptor."""
    config = ModifierConfig()
    stat = fake.word()

    def test_interceptor(
        entity_id: EntityID, stat: str, value: float, context: object
    ) -> float:
        return value

    config.register_interceptor(stat=stat, interceptor=test_interceptor)
    assert config.has_interceptor(stat=stat)


def test_get_interceptor() -> None:
    """Test getting registered interceptor."""
    config = ModifierConfig()
    stat = fake.word()

    def test_interceptor(
        entity_id: EntityID, stat: str, value: float, context: object
    ) -> float:
        return value

    config.register_interceptor(stat=stat, interceptor=test_interceptor)
    interceptors = config.get_interceptors(stat=stat)
    assert len(interceptors) == 1
    assert interceptors[0] is test_interceptor


def test_get_interceptor_nonexistent_returns_none() -> None:
    """Test get_interceptors returns empty list for unregistered stat."""
    config = ModifierConfig()
    interceptors = config.get_interceptors(stat=fake.word())
    assert interceptors == []


def test_has_interceptor_returns_false_for_missing() -> None:
    """Test has_interceptor returns False for unregistered stat."""
    config = ModifierConfig()
    assert config.has_interceptor(stat=fake.word()) is False


def test_register_interceptor_overwrites_existing() -> None:
    """Test registering multiple interceptors for same stat chains them."""
    config = ModifierConfig()
    stat = fake.word()

    def interceptor1(
        entity_id: EntityID, stat: str, value: float, context: object
    ) -> float:
        return value

    def interceptor2(
        entity_id: EntityID, stat: str, value: float, context: object
    ) -> float:
        return value * 2

    config.register_interceptor(stat=stat, interceptor=interceptor1)
    config.register_interceptor(stat=stat, interceptor=interceptor2)
    interceptors = config.get_interceptors(stat=stat)
    assert len(interceptors) == 2
    assert interceptors[0] is interceptor1
    assert interceptors[1] is interceptor2
