"""Tests for formula pattern registry."""

from collections.abc import Callable
from typing import cast

import pytest
from faker import Faker

from yuna.config.patterns import (
    FormulaPattern,
    FormulaPatternRegistry,
)
from yuna.config.types import ConfigResolver, ConfigValue
from yuna.exceptions import ConfigSchemaError

fake = Faker()


class MockConfigResolver:
    """Mock config resolver for testing formulas."""

    def __init__(self, values: dict[str, float | int | str | bool]) -> None:
        self._values = values

    def get(self, key: str) -> float | int | str | bool:
        """Get config value by key."""
        return self._values[key]


def test_formula_pattern_creation() -> None:
    """Test creating formula pattern with dependencies and factory."""
    dependency1 = f"{fake.word()}.{fake.word()}"
    dependency2 = f"{fake.word()}.{fake.word()}"
    multiplier = fake.pyfloat(min_value=0.1, max_value=2.0)

    def factory(value: float) -> Callable[[ConfigResolver], ConfigValue]:
        def formula(cfg: ConfigResolver) -> float:
            return value * float(cfg.get(dependency1)) / float(cfg.get(dependency2))

        return formula

    pattern = FormulaPattern(
        dependencies=(dependency1, dependency2),
        factory=factory,
    )

    assert pattern.dependencies == (dependency1, dependency2)
    assert pattern.factory is factory

    formula = pattern.factory(multiplier)
    assert callable(formula)


def test_formula_pattern_immutability() -> None:
    """Test that FormulaPattern is immutable (frozen dataclass)."""
    dependency = f"{fake.word()}.{fake.word()}"

    def factory(value: float) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: value * cast(float, cfg.get(dependency))

    pattern = FormulaPattern(
        dependencies=(dependency,),
        factory=factory,
    )

    with pytest.raises(expected_exception=AttributeError):
        pattern.dependencies = ("new.dependency",)  # type: ignore[misc]

    with pytest.raises(expected_exception=AttributeError):
        pattern.factory = lambda x: lambda cfg: x  # type: ignore[misc]


def test_formula_pattern_registry_initialization() -> None:
    """Test registry initialization."""
    registry = FormulaPatternRegistry()
    assert len(registry._patterns) == 0


def test_register_pattern() -> None:
    """Test registering a formula pattern."""
    registry = FormulaPatternRegistry()
    pattern_name = fake.word()
    dependency = f"{fake.word()}.{fake.word()}"

    def factory(mult: float) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: mult * float(cfg.get(dependency))

    registry.register(
        name=pattern_name,
        dependencies=(dependency,),
        factory=factory,
    )

    assert pattern_name in registry._patterns
    pattern = registry._patterns[pattern_name]
    assert pattern.dependencies == (dependency,)
    assert pattern.factory is factory


def test_register_pattern_idempotent() -> None:
    """Test that registering same pattern twice is idempotent."""
    registry = FormulaPatternRegistry()
    pattern_name = fake.word()
    dependency = f"{fake.word()}.{fake.word()}"

    def factory1(mult: float) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: mult * float(cfg.get(dependency))

    def factory2(mult: float) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: mult * float(cfg.get(dependency)) * 2.0

    registry.register(
        name=pattern_name,
        dependencies=(dependency,),
        factory=factory1,
    )

    registry.register(
        name=pattern_name,
        dependencies=(dependency,),
        factory=factory2,
    )

    pattern = registry._patterns[pattern_name]
    assert pattern.factory is factory1


def test_create_formula_from_pattern() -> None:
    """Test creating formula instance from registered pattern."""
    registry = FormulaPatternRegistry()
    pattern_name = fake.word()
    dependency = f"{fake.word()}.{fake.word()}"
    multiplier = fake.pyfloat(min_value=0.1, max_value=2.0)
    base_value = fake.pyfloat(min_value=10.0, max_value=100.0)

    def factory(mult: float) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: mult * float(cfg.get(dependency))

    registry.register(
        name=pattern_name,
        dependencies=(dependency,),
        factory=factory,
    )

    formula, dependencies = registry.create(name=pattern_name, mult=multiplier)

    assert dependencies == (dependency,)
    assert callable(formula)

    resolver = MockConfigResolver({dependency: base_value})
    result = formula(resolver)
    assert result == multiplier * base_value


def test_create_formula_unknown_pattern_raises_error() -> None:
    """Test that creating formula from unknown pattern raises error."""
    registry = FormulaPatternRegistry()
    unknown_pattern = fake.word()
    multiplier = fake.pyfloat(min_value=0.1, max_value=2.0)

    with pytest.raises(
        expected_exception=ConfigSchemaError,
        match=f"Unknown formula pattern: {unknown_pattern}",
    ):
        registry.create(name=unknown_pattern, mult=multiplier)


def test_create_formula_invalid_parameters_raises_error() -> None:
    """Test that creating formula with invalid parameters raises error."""
    registry = FormulaPatternRegistry()
    pattern_name = fake.word()
    dependency = f"{fake.word()}.{fake.word()}"

    def factory(mult: float, other: int) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: mult * float(cfg.get(dependency)) + other

    registry.register(
        name=pattern_name,
        dependencies=(dependency,),
        factory=factory,
    )

    with pytest.raises(
        expected_exception=ConfigSchemaError,
        match=f"Invalid parameters for pattern '{pattern_name}'",
    ):
        registry.create(name=pattern_name, wrong_param=5.0)


