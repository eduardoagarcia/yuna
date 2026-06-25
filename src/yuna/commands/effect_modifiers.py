"""Resource effect modifier processing."""

from typing import Any

from yuna.commands.permissions import (
    ActionPermission,
    ResourceEffect,
)
from yuna.modifiers.conventions import EffectModifierConventions
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.types.identifiers import EntityID


class EffectModifierProcessor:
    """Processes modifiers affecting resource effects.

    Integrates modifier pipeline with action permission system to allow
    modifiers to modify resource effects (costs, gains, heat generation, etc.)
    before permission validation.

    Usage:
        processor = EffectModifierProcessor(modifier_pipeline=pipeline)

        # Calculate effective amount for a resource effect
        effective = processor.calculate_effective_effect(
            entity_id=entity_id,
            base_effect=ResourceEffect(
                resource_type="energy",
                modification_type=ResourceModificationType.FLAT,
                amount=-10.0,
            ),
            context=world,
        )

        # Get detailed breakdown
        breakdown = processor.get_effect_breakdown(
            entity_id=entity_id,
            permission=action_permission,
            context=world,
        )
    """

    def __init__(self, modifier_pipeline: ModifierPipeline) -> None:
        """Initialize effect modifier processor.

        Args:
            modifier_pipeline: Modifier pipeline for processing modifiers
        """
        self._pipeline = modifier_pipeline

    def calculate_effective_effect(
        self,
        entity_id: EntityID,
        base_effect: ResourceEffect,
        context: Any,
    ) -> float:
        """Calculate effective resource effect amount after modifiers.

        Applies modifier pipeline to calculate final effect amount considering:
        - Resource-specific modifiers (effect:energy, effect:heat, etc.)
        - Global modifiers (effect:all)
        - Modifier stacking rules
        - Priority ordering

        Args:
            entity_id: Entity executing action
            base_effect: Base resource effect
            context: Game context (world)

        Returns:
            Effective amount after modifiers

        Example:
            # Base energy cost: -10.0
            # With 25% energy efficiency modifier: -7.5
            effective = processor.calculate_effective_effect(
                entity_id=entity_id,
                base_effect=ResourceEffect(
                    resource_type="energy",
                    modification_type=ResourceModificationType.FLAT,
                    amount=-10.0,
                ),
                context=world,
            )
            # Returns: -7.5
        """
        effect_stat = EffectModifierConventions.effect_stat_name(
            base_effect.resource_type
        )

        temp_modifier = Modifier(
            entity_id=entity_id,
            stat=effect_stat,
            modification_type=ModificationType.FLAT,
            value=base_effect.amount,
            priority=ModifierPriority.CRITICAL,
            source="base_effect",
        )

        self._pipeline.queue_modifier(modifier=temp_modifier)

        results = self._pipeline.process(world=context, current_tick=0)
        effective_amount = results.get((entity_id, effect_stat), base_effect.amount)

        self._pipeline.clear_queue()

        return effective_amount

    def get_effect_breakdown(
        self,
        entity_id: EntityID,
        permission: ActionPermission,
        context: Any,
    ) -> dict[str, dict[str, float]]:
        """Get detailed breakdown of effect modifications.

        Provides transparency into how modifiers affect each resource effect,
        showing base value, modifier contributions, and final value.

        Args:
            entity_id: Entity executing action
            permission: Action permission with resource effects
            context: Game context (world)

        Returns:
            Dict mapping resource_type to {base, final, reduction_pct}

        Example:
            breakdown = processor.get_effect_breakdown(
                entity_id=entity_id,
                permission=permission,
                context=world,
            )
            # Returns:
            # {
            #     "energy": {"base": -10.0, "final": -7.5, "reduction_pct": 25.0},
            #     "heat": {"base": 5.0, "final": 3.5, "reduction_pct": 30.0},
            # }
        """
        breakdown = {}

        for effect in permission.resource_effects:
            base_amount = effect.amount
            effective_amount = self.calculate_effective_effect(
                entity_id=entity_id,
                base_effect=effect,
                context=context,
            )

            if base_amount != 0:
                reduction_pct = (
                    (abs(base_amount) - abs(effective_amount)) / abs(base_amount)
                ) * 100.0
            else:
                reduction_pct = 0.0

            breakdown[effect.resource_type] = {
                "base": base_amount,
                "final": effective_amount,
                "reduction_pct": reduction_pct,
            }

        return breakdown

    def calculate_all_effective_effects(
        self,
        entity_id: EntityID,
        permission: ActionPermission,
        context: Any,
    ) -> list[tuple[str, float]]:
        """Calculate effective amounts for all resource effects in permission.

        Args:
            entity_id: Entity executing action
            permission: Action permission with resource effects
            context: Game context (world)

        Returns:
            List of (resource_type, effective_amount) tuples

        Example:
            effects = processor.calculate_all_effective_effects(
                entity_id=entity_id,
                permission=permission,
                context=world,
            )
            # Returns: [("energy", -7.5), ("heat", 3.5)]
        """
        effective_effects = []

        for effect in permission.resource_effects:
            effective_amount = self.calculate_effective_effect(
                entity_id=entity_id,
                base_effect=effect,
                context=context,
            )
            effective_effects.append((effect.resource_type, effective_amount))

        return effective_effects
