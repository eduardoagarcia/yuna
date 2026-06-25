"""Stat conversion helpers for multi-stat modifiers."""

from yuna.modifiers.modifier import StatEffect
from yuna.modifiers.types import ModificationType


class StatConversions:
    """Factory methods for common stat conversion patterns.

    Provides reusable patterns for:
    - Stat-to-stat conversion with scaling
    - Mirrored/synchronized stats
    - Value distribution across multiple stats

    Usage:
        # Convert 10% of capacity to throughput
        effect = StatConversions.convert_stat_to_stat(
            source_stat="capacity",
            target_stat="throughput",
            conversion_rate=0.10,
        )

        # Mirror efficiency changes to quality
        effect = StatConversions.mirror_stat(
            source_stat="efficiency",
            target_stat="quality",
            multiplier=0.5,
        )

        # Distribute 100 points across 3 stats equally
        effects = StatConversions.distribute_value(
            stats=["health", "shield", "armor"],
            total_value=100.0,
        )
    """

    @staticmethod
    def convert_stat_to_stat(
        source_stat: str,
        target_stat: str,
        conversion_rate: float,
        modification_type: ModificationType = ModificationType.FLAT,
    ) -> StatEffect:
        """Convert percentage of source stat to target stat.

        Creates a secondary effect that scales based on source stat value.
        Common use: Convert resource capacity to production rate.

        Args:
            source_stat: Stat to read value from
            target_stat: Stat to apply converted value to
            conversion_rate: Multiplier for source stat (0.0-1.0 typical)
            modification_type: How to apply converted value

        Returns:
            StatEffect configured for stat conversion

        Example:
            # 15% of max_energy → energy_regen
            effect = StatConversions.convert_stat_to_stat(
                source_stat="max_energy",
                target_stat="energy_regen",
                conversion_rate=0.15,
            )
        """
        return StatEffect(
            stat=target_stat,
            value=0.0,
            modification_type=modification_type,
            scaling_stat=source_stat,
            scaling_factor=conversion_rate,
        )

    @staticmethod
    def mirror_stat(
        source_stat: str,
        target_stat: str,
        multiplier: float = 1.0,
    ) -> StatEffect:
        """Keep target stat synchronized with source stat.

        Creates 1:1 mapping between stats with optional multiplier.
        Common use: Sync related attributes or duplicate bonuses.

        Args:
            source_stat: Stat to mirror from
            target_stat: Stat to apply mirrored value to
            multiplier: Scale factor for mirrored value

        Returns:
            StatEffect configured for stat mirroring

        Example:
            # Physical damage mirrors to magical damage at 50%
            effect = StatConversions.mirror_stat(
                source_stat="physical_damage",
                target_stat="magical_damage",
                multiplier=0.5,
            )
        """
        return StatEffect(
            stat=target_stat,
            value=0.0,
            modification_type=ModificationType.FLAT,
            scaling_stat=source_stat,
            scaling_factor=multiplier,
        )

    @staticmethod
    def distribute_value(
        stats: list[str],
        total_value: float,
        distribution: list[float] | None = None,
    ) -> tuple[StatEffect, ...]:
        """Distribute value across multiple stats.

        Splits a total value among stats using weights or equal distribution.
        Common use: Area effects, split bonuses, resource allocation.

        Args:
            stats: Target stats to distribute value across
            total_value: Total value to split
            distribution: Weights for each stat (None = equal split)

        Returns:
            Tuple of StatEffects for each target stat

        Raises:
            ValueError: If distribution length doesn't match stats length

        Example:
            # Distribute 100 damage as 50% fire, 30% ice, 20% lightning
            effects = StatConversions.distribute_value(
                stats=["fire_damage", "ice_damage", "lightning_damage"],
                total_value=100.0,
                distribution=[0.5, 0.3, 0.2],
            )
        """
        if distribution is None:
            weight = 1.0 / len(stats)
            distribution = [weight] * len(stats)

        if len(distribution) != len(stats):
            raise ValueError(
                f"Distribution length ({len(distribution)}) must match "
                f"stats length ({len(stats)})"
            )

        total_weight = sum(distribution)
        if total_weight == 0:
            raise ValueError("Distribution weights sum to zero")

        effects = []
        for stat, weight in zip(stats, distribution, strict=False):
            value = total_value * (weight / total_weight)
            effects.append(
                StatEffect(
                    stat=stat,
                    value=value,
                    modification_type=ModificationType.FLAT,
                )
            )

        return tuple(effects)

    @staticmethod
    def percentage_of_stat(
        source_stat: str,
        target_stat: str,
        percentage: float,
    ) -> StatEffect:
        """Apply percentage of source stat as flat bonus to target.

        Convenience method for common conversion pattern.
        Equivalent to convert_stat_to_stat with FLAT type.

        Args:
            source_stat: Stat to read percentage from
            target_stat: Stat to apply bonus to
            percentage: Percentage as decimal (0.0-1.0)

        Returns:
            StatEffect configured for percentage conversion

        Example:
            # 25% of strength → physical_damage
            effect = StatConversions.percentage_of_stat(
                source_stat="strength",
                target_stat="physical_damage",
                percentage=0.25,
            )
        """
        return StatConversions.convert_stat_to_stat(
            source_stat=source_stat,
            target_stat=target_stat,
            conversion_rate=percentage,
            modification_type=ModificationType.FLAT,
        )
