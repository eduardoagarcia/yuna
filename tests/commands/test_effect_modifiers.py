"""Tests for EffectModifierProcessor."""

from unittest.mock import Mock

from faker import Faker

from yuna.commands.effect_modifiers import EffectModifierProcessor
from yuna.commands.permissions import (
    ActionPermission,
    ResourceEffect,
    ResourceModificationType,
)
from yuna.modifiers.config import ModifierConfig, StackingRule
from yuna.modifiers.conventions import EffectModifierConventions
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.types.identifiers import EntityID

fake = Faker()


def create_test_pipeline(
    *resource_types: str,
) -> tuple[ModifierConfig, ModifierPipeline]:
    """Create pipeline with effect stats registered for given resource types."""

    config = ModifierConfig()
    for resource_type in resource_types:
        config.register_stat(
            name=f"effect:{resource_type}",
            min_value=float("-inf"),
            max_value=float("inf"),
            stacking_rule=StackingRule.ADD,
        )
    pipeline = ModifierPipeline(config=config)
    return config, pipeline


def test_calculate_effective_effect_with_no_modifiers() -> None:
    """Test calculate_effective_effect returns base amount when no modifiers applied."""
    entity_id = EntityID(fake.uuid4())
    resource_type = fake.word()

    config, pipeline = create_test_pipeline(resource_type)
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)
    base_amount = fake.pyfloat(min_value=-100.0, max_value=100.0)

    effect = ResourceEffect(
        resource_type=resource_type,
        modification_type=ResourceModificationType.FLAT,
        amount=base_amount,
    )

    result = processor.calculate_effective_effect(
        entity_id=entity_id,
        base_effect=effect,
        context=Mock(),
    )

    assert result == base_amount


def test_calculate_effective_effect_with_percentage_reduction() -> None:
    """Test calculate_effective_effect applies percentage reduction modifier."""
    entity_id = EntityID(fake.uuid4())
    resource_type = fake.word()
    base_amount = -10.0

    config, pipeline = create_test_pipeline(resource_type)
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)

    reduction_modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type=resource_type,
        reduction_percentage=0.25,
        source="efficiency_upgrade",
    )
    pipeline.queue_modifier(modifier=reduction_modifier)

    effect = ResourceEffect(
        resource_type=resource_type,
        modification_type=ResourceModificationType.FLAT,
        amount=base_amount,
    )

    result = processor.calculate_effective_effect(
        entity_id=entity_id,
        base_effect=effect,
        context=Mock(),
    )

    assert result == -7.5


def test_calculate_effective_effect_with_percentage_increase() -> None:
    """Test calculate_effective_effect applies percentage increase modifier."""
    entity_id = EntityID(fake.uuid4())
    resource_type = fake.word()

    config, pipeline = create_test_pipeline(resource_type)
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)
    base_amount = 5.0

    increase_modifier = EffectModifierConventions.create_effect_increase(
        entity_id=entity_id,
        resource_type=resource_type,
        increase_percentage=0.30,
        source="overclocking_penalty",
    )
    pipeline.queue_modifier(modifier=increase_modifier)

    effect = ResourceEffect(
        resource_type=resource_type,
        modification_type=ResourceModificationType.FLAT,
        amount=base_amount,
    )

    result = processor.calculate_effective_effect(
        entity_id=entity_id,
        base_effect=effect,
        context=Mock(),
    )

    assert result == 6.5


def test_calculate_effective_effect_with_multiple_modifiers() -> None:
    """Test calculate_effective_effect stacks multiple modifiers."""
    entity_id = EntityID(fake.uuid4())
    resource_type = fake.word()

    config, pipeline = create_test_pipeline(resource_type)
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)
    base_amount = -20.0

    modifier1 = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type=resource_type,
        reduction_percentage=0.25,
        source="upgrade1",
    )
    modifier2 = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type=resource_type,
        reduction_percentage=0.15,
        source="upgrade2",
    )

    pipeline.queue_modifier(modifier=modifier1)
    pipeline.queue_modifier(modifier=modifier2)

    effect = ResourceEffect(
        resource_type=resource_type,
        modification_type=ResourceModificationType.FLAT,
        amount=base_amount,
    )

    result = processor.calculate_effective_effect(
        entity_id=entity_id,
        base_effect=effect,
        context=Mock(),
    )

    assert result == -12.0


