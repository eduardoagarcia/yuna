"""Tests for EffectModifierConventions helper class."""

from faker import Faker

from yuna.modifiers.conventions import EffectModifierConventions
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.types.identifiers import EntityID

fake = Faker()


def test_effect_stat_name_returns_formatted_stat() -> None:
    """Test effect_stat_name returns correct format."""
    resource_type = fake.word()

    result = EffectModifierConventions.effect_stat_name(resource_type=resource_type)

    assert result == f"effect:{resource_type}"


def test_effect_stat_name_with_different_resource_types() -> None:
    """Test effect_stat_name with various resource types."""
    energy_stat = EffectModifierConventions.effect_stat_name(resource_type="energy")
    heat_stat = EffectModifierConventions.effect_stat_name(resource_type="heat")
    fuel_stat = EffectModifierConventions.effect_stat_name(resource_type="fuel")

    assert energy_stat == "effect:energy"
    assert heat_stat == "effect:heat"
    assert fuel_stat == "effect:fuel"


def test_all_effects_stat_name_returns_global_stat() -> None:
    """Test all_effects_stat_name returns global modifier stat."""
    result = EffectModifierConventions.all_effects_stat_name()

    assert result == "effect:all"


def test_create_effect_reduction_creates_percentage_modifier() -> None:
    """Test create_effect_reduction creates percentage modifier with negative value."""
    entity_id = EntityID(fake.uuid4())
    resource_type = fake.word()
    reduction = fake.pyfloat(min_value=0.01, max_value=1.0)
    source = fake.word()

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type=resource_type,
        reduction_percentage=reduction,
        source=source,
    )

    assert modifier.entity_id == entity_id
    assert modifier.stat == f"effect:{resource_type}"
    assert modifier.modification_type == ModificationType.PERCENTAGE
    assert modifier.value == -reduction
    assert modifier.priority == ModifierPriority.NORMAL
    assert modifier.source == source


def test_create_effect_reduction_includes_default_tags() -> None:
    """Test create_effect_reduction has effect_modifier and effect_reduction tags."""
    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=EntityID(fake.uuid4()),
        resource_type=fake.word(),
        reduction_percentage=0.25,
        source=fake.word(),
    )

    assert "effect_modifier" in modifier.tags
    assert "effect_reduction" in modifier.tags


def test_create_effect_reduction_preserves_custom_tags() -> None:
    """Test create_effect_reduction preserves custom tags while adding defaults."""
    custom_tags = frozenset({fake.word(), fake.word()})

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=EntityID(fake.uuid4()),
        resource_type=fake.word(),
        reduction_percentage=0.25,
        source=fake.word(),
        tags=custom_tags,
    )

    assert "effect_modifier" in modifier.tags
    assert "effect_reduction" in modifier.tags
    for tag in custom_tags:
        assert tag in modifier.tags


def test_create_effect_reduction_accepts_additional_kwargs() -> None:
    """Test create_effect_reduction accepts additional modifier arguments."""
    duration = fake.random_int(min=1, max=1000)
    category = fake.word()

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=EntityID(fake.uuid4()),
        resource_type=fake.word(),
        reduction_percentage=0.25,
        source=fake.word(),
        duration_ticks=duration,
        categories=(category,),
    )

    assert modifier.duration_ticks == duration
    assert modifier.categories == (category,)


def test_create_effect_increase_creates_percentage_modifier() -> None:
    """Test create_effect_increase creates percentage modifier with positive value."""
    entity_id = EntityID(fake.uuid4())
    resource_type = fake.word()
    increase = fake.pyfloat(min_value=0.01, max_value=1.0)
    source = fake.word()

    modifier = EffectModifierConventions.create_effect_increase(
        entity_id=entity_id,
        resource_type=resource_type,
        increase_percentage=increase,
        source=source,
    )

    assert modifier.entity_id == entity_id
    assert modifier.stat == f"effect:{resource_type}"
    assert modifier.modification_type == ModificationType.PERCENTAGE
    assert modifier.value == increase
    assert modifier.priority == ModifierPriority.NORMAL
    assert modifier.source == source


