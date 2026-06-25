"""Tests for action permission types."""

from faker import Faker

from yuna.commands.permissions import (
    ActionPermission,
    ResourceEffect,
    ResourceModificationType,
)

fake = Faker()


def test_resource_effect_creation() -> None:
    """Test ResourceEffect can be instantiated."""
    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    assert effect is not None


def test_resource_effect_flat_cost() -> None:
    """Test creating flat cost effect."""
    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    assert effect.resource_type == "energy"
    assert effect.modification_type == ResourceModificationType.FLAT
    assert effect.amount == -10.0


def test_resource_effect_flat_gain() -> None:
    """Test creating flat gain effect."""
    effect = ResourceEffect(
        resource_type="heat",
        modification_type=ResourceModificationType.FLAT,
        amount=5.0,
    )
    assert effect.resource_type == "heat"
    assert effect.amount == 5.0


def test_resource_effect_percentage_cost() -> None:
    """Test creating percentage cost effect."""
    effect = ResourceEffect(
        resource_type="stamina",
        modification_type=ResourceModificationType.PERCENTAGE,
        amount=-0.50,
    )
    assert effect.modification_type == ResourceModificationType.PERCENTAGE
    assert effect.amount == -0.50


def test_resource_effect_multiplier() -> None:
    """Test creating multiplier effect."""
    effect = ResourceEffect(
        resource_type="speed",
        modification_type=ResourceModificationType.MULTIPLIER,
        amount=0.75,
    )
    assert effect.modification_type == ResourceModificationType.MULTIPLIER
    assert effect.amount == 0.75


def test_resource_effect_set() -> None:
    """Test creating set effect."""
    effect = ResourceEffect(
        resource_type="mode",
        modification_type=ResourceModificationType.SET,
        amount=1.0,
    )
    assert effect.modification_type == ResourceModificationType.SET
    assert effect.amount == 1.0


def test_resource_effect_with_condition_modifier() -> None:
    """Test creating effect with condition modifier."""

    def condition(amt: float) -> float:
        return amt * 0.5

    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-20.0,
        condition_modifier=condition,
    )
    assert effect.condition_modifier is not None
    assert effect.condition_modifier(-20.0) == -10.0


def test_resource_effect_without_condition_modifier() -> None:
    """Test effect without condition modifier defaults to None."""
    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    assert effect.condition_modifier is None


def test_resource_effect_with_tags() -> None:
    """Test creating effect with tags."""
    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
        tags=frozenset({"movement", "combat"}),
    )
    assert effect.tags == frozenset({"movement", "combat"})


def test_resource_effect_without_tags() -> None:
    """Test effect without tags defaults to empty frozenset."""
    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    assert effect.tags == frozenset()


def test_resource_effect_is_immutable() -> None:
    """Test that ResourceEffect is frozen and immutable."""
    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    try:
        effect.amount = -20.0  # type: ignore[misc]
        msg = "Should not be able to modify frozen dataclass"
        raise AssertionError(msg)
    except AttributeError:
        pass


def test_action_permission_creation() -> None:
    """Test ActionPermission can be instantiated."""
    permission = ActionPermission()
    assert permission is not None


def test_action_permission_empty() -> None:
    """Test creating empty permission with defaults."""
    permission = ActionPermission()
    assert permission.resource_effects == ()
    assert permission.required_stats == {}
    assert permission.forbidden_tags == frozenset()
    assert permission.required_tags == frozenset()
    assert permission.cooldown_ticks == 0
    assert permission.max_uses_per_tick is None


def test_action_permission_with_single_effect() -> None:
    """Test creating permission with single resource effect."""
    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    permission = ActionPermission(resource_effects=(effect,))
    assert len(permission.resource_effects) == 1
    assert permission.resource_effects[0] == effect


def test_action_permission_with_multiple_effects() -> None:
    """Test creating permission with multiple resource effects."""
    effect1 = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-25.0,
    )
    effect2 = ResourceEffect(
        resource_type="heat",
        modification_type=ResourceModificationType.FLAT,
        amount=5.0,
    )
    permission = ActionPermission(resource_effects=(effect1, effect2))
    assert len(permission.resource_effects) == 2