def test_calculate_effective_effect_affects_different_resource_types() -> None:
    """Test calculate_effective_effect only affects matching resource type."""
    config, pipeline = create_test_pipeline("energy", "heat")
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)

    entity_id = EntityID(fake.uuid4())

    energy_modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.25,
        source="energy_efficiency",
    )
    pipeline.queue_modifier(modifier=energy_modifier)

    heat_effect = ResourceEffect(
        resource_type="heat",
        modification_type=ResourceModificationType.FLAT,
        amount=10.0,
    )

    result = processor.calculate_effective_effect(
        entity_id=entity_id,
        base_effect=heat_effect,
        context=Mock(),
    )

    assert result == 10.0


def test_calculate_effective_effect_with_negative_cost() -> None:
    """Test calculate_effective_effect handles negative costs (energy consumption)."""
    entity_id = EntityID(fake.uuid4())
    resource_type = fake.word()

    config, pipeline = create_test_pipeline(resource_type)
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)

    reduction_modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type=resource_type,
        reduction_percentage=0.50,
        source="efficiency",
    )
    pipeline.queue_modifier(modifier=reduction_modifier)

    effect = ResourceEffect(
        resource_type=resource_type,
        modification_type=ResourceModificationType.FLAT,
        amount=-30.0,
    )

    result = processor.calculate_effective_effect(
        entity_id=entity_id,
        base_effect=effect,
        context=Mock(),
    )

    assert result == -15.0


def test_calculate_effective_effect_with_positive_gain() -> None:
    """Test calculate_effective_effect handles positive gains (resource generation)."""
    entity_id = EntityID(fake.uuid4())
    resource_type = fake.word()

    config, pipeline = create_test_pipeline(resource_type)
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)

    increase_modifier = EffectModifierConventions.create_effect_increase(
        entity_id=entity_id,
        resource_type=resource_type,
        increase_percentage=0.50,
        source="amplifier",
    )
    pipeline.queue_modifier(modifier=increase_modifier)

    effect = ResourceEffect(
        resource_type=resource_type,
        modification_type=ResourceModificationType.FLAT,
        amount=20.0,
    )

    result = processor.calculate_effective_effect(
        entity_id=entity_id,
        base_effect=effect,
        context=Mock(),
    )

    assert result == 30.0


def test_get_effect_breakdown_returns_breakdown_for_all_effects() -> None:
    """Test get_effect_breakdown returns breakdown for all resource effects."""
    config, pipeline = create_test_pipeline("energy", "heat")
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)

    entity_id = EntityID(fake.uuid4())

    energy_modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.25,
        source="efficiency",
    )
    pipeline.queue_modifier(modifier=energy_modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-10.0,
            ),
            ResourceEffect(
                resource_type="heat",
                modification_type=ResourceModificationType.FLAT,
                amount=5.0,
            ),
        )
    )

    result = processor.get_effect_breakdown(
        entity_id=entity_id,
        permission=permission,
        context=Mock(),
    )

    assert "energy" in result
    assert "heat" in result
    assert result["energy"]["base"] == -10.0
    assert result["energy"]["final"] == -7.5
    assert result["heat"]["base"] == 5.0
    assert result["heat"]["final"] == 5.0


def test_get_effect_breakdown_calculates_reduction_percentage() -> None:
    """Test get_effect_breakdown calculates reduction percentage correctly."""
    config, pipeline = create_test_pipeline("energy", "heat")
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)

    entity_id = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.30,
        source="efficiency",
    )
    pipeline.queue_modifier(modifier=modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-20.0,
            ),
        )
    )

    result = processor.get_effect_breakdown(
        entity_id=entity_id,
        permission=permission,
        context=Mock(),
    )

    assert result["energy"]["reduction_pct"] == 30.0


def test_get_effect_breakdown_handles_zero_base_amount() -> None:
    """Test get_effect_breakdown handles zero base amount without division error."""
    config, pipeline = create_test_pipeline("energy", "heat")
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)

    entity_id = EntityID(fake.uuid4())

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=0.0,
            ),
        )
    )

    result = processor.get_effect_breakdown(
        entity_id=entity_id,
        permission=permission,
        context=Mock(),
    )

    assert result["energy"]["reduction_pct"] == 0.0


