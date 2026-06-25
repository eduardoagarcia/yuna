"""Tests for permission validator."""

from unittest.mock import Mock, patch

from faker import Faker

from yuna.commands.permissions import (
    ActionPermission,
    ResourceEffect,
    ResourceModificationType,
)
from yuna.commands.validator import PermissionValidator
from yuna.types.identifiers import EntityID

fake = Faker()


def test_validator_creation() -> None:
    """Test PermissionValidator can be instantiated."""
    validator = PermissionValidator()
    assert validator is not None


def test_validate_empty_permission() -> None:
    """Test validating empty permission succeeds."""
    validator = PermissionValidator()
    context = Mock()
    entity_id = EntityID("entity_1")

    permission = ActionPermission()

    can_execute, reason = validator.validate_permission(
        entity_id=entity_id,
        action_id="test_action",
        permission=permission,
        context=context,
        current_tick=0,
    )

    assert can_execute is True
    assert not reason


def test_validate_flat_cost_sufficient_resources() -> None:
    """Test validating flat cost with sufficient resources succeeds."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=100.0)
    entity_id = EntityID("entity_1")

    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    permission = ActionPermission(resource_effects=(effect,))

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True
    assert not reason
    context.get_resource.assert_called_once_with(
        entity_id=entity_id, resource_type="energy"
    )


def test_validate_flat_cost_insufficient_resources() -> None:
    """Test validating flat cost with insufficient resources fails."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=5.0)
    entity_id = EntityID("entity_1")

    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    permission = ActionPermission(resource_effects=(effect,))

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is False
    assert "Insufficient energy" in reason
    assert "need 10.00" in reason
    assert "have 5.00" in reason


def test_validate_flat_gain_always_succeeds() -> None:
    """Test validating flat gain always succeeds regardless of current value."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=0.0)
    entity_id = EntityID("entity_1")

    effect = ResourceEffect(
        resource_type="heat",
        modification_type=ResourceModificationType.FLAT,
        amount=5.0,
    )
    permission = ActionPermission(resource_effects=(effect,))

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True
    assert not reason


def test_validate_percentage_cost_sufficient() -> None:
    """Test validating percentage cost with sufficient resources."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=100.0)
    entity_id = EntityID("entity_1")

    effect = ResourceEffect(
        resource_type="stamina",
        modification_type=ResourceModificationType.PERCENTAGE,
        amount=-0.50,
    )
    permission = ActionPermission(resource_effects=(effect,))

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True
    assert not reason


def test_validate_percentage_cost_with_zero_current() -> None:
    """Test validating percentage cost when current resource is zero."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=0.0)
    entity_id = EntityID("entity_1")

    effect = ResourceEffect(
        resource_type="stamina",
        modification_type=ResourceModificationType.PERCENTAGE,
        amount=-0.75,
    )
    permission = ActionPermission(resource_effects=(effect,))

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True
    assert not reason


def test_validate_multiplier_cost_sufficient() -> None:
    """Test validating multiplier cost with sufficient resources."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=100.0)
    entity_id = EntityID("entity_1")

    effect = ResourceEffect(
        resource_type="speed",
        modification_type=ResourceModificationType.MULTIPLIER,
        amount=0.75,
    )
    permission = ActionPermission(resource_effects=(effect,))

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True
    assert not reason


def test_validate_set_cost_sufficient() -> None:
    """Test validating set effect with sufficient resources."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=100.0)
    entity_id = EntityID("entity_1")

    effect = ResourceEffect(
        resource_type="mode",
        modification_type=ResourceModificationType.SET,
        amount=50.0,
    )
    permission = ActionPermission(resource_effects=(effect,))

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True
    assert not reason


def test_validate_multiple_effects() -> None:
    """Test validating multiple resource effects."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(side_effect=[100.0, 50.0])
    entity_id = EntityID("entity_1")

    effect1 = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-25.0,
    )
    effect2 = ResourceEffect(
        resource_type="action_points",
        modification_type=ResourceModificationType.FLAT,
        amount=-1.0,
    )
    permission = ActionPermission(resource_effects=(effect1, effect2))

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True
    assert not reason


