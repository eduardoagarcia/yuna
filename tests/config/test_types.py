"""Tests for config types."""

from typing import cast

import pytest
from faker import Faker

from yuna.config.types import (
    ConfigConstraints,
    ConfigResolver,
    DerivedConfigKey,
)
from yuna.exceptions import ConfigSchemaError

fake = Faker()


class MockConfigResolver:
    """Mock config resolver for testing."""

    def __init__(self, values: dict[str, float | int | str | bool]) -> None:
        self._values = values

    def get(self, key: str) -> float | int | str | bool:
        """Get config value by key."""
        return self._values[key]


def test_derived_config_key_post_init_skips_validation() -> None:
    """Test that DerivedConfigKey __post_init__ skips validation."""
    key_name = f"{fake.word()}.{fake.word()}"
    min_value = fake.random_int(min=10, max=100)
    max_value = fake.random_int(min=1, max=5)

    derived = DerivedConfigKey[int](
        name=key_name,
        type=int,
        value=None,  # type: ignore[arg-type]
        formula=lambda cfg: 50,
        dependencies=(),
        constraints=ConfigConstraints(min_value=min_value, max_value=max_value),
    )

    assert derived.name == key_name
    assert derived.constraints is not None


def test_derived_config_key_evaluate_no_formula_raises_error() -> None:
    """Test that evaluating without formula raises error."""
    key_name = f"{fake.word()}.{fake.word()}"

    derived = DerivedConfigKey[float](
        name=key_name,
        type=float,
        value=None,  # type: ignore[arg-type]
        formula=None,
        dependencies=(),
    )

    resolver = MockConfigResolver({})

    with pytest.raises(
        expected_exception=ConfigSchemaError,
        match=f"No formula defined for {key_name}",
    ):
        derived.evaluate(resolver=resolver)


def test_derived_config_key_evaluate_formula_raises_error() -> None:
    """Test that formula execution error is caught and wrapped."""
    key_name = f"{fake.word()}.{fake.word()}"
    missing_key = f"{fake.word()}.{fake.word()}"

    def failing_formula(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(missing_key))

    derived = DerivedConfigKey[float](
        name=key_name,
        type=float,
        value=None,  # type: ignore[arg-type]
        formula=failing_formula,
        dependencies=(missing_key,),
    )

    resolver = MockConfigResolver({})

    with pytest.raises(
        expected_exception=ConfigSchemaError,
        match=f"Formula for {key_name} failed",
    ):
        derived.evaluate(resolver=resolver)


def test_derived_config_key_evaluate_wrong_type_raises_error() -> None:
    """Test that formula returning wrong type raises error."""
    key_name = f"{fake.word()}.{fake.word()}"
    base_key = f"{fake.word()}.{fake.word()}"
    base_value = fake.word()

    def wrong_type_formula(cfg: ConfigResolver) -> str:
        return str(cfg.get(base_key))

    derived = DerivedConfigKey[float](
        name=key_name,
        type=float,
        value=None,  # type: ignore[arg-type]
        formula=wrong_type_formula,  # type: ignore[arg-type]
        dependencies=(base_key,),
    )

    resolver = MockConfigResolver({base_key: base_value})

    with pytest.raises(
        expected_exception=ConfigSchemaError,
        match=f"{key_name}: formula returned str, expected float",
    ):
        derived.evaluate(resolver=resolver)


def test_derived_config_key_evaluate_violates_constraints_raises_error() -> None:
    """Test that formula result violating constraints raises error."""
    key_name = f"{fake.word()}.{fake.word()}"
    base_key = f"{fake.word()}.{fake.word()}"
    base_value = fake.random_int(min=1000, max=10000)
    min_value = fake.random_int(min=1, max=10)
    max_value = fake.random_int(min=11, max=100)

    def large_value_formula(cfg: ConfigResolver) -> int:
        return cast(int, cfg.get(base_key))

    derived = DerivedConfigKey[int](
        name=key_name,
        type=int,
        value=None,  # type: ignore[arg-type]
        formula=large_value_formula,
        dependencies=(base_key,),
        constraints=ConfigConstraints(min_value=min_value, max_value=max_value),
    )

    resolver = MockConfigResolver({base_key: base_value})

    with pytest.raises(
        expected_exception=ConfigSchemaError,
        match=f"{key_name}: derived value failed constraints",
    ):
        derived.evaluate(resolver=resolver)


def test_derived_config_key_evaluate_success() -> None:
    """Test successful formula evaluation."""
    key_name = f"{fake.word()}.{fake.word()}"
    base_key = f"{fake.word()}.{fake.word()}"
    base_value = fake.random_int(min=100, max=1000)
    multiplier = fake.pyfloat(min_value=0.1, max_value=2.0)

    def formula(cfg: ConfigResolver) -> float:
        value = cast(float, cfg.get(base_key))
        result: float = value * multiplier
        return result

    derived = DerivedConfigKey[float](
        name=key_name,
        type=float,
        value=None,  # type: ignore[arg-type]
        formula=formula,
        dependencies=(base_key,),
    )

    resolver = MockConfigResolver({base_key: base_value})
    result = derived.evaluate(resolver=resolver)

    expected = base_value * multiplier
    assert abs(result - expected) < 0.0001


