"""Permission validation for action execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yuna.commands.effect_modifiers import EffectModifierProcessor
from yuna.commands.permissions import ResourceModificationType

if TYPE_CHECKING:
    from yuna.commands.permissions import (
        ActionPermission,
        ResourceEffect,
    )
    from yuna.modifiers.pipeline import ModifierPipeline
    from yuna.types.identifiers import EntityID


class PermissionValidator:
    """Validates action permissions against entity state.

    Validates requirements before action execution:
    - Resource costs (negative effects only - gains always succeed)
    - Stat requirements
    - Tag constraints
    - Cooldown restrictions

    Note: Only validates costs. Gains and positive effects always succeed
    and may cause overflow - game systems handle consequences separately.

    When initialized with a modifier pipeline, applies effect modifiers
    to resource effects before validation.

    Usage:
        # Without effect modifiers
        validator = PermissionValidator()

        # With effect modifiers
        validator = PermissionValidator(modifier_pipeline=pipeline)

        can_afford, reason = validator.validate_resource_effects(
            entity_id=entity_id,
            permission=action_permission,
            context=game_world,
        )

        can_execute, reason = validator.validate_permission(
            entity_id=entity_id,
            action_id="attack",
            permission=action_permission,
            context=game_world,
            current_tick=100,
        )
    """

    def __init__(self, modifier_pipeline: ModifierPipeline | None = None) -> None:
        """Initialize permission validator.

        Args:
            modifier_pipeline: Optional modifier pipeline for effect modifications
        """
        self._effect_processor: EffectModifierProcessor | None = None

        if modifier_pipeline is not None:
            self._effect_processor = EffectModifierProcessor(
                modifier_pipeline=modifier_pipeline
            )

    def validate_resource_effects(
        self,
        entity_id: EntityID,
        permission: ActionPermission,
        context: Any,
    ) -> tuple[bool, str]:
        """Validate entity can afford all resource costs.

        Only validates costs (effects that consume resources). Gains are
        not validated and will be applied even if they exceed maximums.

        If effect processor is configured, applies effect modifiers before
        validation (e.g., energy efficiency reduces energy costs).

        Args:
            entity_id: Entity attempting action
            permission: Permission requirements
            context: Game context with resource tracking

        Returns:
            Tuple of (can_afford, reason_if_not)
        """
        if not permission.resource_effects:
            return True, ""

        if not hasattr(context, "get_resource"):
            return False, "Context does not support resource tracking"

        for effect in permission.resource_effects:
            if not self._is_cost(effect=effect):
                continue

            effective_amount = effect.amount

            if self._effect_processor is not None:
                effective_amount = self._effect_processor.calculate_effective_effect(
                    entity_id=entity_id,
                    base_effect=effect,
                    context=context,
                )

            if effect.condition_modifier is not None:
                effective_amount = effect.condition_modifier(effective_amount)

            current = context.get_resource(
                entity_id=entity_id,
                resource_type=effect.resource_type,
            )

            required = self._get_required_amount(
                effect=effect,
                effective_amount=effective_amount,
                current=current,
            )

            if current < required:
                return (
                    False,
                    (
                        f"Insufficient {effect.resource_type}: need "
                        f"{required:.2f}, have {current:.2f}"
                    ),
                )

        return True, ""

    @staticmethod
    def _is_cost(effect: ResourceEffect) -> bool:
        """Check if effect is a cost (consumes resources).

        Args:
            effect: Resource effect to check

        Returns:
            True if effect is a cost, False if it's a gain
        """
        if effect.modification_type == ResourceModificationType.FLAT:
            return effect.amount < 0

        if effect.modification_type == ResourceModificationType.PERCENTAGE:
            return effect.amount < 0

        if effect.modification_type == ResourceModificationType.MULTIPLIER:
            return effect.amount < 1.0

        return True

    @staticmethod
    def _get_required_amount(
        effect: ResourceEffect,
        effective_amount: float,
        current: float,
    ) -> float:
        """Calculate required resource amount for a cost.

        Args:
            effect: Resource effect
            effective_amount: Amount after condition modifier
            current: Current resource value

        Returns:
            Required resource amount
        """
        if effect.modification_type == ResourceModificationType.FLAT:
            return abs(effective_amount)

        if effect.modification_type == ResourceModificationType.PERCENTAGE:
            return abs(current * effective_amount)

        if effect.modification_type == ResourceModificationType.MULTIPLIER:
            return current * (1.0 - effective_amount)

        if effective_amount < current:
            return current - effective_amount
        return 0.0

    @staticmethod
    def validate_stats(
        entity_id: EntityID,
        permission: ActionPermission,
        context: Any,
    ) -> tuple[bool, str]:
        """Validate entity meets stat requirements.

        Args:
            entity_id: Entity attempting action
            permission: Permission requirements
            context: Game context with stat tracking

        Returns:
            Tuple of (meets_requirements, reason_if_not)
        """
        if not permission.required_stats:
            return True, ""

        if not hasattr(context, "get_stat"):
            return False, "Context does not support stat tracking"

        for stat, min_value in permission.required_stats.items():
            current_value = context.get_stat(entity_id=entity_id, stat=stat)

            if current_value < min_value:
                return (
                    False,
                    (
                        f"Insufficient {stat}: need {min_value:.2f}, "
                        f"have {current_value:.2f}"
                    ),
                )

        return True, ""

    @staticmethod
    def validate_tags(
        entity_id: EntityID,
        permission: ActionPermission,
        context: Any,
    ) -> tuple[bool, str]:
        """Validate entity has/lacks required tags.

        Args:
            entity_id: Entity attempting action
            permission: Permission requirements
            context: Game context with tag tracking

        Returns:
            Tuple of (meets_requirements, reason_if_not)
        """
        if not permission.required_tags and not permission.forbidden_tags:
            return True, ""

        if not hasattr(context, "has_tag"):
            return False, "Context does not support tag tracking"

        for required_tag in permission.required_tags:
            if not context.has_tag(entity_id=entity_id, tag=required_tag):
                return False, f"Missing required tag: {required_tag}"

        for forbidden_tag in permission.forbidden_tags:
            if context.has_tag(entity_id=entity_id, tag=forbidden_tag):
                return False, f"Has forbidden tag: {forbidden_tag}"

        return True, ""

    @staticmethod
    def validate_cooldown(
        entity_id: EntityID,
        action_id: str,
        permission: ActionPermission,
        current_tick: int,
    ) -> tuple[bool, str]:
        """Validate action is not on cooldown.

        Note: Cooldown tracking requires external implementation.
        This method currently always returns True.

        Args:
            entity_id: Entity attempting action
            action_id: Action identifier
            permission: Permission requirements
            current_tick: Current game tick

        Returns:
            Tuple of (not_on_cooldown, reason_if_not)
        """
        if permission.cooldown_ticks == 0:
            return True, ""

        return True, ""

    def validate_permission(
        self,
        entity_id: EntityID,
        action_id: str,
        permission: ActionPermission,
        context: Any,
        current_tick: int,
    ) -> tuple[bool, str]:
        """Validate all permission requirements.

        Checks resource effects (costs only), stats, tags, and cooldown.
        Returns failure on first violation.

        Args:
            entity_id: Entity attempting action
            action_id: Action identifier
            permission: Permission requirements
            context: Game context
            current_tick: Current game tick

        Returns:
            Tuple of (can_execute, reason_if_not)
        """
        can_afford, reason = self.validate_resource_effects(
            entity_id=entity_id,
            permission=permission,
            context=context,
        )
        if not can_afford:
            return False, reason

        meets_stats, reason = self.validate_stats(
            entity_id=entity_id,
            permission=permission,
            context=context,
        )
        if not meets_stats:
            return False, reason

        meets_tags, reason = self.validate_tags(
            entity_id=entity_id,
            permission=permission,
            context=context,
        )
        if not meets_tags:
            return False, reason

        not_on_cooldown, reason = self.validate_cooldown(
            entity_id=entity_id,
            action_id=action_id,
            permission=permission,
            current_tick=current_tick,
        )
        if not not_on_cooldown:
            return False, reason

        return True, ""
