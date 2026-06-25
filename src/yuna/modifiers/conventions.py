"""Naming conventions for resource effect modifiers."""

from yuna.modifiers.modifier import Modifier
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.types.identifiers import EntityID


class EffectModifierConventions:
    """Naming conventions and factory methods for resource effect modifiers.

    Provides standardized stat naming for modifiers that affect resource effects
    (costs, gains, heat generation, fuel consumption, etc.).

    Usage:
        # Get stat name for energy effect modifiers
        stat = EffectModifierConventions.effect_stat_name(resource_type="energy")
        # Returns: "effect:energy"

        # Create energy efficiency modifier (reduces energy effects)
        modifier = EffectModifierConventions.create_effect_reduction(
            entity_id=entity_id,
            resource_type="energy",
            reduction_percentage=0.25,
            source="efficiency_upgrade",
        )

        # Create heat reduction modifier (reduces heat generation)
        modifier = EffectModifierConventions.create_effect_reduction(
            entity_id=entity_id,
            resource_type="heat",
            reduction_percentage=0.30,
            source="cooling_system",
        )
    """

    @staticmethod
    def effect_stat_name(resource_type: str) -> str:
        """Get stat name for effect modifier.

        Args:
            resource_type: Resource type identifier (e.g., "energy", "heat", "fuel")

        Returns:
            Stat name for effect modifier

        Example:
            >>> EffectModifierConventions.effect_stat_name(resource_type="energy")
            'effect:energy'
        """
        return f"effect:{resource_type}"

    @staticmethod
    def all_effects_stat_name() -> str:
        """Get stat name for modifiers affecting all resource effects.

        Returns:
            Stat name for global effect modifier

        Example:
            >>> EffectModifierConventions.all_effects_stat_name()
            'effect:all'
        """
        return "effect:all"

    @staticmethod
    def create_effect_reduction(
        entity_id: EntityID,
        resource_type: str,
        reduction_percentage: float,
        source: str,
        **kwargs,
    ) -> Modifier:
        """Create effect reduction modifier.

        Reduces any resource effect by percentage (costs, gains, heat, etc.).
        Negative percentage means reduction.

        Args:
            entity_id: Entity to apply modifier to
            resource_type: Resource type to affect
            reduction_percentage: Reduction as decimal (0.25 = 25% reduction)
            source: Modifier source identifier
            **kwargs: Additional Modifier arguments (duration_ticks, tags, etc.)

        Returns:
            Modifier configured for effect reduction

        Example:
            # 25% energy efficiency (reduces energy effects)
            modifier = EffectModifierConventions.create_effect_reduction(
                entity_id=entity_id,
                resource_type="energy",
                reduction_percentage=0.25,
                source="efficiency_upgrade",
            )
        """
        return Modifier(
            entity_id=entity_id,
            stat=EffectModifierConventions.effect_stat_name(resource_type),
            modification_type=ModificationType.PERCENTAGE,
            value=-reduction_percentage,
            priority=ModifierPriority.NORMAL,
            source=source,
            tags=kwargs.pop("tags", frozenset())
            | frozenset({"effect_modifier", "effect_reduction"}),
            **kwargs,
        )

    @staticmethod
    def create_effect_increase(
        entity_id: EntityID,
        resource_type: str,
        increase_percentage: float,
        source: str,
        **kwargs,
    ) -> Modifier:
        """Create effect increase modifier.

        Increases any resource effect by percentage (costs, gains, heat, etc.).
        Positive percentage means increase.

        Args:
            entity_id: Entity to apply modifier to
            resource_type: Resource type to affect
            increase_percentage: Increase as decimal (0.30 = 30% increase)
            source: Modifier source identifier
            **kwargs: Additional Modifier arguments (duration_ticks, tags, etc.)

        Returns:
            Modifier configured for effect increase

        Example:
            # 30% increased heat generation (penalty)
            modifier = EffectModifierConventions.create_effect_increase(
                entity_id=entity_id,
                resource_type="heat",
                increase_percentage=0.30,
                source="overclocking_penalty",
            )
        """
        return Modifier(
            entity_id=entity_id,
            stat=EffectModifierConventions.effect_stat_name(resource_type),
            modification_type=ModificationType.PERCENTAGE,
            value=increase_percentage,
            priority=ModifierPriority.NORMAL,
            source=source,
            tags=kwargs.pop("tags", frozenset())
            | frozenset({"effect_modifier", "effect_increase"}),
            **kwargs,
        )

    @staticmethod
    def is_effect_modifier(modifier: Modifier) -> bool:
        """Check if modifier affects resource effects.

        Args:
            modifier: Modifier to check

        Returns:
            True if modifier affects resource effects

        Example:
            >>> modifier = Modifier(entity_id=id, stat="effect:energy", ...)
            >>> EffectModifierConventions.is_effect_modifier(modifier)
            True
            >>> modifier = Modifier(entity_id=id, stat="health", ...)
            >>> EffectModifierConventions.is_effect_modifier(modifier)
            False
        """
        return modifier.stat.startswith("effect:")
