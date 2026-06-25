"""Value scaling and interpolation functions for modifiers."""

import math
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yuna.modifiers.context import ModifierContext

EASE_IN_OUT_THRESHOLD = 0.5


class ValueCalculators:
    """Factory for common value calculation patterns."""

    @staticmethod
    def scale_by_stat(
        stat_name: str,
        multiplier: float = 1.0,
        additive: bool = False,
    ) -> Callable[[float, ModifierContext], float]:
        """Scale value by entity stat.

        Args:
            stat_name: Stat to scale by
            multiplier: Scaling multiplier
            additive: If True, add scaled value; if False, multiply

        Returns:
            Calculator function that scales value by stat

        Example:
            # Add 50% of strength to damage
            calculator = ValueCalculators.scale_by_stat(
                stat_name="strength",
                multiplier=0.5,
                additive=True,
            )
            # If strength=100, base_value=10 -> 10 + (100 * 0.5) = 60
        """

        def calculator(base_value: float, context: ModifierContext) -> float:
            if context.world is None or context.entity_id is None:
                return base_value

            stat_value = float(
                context.world.get_stat(entity_id=context.entity_id, stat=stat_name)
            )
            scaled = stat_value * multiplier

            if additive:
                return base_value + scaled
            return base_value * scaled

        return calculator

    @staticmethod
    def scale_by_percentage(
        stat_name: str,
        percentage: float,
    ) -> Callable[[float, ModifierContext], float]:
        """Scale value by percentage of stat.

        Args:
            stat_name: Stat to get percentage from
            percentage: Percentage value (0.1 = 10%)

        Returns:
            Calculator function that returns percentage of stat

        Example:
            # 10% of max_health
            calculator = ValueCalculators.scale_by_percentage(
                stat_name="max_health",
                percentage=0.10,
            )
            # If max_health=1000 -> 100
        """

        def calculator(base_value: float, context: ModifierContext) -> float:
            if context.world is None or context.entity_id is None:
                return base_value

            stat_value = float(
                context.world.get_stat(entity_id=context.entity_id, stat=stat_name)
            )
            return stat_value * percentage

        return calculator

    @staticmethod
    def diminishing_returns(
        base_value: float,
        diminishing_factor: float = 0.5,
    ) -> Callable[[float, ModifierContext], float]:
        """Apply diminishing returns based on modifier count.

        Formula: base_value * (1 - (1 - diminishing_factor) ^ stack_count)

        Args:
            base_value: Base value before diminishing
            diminishing_factor: Diminishing factor (0-1)

        Returns:
            Calculator that applies diminishing returns

        Example:
            # Each stack gives diminishing value
            calculator = ValueCalculators.diminishing_returns(
                base_value=10.0,
                diminishing_factor=0.6,
            )
            # Stack 1: 10.0 * (1 - (1 - 0.6)^1) = 6.0
            # Stack 2: 10.0 * (1 - (1 - 0.6)^2) = 8.4
            # Stack 3: 10.0 * (1 - (1 - 0.6)^3) = 9.36
        """

        def calculator(value: float, context: ModifierContext) -> float:
            modifier_count = len(context.modifiers)
            if modifier_count <= 1:
                return base_value

            diminished = base_value * (
                1.0 - ((1.0 - diminishing_factor) ** modifier_count)
            )
            return diminished

        return calculator


class CurveFunctions:
    """Common mathematical curves for value transformation."""

    @staticmethod
    def linear(x: float) -> float:
        """Identity function: y = x"""
        return x

    @staticmethod
    def quadratic(x: float) -> float:
        """Quadratic growth: y = x^2"""
        return x * x

    @staticmethod
    def cubic(x: float) -> float:
        """Cubic growth: y = x^3"""
        return x * x * x

    @staticmethod
    def square_root(x: float) -> float:
        """Square root: y = sqrt(x)"""
        return math.sqrt(abs(x)) * (1.0 if x >= 0 else -1.0)

    @staticmethod
    def exponential(base: float = 2.0) -> Callable[[float], float]:
        """Exponential growth: y = base^x"""

        def curve(x: float) -> float:
            return float(base**x)

        return curve

    @staticmethod
    def logarithmic(base: float = 2.0) -> Callable[[float], float]:
        """Logarithmic growth: y = log_base(x)"""

        def curve(x: float) -> float:
            if x <= 0:
                return 0.0
            return math.log(x, base)

        return curve

    @staticmethod
    def sigmoid(steepness: float = 1.0) -> Callable[[float], float]:
        """S-curve: y = 1 / (1 + e^(-steepness * x))"""

        def curve(x: float) -> float:
            return 1.0 / (1.0 + math.exp(-steepness * x))

        return curve

    @staticmethod
    def inverse(x: float) -> float:
        """Inverse: y = 1/x"""
        if x == 0:
            return 0.0
        return 1.0 / x


class TimeInterpolation:
    """Time-based value interpolation methods."""

    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    SPIKE = "spike"

    @staticmethod
    def interpolate(
        start_value: float,
        end_value: float,
        progress: float,
        method: str,
    ) -> float:
        """Interpolate between start and end based on progress [0, 1].

        Args:
            start_value: Starting value
            end_value: Ending value
            progress: Progress from 0.0 to 1.0
            method: Interpolation method

        Returns:
            Interpolated value

        Example:
            # Linear interpolation from 0 to 100 at 50% progress
            value = TimeInterpolation.interpolate(
                start_value=0.0,
                end_value=100.0,
                progress=0.5,
                method=TimeInterpolation.LINEAR,
            )
            # Returns: 50.0
        """
        progress = max(0.0, min(1.0, progress))

        if method == TimeInterpolation.LINEAR:
            return start_value + (end_value - start_value) * progress

        if method == TimeInterpolation.EASE_IN:
            t = progress * progress
            return start_value + (end_value - start_value) * t

        if method == TimeInterpolation.EASE_OUT:
            t = 1.0 - (1.0 - progress) * (1.0 - progress)
            return start_value + (end_value - start_value) * t

        if method == TimeInterpolation.EASE_IN_OUT:
            t = (
                2.0 * progress * progress
                if progress < EASE_IN_OUT_THRESHOLD
                else 1.0 - ((-2.0 * progress + 2.0) ** 2) / 2.0
            )
            return start_value + (end_value - start_value) * t

        if method == TimeInterpolation.SPIKE:
            t = 1.0 - abs(2.0 * progress - 1.0)
            return start_value + (end_value - start_value) * t

        return start_value + (end_value - start_value) * progress
