"""Configuration for stat modifications."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from yuna.exceptions import ValidationError

if TYPE_CHECKING:
    from yuna.modifiers.applicator import StatApplicator
    from yuna.modifiers.interceptor import StatInterceptor
    from yuna.modifiers.reader import StatValueReader


class StackingRule(Enum):
    """Rule for stacking multiple modifiers.

    Values:
        ADD: Sum all modifier values
        MULTIPLY: Multiply all modifier values
        MAX: Take maximum value
        MIN: Take minimum value
    """

    ADD = auto()
    MULTIPLY = auto()
    MAX = auto()
    MIN = auto()


@dataclass(frozen=True)
class StatConfig:
    """Configuration for a stat.

    Attributes:
        name: Stat identifier
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        stacking_rule: How multiple modifiers combine
        precision: Decimal places to round to (None = no rounding)
    """

    name: str
    min_value: float
    max_value: float
    stacking_rule: StackingRule
    precision: int | None = None


@dataclass(frozen=True)
class CategoryStackingConfig:
    """Stacking rules for modifier category.

    Attributes:
        category: Category identifier
        stacking_rule: How modifiers in category stack
        max_stack_count: Maximum modifiers from category (None = unlimited)
        stack_merge_strategy: How to merge when exceeding max (newest, strongest, sum)
    """

    category: str
    stacking_rule: StackingRule
    max_stack_count: int | None = None
    stack_merge_strategy: str = "newest"


class ModifierConfig:
    """Registry for stat configurations.

    Responsibilities:
    - Store stat definitions
    - Retrieve stat config by name
    - Validate stat existence
    - Store category-specific stacking rules
    - Retrieve category stacking config
    - Store optional applicators for automatic stat application

    Usage:
        config = ModifierConfig()
        config.register_stat(
            name="health",
            min_value=0.0,
            max_value=100.0,
            stacking_rule=StackingRule.ADD,
        )
        config.register_applicator(
            stat="health",
            applicator=lambda entity_id, stat, value, world: apply_health(...),
        )
        config.register_category_stacking(
            category="equipment",
            stacking_rule=StackingRule.ADD,
            max_stack_count=5,
        )
        stat_config = config.get_stat_config(name="health")
        category_config = config.get_category_stacking(category="equipment")
    """

    def __init__(self) -> None:
        self._stats: dict[str, StatConfig] = {}
        self._category_stacking: dict[str, CategoryStackingConfig] = {}
        self._applicators: dict[str, StatApplicator] = {}
        self._value_readers: dict[str, StatValueReader] = {}
        self._interceptors: dict[str, list[StatInterceptor]] = {}

    def register_stat(
        self,
        name: str,
        min_value: float,
        max_value: float,
        stacking_rule: StackingRule,
        precision: int | None = None,
    ) -> None:
        """Register stat configuration.

        Args:
            name: Stat identifier
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            stacking_rule: How modifiers combine
            precision: Decimal places to round to (None = no rounding)
        """
        stat_config = StatConfig(
            name=name,
            min_value=min_value,
            max_value=max_value,
            stacking_rule=stacking_rule,
            precision=precision,
        )
        self._stats[name] = stat_config

    def get_stat_config(self, name: str) -> StatConfig:
        """Get stat configuration by name.

        Args:
            name: Stat identifier

        Returns:
            Stat configuration

        Raises:
            ValidationError: If stat not registered
        """
        if name not in self._stats:
            raise ValidationError(
                reason=f"Stat '{name}' not registered",
                field="name",
                value=name,
            )
        return self._stats[name]

    def has_stat(self, name: str) -> bool:
        """Check if stat is registered.

        Args:
            name: Stat identifier

        Returns:
            True if stat registered
        """
        return name in self._stats

    def clear(self) -> None:
        """Remove all registered stats."""
        self._stats.clear()

    def get_all_stat_names(self) -> list[str]:
        """Get list of all registered stat names.

        Returns:
            List of stat names
        """
        return list(self._stats.keys())

    def register_category_stacking(
        self,
        category: str,
        stacking_rule: StackingRule,
        max_stack_count: int | None = None,
        stack_merge_strategy: str = "newest",
    ) -> None:
        """Register category-specific stacking rules.

        Args:
            category: Category identifier
            stacking_rule: How modifiers in category stack
            max_stack_count: Maximum modifiers from category (None = unlimited)
            stack_merge_strategy: How to merge when exceeding max
        """
        category_config = CategoryStackingConfig(
            category=category,
            stacking_rule=stacking_rule,
            max_stack_count=max_stack_count,
            stack_merge_strategy=stack_merge_strategy,
        )
        self._category_stacking[category] = category_config

    def get_category_stacking(self, category: str) -> CategoryStackingConfig | None:
        """Get stacking config for category.

        Args:
            category: Category identifier

        Returns:
            Category stacking configuration or None if not registered
        """
        return self._category_stacking.get(category)

    def has_category_stacking(self, category: str) -> bool:
        """Check if category has stacking config.

        Args:
            category: Category identifier

        Returns:
            True if category has stacking config
        """
        return category in self._category_stacking

    def register_applicator(self, stat: str, applicator: StatApplicator) -> None:
        """Register applicator for automatic stat application.

        Optional mechanism - if registered, ApplyStage automatically
        writes final values to components. If not registered, game
        must manually read final_values dict.

        Args:
            stat: Stat identifier
            applicator: Callable that writes value to component
        """
        self._applicators[stat] = applicator

    def get_applicator(self, stat: str) -> StatApplicator | None:
        """Get applicator for stat.

        Args:
            stat: Stat identifier

        Returns:
            Applicator function or None if not registered
        """
        return self._applicators.get(stat)

    def has_applicator(self, stat: str) -> bool:
        """Check if stat has applicator registered.

        Args:
            stat: Stat identifier

        Returns:
            True if applicator registered
        """
        return stat in self._applicators

    def register_value_reader(self, stat: str, reader: StatValueReader) -> None:
        """Register value reader for reading current stat values.

        Optional mechanism - if registered, StackStage reads current
        component value as baseline for stacking. If not registered,
        baseline defaults to 0.0.

        Args:
            stat: Stat identifier
            reader: Callable that reads current value from component
        """
        self._value_readers[stat] = reader

    def get_value_reader(self, stat: str) -> StatValueReader | None:
        """Get value reader for stat.

        Args:
            stat: Stat identifier

        Returns:
            Reader function or None if not registered
        """
        return self._value_readers.get(stat)

    def has_value_reader(self, stat: str) -> bool:
        """Check if stat has value reader registered.

        Args:
            stat: Stat identifier

        Returns:
            True if value reader registered
        """
        return stat in self._value_readers

    def register_interceptor(self, stat: str, interceptor: StatInterceptor) -> None:
        """Register interceptor for stat value interception.

        Multiple interceptors can be registered for the same stat and will be
        chained in registration order.

        Args:
            stat: Stat identifier
            interceptor: Callable that intercepts and potentially reroutes value
        """
        if stat not in self._interceptors:
            self._interceptors[stat] = []
        self._interceptors[stat].append(interceptor)

    def get_interceptors(self, stat: str) -> list[StatInterceptor]:
        """Get all interceptors for stat in registration order.

        Args:
            stat: Stat identifier

        Returns:
            List of interceptor functions (empty if none registered)
        """
        return self._interceptors.get(stat, [])

    def has_interceptor(self, stat: str) -> bool:
        """Check if stat has any interceptors registered.

        Args:
            stat: Stat identifier

        Returns:
            True if one or more interceptors registered
        """
        return stat in self._interceptors and len(self._interceptors[stat]) > 0
