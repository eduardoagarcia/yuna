"""Schemas to declare available configuration keys, types, constraints, defaults."""

from collections.abc import Callable
from typing import Any, ClassVar

from yuna.config.patterns import FormulaPatternRegistry
from yuna.config.types import (
    ConfigConstraints,
    ConfigKey,
    ConfigResolver,
    ConfigValue,
    DerivedConfigKey,
)
from yuna.exceptions import ConfigSchemaError


class ConfigSchema:
    """Registry of configuration keys with namespace support.

    Supports nested schemas via composition with automatic key prefixing.

    Example:
        wall_schema = ConfigSchema(namespace="wall")
        wall_schema.define("density", float, value=0.085)

        game_schema = ConfigSchema(namespace="game")
        game_schema.merge(wall_schema)

        main_schema = ConfigSchema()
        main_schema.merge(game_schema)

        main_schema.has_key("game.wall.density")
    """

    _formula_patterns: ClassVar[FormulaPatternRegistry] = FormulaPatternRegistry()

    def __init__(self, namespace: str = "") -> None:
        self._namespace = namespace
        self._keys: dict[str, ConfigKey] = {}

    def define(
        self,
        key: str,
        value_type: type[ConfigValue],
        value: ConfigValue,
        constraints: ConfigConstraints | None = None,
        description: str = "",
    ) -> None:
        """Define a config key in this schema.

        Key is automatically prefixed with schema namespace.

        Example:
            schema = ConfigSchema(namespace="board")
            schema.define("width", int, value=32)

        Args:
            key: Key name (will be prefixed with namespace)
            value_type: Type of config value
            value: Default value
            constraints: Optional validation constraints
            description: Human-readable description
        """
        full_key = self._build_key_name(key)
        config_key = ConfigKey(
            name=full_key,
            type=value_type,
            value=value,
            constraints=constraints,
            description=description,
        )
        self._register_key(config_key)

    def register(self, key: ConfigKey) -> None:
        """Register a pre-built ConfigKey.

        Key name is NOT prefixed with namespace.
        Use define() for automatic namespace prefixing.
        """
        self._register_key(key)

    def merge(self, other: ConfigSchema) -> None:
        """Merge another schema into this one.

        Keys from other schema are prefixed with this schema's namespace.

        Example:
            child = ConfigSchema(namespace="child")
            child.define("key", int, value=1)

            parent = ConfigSchema(namespace="parent")
            parent.merge(child)

            parent.has_key("parent.child.key")
        """
        for key in other._keys.values():
            prefixed_key: ConfigKey[Any] | DerivedConfigKey[Any]
            if isinstance(key, DerivedConfigKey):
                prefixed_key = DerivedConfigKey(
                    name=self._build_key_name(key.name),
                    type=key.type,
                    value=key.value,
                    formula=key.formula,
                    dependencies=key.dependencies,
                    constraints=key.constraints,
                    description=key.description,
                )
            else:
                prefixed_key = ConfigKey(
                    name=self._build_key_name(key.name),
                    type=key.type,
                    value=key.value,
                    constraints=key.constraints,
                    description=key.description,
                )
            self._register_key(prefixed_key)

    def get_key(self, name: str) -> ConfigKey:
        """Get registered key by name."""
        if name not in self._keys:
            raise ConfigSchemaError(f"Unknown config key: {name}")
        return self._keys[name]

    def has_key(self, name: str) -> bool:
        """Check if key exists."""
        return name in self._keys

    def get_all_keys(self) -> dict[str, ConfigKey]:
        """Get all registered keys."""
        return dict(self._keys)

    def validate_value(self, name: str, value: Any) -> tuple[bool, str]:
        """Validate a value for a key."""
        key = self.get_key(name=name)
        return key.validate(value=value)

    def _build_key_name(self, key: str) -> str:
        """Build full key name with namespace prefix."""
        if self._namespace:
            return f"{self._namespace}.{key}"
        return key

    def _register_key(self, key: ConfigKey) -> None:
        """Register a config key."""
        if key.name in self._keys:
            raise ConfigSchemaError(f"Key {key.name} already registered")
        self._keys[key.name] = key

    def define_derived(
        self,
        key: str,
        value_type: type[ConfigValue],
        formula: Callable[[ConfigResolver], ConfigValue],
        dependencies: tuple[str, ...] = (),
        constraints: ConfigConstraints | None = None,
        description: str = "",
    ) -> None:
        """Define a config key with value computed from formula.

        Args:
            key: Key name (prefixed with namespace)
            value_type: Type of computed value
            formula: Pure function taking ConfigResolver, returning value
            dependencies: Tuple of source key names for validation
            constraints: Validation constraints for computed value
            description: Human-readable formula explanation

        Example:
            schema.define_derived(
                key="battery_drain_per_tick",
                value_type=float,
                formula=lambda cfg: 1.0 / cfg.get("core.base_survival_ticks"),
                dependencies=("core.base_survival_ticks",),
                constraints=ConfigConstraints(min_value=0.0),
            )
        """
        full_key = self._build_key_name(key)

        derived_key = DerivedConfigKey(
            name=full_key,
            type=value_type,
            value=None,
            formula=formula,
            dependencies=dependencies,
            constraints=constraints,
            description=description,
        )

        self._register_key(derived_key)

    @classmethod
    def register_formula_pattern(
        cls,
        name: str,
        dependencies: tuple[str, ...],
        factory: Callable[..., Callable[[ConfigResolver], ConfigValue]],
    ) -> None:
        """Register a reusable formula pattern (class-level).

        Patterns are shared across all ConfigSchema instances.

        Args:
            name: Unique pattern identifier
            dependencies: Config keys the formula depends on
            factory: Function that takes parameters and returns formula function

        Example:
            ConfigSchema.register_formula_pattern(
                name="driver-cost",
                dependencies=("core.driver_baseline", "core.base_ticks"),
                factory=lambda mult: lambda cfg: (
                    mult * float(cfg.get("core.driver_baseline"))
                    / float(cfg.get("core.base_ticks"))
                )
            )
        """
        cls._formula_patterns.register(
            name=name,
            dependencies=dependencies,
            factory=factory,
        )

    def define_derived_from_pattern(
        self,
        key: str,
        value_type: type[ConfigValue],
        pattern: str,
        pattern_params: dict[str, Any] | None = None,
        constraints: ConfigConstraints | None = None,
        description: str = "",
    ) -> None:
        """Define derived config key using registered formula pattern.

        Args:
            key: Key name (prefixed with namespace)
            value_type: Type of computed value
            pattern: Registered pattern name
            pattern_params: Parameters to pass to pattern factory
            constraints: Validation constraints for computed value
            description: Human-readable formula explanation

        Example:
            schema.define_derived_from_pattern(
                key="battery_cost",
                value_type=float,
                pattern="driver-cost",
                pattern_params={"mult": 0.2},
                description="Navigation battery cost (0.2× passive drain)",
            )
        """
        if pattern_params is None:
            pattern_params = {}

        formula, dependencies = self._formula_patterns.create(
            name=pattern,
            **pattern_params,
        )

        self.define_derived(
            key=key,
            value_type=value_type,
            formula=formula,
            dependencies=dependencies,
            constraints=constraints,
            description=description,
        )

    def validate_dependencies(self) -> None:
        """Validate all derived key dependencies exist and have no cycles.

        Should be called after schema is fully constructed.

        Raises:
            ConfigSchemaError: If dependency missing or circular
        """
        graph: dict[str, list[str]] = {}

        for key_name, config_key in self._keys.items():
            if isinstance(config_key, DerivedConfigKey):
                graph[key_name] = list(config_key.dependencies)

                for dep in config_key.dependencies:
                    if not self.has_key(dep):
                        raise ConfigSchemaError(
                            f"{key_name} depends on unknown key: {dep}"
                        )

        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    raise ConfigSchemaError(
                        f"Circular dependency detected involving: {node}"
                    )
