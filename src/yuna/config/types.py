"""Configuration system types."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from yuna.config.validators import Validator
from yuna.exceptions import ConfigSchemaError

ConfigValue = int | float | str | bool


class ConfigResolver(Protocol):
    """Protocol for resolving config values.

    Used by DerivedConfigKey formulas to access other config values.
    Typically implemented by ConfigStore.
    """

    def get(self, key: str) -> ConfigValue: ...


@dataclass(frozen=True)
class ConfigConstraints[T: ConfigValue]:
    """Optional constraints for configuration values.

    Separates validation logic from core ConfigKey definition.
    Only specify constraints when needed.

    Example:
        ConfigConstraints(min_value=1, max_value=100)
        ConfigConstraints(validator=must_be_power_of_two)
    """

    min_value: T | None = None
    max_value: T | None = None
    validator: Validator[T] | None = None

    def validate(self, value: T, key: str) -> tuple[bool, str]:
        """Validate value against all constraints.

        Args:
            value: Value to validate
            key: Name of config key for error messages

        Returns:
            Tuple of (valid, error_message)
        """
        if self.min_value is not None and value < self.min_value:  # type: ignore[operator]
            return False, f"{key}: {value} < min {self.min_value}"

        if self.max_value is not None and value > self.max_value:  # type: ignore[operator]
            return False, f"{key}: {value} > max {self.max_value}"

        if self.validator is not None:
            valid, message = self.validator(value)
            if not valid:
                return False, f"{key}: {message}"

        return True, ""

    def clamp(self, value: T) -> T:
        """Clamp value to min/max constraints."""
        if self.min_value is not None:
            value = max(value, self.min_value)
        if self.max_value is not None:
            value = min(value, self.max_value)
        return value


@dataclass(frozen=True)
class ConfigKey[T: ConfigValue]:
    """Defines a single configuration key.

    Simplified design - constraints are optional and separate.

    Example:
        ConfigKey(
            name="cache.size",
            type=int,
            value=16,
            constraints=ConfigConstraints(min_value=1, max_value=256),
        )

        ConfigKey(name="enabled", type=bool, value=True)
    """

    name: str
    type: type[T]
    value: T
    constraints: ConfigConstraints[T] | None = None
    description: str = ""

    def __post_init__(self) -> None:
        if self.constraints is not None:
            valid, reason = self.constraints.validate(
                value=self.value,
                key=self.name,
            )
            if not valid:
                raise ConfigSchemaError(f"Invalid default for {self.name}: {reason}")

    def validate(self, value: T) -> tuple[bool, str]:
        """Validate value against type and constraints."""
        if not isinstance(value, self.type):
            return False, f"Expected {self.type.__name__}, got {type(value).__name__}"

        if self.constraints is not None:
            return self.constraints.validate(value=value, key=self.name)

        return True, ""

    def clamp(self, value: T) -> T:
        """Clamp value to constraints if present."""
        if self.constraints is not None:
            return self.constraints.clamp(value)
        return value


@dataclass(frozen=True)
class DerivedConfigKey[T: ConfigValue](ConfigKey[T]):
    """Config key with value computed from other keys via formula.

    Evaluated lazily at runtime with memoization for performance.
    Formulas are pure functions that take a ConfigResolver and return a value.

    Example:
        DerivedConfigKey(
            name="bot.battery_drain_per_tick",
            type=float,
            value=None,
            formula=lambda cfg: 1.0 / float(cfg.get("core.base_survival_ticks")),
            dependencies=("core.base_survival_ticks",),
            constraints=ConfigConstraints(min_value=0.0, max_value=0.01),
            description="Battery drain: 1.0 / base_survival_ticks",
        )
    """

    dependencies: tuple[str, ...] = field(default_factory=tuple)
    formula: Callable[[ConfigResolver], T] | None = None

    def __post_init__(self) -> None:
        """Skip validation - value will be computed lazily."""
        pass

    def evaluate(self, resolver: ConfigResolver) -> T:
        """Compute value using formula.

        Args:
            resolver: Config resolver (typically ConfigStore)

        Returns:
            Computed value

        Raises:
            ConfigSchemaError: If formula fails or returns wrong type
        """
        if self.formula is None:
            raise ConfigSchemaError(f"No formula defined for {self.name}")

        try:
            result = self.formula(resolver)
        except Exception as e:
            raise ConfigSchemaError(f"Formula for {self.name} failed: {e}") from e

        if not isinstance(result, self.type):
            raise ConfigSchemaError(
                f"{self.name}: formula returned {type(result).__name__}, "
                f"expected {self.type.__name__}"
            )

        if self.constraints is not None:
            valid, reason = self.constraints.validate(value=result, key=self.name)
            if not valid:
                raise ConfigSchemaError(
                    f"{self.name}: derived value failed constraints: {reason}"
                )

        return result
