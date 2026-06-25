"""Integration tests for PermissionValidator with effect modifiers."""

from unittest.mock import Mock

from faker import Faker

from yuna.commands.permissions import (
    ActionPermission,
    ResourceEffect,
    ResourceModificationType,
)
from yuna.commands.validator import PermissionValidator
from yuna.modifiers.config import ModifierConfig, StackingRule
from yuna.modifiers.conventions import EffectModifierConventions
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.types.identifiers import EntityID

fake = Faker()


def create_test_pipeline_with_validator(
    *resource_types: str,
) -> tuple[ModifierConfig, ModifierPipeline, PermissionValidator]:
    """Create pipeline and validator with effect stats registered."""
    config = ModifierConfig()
    for resource_type in resource_types:
        config.register_stat(
            name=f"effect:{resource_type}",
            min_value=float("-inf"),
            max_value=float("inf"),
            stacking_rule=StackingRule.ADD,
        )
    pipeline = ModifierPipeline(config=config)
    validator = PermissionValidator(modifier_pipeline=pipeline)
    return config, pipeline, validator


def test_validator_without_pipeline_validates_base_cost() -> None:
    """Test validator without pipeline uses base effect amounts."""
    validator = PermissionValidator()
    entity_id = EntityID(fake.uuid4())

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-10.0,
            ),
        )
    )

    context = Mock()
    context.get_resource.return_value = 5.0

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is False
    assert "need 10.00" in reason
    assert "have 5.00" in reason


def test_validator_with_pipeline_applies_effect_modifiers() -> None:
    """Test validator with pipeline applies effect modifiers to costs."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity_id = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.50,
        source="efficiency_upgrade",
    )
    pipeline.queue_modifier(modifier=modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-10.0,
            ),
        )
    )

    context = Mock()
    context.get_resource.return_value = 6.0

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True
    assert not reason


def test_validator_with_pipeline_makes_action_affordable() -> None:
    """Test effect modifiers can make unaffordable action affordable."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity_id = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.60,
        source="efficiency_upgrade",
    )
    pipeline.queue_modifier(modifier=modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-25.0,
            ),
        )
    )

    context = Mock()
    context.get_resource.return_value = 12.0

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True


def test_validator_with_pipeline_can_still_fail_validation() -> None:
    """Test effect modifiers don't always make actions affordable."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity_id = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.20,
        source="small_efficiency",
    )
    pipeline.queue_modifier(modifier=modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-50.0,
            ),
        )
    )

    context = Mock()
    context.get_resource.return_value = 20.0

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is False


def test_validator_with_multiple_effect_modifiers_stacks() -> None:
    """Test validator correctly stacks multiple effect modifiers."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity_id = EntityID(fake.uuid4())

    modifier1 = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.25,
        source="upgrade1",
    )
    modifier2 = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.25,
        source="upgrade2",
    )

    pipeline.queue_modifier(modifier=modifier1)
    pipeline.queue_modifier(modifier=modifier2)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-40.0,
            ),
        )
    )

    context = Mock()
    context.get_resource.return_value = 25.0

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True


def test_validator_effect_increase_makes_action_less_affordable() -> None:
    """Test effect increase modifiers make actions more expensive."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity_id = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_increase(
        entity_id=entity_id,
        resource_type="energy",
        increase_percentage=1.0,
        source="overload_penalty",
    )
    pipeline.queue_modifier(modifier=modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-10.0,
            ),
        )
    )

    context = Mock()
    context.get_resource.return_value = 15.0

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is False


def test_validator_with_multiple_resource_types() -> None:
    """Test validator correctly handles multiple resource effects."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity_id = EntityID(fake.uuid4())

    energy_modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.50,
        source="energy_efficiency",
    )
    pipeline.queue_modifier(modifier=energy_modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-20.0,
            ),
            ResourceEffect(
                resource_type="heat",
                modification_type=ResourceModificationType.FLAT,
                amount=-5.0,
            ),
        )
    )

    context = Mock()
    context.get_resource.side_effect = lambda entity_id, resource_type: (
        15.0 if resource_type == "energy" else 3.0
    )

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is False
    assert "heat" in reason


def test_validator_entity_isolation_with_modifiers() -> None:
    """Test modifiers only affect their own entity."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity1,
        resource_type="energy",
        reduction_percentage=0.75,
        source="entity1_efficiency",
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

    context = Mock()
    context.get_resource.return_value = 15.0

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity2,
        permission=permission,
        context=context,
    )

    assert can_afford is False


def test_validator_with_condition_modifier_and_effect_modifier() -> None:
    """Test validator applies both effect modifiers and condition modifiers."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity_id = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.50,
        source="efficiency",
    )
    pipeline.queue_modifier(modifier=modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-20.0,
                condition_modifier=lambda x: x * 0.5,
            ),
        )
    )

    context = Mock()
    context.get_resource.return_value = 6.0

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True


def test_validator_ignores_gains_with_modifiers() -> None:
    """Test validator doesn't validate gains even with modifiers."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity_id = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_increase(
        entity_id=entity_id,
        resource_type="energy",
        increase_percentage=2.0,
        source="amplifier",
    )
    pipeline.queue_modifier(modifier=modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=50.0,
            ),
        )
    )

    context = Mock()
    context.get_resource.return_value = 10.0

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True


def test_validator_with_zero_cost_after_modifier() -> None:
    """Test validator handles cost reduced to zero by modifiers."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity_id = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=1.0,
        source="free_action",
    )
    pipeline.queue_modifier(modifier=modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-100.0,
            ),
        )
    )

    context = Mock()
    context.get_resource.return_value = 5.0

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True


def test_validator_full_permission_check_with_modifiers() -> None:
    """Test validate_permission integrates effect modifiers."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity_id = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.50,
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
        ),
        required_stats={},
        required_tags=frozenset(),
        forbidden_tags=frozenset(),
    )

    context = Mock()
    context.get_resource.return_value = 15.0
    context.get_stat = Mock()
    context.has_tag = Mock(return_value=False)

    can_execute, reason = validator.validate_permission(
        entity_id=entity_id,
        action_id="test_action",
        permission=permission,
        context=context,
        current_tick=0,
    )

    assert can_execute is True


def test_validator_validates_effective_cost_not_base() -> None:
    """Test validator checks effective cost after modifiers, not base cost."""
    config, pipeline, validator = create_test_pipeline_with_validator("energy", "heat")

    entity_id = EntityID(fake.uuid4())

    modifier = EffectModifierConventions.create_effect_reduction(
        entity_id=entity_id,
        resource_type="energy",
        reduction_percentage=0.80,
        source="high_efficiency",
    )
    pipeline.queue_modifier(modifier=modifier)

    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-100.0,
            ),
        )
    )

    context = Mock()
    context.get_resource.return_value = 25.0

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True