def test_action_permission_with_required_stats() -> None:
    """Test creating permission with stat requirements."""
    permission = ActionPermission(
        required_stats={"strength": 10.0, "intelligence": 5.0}
    )
    assert permission.required_stats == {"strength": 10.0, "intelligence": 5.0}


def test_action_permission_with_forbidden_tags() -> None:
    """Test creating permission with forbidden tags."""
    permission = ActionPermission(forbidden_tags=frozenset({"stunned", "disabled"}))
    assert permission.forbidden_tags == frozenset({"stunned", "disabled"})


def test_action_permission_with_required_tags() -> None:
    """Test creating permission with required tags."""
    permission = ActionPermission(required_tags=frozenset({"alive", "conscious"}))
    assert permission.required_tags == frozenset({"alive", "conscious"})


def test_action_permission_with_cooldown() -> None:
    """Test creating permission with cooldown."""
    permission = ActionPermission(cooldown_ticks=100)
    assert permission.cooldown_ticks == 100


def test_action_permission_with_max_uses() -> None:
    """Test creating permission with max uses per tick."""
    permission = ActionPermission(max_uses_per_tick=1)
    assert permission.max_uses_per_tick == 1


def test_action_permission_complex() -> None:
    """Test creating complex permission with all fields."""
    effect1 = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-25.0,
    )
    effect2 = ResourceEffect(
        resource_type="heat",
        modification_type=ResourceModificationType.FLAT,
        amount=5.0,
    )
    permission = ActionPermission(
        resource_effects=(effect1, effect2),
        required_stats={"strength": 10.0, "intelligence": 5.0},
        forbidden_tags=frozenset({"stunned", "disabled"}),
        required_tags=frozenset({"alive"}),
        cooldown_ticks=100,
        max_uses_per_tick=1,
    )
    assert len(permission.resource_effects) == 2
    assert permission.required_stats == {"strength": 10.0, "intelligence": 5.0}
    assert permission.forbidden_tags == frozenset({"stunned", "disabled"})
    assert permission.required_tags == frozenset({"alive"})
    assert permission.cooldown_ticks == 100
    assert permission.max_uses_per_tick == 1


def test_action_permission_is_immutable() -> None:
    """Test that ActionPermission is frozen and immutable."""
    permission = ActionPermission(cooldown_ticks=100)
    try:
        permission.cooldown_ticks = 200  # type: ignore[misc]
        msg = "Should not be able to modify frozen dataclass"
        raise AssertionError(msg)
    except AttributeError:
        pass


def test_resource_modification_type_enum_values() -> None:
    """Test ResourceModificationType enum has expected values."""
    assert hasattr(ResourceModificationType, "SET")
    assert hasattr(ResourceModificationType, "FLAT")
    assert hasattr(ResourceModificationType, "PERCENTAGE")
    assert hasattr(ResourceModificationType, "MULTIPLIER")


def test_resource_effect_equality() -> None:
    """Test ResourceEffect equality comparison."""
    effect1 = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    effect2 = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    assert effect1 == effect2


def test_resource_effect_inequality() -> None:
    """Test ResourceEffect inequality comparison."""
    effect1 = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    effect2 = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-20.0,
    )
    assert effect1 != effect2


def test_action_permission_equality() -> None:
    """Test ActionPermission equality comparison."""
    effect = ResourceEffect(
        resource_type="energy",
        modification_type=ResourceModificationType.FLAT,
        amount=-10.0,
    )
    permission1 = ActionPermission(resource_effects=(effect,), cooldown_ticks=100)
    permission2 = ActionPermission(resource_effects=(effect,), cooldown_ticks=100)
    assert permission1 == permission2


def test_action_permission_inequality() -> None:
    """Test ActionPermission inequality comparison."""
    permission1 = ActionPermission(cooldown_ticks=100)
    permission2 = ActionPermission(cooldown_ticks=200)
    assert permission1 != permission2
