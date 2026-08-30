"""Formula pattern registry for reusable config derivations."""

from collections.abc import Callable
from dataclasses import dataclass

from yuna.config.types import ConfigResolver, ConfigValue
from yuna.exceptions import ConfigSchemaError


@dataclass(frozen=True)
class FormulaPattern:
    """Reusable formula pattern with parameter substitution.

    A pattern is a template for creating formula functions. It defines:
    - Dependencies: Config keys the formula needs
    - Factory: Function that takes parameters and returns a formula function

    Example:
        pattern = FormulaPattern(
            dependencies=("core.baseline", "core.multiplier"),
            factory=lambda value: lambda cfg: (
                value * float(cfg.get("core.multiplier"))
                / float(cfg.get("core.baseline"))
            )
        )
    """

    dependencies: tuple[str, ...]
    factory: Callable[..., Callable[[ConfigResolver], ConfigValue]]


class FormulaPatternRegistry:
    """Registry for reusable formula patterns.

    Allows registration of formula patterns that can be instantiated
    with specific parameters. Patterns are game-agnostic and reusable.

    Example:
        registry = FormulaPatternRegistry()

        registry.register(
            name="linear_cost",
            dependencies=("core.baseline",),
            factory=lambda multiplier: lambda cfg: (
                multiplier / float(cfg.get("core.baseline"))
            )
        )

        formula, deps = registry.create(name="linear_cost", multiplier=0.5)
    """

    def __init__(self) -> None:
        self._patterns: dict[str, FormulaPattern] = {}

    def register(
        self,
        name: str,
        dependencies: tuple[str, ...],
        factory: Callable[..., Callable[[ConfigResolver], ConfigValue]],
    ) -> None:
        """Register a formula pattern.

        Idempotent: if pattern already registered, silently returns.

        Args:
            name: Unique pattern identifier
            dependencies: Config keys the formula depends on
            factory: Function that takes parameters and returns formula function

        Example:
            registry.register(
                name="driver-cost",
                dependencies=("core.driver_baseline", "core.base_ticks"),
                factory=lambda mult: lambda cfg: (
                    mult * float(cfg.get("core.driver_baseline"))
                    / float(cfg.get("core.base_ticks"))
                )
            )
        """
        if name in self._patterns:
            return

        self._patterns[name] = FormulaPattern(
            dependencies=dependencies,
            factory=factory,
        )

    def create(
        self,
        name: str,
        **params,
    ) -> tuple[Callable[[ConfigResolver], ConfigValue], tuple[str, ...]]:
        """Create formula instance from pattern with parameters.

        Args:
            name: Registered pattern name
            **params: Parameters to pass to pattern factory

        Returns:
            Tuple of (formula_function, dependencies)

        Raises:
            ConfigSchemaError: If pattern not found

        Example:
            formula, deps = registry.create(name="driver-cost", mult=0.2)
        """
        if name not in self._patterns:
            raise ConfigSchemaError(f"Unknown formula pattern: {name}")

        pattern = self._patterns[name]

        try:
            formula = pattern.factory(**params)
        except TypeError as e:
            raise ConfigSchemaError(
                f"Invalid parameters for pattern '{name}': {e}"
            ) from e

        return formula, pattern.dependencies

    def has_pattern(self, name: str) -> bool:
        """Check if pattern is registered.

        Args:
            name: Pattern name to check

        Returns:
            True if pattern registered
        """
        return name in self._patterns

    def list_patterns(self) -> list[str]:
        """List all registered pattern names.

        Returns:
            List of pattern names
        """
        return list(self._patterns.keys())