def test_create_formula_with_multiple_parameters() -> None:
    """Test creating formula with multiple parameters."""
    registry = FormulaPatternRegistry()
    pattern_name = fake.word()
    dep1 = f"{fake.unique.word()}.{fake.unique.word()}"
    dep2 = f"{fake.unique.word()}.{fake.unique.word()}"
    mult = fake.pyfloat(min_value=0.1, max_value=2.0)
    offset = fake.pyfloat(min_value=0.0, max_value=10.0)
    base1 = fake.pyfloat(min_value=10.0, max_value=100.0)
    base2 = fake.pyfloat(min_value=10.0, max_value=100.0)

    def factory(
        multiplier: float, add: float
    ) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: (
            multiplier * float(cfg.get(dep1)) / float(cfg.get(dep2)) + add
        )

    registry.register(
        name=pattern_name,
        dependencies=(dep1, dep2),
        factory=factory,
    )

    formula, dependencies = registry.create(
        name=pattern_name,
        multiplier=mult,
        add=offset,
    )

    assert dependencies == (dep1, dep2)

    resolver = MockConfigResolver({dep1: base1, dep2: base2})
    result = formula(resolver)
    expected = mult * base1 / base2 + offset
    assert abs(result - expected) < 0.0001


def test_has_pattern() -> None:
    """Test checking if pattern is registered."""
    registry = FormulaPatternRegistry()
    pattern_name = fake.word()
    dependency = f"{fake.word()}.{fake.word()}"

    assert not registry.has_pattern(pattern_name)

    def factory(mult: float) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: mult * float(cfg.get(dependency))

    registry.register(
        name=pattern_name,
        dependencies=(dependency,),
        factory=factory,
    )

    assert registry.has_pattern(pattern_name)


def test_list_patterns() -> None:
    """Test listing all registered pattern names."""
    registry = FormulaPatternRegistry()
    assert registry.list_patterns() == []

    pattern1 = fake.unique.word()
    pattern2 = fake.unique.word()
    pattern3 = fake.unique.word()
    dependency = f"{fake.word()}.{fake.word()}"

    def factory(mult: float) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: mult * float(cfg.get(dependency))

    registry.register(name=pattern1, dependencies=(dependency,), factory=factory)
    registry.register(name=pattern2, dependencies=(dependency,), factory=factory)
    registry.register(name=pattern3, dependencies=(dependency,), factory=factory)

    patterns = registry.list_patterns()
    assert len(patterns) == 3
    assert pattern1 in patterns
    assert pattern2 in patterns
    assert pattern3 in patterns


def test_create_formula_with_complex_logic() -> None:
    """Test creating formula with complex calculation logic."""
    registry = FormulaPatternRegistry()
    pattern_name = fake.word()
    baseline_key = f"{fake.unique.word()}.{fake.unique.word()}"
    ticks_key = f"{fake.unique.word()}.{fake.unique.word()}"
    baseline = fake.pyfloat(min_value=50.0, max_value=150.0)
    ticks = fake.random_int(min=100, max=1000)
    mult = fake.pyfloat(min_value=0.1, max_value=0.5)

    def driver_cost_factory(
        multiplier: float,
    ) -> Callable[[ConfigResolver], ConfigValue]:
        def formula(cfg: ConfigResolver) -> float:
            base = float(cfg.get(baseline_key))
            tick_count = float(cfg.get(ticks_key))
            return (multiplier * base) / tick_count

        return formula

    registry.register(
        name=pattern_name,
        dependencies=(baseline_key, ticks_key),
        factory=driver_cost_factory,
    )

    formula, dependencies = registry.create(name=pattern_name, multiplier=mult)

    assert len(dependencies) == 2
    assert baseline_key in dependencies
    assert ticks_key in dependencies

    resolver = MockConfigResolver({baseline_key: baseline, ticks_key: ticks})
    result = formula(resolver)
    expected = (mult * baseline) / ticks
    assert abs(result - expected) < 0.000001


def test_pattern_with_no_dependencies() -> None:
    """Test pattern with empty dependencies tuple."""
    registry = FormulaPatternRegistry()
    pattern_name = fake.word()
    constant = fake.pyfloat(min_value=1.0, max_value=100.0)

    def constant_factory(value: float) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: value

    registry.register(
        name=pattern_name,
        dependencies=(),
        factory=constant_factory,
    )

    formula, dependencies = registry.create(name=pattern_name, value=constant)

    assert dependencies == ()
    assert callable(formula)

    resolver = MockConfigResolver({})
    result = formula(resolver)
    assert result == constant


def test_multiple_patterns_independent() -> None:
    """Test that multiple patterns are stored independently."""
    registry = FormulaPatternRegistry()
    pattern1 = fake.unique.word()
    pattern2 = fake.unique.word()
    dep1 = f"{fake.word()}.{fake.word()}"
    dep2 = f"{fake.word()}.{fake.word()}"

    def factory1(mult: float) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: mult * float(cfg.get(dep1))

    def factory2(mult: float) -> Callable[[ConfigResolver], ConfigValue]:
        return lambda cfg: mult * float(cfg.get(dep2))

    registry.register(name=pattern1, dependencies=(dep1,), factory=factory1)
    registry.register(name=pattern2, dependencies=(dep2,), factory=factory2)

    formula1, deps1 = registry.create(name=pattern1, mult=2.0)
    formula2, deps2 = registry.create(name=pattern2, mult=3.0)

    assert deps1 == (dep1,)
    assert deps2 == (dep2,)

    resolver1 = MockConfigResolver({dep1: 10.0})
    resolver2 = MockConfigResolver({dep2: 20.0})

    assert formula1(resolver1) == 20.0
    assert formula2(resolver2) == 60.0
