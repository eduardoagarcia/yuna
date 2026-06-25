"""Configuration modifiers.

Integrates configuration system with CORE's modifier pipeline.
"""

from dataclasses import dataclass
from enum import Enum

from yuna.config.types import ConfigValue
from yuna.modifiers.types import ModifierPriority


class ConfigModificationType(Enum):
    """How the modifier affects the config value.

    Values:
        SET: Replace value entirely
        ADD: Add to numeric value
        MULTIPLY: Multiply numeric value
        MAX: Take maximum of current and modifier value
        MIN: Take minimum of current and modifier value
    """

    SET = "set"
    ADD = "add"
    MULTIPLY = "multiply"
    MAX = "max"
    MIN = "min"


@dataclass(frozen=True)
class ConfigModifier:
    """Modifier that changes a configuration value.

    Examples:
        # Temporary cache upgrade (60 ticks)
        ConfigModifier(
            key="cache.size",
            value=32,
            modification_type=ConfigModificationType.SET,
            duration_ticks=60,
            priority=ModifierPriority.HIGH,
        )

        # Permanent sensor range boost
        ConfigModifier(
            key="sensor.range",
            value=1.5,
            modification_type=ConfigModificationType.MULTIPLY,
            duration_ticks=None,
            priority=ModifierPriority.NORMAL,
        )

        # Sensor damage (reduce range)
        ConfigModifier(
            key="sensor.range",
            value=0.8,
            modification_type=ConfigModificationType.MULTIPLY,
            duration_ticks=None,
            priority=ModifierPriority.HIGH,
        )
    """

    key: str
    value: ConfigValue
    modification_type: ConfigModificationType
    duration_ticks: int | None = None
    priority: ModifierPriority = ModifierPriority.NORMAL
    source: str = "config_modifier"

    def apply(self, base_value: ConfigValue) -> ConfigValue:
        """Apply modification to base value.

        Args:
            base_value: Current config value

        Returns:
            Modified config value

        Raises:
            ValueError: If modification type is unknown
        """
        if self.modification_type == ConfigModificationType.SET:
            return self.value

        if self.modification_type == ConfigModificationType.ADD:
            return base_value + self.value  # type: ignore[operator]

        if self.modification_type == ConfigModificationType.MULTIPLY:
            return base_value * self.value  # type: ignore[operator]

        if self.modification_type == ConfigModificationType.MAX:
            return max(base_value, self.value)

        if self.modification_type == ConfigModificationType.MIN:
            return min(base_value, self.value)

        raise ValueError(
            f"Unknown modification type: {self.modification_type}"
        )  # pragma: no cover


@dataclass
class ConfigModifierProcessor:
    """Processes config modifiers to compute final values.

    Integrates with CORE's modifier pipeline pattern.

    Usage:
        processor = ConfigModifierProcessor()
        modifiers = [modifier1, modifier2, modifier3]
        final_value = processor.apply_modifiers(
            base_value=100,
            modifiers=modifiers,
        )
    """

    @staticmethod
    def apply_modifiers(
        base_value: ConfigValue,
        modifiers: list[ConfigModifier],
    ) -> ConfigValue:
        """Apply modifiers in priority order.

        Order: CRITICAL (0) → HIGH (100) → NORMAL (200) → LOW (300)
        Within same priority: order preserved

        Args:
            base_value: Starting config value
            modifiers: List of modifiers to apply

        Returns:
            Final value after all modifiers applied
        """
        sorted_modifiers = sorted(
            modifiers,
            key=lambda m: m.priority.value,
        )

        current_value = base_value
        for modifier in sorted_modifiers:
            current_value = modifier.apply(current_value)

        return current_value