def test_calculate_all_effective_effects_returns_all_effects() -> None:
    """Test calculate_all_effective_effects returns all resource effects."""
    config, pipeline = create_test_pipeline("energy", "heat")
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)

    entity_id = EntityID(fake.uuid4())

    energy_modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.25,
        source="efficiency",
    )
    pipeline.queue_modifier(modifier=energy_modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-10.0,
            ),
            ResourceEffect(
                resource_type="heat",
                modification_type=ResourceModificationType.FLAT,
                amount=5.0,
            ),
        )
    )

    result = processor.calculate_all_effective_effects(
        entity_id=entity_id,
        permission=permission,
        context=Mock(),
    )

    assert len(result) == 2
    assert ("energy", -7.5) in result
    assert ("heat", 5.0) in result


def test_calculate_effective_effect_with_flat_modifier() -> None:
    """Test calculate_effective_effect works with flat modifiers."""
    entity_id = EntityID(fake.uuid4())
    resource_type = fake.word()

    config, pipeline = create_test_pipeline(resource_type)
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)
    base_amount = -20.0

    flat_modifier = Modifier(
        entity_id=entity_id,
        stat=EffectModifierConventions.effect_stat_name(resource_type),
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source="flat_bonus",
    )
    pipeline.queue_modifier(modifier=flat_modifier)

    effect = ResourceEffect(
        resource_type=resource_type,
        modification_type=ResourceModificationType.FLAT,
        amount=base_amount,
    )

    result = processor.calculate_effective_effect(
        entity_id=entity_id,
        base_effect=effect,
        context=Mock(),
    )

    assert result == -15.0


def test_calculate_effective_effect_with_multiplier_modifier() -> None:
    """Test calculate_effective_effect works with multiplier modifiers."""
    entity_id = EntityID(fake.uuid4())
    resource_type = fake.word()

    config, pipeline = create_test_pipeline(resource_type)
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)
    base_amount = -10.0

    multiplier_modifier = Modifier(
        entity_id=entity_id,
        stat=EffectModifierConventions.effect_stat_name(resource_type),
        modification_type=ModificationType.MULTIPLIER,
        value=0.5,
        priority=ModifierPriority.NORMAL,
        source="half_cost",
    )
    pipeline.queue_modifier(modifier=multiplier_modifier)

    effect = ResourceEffect(
        resource_type=resource_type,
        modification_type=ResourceModificationType.FLAT,
        amount=base_amount,
    )

    result = processor.calculate_effective_effect(
        entity_id=entity_id,
        base_effect=effect,
        context=Mock(),
    )

    assert result == -5.0


def test_calculate_effective_effect_different_entities_isolated() -> None:
    """Test calculate_effective_effect modifiers only affect their own entity."""
    config, pipeline = create_test_pipeline("energy", "heat")
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    resource_type = fake.word()

    modifier1 = EffectModifierConventions.create_effect_reduction(
        entity_id=entity1,
        resource_type=resource_type,
        reduction_percentage=0.50,
        source="entity1_efficiency",
    )
    pipeline.queue_modifier(modifier=modifier1)

    effect = ResourceEffect(
        resource_type=resource_type,
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )

    result = processor.calculate_effective_effect(
        entity_id=entity2,
        base_effect=effect,
        context=Mock(),
    )

    assert result == -10.0


def test_get_effect_breakdown_with_increase_shows_negative_reduction() -> None:
    """Test get_effect_breakdown shows negative reduction percentage for increases."""
    config, pipeline = create_test_pipeline("energy", "heat")
    processor = EffectModifierProcessor(modifier_pipeline=pipeline)

    entity_id = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_increase(
        entity_id=entity_id,
        resource_type="heat",
        increase_percentage=0.50,
        source="overheating",
    )
    pipeline.queue_modifier(modifier=modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="heat",
                modification_type=ResourceModificationType.FLAT,
                amount=10.0,
            ),
        )
    )

    result = processor.get_effect_breakdown(
        entity_id=entity_id,
        permission=permission,
        context=Mock(),
    )

    assert result["heat"]["base"] == 10.0
    assert result["heat"]["final"] == 15.0
    assert result["heat"]["reduction_pct"] == -50.0