def test_derived_config_key_evaluate_with_constraints_success() -> None:
    """Test successful formula evaluation with constraints."""
    key_name = f"{fake.word()}.{fake.word()}"
    base_key = f"{fake.word()}.{fake.word()}"
    base_value = fake.random_int(min=100, max=200)
    min_value = 0.0
    max_value = 200.0

    def formula(cfg: ConfigResolver) -> float:
        return cast(float, cfg.get(base_key)) * 0.5

    derived = DerivedConfigKey[float](
        name=key_name,
        type=float,
        value=None,  # type: ignore[arg-type]
        formula=formula,
        dependencies=(base_key,),
        constraints=ConfigConstraints(min_value=min_value, max_value=max_value),
    )

    resolver = MockConfigResolver({base_key: base_value})
    result = derived.evaluate(resolver=resolver)

    expected = base_value * 0.5
    assert abs(result - expected) < 0.0001
    assert result >= min_value
    assert result <= max_value


def test_derived_config_key_evaluate_with_multiple_dependencies() -> None:
    """Test formula evaluation with multiple dependencies."""
    key_name = f"{fake.word()}.{fake.word()}"
    dep1 = f"{fake.word()}.dep1"
    dep2 = f"{fake.word()}.dep2"
    dep3 = f"{fake.word()}.dep3"
    val1 = fake.pyfloat(min_value=1.0, max_value=100.0)
    val2 = fake.pyfloat(min_value=1.0, max_value=100.0)
    val3 = fake.pyfloat(min_value=1.0, max_value=100.0)

    def complex_formula(cfg: ConfigResolver) -> float:
        a = cast(float, cfg.get(dep1))
        b = cast(float, cfg.get(dep2))
        c = cast(float, cfg.get(dep3))
        return (a * b) / c + 10.0

    derived = DerivedConfigKey[float](
        name=key_name,
        type=float,
        value=None,  # type: ignore[arg-type]
        formula=complex_formula,
        dependencies=(dep1, dep2, dep3),
    )

    resolver = MockConfigResolver({dep1: val1, dep2: val2, dep3: val3})
    result = derived.evaluate(resolver=resolver)

    expected = (val1 * val2) / val3 + 10.0
    assert abs(result - expected) < 0.0001


def test_derived_config_key_evaluate_int_type() -> None:
    """Test formula evaluation returning int type."""
    key_name = f"{fake.word()}.{fake.word()}"
    base_key = f"{fake.word()}.{fake.word()}"
    base_value = fake.random_int(min=10, max=100)

    def int_formula(cfg: ConfigResolver) -> int:
        return cast(int, cfg.get(base_key)) * 2

    derived = DerivedConfigKey[int](
        name=key_name,
        type=int,
        value=None,  # type: ignore[arg-type]
        formula=int_formula,
        dependencies=(base_key,),
    )

    resolver = MockConfigResolver({base_key: base_value})
    result = derived.evaluate(resolver=resolver)

    assert result == base_value * 2
    assert isinstance(result, int)


def test_derived_config_key_evaluate_bool_type() -> None:
    """Test formula evaluation returning bool type."""
    key_name = f"{fake.word()}.{fake.word()}"
    base_key = f"{fake.word()}.{fake.word()}"
    base_value = fake.random_int(min=1, max=100)

    def bool_formula(cfg: ConfigResolver) -> bool:
        return cast(int, cfg.get(base_key)) > 50

    derived = DerivedConfigKey[bool](
        name=key_name,
        type=bool,
        value=None,  # type: ignore[arg-type]
        formula=bool_formula,
        dependencies=(base_key,),
    )

    resolver = MockConfigResolver({base_key: base_value})
    result = derived.evaluate(resolver=resolver)

    assert result == (base_value > 50)
    assert isinstance(result, bool)


def test_derived_config_key_evaluate_str_type() -> None:
    """Test formula evaluation returning str type."""
    key_name = f"{fake.word()}.{fake.word()}"
    base_key = f"{fake.word()}.{fake.word()}"
    base_value = fake.random_int(min=1, max=100)

    def str_formula(cfg: ConfigResolver) -> str:
        val = cast(int, cfg.get(base_key))
        return f"value_{val}"

    derived = DerivedConfigKey[str](
        name=key_name,
        type=str,
        value=None,  # type: ignore[arg-type]
        formula=str_formula,
        dependencies=(base_key,),
    )

    resolver = MockConfigResolver({base_key: base_value})
    result = derived.evaluate(resolver=resolver)

    assert result == f"value_{base_value}"
    assert isinstance(result, str)
