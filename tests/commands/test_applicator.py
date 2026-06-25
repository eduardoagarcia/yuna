"""Tests for ResourceEffectApplicator."""

from unittest.mock import Mock

from faker import Faker

from yuna.commands.applicator import ResourceEffectApplicator
from yuna.commands.permissions import (
    ActionPermission,
    ResourceEffect,
    ResourceModificationType,
)
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.types.identifiers import EntityID

fake = Faker()


def test_apply_effects_with_no_effects() -> None:
    """Test applying permission with no resource effects is a no-op."""
    entity_id = EntityID(fake.uuid4())
    permission = ActionPermission()
    context = Mock()

    ResourceEffectApplicator.apply_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    context.modifiers.queue_modifier.assert_not_called()


def test_apply_effects_with_single_flat_cost() -> None:
    """Test applying single flat resource cost."""
    entity_id = EntityID(fake.uuid4())
    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="battery",
                modification_type=ResourceModificationType.FLAT,
                amount=-0.5,
            ),
        )
    )
    context = Mock()

    ResourceEffectApplicator.apply_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
        source="test_command",
    )

    context.modifiers.queue_modifier.assert_called_once()
    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.entity_id == entity_id
    assert modifier.stat == "battery"
    assert modifier.modification_type == ModificationType.FLAT
    assert modifier.value == -0.5
    assert modifier.priority == ModifierPriority.NORMAL
    assert modifier.source == "test_command"


def test_apply_effects_with_multiple_effects() -> None:
    """Test applying multiple resource effects."""
    entity_id = EntityID(fake.uuid4())
    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="battery",
                modification_type=ResourceModificationType.FLAT,
                amount=-0.3,
            ),
            ResourceEffect(
                resource_type="temperature",
                modification_type=ResourceModificationType.FLAT,
                amount=0.2,
            ),
            ResourceEffect(
                resource_type="health",
                modification_type=ResourceModificationType.PERCENTAGE,
                amount=-0.1,
            ),
        )
    )
    context = Mock()

    ResourceEffectApplicator.apply_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert context.modifiers.queue_modifier.call_count == 3

    calls = context.modifiers.queue_modifier.call_args_list
    battery_modifier = calls[0].kwargs["modifier"]
    temp_modifier = calls[1].kwargs["modifier"]
    health_modifier = calls[2].kwargs["modifier"]

    assert battery_modifier.stat == "battery"
    assert battery_modifier.value == -0.3
    assert battery_modifier.modification_type == ModificationType.FLAT

    assert temp_modifier.stat == "temperature"
    assert temp_modifier.value == 0.2
    assert temp_modifier.modification_type == ModificationType.FLAT

    assert health_modifier.stat == "health"
    assert health_modifier.value == -0.1
    assert health_modifier.modification_type == ModificationType.PERCENTAGE


def test_apply_effects_with_custom_stat_map() -> None:
    """Test applying effects with custom stat name mapping."""
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
    stat_map = {"energy": "battery"}

    ResourceEffectApplicator.apply_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
        stat_map=stat_map,
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.stat == "battery"
    assert modifier.value == -10.0


def test_apply_effects_with_set_modification_type() -> None:
    """Test applying effect with SET modification type."""
    entity_id = EntityID(fake.uuid4())
    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="battery",
                modification_type=ResourceModificationType.SET,
                amount=1.0,
            ),
        )
    )
    context = Mock()

    ResourceEffectApplicator.apply_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.modification_type == ModificationType.SET
    assert modifier.value == 1.0


def test_apply_effects_with_multiplier_modification_type() -> None:
    """Test applying effect with MULTIPLIER modification type."""
    entity_id = EntityID(fake.uuid4())
    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="damage",
                modification_type=ResourceModificationType.MULTIPLIER,
                amount=1.5,
            ),
        )
    )
    context = Mock()

    ResourceEffectApplicator.apply_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.modification_type == ModificationType.MULTIPLIER
    assert modifier.value == 1.5