def test_create_effect_increase_includes_default_tags() -> None:
    """Test create_effect_increase includes effect_modifier and effect_increase tags."""
    modifier = EffectModifierConventions.create_effect_increase(
        entity_id=EntityID(fake.uuid4()),
        resource_type=fake.word(),
        increase_percentage=0.30,
        source=fake.word(),
    )

    assert "effect_modifier" in modifier.tags
    assert "effect_increase" in modifier.tags


def test_create_effect_increase_preserves_custom_tags() -> None:
    """Test create_effect_increase preserves custom tags while adding defaults."""
    custom_tags = frozenset({fake.word(), fake.word()})

    modifier = EffectModifierConventions.create_effect_increase(
        entity_id=EntityID(fake.uuid4()),
        resource_type=fake.word(),
        increase_percentage=0.30,
        source=fake.word(),
        tags=custom_tags,
    )

    assert "effect_modifier" in modifier.tags
    assert "effect_increase" in modifier.tags
    for tag in custom_tags:
        assert tag in modifier.tags


def test_create_effect_increase_accepts_additional_kwargs() -> None:
    """Test create_effect_increase accepts additional modifier arguments."""
    duration = fake.random_int(min=1, max=1000)
    category = fake.word()

    modifier = EffectModifierConventions.create_effect_increase(
        entity_id=EntityID(fake.uuid4()),
        resource_type=fake.word(),
        increase_percentage=0.30,
        source=fake.word(),
        duration_ticks=duration,
        categories=(category,),
    )

    assert modifier.duration_ticks == duration
    assert modifier.categories == (category,)


def test_is_effect_modifier_returns_true_for_effect_stat() -> None:
    """Test is_effect_modifier returns True for effect: prefixed stats."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat="effect:energy",
        modification_type=ModificationType.PERCENTAGE,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    assert EffectModifierConventions.is_effect_modifier(modifier) is True


def test_is_effect_modifier_returns_true_for_all_effects() -> None:
    """Test is_effect_modifier returns True for effect:all."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat="effect:all",
        modification_type=ModificationType.PERCENTAGE,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    assert EffectModifierConventions.is_effect_modifier(modifier) is True


def test_is_effect_modifier_returns_false_for_non_effect_stat() -> None:
    """Test is_effect_modifier returns False for non-effect stats."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat="health",
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    assert EffectModifierConventions.is_effect_modifier(modifier) is False


def test_is_effect_modifier_returns_false_for_partial_match() -> None:
    """Test is_effect_modifier returns False for stats w 'effect' but not prefixed."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat="side_effect_damage",
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    assert EffectModifierConventions.is_effect_modifier(modifier) is False


def test_create_effect_reduction_with_zero_reduction() -> None:
    """Test create_effect_reduction handles zero reduction."""
    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=EntityID(fake.uuid4()),
        resource_type=fake.word(),
        reduction_percentage=0.0,
        source=fake.word(),
    )

    assert modifier.value == 0.0


def test_create_effect_increase_with_zero_increase() -> None:
    """Test create_effect_increase handles zero increase."""
    modifier = EffectModifierConventions.create_effect_increase(
        entity_id=EntityID(fake.uuid4()),
        resource_type=fake.word(),
        increase_percentage=0.0,
        source=fake.word(),
    )

    assert modifier.value == 0.0


def test_create_effect_reduction_with_high_reduction() -> None:
    """Test create_effect_reduction handles high reduction values."""
    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=EntityID(fake.uuid4()),
        resource_type=fake.word(),
        reduction_percentage=0.99,
        source=fake.word(),
    )

    assert modifier.value == -0.99


def test_create_effect_increase_with_high_increase() -> None:
    """Test create_effect_increase handles high increase values."""
    modifier = EffectModifierConventions.create_effect_increase(
        entity_id=EntityID(fake.uuid4()),
        resource_type=fake.word(),
        increase_percentage=2.0,
        source=fake.word(),
    )

    assert modifier.value == 2.0
