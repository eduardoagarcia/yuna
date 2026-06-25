"""Condition helpers for modifier activation."""

from collections.abc import Callable
from typing import Any, cast

from yuna.modifiers.context import ModifierContext


class Conditions:
    """Factory for common modifier activation conditions.

    Provides reusable condition functions for conditional modifiers.
    Conditions are evaluated against ModifierContext during pipeline processing.

    Supports numeric comparisons (float/int) and equality checks (bool/str/any).

    Usage:
        # Numeric comparison
        modifier = Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.PERCENTAGE,
            value=0.20,
            priority=ModifierPriority.NORMAL,
            source="low_health_bonus",
            activation_condition=Conditions.stat_below("health", 50.0),
        )

        # Boolean check
        modifier = Modifier(
            entity_id=entity_id,
            stat="speed",
            modification_type=ModificationType.PERCENTAGE,
            value=0.30,
            priority=ModifierPriority.HIGH,
            source="combat_bonus",
            activation_condition=Conditions.stat_equals("in_combat", True),
        )

        # String check
        modifier = Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.MULTIPLICATIVE,
            value=2.0,
            priority=ModifierPriority.CRITICAL,
            source="elemental_affinity",
            activation_condition=Conditions.stat_equals("element", "fire"),
        )
    """

    @staticmethod
    def stat_above(
        stat_name: str, threshold: float
    ) -> Callable[[ModifierContext], bool]:
        """Create condition that activates when stat > threshold.

        Args:
            stat_name: Name of stat to check
            threshold: Minimum value for activation

        Returns:
            Condition function
        """

        def condition(context: ModifierContext) -> bool:
            if context.world is None:
                return False
            current_value = cast(
                float,
                context.world.get_stat(entity_id=context.entity_id, stat=stat_name),
            )
            return current_value > threshold

        return condition

    @staticmethod
    def stat_below(
        stat_name: str, threshold: float
    ) -> Callable[[ModifierContext], bool]:
        """Create condition that activates when stat < threshold.

        Args:
            stat_name: Name of stat to check
            threshold: Maximum value for activation

        Returns:
            Condition function
        """

        def condition(context: ModifierContext) -> bool:
            if context.world is None:
                return False
            current_value = cast(
                float,
                context.world.get_stat(entity_id=context.entity_id, stat=stat_name),
            )
            return current_value < threshold

        return condition

    @staticmethod
    def has_tag(tag: str) -> Callable[[ModifierContext], bool]:
        """Create condition that activates when entity has tag.

        Args:
            tag: Tag to check for

        Returns:
            Condition function
        """

        def condition(context: ModifierContext) -> bool:
            if context.world is None:
                return False
            entity_tags = context.world.get_entity_tags(entity_id=context.entity_id)
            return tag in entity_tags

        return condition

    @staticmethod
    def lacks_tag(tag: str) -> Callable[[ModifierContext], bool]:
        """Create condition that activates when entity lacks tag.

        Args:
            tag: Tag that must be absent

        Returns:
            Condition function
        """

        def condition(context: ModifierContext) -> bool:
            if context.world is None:
                return False
            entity_tags = context.world.get_entity_tags(entity_id=context.entity_id)
            return tag not in entity_tags

        return condition

    @staticmethod
    def tick_range(min_tick: int, max_tick: int) -> Callable[[ModifierContext], bool]:
        """Create condition that activates only during tick range.

        Args:
            min_tick: First tick of activation
            max_tick: Last tick of activation

        Returns:
            Condition function
        """

        def condition(context: ModifierContext) -> bool:
            if context.world is None:
                return False
            current_tick = cast(int, context.world.tick)
            return min_tick <= current_tick <= max_tick

        return condition

    @staticmethod
    def all_of(
        *conditions: Callable[[ModifierContext], bool],
    ) -> Callable[[ModifierContext], bool]:
        """Create condition that activates when all subconditions are true (AND).

        Args:
            *conditions: Condition functions to combine

        Returns:
            Combined condition function
        """

        def condition(context: ModifierContext) -> bool:
            return all(cond(context) for cond in conditions)

        return condition

    @staticmethod
    def any_of(
        *conditions: Callable[[ModifierContext], bool],
    ) -> Callable[[ModifierContext], bool]:
        """Create condition that activates when any subcondition is true (OR).

        Args:
            *conditions: Condition functions to combine

        Returns:
            Combined condition function
        """

        def condition(context: ModifierContext) -> bool:
            return any(cond(context) for cond in conditions)

        return condition

    @staticmethod
    def stat_equals(stat_name: str, value: Any) -> Callable[[ModifierContext], bool]:
        """Create condition that activates when stat equals value.

        Supports any type (bool, str, int, float, etc.) with direct equality check.

        Args:
            stat_name: Name of stat to check
            value: Expected value for activation

        Returns:
            Condition function

        Example:
            # Boolean stat
            Conditions.stat_equals("in_combat", True)

            # String stat
            Conditions.stat_equals("element", "fire")

            # Numeric stat
            Conditions.stat_equals("level", 10)
        """

        def condition(context: ModifierContext) -> bool:
            if context.world is None:
                return False
            current_value = context.world.get_stat(
                entity_id=context.entity_id, stat=stat_name
            )
            return bool(current_value == value)

        return condition

    @staticmethod
    def stat_not_equals(
        stat_name: str, value: Any
    ) -> Callable[[ModifierContext], bool]:
        """Create condition that activates when stat does not equal value.

        Supports any type (bool, str, int, float, etc.) with direct inequality check.

        Args:
            stat_name: Name of stat to check
            value: Value that must not match for activation

        Returns:
            Condition function

        Example:
            # Boolean stat (not in combat)
            Conditions.stat_not_equals("in_combat", True)

            # String stat (not fire element)
            Conditions.stat_not_equals("element", "fire")
        """

        def condition(context: ModifierContext) -> bool:
            if context.world is None:
                return False
            current_value = context.world.get_stat(
                entity_id=context.entity_id, stat=stat_name
            )
            return bool(current_value != value)

        return condition

    @staticmethod
    def stat_in(
        stat_name: str, values: frozenset[Any]
    ) -> Callable[[ModifierContext], bool]:
        """Create condition that activates when stat is in set of values.

        Supports any hashable type (bool, str, int, float, etc.).

        Args:
            stat_name: Name of stat to check
            values: Set of acceptable values for activation

        Returns:
            Condition function

        Example:
            # String stat (fire or ice element)
            Conditions.stat_in("element", frozenset({"fire", "ice"}))

            # Numeric stat (level 10, 20, or 30)
            Conditions.stat_in("level", frozenset({10, 20, 30}))
        """

        def condition(context: ModifierContext) -> bool:
            if context.world is None:
                return False
            current_value = context.world.get_stat(
                entity_id=context.entity_id, stat=stat_name
            )
            return bool(current_value in values)

        return condition

    @staticmethod
    def stat_not_in(
        stat_name: str, values: frozenset[Any]
    ) -> Callable[[ModifierContext], bool]:
        """Create condition that activates when stat is not in set of values.

        Supports any hashable type (bool, str, int, float, etc.).

        Args:
            stat_name: Name of stat to check
            values: Set of values that must not match for activation

        Returns:
            Condition function

        Example:
            # String stat (not fire or ice element)
            Conditions.stat_not_in("element", frozenset({"fire", "ice"}))

            # Numeric stat (not beginner levels)
            Conditions.stat_not_in("level", frozenset({1, 2, 3}))
        """

        def condition(context: ModifierContext) -> bool:
            if context.world is None:
                return False
            current_value = context.world.get_stat(
                entity_id=context.entity_id, stat=stat_name
            )
            return bool(current_value not in values)

        return condition