def test_apply_single_effect_flat() -> None:
    """Test applying single effect with FLAT modification."""
    entity_id = EntityID(fake.uuid4())
    context = Mock()

    ResourceEffectApplicator.apply_single_effect(
        entity_id=entity_id,
        resource_type="battery",
        modification_type=ResourceModificationType.FLAT,
        amount=-0.5,
        context=context,
        source="movement",
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.entity_id == entity_id
    assert modifier.stat == "battery"
    assert modifier.modification_type == ModificationType.FLAT
    assert modifier.value == -0.5
    assert modifier.source == "movement"


def test_apply_single_effect_with_custom_stat_name() -> None:
    """Test applying single effect with custom stat name."""
    entity_id = EntityID(fake.uuid4())
    context = Mock()

    ResourceEffectApplicator.apply_single_effect(
        entity_id=entity_id,
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-5.0,
        context=context,
        stat_name="battery",
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.stat == "battery"
    assert modifier.value == -5.0


def test_apply_single_effect_percentage() -> None:
    """Test applying single effect with PERCENTAGE modification."""
    entity_id = EntityID(fake.uuid4())
    context = Mock()

    ResourceEffectApplicator.apply_single_effect(
        entity_id=entity_id,
        resource_type="health",
        modification_type=ResourceModificationType.PERCENTAGE,
        amount=-0.25,
        context=context,
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.modification_type == ModificationType.PERCENTAGE
    assert modifier.value == -0.25


def test_apply_single_effect_set() -> None:
    """Test applying single effect with SET modification."""
    entity_id = EntityID(fake.uuid4())
    context = Mock()

    ResourceEffectApplicator.apply_single_effect(
        entity_id=entity_id,
        resource_type="shield",
        modification_type=ResourceModificationType.SET,
        amount=100.0,
        context=context,
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.modification_type == ModificationType.SET
    assert modifier.value == 100.0


def test_apply_single_effect_multiplier() -> None:
    """Test applying single effect with MULTIPLIER modification."""
    entity_id = EntityID(fake.uuid4())
    context = Mock()

    ResourceEffectApplicator.apply_single_effect(
        entity_id=entity_id,
        resource_type="speed",
        modification_type=ResourceModificationType.MULTIPLIER,
        amount=2.0,
        context=context,
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.modification_type == ModificationType.MULTIPLIER
    assert modifier.value == 2.0


def test_apply_effects_default_source() -> None:
    """Test applying effects uses default source when not specified."""
    entity_id = EntityID(fake.uuid4())
    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="battery",
                modification_type=ResourceModificationType.FLAT,
                amount=-1.0,
            ),
        )
    )
    context = Mock()

    ResourceEffectApplicator.apply_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.source == "command"


def test_apply_single_effect_default_source() -> None:
    """Test applying single effect uses default source when not specified."""
    entity_id = EntityID(fake.uuid4())
    context = Mock()

    ResourceEffectApplicator.apply_single_effect(
        entity_id=entity_id,
        resource_type="battery",
        modification_type=ResourceModificationType.FLAT,
        amount=-1.0,
        context=context,
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.source == "command"


def test_apply_effects_identity_stat_mapping_when_no_custom_map() -> None:
    """Test resource_type maps to same stat name when no custom map provided."""
    entity_id = EntityID(fake.uuid4())
    permission = ActionPermission(
        resource_effects=(
            ResourceEffect(
                resource_type="custom_resource",
                modification_type=ResourceModificationType.FLAT,
                amount=5.0,
            ),
        )
    )
    context = Mock()

    ResourceEffectApplicator.apply_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.stat == "custom_resource"


def test_apply_single_effect_identity_stat_mapping_when_no_custom_name() -> None:
    """Test resource_type maps to same stat name when no custom stat_name provided."""
    entity_id = EntityID(fake.uuid4())
    context = Mock()

    ResourceEffectApplicator.apply_single_effect(
        entity_id=entity_id,
        resource_type="mana",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
        context=context,
    )

    call_args = context.modifiers.queue_modifier.call_args
    modifier = call_args.kwargs["modifier"]

    assert modifier.stat == "mana"