def test_validate_effect_with_condition_modifier() -> None:
    """Test validating effect with condition modifier."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=15.0)
    entity_id = EntityID("entity_1")

    def condition_modifier(amt: float) -> float:
        return amt * 0.5

    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-20.0,
        condition_modifier=condition_modifier,
    )
    permission = ActionPermission(resource_effects=(effect,))

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True
    assert not reason


def test_validate_stats_sufficient() -> None:
    """Test validating stat requirements with sufficient stats."""
    validator = PermissionValidator()
    context = Mock()
    context.get_stat = Mock(side_effect=[15.0, 8.0])
    entity_id = EntityID("entity_1")

    permission = ActionPermission(
        required_stats={"strength": 10.0, "intelligence": 5.0}
    )

    meets_stats, reason = validator.validate_stats(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert meets_stats is True
    assert not reason


def test_validate_stats_insufficient() -> None:
    """Test validating stat requirements with insufficient stats."""
    validator = PermissionValidator()
    context = Mock()
    context.get_stat = Mock(return_value=5.0)
    entity_id = EntityID("entity_1")

    permission = ActionPermission(required_stats={"strength": 10.0})

    meets_stats, reason = validator.validate_stats(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert meets_stats is False
    assert "Insufficient strength" in reason
    assert "need 10.00" in reason
    assert "have 5.00" in reason


def test_validate_tags_has_required() -> None:
    """Test validating tags when entity has required tags."""
    validator = PermissionValidator()
    context = Mock()
    context.has_tag = Mock(side_effect=[True, True])
    entity_id = EntityID("entity_1")

    permission = ActionPermission(required_tags=frozenset({"alive", "conscious"}))

    meets_tags, reason = validator.validate_tags(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert meets_tags is True
    assert not reason


def test_validate_tags_missing_required() -> None:
    """Test validating tags when entity missing required tag."""
    validator = PermissionValidator()
    context = Mock()
    context.has_tag = Mock(return_value=False)
    entity_id = EntityID("entity_1")

    permission = ActionPermission(required_tags=frozenset({"alive"}))

    meets_tags, reason = validator.validate_tags(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert meets_tags is False
    assert "Missing required tag: alive" in reason


def test_validate_tags_lacks_forbidden() -> None:
    """Test validating tags when entity lacks forbidden tags."""
    validator = PermissionValidator()
    context = Mock()
    context.has_tag = Mock(side_effect=[False, False])
    entity_id = EntityID("entity_1")

    permission = ActionPermission(forbidden_tags=frozenset({"stunned", "disabled"}))

    meets_tags, reason = validator.validate_tags(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert meets_tags is True
    assert not reason


def test_validate_tags_has_forbidden() -> None:
    """Test validating tags when entity has forbidden tag."""
    validator = PermissionValidator()
    context = Mock()
    context.has_tag = Mock(return_value=True)
    entity_id = EntityID("entity_1")

    permission = ActionPermission(forbidden_tags=frozenset({"stunned"}))

    meets_tags, reason = validator.validate_tags(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert meets_tags is False
    assert "Has forbidden tag: stunned" in reason


def test_validate_cooldown_zero() -> None:
    """Test validating cooldown when no cooldown set."""
    validator = PermissionValidator()
    entity_id = EntityID("entity_1")

    permission = ActionPermission(cooldown_ticks=0)

    not_on_cooldown, reason = validator.validate_cooldown(
        entity_id=entity_id,
        action_id="test_action",
        permission=permission,
        current_tick=100,
    )

    assert not_on_cooldown is True
    assert not reason


def test_validate_permission_all_requirements_met() -> None:
    """Test complete permission validation when all requirements met."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=100.0)
    context.get_stat = Mock(return_value=15.0)
    context.has_tag = Mock(side_effect=[True, False])
    entity_id = EntityID("entity_1")

    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    permission = ActionPermission(
        resource_effects=(effect,),
        required_stats={"strength": 10.0},
        required_tags=frozenset({"alive"}),
        forbidden_tags=frozenset({"stunned"}),
        cooldown_ticks=0,
    )

    can_execute, reason = validator.validate_permission(
        entity_id=entity_id,
        action_id="test_action",
        permission=permission,
        context=context,
        current_tick=100,
    )

    assert can_execute is True
    assert not reason


def test_validate_permission_fails_on_resources() -> None:
    """Test permission validation fails on insufficient resources."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=5.0)
    entity_id = EntityID("entity_1")

    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    permission = ActionPermission(resource_effects=(effect,))

    can_execute, reason = validator.validate_permission(
        entity_id=entity_id,
        action_id="test_action",
        permission=permission,
        context=context,
        current_tick=100,
    )

    assert can_execute is False
    assert "Insufficient energy" in reason


def test_validate_permission_fails_on_stats() -> None:
    """Test permission validation fails on insufficient stats."""
    validator = PermissionValidator()
    context = Mock()
    context.get_stat = Mock(return_value=5.0)
    entity_id = EntityID("entity_1")

    permission = ActionPermission(required_stats={"strength": 10.0})

    can_execute, reason = validator.validate_permission(
        entity_id=entity_id,
        action_id="test_action",
        permission=permission,
        context=context,
        current_tick=100,
    )

    assert can_execute is False
    assert "Insufficient strength" in reason


def test_validate_permission_fails_on_tags() -> None:
    """Test permission validation fails on tag violation."""
    validator = PermissionValidator()
    context = Mock()
    context.has_tag = Mock(return_value=True)
    entity_id = EntityID("entity_1")

    permission = ActionPermission(forbidden_tags=frozenset({"stunned"}))

    can_execute, reason = validator.validate_permission(
        entity_id=entity_id,
        action_id="test_action",
        permission=permission,
        context=context,
        current_tick=100,
    )

    assert can_execute is False
    assert "Has forbidden tag: stunned" in reason


def test_validate_resource_effects_no_context_support() -> None:
    """Test validation fails when context doesn't support resources."""
    validator = PermissionValidator()
    context = Mock(spec=[])
    entity_id = EntityID("entity_1")

    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    permission = ActionPermission(resource_effects=(effect,))

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is False
    assert "does not support resource tracking" in reason


def test_validate_stats_no_context_support() -> None:
    """Test validation fails when context doesn't support stats."""
    validator = PermissionValidator()
    context = Mock(spec=[])
    entity_id = EntityID("entity_1")

    permission = ActionPermission(required_stats={"strength": 10.0})

    meets_stats, reason = validator.validate_stats(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert meets_stats is False
    assert "does not support stat tracking" in reason


def test_validate_tags_no_context_support() -> None:
    """Test validation fails when context doesn't support tags."""
    validator = PermissionValidator()
    context = Mock(spec=[])
    entity_id = EntityID("entity_1")

    permission = ActionPermission(required_tags=frozenset({"alive"}))

    meets_tags, reason = validator.validate_tags(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert meets_tags is False
    assert "does not support tag tracking" in reason


def test_validate_set_cost_when_setting_to_higher_value() -> None:
    """Test validating set effect when setting to value higher than current."""
    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=50.0)
    entity_id = EntityID("entity_1")

    effect = ResourceEffect(
        resource_type="mode",
        modification_type=ResourceModificationType.SET,
        amount=100.0,
    )
    permission = ActionPermission(resource_effects=(effect,))

    can_afford, reason = validator.validate_resource_effects(
        entity_id=entity_id,
        permission=permission,
        context=context,
    )

    assert can_afford is True
    assert not reason


def test_validate_cooldown_with_nonzero_ticks() -> None:
    """Test validating cooldown when cooldown_ticks is greater than zero."""
    validator = PermissionValidator()
    entity_id = EntityID("entity_1")

    permission = ActionPermission(cooldown_ticks=100)

    not_on_cooldown, reason = validator.validate_cooldown(
        entity_id=entity_id,
        action_id="test_action",
        permission=permission,
        current_tick=200,
    )

    assert not_on_cooldown is True
    assert not reason


def test_is_cost_with_unknown_modification_type() -> None:
    """Test _is_cost returns True for unknown modification type."""
    validator = PermissionValidator()

    effect_mock = Mock()
    effect_mock.modification_type = "UNKNOWN_TYPE"

    result = validator._is_cost(effect=effect_mock)

    assert result is True


def test_get_required_amount_with_unknown_modification_type() -> None:
    """Test _get_required_amount returns current - effective_amount.

    For unknown modification type.
    """
    validator = PermissionValidator()

    effect_mock = Mock()
    effect_mock.modification_type = "UNKNOWN_TYPE"

    result = validator._get_required_amount(
        effect=effect_mock, effective_amount=10.0, current=100.0
    )

    assert result == 90.0


@patch.object(PermissionValidator, "validate_cooldown")
def test_validate_permission_fails_on_cooldown(mock_validate_cooldown: Mock) -> None:
    """Test permission validation fails when cooldown validation fails."""
    mock_validate_cooldown.return_value = (False, "Action on cooldown")

    validator = PermissionValidator()
    context = Mock()
    context.get_resource = Mock(return_value=100.0)
    context.get_stat = Mock(return_value=15.0)
    context.has_tag = Mock(return_value=True)
    entity_id = EntityID("entity_1")

    permission = ActionPermission(cooldown_ticks=10)

    can_execute, reason = validator.validate_permission(
        entity_id=entity_id,
        action_id="test_action",
        permission=permission,
        context=context,
        current_tick=100,
    )

    assert can_execute is False
    assert reason == "Action on cooldown"
